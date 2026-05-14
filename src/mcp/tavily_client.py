"""
Tavily MCP client — connects to Tavily Search to verify norm freshness.

In MCP protocol terms: Tavily acts as a Tool Server providing a `search` tool.
We call it via the MCP tool-calling interface using the `mcp` SDK.

Fallback: if MCP SDK or API key unavailable, returns UNVERIFIED verdict.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Optional

import diskcache
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.state import FreshnessVerdict
from src.config import settings

log = structlog.get_logger(__name__)

_cache: Optional[diskcache.Cache] = None


def _get_cache() -> diskcache.Cache:
    global _cache
    if _cache is None:
        import pathlib
        cache_dir = pathlib.Path(settings.cache_dir) / "mcp"
        cache_dir.mkdir(parents=True, exist_ok=True)
        _cache = diskcache.Cache(str(cache_dir))
    return _cache


def is_mcp_available() -> bool:
    """Check if the Tavily API key is configured."""
    return bool(settings.tavily_api_key and settings.tavily_api_key != "tvly-your-key-here")


def _classify_freshness(search_results: list) -> tuple[str, str]:
    """
    Classify norm freshness from Tavily search results.

    Returns (verdict, source_url):
      - CURRENT: No amendments found in recent results
      - AMENDED: Found evidence of amendment or replacement
      - UNKNOWN: Insufficient data to determine
    """
    if not search_results:
        return "UNKNOWN", ""

    amendment_keywords = [
        "изменение", "amendment", "поправка", "отменён", "отменен",
        "replaced", "superseded", "withdrawn", "new edition", "новая редакция",
        "актуализированная", "введён в действие", "взамен",
    ]

    best_url = search_results[0].get("url", "") if search_results else ""

    combined_text = " ".join(
        (r.get("title", "") + " " + r.get("content", ""))
        for r in search_results[:3]
    ).lower()

    for kw in amendment_keywords:
        if kw.lower() in combined_text:
            return "AMENDED", best_url

    # If search returned results but no amendment keywords → likely current
    if search_results:
        return "CURRENT", best_url

    return "UNKNOWN", ""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def _call_tavily(query: str) -> list:
    """Call Tavily REST API with retry logic."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=3,
        include_domains=["online.zakon.kz", "adilet.zan.kz", "egov.kz", "kazntu.kz"],
    )
    return response.get("results", [])


def check_norm_freshness(norm_identifier: str) -> FreshnessVerdict:
    """
    Check whether a regulatory norm is current or has been amended.

    Uses disk cache with TTL to avoid redundant API calls.
    """
    cache = _get_cache()
    cache_key = f"freshness::{norm_identifier}"
    cached = cache.get(cache_key)
    if cached is not None:
        log.debug("mcp_cache_hit", norm=norm_identifier)
        return cached

    query = (
        f"{norm_identifier} изменение поправка Казахстан 2024 2025 строительные нормы"
    )

    try:
        results = _call_tavily(query)
        verdict, source_url = _classify_freshness(results)
    except Exception as exc:
        log.warning("tavily_call_failed", norm=norm_identifier, error=str(exc))
        verdict, source_url = "UNVERIFIED", ""

    freshness: FreshnessVerdict = {
        "verdict": verdict,
        "source_url": source_url,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    # Cache result for configured TTL
    ttl_seconds = settings.mcp_cache_ttl_hours * 3600
    cache.set(cache_key, freshness, expire=ttl_seconds)

    log.info("norm_freshness_checked", norm=norm_identifier, verdict=verdict)
    return freshness
