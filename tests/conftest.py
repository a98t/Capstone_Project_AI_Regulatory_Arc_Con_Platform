"""
pytest fixtures and shared test utilities.
"""

from __future__ import annotations

import os

# Disable slowapi rate limiting in tests so many requests don't hit 20/min cap
os.environ.setdefault("RATELIMIT_ENABLED", "0")

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.agents.state import AgentState, ComplianceReport


@pytest.fixture
def sample_compliance_report() -> ComplianceReport:
    return ComplianceReport(
        items=[
            {
                "article_ref": "СНиП 2.08.01-89 п.3.1",
                "doc_name": "СНиП 2.08.01-89",
                "doc_number": "2.08.01-89",
                "status": "VIOLATION",
                "description": "Minimum corridor width for residential buildings must be ≥ 1.4m.",
                "plain_language": "The corridor is too narrow.",
                "risk_level": "HIGH",
            },
            {
                "article_ref": "СП 14.13330.2018 п.6.2",
                "doc_name": "СП 14.13330.2018",
                "doc_number": "14.13330.2018",
                "status": "REQUIRES_ACTION",
                "description": "Seismic zone 7 requires reinforced frame for buildings > 5 floors.",
                "plain_language": "Seismic reinforcement required.",
                "risk_level": "MEDIUM",
            },
        ],
        total_norms=2,
        violations=1,
        requires_action=1,
        advisory=0,
        compliant=0,
        overall_risk="HIGH",
    )


@pytest.fixture
def sample_state(sample_compliance_report) -> AgentState:
    return AgentState(
        building_type="Residential",
        floors=9,
        city="Almaty",
        material="Reinforced concrete",
        purpose="Apartments",
        notes="",
        raw_query="Residential 9 floors Almaty Reinforced concrete Apartments.",
        session_id="test-session-123",
        retrieved_chunks=[],
        search_confidence=0.82,
        search_error=None,
        compliance_report=sample_compliance_report,
        norm_identifiers=["СНиП 2.08.01-89", "СП 14.13330.2018"],
        compliance_error=None,
        freshness_verdicts={},
        mcp_available=False,
        update_error=None,
        final_response=None,
        explanation_error=None,
        agent_trace=[],
        errors=[],
        total_duration_ms=0,
    )


@pytest.fixture
def mock_llm():
    """Mock LLM that returns deterministic JSON responses."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content='{"items": [], "total_norms": 0, "violations": 0, "requires_action": 0, '
                '"advisory": 0, "compliant": 0, "overall_risk": "CLEAR"}'
    )
    return mock


@pytest.fixture
def mock_retriever_empty():
    """Mock retriever that returns no results."""
    with patch("src.rag.retriever.search", return_value=[]) as mock:
        yield mock


@pytest.fixture
def mock_retriever_with_chunks():
    """Mock retriever that returns sample chunks."""
    from src.rag.retriever import RetrievedChunk

    chunks = [
        RetrievedChunk(
            text="Минимальная ширина коридора жилых зданий должна быть не менее 1,4 м.",
            score=0.88,
            article_ref="СНиП 2.08.01-89 п.3.1",
            doc_name="СНиП 2.08.01-89",
            doc_number="2.08.01-89",
            doc_type="СНиП",
            year=1989,
            language="ru",
            is_low_confidence=False,
        )
    ]
    with patch("src.rag.retriever.search", return_value=chunks) as mock:
        yield mock, chunks
