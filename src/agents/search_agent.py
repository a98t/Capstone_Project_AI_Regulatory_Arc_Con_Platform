"""
Search Agent — retrieves relevant regulatory norm chunks from Qdrant via RAG.

Input:  building parameters from AgentState
Output: retrieved_chunks, search_confidence
"""

from __future__ import annotations

import time
from typing import Any, Dict

import structlog

from src.agents.state import AgentState, AgentStep
from src.config import settings
from src.rag.quality import compute_search_confidence
from src.rag.retriever import search

log = structlog.get_logger(__name__)


def _build_search_query(state: AgentState) -> str:
    """Construct a natural language query from building parameters."""
    parts = []
    if state.get("building_type"):
        parts.append(state["building_type"])
    if state.get("floors"):
        parts.append(f"{state['floors']} этажей")
    if state.get("city"):
        parts.append(state["city"])
    if state.get("material"):
        parts.append(state["material"])
    if state.get("purpose"):
        parts.append(state["purpose"])
    if state.get("notes"):
        parts.append(state["notes"])

    base = " ".join(parts)
    # Append domain context to improve retrieval specificity
    return f"Нормативные требования для: {base}. Применимые СНиП, СП, ҚНжЕ нормы."


def search_agent(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Search Agent.

    Queries the Qdrant vector store for regulation chunks matching
    the user's building parameters. Applies confidence threshold filtering.
    """
    start = time.monotonic()
    log.info("search_agent_start", session_id=state.get("session_id"))

    try:
        query = _build_search_query(state)
        chunks = search(query=query, top_k=settings.rag_top_k)

        # Also run a secondary query focused on the city for region-specific norms
        city = state.get("city", "")
        if city:
            city_chunks = search(
                query=f"Сейсмическая зона нормы {city} Казахстан строительство",
                top_k=3,
            )
            # Merge, deduplicate by article_ref + doc_name
            seen = {(c.doc_name, c.article_ref) for c in chunks}
            for c in city_chunks:
                if (c.doc_name, c.article_ref) not in seen:
                    chunks.append(c)
                    seen.add((c.doc_name, c.article_ref))

        confidence = compute_search_confidence(chunks)
        duration_ms = int((time.monotonic() - start) * 1000)

        step: AgentStep = {
            "agent": "SearchAgent",
            "status": "done",
            "message": f"Retrieved {len(chunks)} chunks (confidence: {confidence:.2f})",
            "duration_ms": duration_ms,
        }

        log.info(
            "search_agent_done",
            chunks=len(chunks),
            confidence=confidence,
            duration_ms=duration_ms,
        )

        return {
            "retrieved_chunks": chunks,
            "search_confidence": confidence,
            "search_error": None,
            "agent_trace": state.get("agent_trace", []) + [step],
        }

    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        log.exception("search_agent_error", error=str(exc))
        step: AgentStep = {
            "agent": "SearchAgent",
            "status": "error",
            "message": str(exc),
            "duration_ms": duration_ms,
        }
        return {
            "retrieved_chunks": [],
            "search_confidence": 0.0,
            "search_error": str(exc),
            "agent_trace": state.get("agent_trace", []) + [step],
            "errors": state.get("errors", []) + [f"SearchAgent: {exc}"],
        }
