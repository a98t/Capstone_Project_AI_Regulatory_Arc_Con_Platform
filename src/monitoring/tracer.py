"""
Langfuse tracing wrapper — instruments all LLM calls with token usage,
latency, and agent step tracking.
"""

from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional

import structlog

from src.config import settings

log = structlog.get_logger(__name__)

# Lazy-initialize Langfuse client
_langfuse = None


def _get_langfuse():
    global _langfuse
    if _langfuse is None:
        if (
            settings.langfuse_public_key
            and settings.langfuse_public_key != "pk-lf-your-key-here"
        ):
            try:
                from langfuse import Langfuse
                _langfuse = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                log.info("langfuse_initialized")
            except Exception as exc:
                log.warning("langfuse_init_failed", error=str(exc))
                _langfuse = None
        else:
            log.info("langfuse_disabled", reason="No API key configured")
    return _langfuse


@contextmanager
def trace_agent(session_id: str, agent_name: str, input_data: dict):
    """
    Context manager that creates a Langfuse span for an agent execution.

    Usage:
        with trace_agent(session_id, "SearchAgent", {"query": query}):
            result = do_agent_work()
    """
    lf = _get_langfuse()
    trace = None
    span = None
    start = time.monotonic()

    if lf:
        try:
            trace = lf.trace(
                name=f"derek_ai_{agent_name}",
                session_id=session_id,
                input=input_data,
                tags=["capstone", agent_name.lower()],
            )
            span = trace.span(name=agent_name, input=input_data)
        except Exception as exc:
            log.warning("langfuse_trace_start_failed", error=str(exc))

    try:
        yield trace
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        if span:
            try:
                span.end(output={"duration_ms": duration_ms})
            except Exception as exc:
                log.warning("langfuse_span_end_failed", error=str(exc))


def trace_llm_call(
    session_id: str,
    agent_name: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: int,
):
    """Record an LLM call's token usage to Langfuse."""
    lf = _get_langfuse()
    if not lf:
        return

    try:
        lf.generation(
            name=f"{agent_name}_llm_call",
            session_id=session_id,
            model=model,
            usage={
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": prompt_tokens + completion_tokens,
            },
            metadata={"duration_ms": duration_ms},
        )
    except Exception as exc:
        log.warning("langfuse_generation_failed", error=str(exc))


def log_user_feedback(session_id: str, rating: int, comment: str):
    """Record user feedback score to Langfuse."""
    lf = _get_langfuse()
    if not lf:
        return

    try:
        lf.score(
            trace_id=session_id,
            name="user_rating",
            value=rating,
            comment=comment,
        )
    except Exception as exc:
        log.warning("langfuse_score_failed", error=str(exc))
