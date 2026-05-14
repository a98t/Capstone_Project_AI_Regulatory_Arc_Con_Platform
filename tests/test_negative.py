"""
Negative test scenarios — empty input, unknown locations, no results.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


class TestInputValidation:
    def test_empty_building_type_rejected(self, client):
        response = client.post(
            "/api/analyze",
            json={
                "building_type": " ",
                "floors": 5,
                "city": "Almaty",
                "material": "Concrete",
                "purpose": "Offices",
            },
        )
        assert response.status_code == 422

    def test_negative_floors_rejected(self, client):
        response = client.post(
            "/api/analyze",
            json={
                "building_type": "Residential",
                "floors": -1,
                "city": "Almaty",
                "material": "Concrete",
                "purpose": "Apartments",
            },
        )
        assert response.status_code == 422

    def test_zero_floors_rejected(self, client):
        response = client.post(
            "/api/analyze",
            json={
                "building_type": "Residential",
                "floors": 0,
                "city": "Almaty",
                "material": "Concrete",
                "purpose": "Apartments",
            },
        )
        assert response.status_code == 422

    def test_excessively_tall_building_rejected(self, client):
        response = client.post(
            "/api/analyze",
            json={
                "building_type": "Residential",
                "floors": 999,
                "city": "Almaty",
                "material": "Concrete",
                "purpose": "Apartments",
            },
        )
        assert response.status_code == 422

    def test_missing_required_field(self, client):
        response = client.post(
            "/api/analyze",
            json={
                "floors": 5,
                "city": "Almaty",
                # missing building_type
            },
        )
        assert response.status_code == 422


class TestNoResults:
    def test_no_retrieval_results_graceful(self, client):
        """When retriever returns nothing, pipeline should still return 200."""
        with patch("src.rag.retriever.search", return_value=[]):
            from unittest.mock import MagicMock
            with patch("src.agents.llm.get_llm") as mock_llm_factory:
                mock_llm = MagicMock()
                mock_llm.invoke.return_value = MagicMock(
                    content=(
                        '{"items": [], "total_norms": 0, "violations": 0, '
                        '"requires_action": 0, "advisory": 0, "compliant": 0, '
                        '"overall_risk": "CLEAR"}'
                    )
                )
                mock_llm_factory.return_value = mock_llm

                response = client.post(
                    "/api/analyze",
                    json={
                        "building_type": "Residential",
                        "floors": 2,
                        "city": "Almaty",
                        "material": "Wood",
                        "purpose": "Apartments",
                    },
                )

        assert response.status_code == 200

    def test_keyword_search_empty_query_rejected(self, client):
        response = client.get("/api/search/keyword?q=&limit=10")
        assert response.status_code == 422

    def test_health_endpoint_accessible(self, client):
        with patch("qdrant_client.QdrantClient") as mock_qc:
            mock_qc.return_value.get_collections.return_value = []
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
