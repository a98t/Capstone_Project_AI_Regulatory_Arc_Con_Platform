"""
Update Agent — verifies that retrieved norm documents are current via MCP (Tavily).

Input:  norm_identifiers from Compliance Agent
Output: freshness_verdicts, mcp_available
"""

from __future__ import annotations

import time
from typing import Any, Dict

import structlog

from src.agents.state import AgentState, AgentStep, FreshnessVerdict
from src.mcp.tavily_client import check_norm_freshness, is_mcp_available

log = structlog.get_logger(__name__)


def update_agent(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Update Agent.

    For each distinct regulatory document name from the compliance report,
    calls the Tavily MCP server to check whether the norm has been amended.
    Falls back gracefully if MCP is unavailable.
    """
    start = time.monotonic()
    log.info("update_agent_start", session_id=state.get("session_id"))

    norm_identifiers = state.get("norm_identifiers", [])
    verdicts: Dict[str, FreshnessVerdict] = {}

    if not norm_identifiers:
        step: AgentStep = {
            "agent": "UpdateAgent",
            "status": "skipped",
            "message": "No norm identifiers to verify",
            "duration_ms": 0,
        }
        return {
            "freshness_verdicts": {},
            "mcp_available": False,
            "update_error": None,
            "agent_trace": state.get("agent_trace", []) + [step],
        }

    mcp_ok = is_mcp_available()

    if not mcp_ok:
        log.warning("mcp_unavailable", reason="Tavily API key missing or unreachable")
        for norm_id in norm_identifiers:
            verdicts[norm_id] = {
                "verdict": "UNVERIFIED",
                "source_url": "",
                "checked_at": "",
            }
        duration_ms = int((time.monotonic() - start) * 1000)
        step: AgentStep = {
            "agent": "UpdateAgent",
            "status": "skipped",
            "message": "MCP unavailable — all norms flagged as UNVERIFIED",
            "duration_ms": duration_ms,
        }
        return {
            "freshness_verdicts": verdicts,
            "mcp_available": False,
            "update_error": "MCP server unavailable",
            "agent_trace": state.get("agent_trace", []) + [step],
        }

    # Check each norm (limit to first 5 to stay within rate limits)
    norms_to_check = norm_identifiers[:5]
    errors = []

    for norm_id in norms_to_check:
        try:
            verdict = check_norm_freshness(norm_id)
            verdicts[norm_id] = verdict
            log.info("norm_checked", norm=norm_id, verdict=verdict["verdict"])
        except Exception as exc:
            log.warning("norm_check_failed", norm=norm_id, error=str(exc))
            verdicts[norm_id] = {
                "verdict": "UNVERIFIED",
                "source_url": "",
                "checked_at": "",
            }
            errors.append(str(exc))

    # Any remaining norms beyond limit
    for norm_id in norm_identifiers[5:]:
        verdicts[norm_id] = {
            "verdict": "UNVERIFIED",
            "source_url": "",
            "checked_at": "rate_limit",
        }

    duration_ms = int((time.monotonic() - start) * 1000)
    current_count = sum(1 for v in verdicts.values() if v["verdict"] == "CURRENT")
    amended_count = sum(1 for v in verdicts.values() if v["verdict"] == "AMENDED")

    step: AgentStep = {
        "agent": "UpdateAgent",
        "status": "done",
        "message": f"Verified {len(norms_to_check)} norms: {current_count} current, {amended_count} amended",
        "duration_ms": duration_ms,
    }

    log.info(
        "update_agent_done",
        total=len(verdicts),
        current=current_count,
        amended=amended_count,
        duration_ms=duration_ms,
    )

    return {
        "freshness_verdicts": verdicts,
        "mcp_available": True,
        "update_error": "; ".join(errors) if errors else None,
        "agent_trace": state.get("agent_trace", []) + [step],
    }
