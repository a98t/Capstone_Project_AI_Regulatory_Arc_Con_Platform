"""
Article-aware text chunker for Kazakhstan construction regulatory documents.

Regulatory documents (СНиП, СП, ҚНжЕ) have a structured hierarchy:
  Chapter (Раздел/Глава) → Section (Пункт) → Sub-item (п.п.)

This chunker splits on article/section boundaries rather than arbitrary
character counts, preserving the regulatory context within each chunk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from src.ingestion.parser import ParsedDocument

# Patterns that indicate a new section/article starts
_SECTION_PATTERNS = [
    re.compile(r"^\s*Раздел\s+\d+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Глава\s+\d+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*\d+\s+[А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s]{5,}", re.MULTILINE),  # "1 Область применения"
    re.compile(r"^\s*\d+\.\d+\.?\s+", re.MULTILINE),  # "1.1 " or "1.1. "
    re.compile(r"^\s*п\.?\s*\d+\.\d+", re.MULTILINE | re.IGNORECASE),          # "п. 1.1"
    re.compile(r"^\s*\d+\)\s+", re.MULTILINE),                                  # "1) "
]

# Article reference extraction for metadata
_ARTICLE_REF_PATTERN = re.compile(
    r"(?:п\.?\s*|пункт\s+|раздел\s+|глава\s+)?(\d+(?:\.\d+)*\.?)",
    re.IGNORECASE,
)

MAX_CHUNK_TOKENS = 800   # approximate token count (1 token ≈ 4 chars for Russian)
CHUNK_OVERLAP_CHARS = 200


@dataclass
class DocumentChunk:
    chunk_index: int
    text: str
    article_ref: str          # e.g. "п. 8.4" or "Раздел 3"
    doc_name: str
    doc_number: str
    doc_type: str
    year: Optional[int]
    language: str
    doc_hash: str
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)


def _find_split_points(text: str) -> List[int]:
    """
    Find all positions in text where a new section/article begins.
    Returns sorted list of character positions.
    """
    positions = set()
    for pattern in _SECTION_PATTERNS:
        for match in pattern.finditer(text):
            positions.add(match.start())
    return sorted(positions)


def _extract_article_ref(text: str) -> str:
    """Extract the leading article reference from a chunk's text."""
    first_line = text.strip().split("\n")[0][:100]
    match = _ARTICLE_REF_PATTERN.search(first_line)
    if match:
        return first_line[:60].strip()
    return first_line[:60].strip() or "—"


def _merge_small_splits(splits: List[str], max_chars: int) -> List[str]:
    """
    Merge consecutive splits that are too small (< 150 chars)
    and split any single chunk that exceeds max_chars.
    """
    merged: List[str] = []
    buffer = ""

    for split in splits:
        if not split.strip():
            continue
        if len(buffer) + len(split) < max_chars:
            buffer += ("\n" if buffer else "") + split
        else:
            if buffer:
                merged.append(buffer)
            # If the split itself is too large, break it at sentence boundaries
            if len(split) > max_chars:
                sentences = re.split(r"(?<=[.!?])\s+", split)
                sub_buffer = ""
                for sentence in sentences:
                    if len(sub_buffer) + len(sentence) < max_chars:
                        sub_buffer += (" " if sub_buffer else "") + sentence
                    else:
                        if sub_buffer:
                            merged.append(sub_buffer)
                        sub_buffer = sentence
                if sub_buffer:
                    merged.append(sub_buffer)
            else:
                buffer = split
    if buffer:
        merged.append(buffer)

    return merged


def chunk_document(doc: ParsedDocument) -> List[DocumentChunk]:
    """
    Split a ParsedDocument into DocumentChunks at article/section boundaries.
    """
    text = doc.full_text
    split_points = _find_split_points(text)

    # No structural markers found → fall back to character-based splitting
    if not split_points:
        raw_splits = [
            text[i : i + MAX_CHUNK_TOKENS * 4]
            for i in range(0, len(text), MAX_CHUNK_TOKENS * 4 - CHUNK_OVERLAP_CHARS)
        ]
    else:
        # Build raw splits from split points
        raw_splits = []
        prev = 0
        for pos in split_points:
            if pos > prev:
                raw_splits.append(text[prev:pos])
            prev = pos
        if prev < len(text):
            raw_splits.append(text[prev:])

    merged_splits = _merge_small_splits(raw_splits, max_chars=MAX_CHUNK_TOKENS * 4)

    chunks: List[DocumentChunk] = []
    for idx, chunk_text in enumerate(merged_splits):
        if not chunk_text.strip():
            continue
        chunks.append(
            DocumentChunk(
                chunk_index=idx,
                text=chunk_text.strip(),
                article_ref=_extract_article_ref(chunk_text),
                doc_name=doc.title,
                doc_number=doc.doc_number,
                doc_type=doc.doc_type,
                year=doc.year,
                language=doc.language,
                doc_hash=doc.doc_hash,
            )
        )

    return chunks
