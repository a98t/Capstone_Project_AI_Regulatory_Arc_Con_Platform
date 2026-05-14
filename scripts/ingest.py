#!/usr/bin/env python
"""
CLI ingestion pipeline — parse PDFs, chunk, embed, and index to Qdrant.

Usage:
    python scripts/ingest.py --dir data/regulations
    python scripts/ingest.py --dir data/regulations --batch-size 16
    python scripts/ingest.py --dir data/regulations --dry-run
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog

from src.ingestion.chunker import chunk_document
from src.ingestion.indexer import ensure_collection, get_indexed_hashes, index_chunks
from src.ingestion.parser import parse_pdf, parse_text_file

log = structlog.get_logger(__name__)


def ingest_directory(doc_dir: Path, batch_size: int = 32, dry_run: bool = False) -> None:
    pdf_files = list(doc_dir.rglob("*.pdf"))
    txt_files = list(doc_dir.rglob("*.txt"))
    all_files = pdf_files + txt_files
    log.info("ingestion_start", total_files=len(all_files), pdfs=len(pdf_files), txt=len(txt_files), dry_run=dry_run)

    if not all_files:
        print(f"No PDF or TXT files found in {doc_dir}")
        return

    if not dry_run:
        from qdrant_client import QdrantClient
        from src.config import settings
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        ensure_collection(client)
        already_indexed = get_indexed_hashes(client)
    else:
        client = None
        already_indexed = set()

    stats = {"parsed": 0, "skipped": 0, "failed": 0, "chunks_indexed": 0}
    start = time.monotonic()

    for i, file_path in enumerate(all_files, 1):
        try:
            if file_path.suffix.lower() == ".pdf":
                doc = parse_pdf(file_path)
            else:
                doc = parse_text_file(file_path)

            if doc is None:
                log.warning("parse_failed", file=str(file_path))
                stats["failed"] += 1
                continue

            if doc.doc_hash in already_indexed:
                log.debug("already_indexed", file=file_path.name)
                stats["skipped"] += 1
                continue

            chunks = chunk_document(doc)
            log.info(
                "document_parsed",
                file=file_path.name,
                chunks=len(chunks),
                method=doc.extraction_method,
            )

            if not dry_run:
                indexed = index_chunks(chunks)
                stats["chunks_indexed"] += indexed

            stats["parsed"] += 1
            already_indexed.add(doc.doc_hash)

        except Exception as exc:
            log.exception("ingest_error", file=str(file_path), error=str(exc))
            stats["failed"] += 1

        # Progress report every 50 docs
        if i % 50 == 0:
            elapsed = time.monotonic() - start
            print(f"  Progress: {i}/{len(all_files)} | {elapsed:.0f}s elapsed")

    elapsed = time.monotonic() - start
    print(
        f"\nIngestion complete in {elapsed:.1f}s\n"
        f"  Parsed:   {stats['parsed']}\n"
        f"  Skipped:  {stats['skipped']} (already indexed)\n"
        f"  Failed:   {stats['failed']}\n"
        f"  Chunks:   {stats['chunks_indexed']}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest regulatory PDF documents into the Qdrant vector database."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        required=True,
        help="Directory containing PDF files (searched recursively)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of chunks per embedding batch (default: 32)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk without writing to Qdrant",
    )

    args = parser.parse_args()

    if not args.dir.exists():
        print(f"ERROR: Directory '{args.dir}' does not exist.")
        sys.exit(1)

    ingest_directory(args.dir, batch_size=args.batch_size, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
