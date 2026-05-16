#!/usr/bin/env python
"""
Check the current state of the Qdrant index — collection stats and sample docs.

Usage:
    python scripts/check_index.py
    python scripts/check_index.py --sample 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.ingestion.indexer import get_indexed_hashes
from src.qdrant_client_factory import create_qdrant_client


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Qdrant index status.")
    parser.add_argument("--sample", type=int, default=3, help="Number of sample points to display")
    args = parser.parse_args()

    try:
        client = create_qdrant_client()
        info = client.get_collection(settings.qdrant_collection)

        # vectors_count was removed in newer Qdrant server versions — use points_count
        vectors = getattr(info, "vectors_count", None) or getattr(info, "points_count", 0)

        print(f"\n{'='*50}")
        print(f"Collection: {settings.qdrant_collection}")
        print(f"Vectors:    {vectors:,}")
        print(f"Points:     {info.points_count:,}")
        print(f"Status:     {info.status}")
        print(f"{'='*50}\n")

        # Indexed document hashes
        hashes = get_indexed_hashes(client)
        print(f"Unique documents indexed: {len(hashes)}")

        # Sample points
        if args.sample > 0:
            results, _ = client.scroll(
                collection_name=settings.qdrant_collection,
                limit=args.sample,
                with_payload=True,
                with_vectors=False,
            )
            print(f"\nSample {len(results)} points:")
            for point in results:
                p = point.payload or {}
                print(
                    f"  [{p.get('doc_type', '?')}] {p.get('doc_name', '?')[:50]} "
                    f"| {p.get('article_ref', '')} | {p.get('year', '?')}"
                )

    except Exception as exc:
        print(f"ERROR: Cannot connect to Qdrant: {exc}")
        print(f"  Host: {settings.qdrant_host}:{settings.qdrant_port}")
        print("  Is Docker running? Try: docker compose up -d")
        sys.exit(1)


if __name__ == "__main__":
    main()
