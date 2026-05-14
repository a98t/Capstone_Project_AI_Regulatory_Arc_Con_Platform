"""
Embedder — generates dense vector embeddings for document chunks.

Uses BAAI/bge-m3 (multilingual, 1024-dim) which supports Russian and Kazakh.
Results are cached to disk so documents are never re-embedded on restart.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List

import diskcache
import structlog
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.ingestion.chunker import DocumentChunk

log = structlog.get_logger(__name__)

# Global model instance (loaded once per process)
_model: SentenceTransformer | None = None
_cache: diskcache.Cache | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        log.info("loading_embedding_model", model=settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        log.info("embedding_model_loaded", model=settings.embedding_model)
    return _model


def _get_cache() -> diskcache.Cache:
    global _cache
    if _cache is None:
        cache_dir = Path(settings.cache_dir) / "embeddings"
        cache_dir.mkdir(parents=True, exist_ok=True)
        _cache = diskcache.Cache(str(cache_dir), size_limit=10 * 1024 ** 3)  # 10 GB
    return _cache


def _cache_key(text: str, model_name: str) -> str:
    content = f"{model_name}::{text}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts. Returns a list of float vectors.
    Hits disk cache first; computes only uncached texts.
    """
    model = _get_model()
    cache = _get_cache()
    model_name = settings.embedding_model

    results: List[List[float] | None] = [None] * len(texts)
    uncached_indices: List[int] = []
    uncached_texts: List[str] = []

    for i, text in enumerate(texts):
        key = _cache_key(text, model_name)
        cached = cache.get(key)
        if cached is not None:
            results[i] = cached
        else:
            uncached_indices.append(i)
            uncached_texts.append(text)

    if uncached_texts:
        log.info("computing_embeddings", count=len(uncached_texts))
        embeddings = model.encode(
            uncached_texts,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=len(uncached_texts) > 50,
            normalize_embeddings=True,  # cosine similarity requires normalized vectors
        ).tolist()

        for i, embedding in zip(uncached_indices, embeddings):
            key = _cache_key(texts[i], model_name)
            cache.set(key, embedding)
            results[i] = embedding

    return results  # type: ignore[return-value]


def embed_chunks(chunks: List[DocumentChunk]) -> List[List[float]]:
    """Embed a list of DocumentChunk objects using their text content."""
    texts = [chunk.text for chunk in chunks]
    return embed_texts(texts)


def embed_query(query: str) -> List[float]:
    """Embed a single query string for retrieval."""
    # bge-m3 benefits from a query prefix for retrieval tasks
    prefixed = f"Represent this sentence for searching relevant passages: {query}"
    return embed_texts([prefixed])[0]
