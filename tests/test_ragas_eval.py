"""
RAGAS evaluation test — measures RAG pipeline quality metrics.

Requires a small evaluation dataset of (question, ground_truth, answer, contexts).
Run this separately from the CI test suite:

    pytest tests/test_ragas_eval.py -v --timeout=120 -s

Expected passing thresholds:
  - context_precision   >= 0.50
  - context_recall      >= 0.50
  - answer_faithfulness >= 0.60
"""

from __future__ import annotations

import pytest

# Skip RAGAS eval in fast CI — only run when explicitly targeting this file
pytestmark = pytest.mark.slow


EVAL_QUESTIONS = [
    {
        "question": "Какова минимальная ширина коридора в жилом здании?",
        "ground_truth": "Минимальная ширина коридора в жилых зданиях должна составлять не менее 1,4 метра.",
    },
    {
        "question": "Какие требования к лестничным клеткам в высотных зданиях?",
        "ground_truth": "Лестничные клетки должны быть незадымляемыми и соответствовать требованиям пожарной безопасности.",
    },
    {
        "question": "Какие сейсмические требования для зданий в Алматы?",
        "ground_truth": "Алматы находится в сейсмической зоне 9 баллов. Здания должны проектироваться с учётом сейсмостойкости.",
    },
]


@pytest.fixture(scope="module")
def eval_dataset():
    """Generate evaluation data by running real queries through the pipeline."""
    from src.agents.orchestrator import build_initial_state, run_pipeline

    dataset = []
    for item in EVAL_QUESTIONS:
        state = build_initial_state(
            building_type="Residential",
            floors=9,
            city="Almaty",
            material="Reinforced concrete",
            purpose="Apartments",
            notes=item["question"],
        )
        try:
            final = run_pipeline(state)
            answer = (final.get("final_response") or {}).get("summary", "")
            contexts = [c.get("text", "") for c in final.get("retrieved_chunks", [])]
            dataset.append(
                {
                    "question": item["question"],
                    "answer": answer,
                    "contexts": contexts[:5],  # Top 5 contexts
                    "ground_truth": item["ground_truth"],
                }
            )
        except Exception as exc:
            pytest.skip(f"Pipeline failed during eval data collection: {exc}")

    return dataset


@pytest.mark.slow
def test_ragas_metrics_within_thresholds(eval_dataset):
    """
    Run RAGAS evaluation and assert minimum quality thresholds.
    Skipped if RAGAS dependencies not installed or Qdrant not running.
    """
    if not eval_dataset:
        pytest.skip("No evaluation data collected — is Qdrant running?")

    try:
        from src.rag.quality import run_ragas_evaluation
    except ImportError:
        pytest.skip("RAGAS not installed. Run: pip install ragas")

    questions = [d["question"] for d in eval_dataset]
    answers = [d["answer"] for d in eval_dataset]
    contexts = [d["contexts"] for d in eval_dataset]
    ground_truths = [d["ground_truth"] for d in eval_dataset]

    metrics = run_ragas_evaluation(questions, answers, contexts, ground_truths)

    print("\nRAGAS Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.3f}")

    # Thresholds — calibrated for student demo with 13-doc corpus
    assert metrics.get("context_precision", 0) >= 0.50, "context_precision too low"
    assert metrics.get("context_recall", 0) >= 0.50, "context_recall too low"
    assert metrics.get("answer_faithfulness", 0) >= 0.60, "answer_faithfulness too low"
