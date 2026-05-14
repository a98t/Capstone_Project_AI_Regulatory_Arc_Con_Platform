"""
Pydantic v2 request/response models for the FastAPI API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    building_type: str = Field(..., min_length=2, max_length=100, examples=["Residential"])
    floors: int = Field(..., ge=1, le=200, examples=[9])
    city: str = Field(..., min_length=2, max_length=100, examples=["Almaty"])
    material: str = Field(default="not specified", max_length=100, examples=["Reinforced concrete"])
    purpose: str = Field(default="not specified", max_length=200, examples=["Apartments"])
    notes: str = Field(default="", max_length=1000)

    @field_validator("building_type", "city", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class FeedbackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(default="", max_length=500)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)
    limit: int = Field(default=20, ge=1, le=100)


# ─────────────────────────────────────────────
# Response models
# ─────────────────────────────────────────────

class FreshnessInfo(BaseModel):
    verdict: str               # CURRENT | AMENDED | UNKNOWN | UNVERIFIED
    source_url: str
    mcp_verified: bool


class FindingItem(BaseModel):
    article_ref: str
    doc_name: str
    status: str                # COMPLIANT | VIOLATION | REQUIRES_ACTION | ADVISORY
    description: str
    plain_language: str
    risk_level: str            # HIGH | MEDIUM | LOW | ADVISORY
    freshness: FreshnessInfo


class ReportSummary(BaseModel):
    total_norms: int
    violations: int
    requires_action: int
    advisory: int
    compliant: int
    overall_risk: str          # HIGH | MEDIUM | LOW | CLEAR


class AgentStepInfo(BaseModel):
    agent: str
    status: str
    message: str
    duration_ms: int


class AnalyzeResponse(BaseModel):
    session_id: str
    summary: ReportSummary
    narrative: str             # Plain-language summary from Explanation Agent
    findings: List[FindingItem]
    disclaimer: str
    agent_trace: List[AgentStepInfo]
    total_duration_ms: int
    search_confidence: float
    errors: List[str]


class SearchResult(BaseModel):
    doc_name: str
    doc_type: str
    year: Optional[int]
    article_ref: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int


class HealthResponse(BaseModel):
    status: str                # "ok" | "degraded" | "error"
    qdrant: bool
    llm: bool
    mcp: bool
    details: Dict[str, Any]
