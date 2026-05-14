"""
/api/search — legacy keyword and semantic search endpoint.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Request

from src.api.middleware import limiter
from src.api.models import SearchRequest, SearchResponse, SearchResult
from src.rag.retriever import search, keyword_search

log = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
@limiter.limit("60/minute")
async def semantic_search_endpoint(request: Request, body: SearchRequest) -> SearchResponse:
    """Semantic vector search over the regulatory document index."""
    chunks = search(query=body.query, top_k=body.limit)

    results = [
        SearchResult(
            doc_name=c.doc_name,
            doc_type=c.doc_type,
            year=c.year,
            article_ref=c.article_ref,
            score=round(c.score, 4),
            snippet=c.text[:400],
        )
        for c in chunks
    ]

    return SearchResponse(results=results, total=len(results))


@router.get("/search/keyword", response_model=SearchResponse)
@limiter.limit("60/minute")
async def keyword_search_endpoint(request: Request, q: str, limit: int = 20) -> SearchResponse:
    """Keyword-based search (legacy mode compatible with derek-info.kz)."""
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=422, detail="Query parameter 'q' is required.")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="'limit' must be between 1 and 100.")

    chunks = keyword_search(keyword=q.strip(), limit=limit)

    results = [
        SearchResult(
            doc_name=c.doc_name,
            doc_type=c.doc_type,
            year=c.year,
            article_ref=c.article_ref,
            score=round(c.score, 4),
            snippet=c.text[:400],
        )
        for c in chunks
    ]

    return SearchResponse(results=results, total=len(results))
