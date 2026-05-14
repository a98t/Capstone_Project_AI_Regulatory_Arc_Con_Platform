"""
/api/analyze — trigger the full multi-agent pipeline and stream progress via SSE.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi.errors import RateLimitExceeded

from src.agents.orchestrator import build_initial_state, run_pipeline, stream_pipeline
from src.api.middleware import limiter
from src.api.models import (
    AgentStepInfo,
    AnalyzeRequest,
    AnalyzeResponse,
    FindingItem,
    FreshnessInfo,
    ReportSummary,
)
from src.guardrails.input_filter import validate_input

log = structlog.get_logger(__name__)
router = APIRouter()


def _build_response(final_state: dict) -> AnalyzeResponse:
    """Map AgentState dict to AnalyzeResponse Pydantic model."""
    report = final_state.get("compliance_report") or {}
    final_resp = final_state.get("final_response") or {}
    verdicts = final_state.get("freshness_verdicts", {})

    summary = ReportSummary(
        total_norms=report.get("total_norms", 0),
        violations=report.get("violations", 0),
        requires_action=report.get("requires_action", 0),
        advisory=report.get("advisory", 0),
        compliant=report.get("compliant", 0),
        overall_risk=report.get("overall_risk", "UNKNOWN"),
    )

    findings = []
    for item in final_resp.get("findings", []):
        fr = item.get("freshness", {})
        findings.append(
            FindingItem(
                article_ref=item.get("article_ref", ""),
                doc_name=item.get("doc_name", ""),
                status=item.get("status", "ADVISORY"),
                description=item.get("description", ""),
                plain_language=item.get("plain_language", ""),
                risk_level=item.get("risk_level", "LOW"),
                freshness=FreshnessInfo(
                    verdict=fr.get("verdict", "UNVERIFIED"),
                    source_url=fr.get("source_url", ""),
                    mcp_verified=fr.get("mcp_verified", False),
                ),
            )
        )

    trace = [
        AgentStepInfo(
            agent=step.get("agent", ""),
            status=step.get("status", ""),
            message=step.get("message", ""),
            duration_ms=step.get("duration_ms", 0),
        )
        for step in final_state.get("agent_trace", [])
    ]

    return AnalyzeResponse(
        session_id=final_state.get("session_id", ""),
        summary=summary,
        narrative=final_resp.get("summary", ""),
        findings=findings,
        disclaimer=final_resp.get("disclaimer", ""),
        agent_trace=trace,
        total_duration_ms=final_state.get("total_duration_ms", 0),
        search_confidence=final_state.get("search_confidence", 0.0),
        errors=final_state.get("errors", []),
    )


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("20/minute")
async def analyze(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Run the full multi-agent compliance analysis pipeline.

    Rate limited to 20 requests/minute per IP.
    """
    # Guardrail validation
    filter_result = validate_input(
        building_type=body.building_type,
        floors=body.floors,
        city=body.city,
        material=body.material,
        purpose=body.purpose,
        notes=body.notes,
    )
    if not filter_result.is_valid:
        raise HTTPException(status_code=422, detail=filter_result.reason)

    initial_state = build_initial_state(
        building_type=body.building_type,
        floors=body.floors,
        city=body.city,
        material=body.material,
        purpose=body.purpose,
        notes=body.notes,
    )

    # Run in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    final_state = await loop.run_in_executor(None, run_pipeline, initial_state)

    return _build_response(final_state)


async def _sse_generator(initial_state: dict) -> AsyncGenerator[str, None]:
    """Format agent events as SSE messages."""
    async for event in stream_pipeline(initial_state):
        data = json.dumps(event)
        yield f"data: {data}\n\n"


@router.get("/stream/{session_id}")
async def stream_analysis(session_id: str, request: Request):
    """
    SSE endpoint — streams real-time agent progress for a session.
    The frontend subscribes before calling /analyze to receive live updates.
    """
    # In a full implementation this would look up the session's state.
    # For the demo, the frontend uses this endpoint to display agent status
    # while /analyze runs in parallel.
    return StreamingResponse(
        content=iter([f"data: {json.dumps({'event': 'connected', 'session_id': session_id})}\n\n"]),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
