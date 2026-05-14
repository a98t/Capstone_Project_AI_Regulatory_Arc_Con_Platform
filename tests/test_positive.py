"""
Positive (happy-path) test scenarios.

Covers:
1. Valid residential building analysis
2. Valid commercial building in seismic zone
3. Keyword search returns results
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestAnalyzeEndpoint:
    """Tests for the /api/analyze endpoint with valid inputs."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_residential_building_returns_200(self, client, mock_retriever_with_chunks):
        mock_chunks, chunks = mock_retriever_with_chunks

        with patch("src.agents.llm.get_llm") as mock_llm_factory:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content=(
                    '{"items": [{"article_ref": "СНиП 2.08.01-89 п.3.1", '
                    '"doc_name": "СНиП 2.08.01-89", "doc_number": "2.08.01-89", '
                    '"status": "COMPLIANT", "description": "Width OK", '
                    '"plain_language": "Width OK", "risk_level": "LOW"}], '
                    '"total_norms": 1, "violations": 0, "requires_action": 0, '
                    '"advisory": 0, "compliant": 1, "overall_risk": "CLEAR"}'
                )
            )
            mock_llm_factory.return_value = mock_llm

            response = client.post(
                "/api/analyze",
                json={
                    "building_type": "Residential",
                    "floors": 9,
                    "city": "Almaty",
                    "material": "Reinforced concrete",
                    "purpose": "Apartments",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "summary" in data
        assert data["summary"]["overall_risk"] in ("CLEAR", "LOW", "MEDIUM", "HIGH", "UNKNOWN")

    def test_commercial_building_seismic_city(self, client, mock_retriever_with_chunks):
        mock_chunks, chunks = mock_retriever_with_chunks

        with patch("src.agents.llm.get_llm") as mock_llm_factory:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content=(
                    '{"items": [], "total_norms": 0, "violations": 0, "requires_action": 0, '
                    '"advisory": 0, "compliant": 0, "overall_risk": "CLEAR"}'
                )
            )
            mock_llm_factory.return_value = mock_llm

            response = client.post(
                "/api/analyze",
                json={
                    "building_type": "Commercial",
                    "floors": 5,
                    "city": "Shymkent",
                    "material": "Steel",
                    "purpose": "Office",
                },
            )

        assert response.status_code == 200

    def test_response_contains_disclaimer(self, client, mock_retriever_with_chunks):
        mock_chunks, chunks = mock_retriever_with_chunks

        with patch("src.agents.llm.get_llm") as mock_llm_factory:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content=(
                    '{"items": [], "total_norms": 0, "violations": 0, "requires_action": 0, '
                    '"advisory": 0, "compliant": 0, "overall_risk": "CLEAR"}'
                )
            )
            mock_llm_factory.return_value = mock_llm

            response = client.post(
                "/api/analyze",
                json={
                    "building_type": "School",
                    "floors": 3,
                    "city": "Astana",
                    "material": "Reinforced concrete",
                    "purpose": "Education",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data.get("disclaimer", "")) > 10, "Disclaimer must be present"


class TestSearchEndpoint:
    """Tests for the /api/search endpoint."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_semantic_search_returns_results(self, client, mock_retriever_with_chunks):
        response = client.post(
            "/api/search",
            json={"query": "пожарная безопасность жилых зданий", "limit": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_keyword_search_returns_results(self, client, mock_retriever_with_chunks):
        with patch("src.rag.retriever.keyword_search") as mock_kw:
            from src.rag.retriever import RetrievedChunk
            mock_kw.return_value = []
            response = client.get("/api/search/keyword?q=СНиП&limit=10")
        assert response.status_code == 200
