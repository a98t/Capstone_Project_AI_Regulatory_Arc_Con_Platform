"""
LangGraph Orchestrator — defines the multi-agent state machine.

Pipeline:
  START → search_agent → compliance_agent → update_agent → explanation_agent → END

The orchestrator also exposes a streaming interface for real-time
agent status updates via SSE.
"""

from __future__ import annotations

import time
import uuid
from typing import AsyncGenerator

import structlog
from langgraph.graph import END, START, StateGraph

from src.agents.compliance_agent import compliance_agent
from src.agents.explanation_agent import explanation_agent
from src.agents.search_agent import search_agent
from src.agents.state import AgentState
from src.agents.update_agent import update_agent

log = structlog.get_logger(__name__)


def _build_graph() -> StateGraph:
    """Construct and compile the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("search_agent", search_agent)
    graph.add_node("compliance_agent", compliance_agent)
    graph.add_node("update_agent", update_agent)
    graph.add_node("explanation_agent", explanation_agent)

    # Define linear pipeline edges
    graph.add_edge(START, "search_agent")
    graph.add_edge("search_agent", "compliance_agent")
    graph.add_edge("compliance_agent", "update_agent")
    graph.add_edge("update_agent", "explanation_agent")
    graph.add_edge("explanation_agent", END)

    return graph.compile()


# Compiled graph — built once at import time
_graph = _build_graph()


def build_initial_state(
    building_type: str,
    floors: int,
    city: str,
    material: str,
    purpose: str,
    notes: str = "",
) -> AgentState:
    """Construct the initial AgentState from user inputs."""
    raw_query = (
        f"{building_type}, {floors} floors, {city}, {material}, {purpose}. {notes}"
    ).strip()

    return AgentState(
        # Input
        building_type=building_type,
        floors=floors,
        city=city,
        material=material,
        purpose=purpose,
        notes=notes,
        raw_query=raw_query,
        session_id=str(uuid.uuid4()),
        # Search Agent output (empty until agent runs)
        retrieved_chunks=[],
        search_confidence=0.0,
        search_error=None,
        # Compliance Agent output
        compliance_report=None,
        norm_identifiers=[],
        compliance_error=None,
        # Update Agent output
        freshness_verdicts={},
        mcp_available=False,
        update_error=None,
        # Explanation Agent output
        final_response=None,
        explanation_error=None,
        # Metadata
        agent_trace=[],
        errors=[],
        total_duration_ms=0,
    )


def run_pipeline(initial_state: AgentState) -> AgentState:
    """
    Run the full multi-agent pipeline synchronously.
    Returns the final AgentState with all agent outputs populated.
    """
    start = time.monotonic()
    log.info("pipeline_start", session_id=initial_state["session_id"])

    try:
        final_state = _graph.invoke(initial_state)
        duration_ms = int((time.monotonic() - start) * 1000)
        final_state["total_duration_ms"] = duration_ms
        log.info(
            "pipeline_complete",
            session_id=initial_state["session_id"],
            duration_ms=duration_ms,
            errors=len(final_state.get("errors", [])),
        )
        return final_state
    except Exception as exc:
        log.exception("pipeline_error", error=str(exc))
        raise


async def stream_pipeline(initial_state: AgentState) -> AsyncGenerator[dict, None]:
    """
    Stream agent progress events as they complete.

    Yields dicts with structure:
      {"event": "agent_update", "agent": str, "status": str, "message": str}
      {"event": "complete", "session_id": str}
      {"event": "error", "message": str}

    Used by the FastAPI SSE endpoint to push real-time updates to the frontend.
    """
    log.info("pipeline_stream_start", session_id=initial_state["session_id"])
    seen_agents: set[str] = set()

    try:
        async for event in _graph.astream(initial_state):
            # LangGraph emits events keyed by node name
            for node_name, node_output in event.items():
                if node_name in ("__start__", "__end__"):
                    continue

                trace = node_output.get("agent_trace", [])
                for step in trace:
                    agent_name = step.get("agent", node_name)
                    if agent_name not in seen_agents:
                        seen_agents.add(agent_name)
                        yield {
                            "event": "agent_update",
                            "agent": agent_name,
                            "status": step.get("status", "done"),
                            "message": step.get("message", ""),
                            "duration_ms": step.get("duration_ms", 0),
                        }

        yield {"event": "complete", "session_id": initial_state["session_id"]}

    except Exception as exc:
        log.exception("pipeline_stream_error", error=str(exc))
        yield {"event": "error", "message": str(exc)}
