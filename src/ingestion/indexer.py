"""
Qdrant indexer — ingests DocumentChunks with embeddings into Qdrant.

Features:
- Skip already-indexed documents (by doc_hash)
- Batch upsert for efficiency
- Rich payload stored per vector for filtered retrieval
"""

from __future__ import annotations

from typing import List
from uuid import uuid4

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from src.config import settings
from src.ingestion.chunker import DocumentChunk
from src.ingestion.embedder import embed_chunks

log = structlog.get_logger(__name__)

VECTOR_SIZE = 1024  # bge-m3 output dimension
BATCH_SIZE = 64


def _get_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(client: QdrantClient) -> None:
    """Create the Qdrant collection if it does not already exist."""
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        log.info("collection_created", name=settings.qdrant_collection)
    else:
        log.info("collection_exists", name=settings.qdrant_collection)


def get_indexed_hashes(client: QdrantClient) -> set[str]:
    """
    Retrieve all doc_hash values already stored in Qdrant.
    Used to skip re-indexing unchanged documents.
    """
    hashes: set[str] = set()
    offset = None
    while True:
        results, next_offset = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=1000,
            offset=offset,
            with_payload=["doc_hash"],
            with_vectors=False,
        )
        for point in results:
            if point.payload and "doc_hash" in point.payload:
                hashes.add(point.payload["doc_hash"])
        if next_offset is None:
            break
        offset = next_offset
    return hashes


def index_chunks(chunks: List[DocumentChunk]) -> int:
    """
    Embed and upsert chunks into Qdrant.
    Returns the number of points successfully indexed.
    """
    if not chunks:
        return 0

    client = _get_client()
    ensure_collection(client)

    embeddings = embed_chunks(chunks)
    points: List[PointStruct] = []

    for chunk, embedding in zip(chunks, embeddings):
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "text": chunk.text,
                "article_ref": chunk.article_ref,
                "doc_name": chunk.doc_name,
                "doc_number": chunk.doc_number,
                "doc_type": chunk.doc_type,
                "year": chunk.year,
                "language": chunk.language,
                "doc_hash": chunk.doc_hash,
                "chunk_index": chunk.chunk_index,
                "char_count": chunk.char_count,
            },
        )
        points.append(point)

    # Batch upsert
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        client.upsert(collection_name=settings.qdrant_collection, points=batch)
        log.info("indexed_batch", start=i, end=i + len(batch))

    log.info("indexing_complete", total_points=len(points))
    return len(points)


def get_collection_stats() -> dict:
    """Return basic stats about the current collection."""
    client = _get_client()
    info = client.get_collection(settings.qdrant_collection)
    return {
        "collection": settings.qdrant_collection,
        "vectors_count": info.vectors_count,
        "indexed_vectors_count": info.indexed_vectors_count,
        "status": str(info.status),
    }
