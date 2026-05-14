"""
Qdrant retriever — semantic search interface for the agent pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from src.config import settings
from src.ingestion.embedder import embed_query

log = structlog.get_logger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    score: float                # cosine similarity [0, 1]
    article_ref: str
    doc_name: str
    doc_number: str
    doc_type: str
    year: Optional[int]
    language: str
    is_low_confidence: bool     # True if score < threshold


def _get_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def search(
    query: str,
    top_k: int = None,
    doc_type_filter: Optional[str] = None,
    language_filter: Optional[str] = None,
) -> List[RetrievedChunk]:
    """
    Perform semantic search against the Qdrant collection.

    Args:
        query: Natural language query (Russian, Kazakh, or English)
        top_k: Number of results to return (defaults to settings.rag_top_k)
        doc_type_filter: Optional filter by document type (e.g. "СНиП")
        language_filter: Optional filter by language (e.g. "ru")

    Returns:
        List of RetrievedChunk sorted by descending similarity score.
    """
    if top_k is None:
        top_k = settings.rag_top_k

    client = _get_client()
    query_vector = embed_query(query)

    # Build optional payload filter
    qdrant_filter = None
    conditions = []
    if doc_type_filter:
        conditions.append(
            FieldCondition(key="doc_type", match=MatchValue(value=doc_type_filter))
        )
    if language_filter:
        conditions.append(
            FieldCondition(key="language", match=MatchValue(value=language_filter))
        )
    if conditions:
        qdrant_filter = Filter(must=conditions)

    # Use query_points (Qdrant client >= 1.7) with fallback to legacy search
    try:
        response = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        results = response.points
    except AttributeError:
        # Older qdrant-client fallback
        results = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

    chunks: List[RetrievedChunk] = []
    for hit in results:
        payload = hit.payload or {}
        chunks.append(
            RetrievedChunk(
                text=payload.get("text", ""),
                score=hit.score,
                article_ref=payload.get("article_ref", "—"),
                doc_name=payload.get("doc_name", "Unknown"),
                doc_number=payload.get("doc_number", ""),
                doc_type=payload.get("doc_type", "UNKNOWN"),
                year=payload.get("year"),
                language=payload.get("language", "ru"),
                is_low_confidence=hit.score < settings.rag_confidence_threshold,
            )
        )

    log.info(
        "search_complete",
        query=query[:80],
        results=len(chunks),
        low_confidence=sum(1 for c in chunks if c.is_low_confidence),
    )
    return chunks


def keyword_search(keyword: str, limit: int = 20) -> List[dict]:
    """
    Basic keyword search using Qdrant's scroll + payload filter.
    Used for legacy-mode document directory browsing.
    """
    client = _get_client()
    results, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="doc_name",
                    match=MatchValue(value=keyword),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [r.payload for r in results if r.payload]
