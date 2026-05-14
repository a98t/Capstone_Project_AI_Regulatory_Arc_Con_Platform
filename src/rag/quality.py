"""
RAG quality helpers — confidence scoring and RAGAS evaluation utilities.
"""

from __future__ import annotations

from typing import List

from src.config import settings
from src.rag.retriever import RetrievedChunk


def compute_search_confidence(chunks: List[RetrievedChunk]) -> float:
    """
    Compute an overall confidence score for a set of retrieved chunks.
    Returns the average similarity score of chunks above the threshold.
    Returns 0.0 if no chunks pass the threshold.
    """
    passing = [c for c in chunks if not c.is_low_confidence]
    if not passing:
        return 0.0
    return sum(c.score for c in passing) / len(passing)


def filter_confident_chunks(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    """Return only chunks that meet the confidence threshold."""
    return [c for c in chunks if not c.is_low_confidence]


def format_chunks_for_llm(chunks: List[RetrievedChunk]) -> str:
    """
    Format retrieved chunks into a structured context string for LLM prompts.
    Each chunk is prefixed with its source reference.
    """
    if not chunks:
        return "Нет релевантных нормативных документов в базе данных."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        year_str = f" ({chunk.year})" if chunk.year else ""
        confidence_flag = " [низкая достоверность]" if chunk.is_low_confidence else ""
        parts.append(
            f"[{i}] Источник: {chunk.doc_name}{year_str}, {chunk.article_ref}{confidence_flag}\n"
            f"{chunk.text}\n"
        )
    return "\n---\n".join(parts)


def run_ragas_evaluation(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: List[str],
) -> dict:
    """
    Run RAGAS evaluation metrics on a set of QA pairs.
    Returns a dict of metric scores.

    Used in test_ragas_eval.py — requires RAGAS installed.
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_faithfulness,
            context_recall,
            context_precision,
        )

        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
        dataset = Dataset.from_dict(data)
        result = evaluate(
            dataset,
            metrics=[answer_faithfulness, context_recall, context_precision],
        )
        return result.to_pandas().to_dict(orient="records")[0]
    except ImportError:
        return {"error": "ragas not installed"}
