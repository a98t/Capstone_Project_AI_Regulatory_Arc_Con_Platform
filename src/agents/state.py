"""
AgentState — shared state TypedDict passed between all LangGraph nodes.

All agents read from and write to this structure.
No agent should access data outside of what is passed through the state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from src.rag.retriever import RetrievedChunk


class AgentStep(TypedDict):
    agent: str
    status: str      # "running" | "done" | "error" | "skipped"
    message: str
    duration_ms: int


class ComplianceItem(TypedDict):
    article_ref: str
    doc_name: str
    status: str          # "COMPLIANT" | "VIOLATION" | "REQUIRES_ACTION" | "ADVISORY"
    description: str
    plain_language: str
    risk_level: str      # "HIGH" | "MEDIUM" | "LOW" | "ADVISORY"


class FreshnessVerdict(TypedDict):
    verdict: str         # "CURRENT" | "AMENDED" | "UNKNOWN" | "UNVERIFIED"
    source_url: str
    checked_at: str      # ISO timestamp


class ComplianceReport(TypedDict):
    items: List[ComplianceItem]
    total_norms: int
    violations: int
    requires_action: int
    advisory: int
    compliant: int
    overall_risk: str    # "HIGH" | "MEDIUM" | "LOW" | "CLEAR"


class FinalResponse(TypedDict):
    summary: str
    findings: List[Dict[str, Any]]
    disclaimer: str
    language: str


class AgentState(TypedDict):
    # --- Input ---
    building_type: str
    floors: int
    city: str
    material: str
    purpose: str
    notes: str
    raw_query: str
    session_id: str

    # --- Search Agent output ---
    retrieved_chunks: List[RetrievedChunk]
    search_confidence: float
    search_error: Optional[str]

    # --- Compliance Agent output ---
    compliance_report: Optional[ComplianceReport]
    norm_identifiers: List[str]   # distinct doc_name values for Update Agent
    compliance_error: Optional[str]

    # --- Update Agent output ---
    freshness_verdicts: Dict[str, FreshnessVerdict]
    mcp_available: bool
    update_error: Optional[str]

    # --- Explanation Agent output ---
    final_response: Optional[FinalResponse]
    explanation_error: Optional[str]

    # --- Pipeline metadata ---
    agent_trace: List[AgentStep]
    errors: List[str]
    total_duration_ms: int
