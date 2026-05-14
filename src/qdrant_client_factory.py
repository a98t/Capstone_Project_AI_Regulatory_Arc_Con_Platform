"""
Centralized Qdrant client factory.

Keeps client options consistent across ingestion, retrieval, and health checks.
"""

from __future__ import annotations

from qdrant_client import QdrantClient

from src.config import settings


def create_qdrant_client() -> QdrantClient:
    """Create a configured Qdrant client instance."""
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        # Dev environments often run older server images; this avoids noisy warnings.
        check_compatibility=False,
    )
