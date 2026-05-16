"""
/api/prompt — accept a free-text natural-language query, extract building
parameters using an LLM, then run the full compliance pipeline.

Example prompt:
  "I want to design a 12-storey building in Almaty with a 2-level basement.
   Primary material is reinforced concrete. The public road is 10 m from the
   site. MEP communications are underground and need to be relocated."
"""

from __future__ import annotations

import json
import re
import time
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.llm import get_llm
from src.agents.orchestrator import build_initial_state, run_pipeline, stream_pipeline
from src.api.middleware import limiter
from src.api.models import AnalyzeResponse
from src.api.routers.analyze import _build_response

log = structlog.get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=4000,
                        description="Natural-language description of the construction project")


class ParsedParams(BaseModel):
    building_type: str = "Residential"
    floors: int = 1
    city: str = "Almaty"
    material: str = "Reinforced concrete"
    purpose: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Parameter extraction helpers
# ---------------------------------------------------------------------------

_EXTRACT_SYSTEM = """You are a parameter extractor for a construction compliance system.

Given a free-text description of a construction project, extract the following fields as JSON.
If a field cannot be determined from the text, use the default value shown.

Return ONLY valid JSON, no markdown, no extra text.

Fields:
- building_type: one of [Residential, Commercial, Industrial, School, Hospital, Warehouse, Mixed-use, Other]  (default: "Residential")
- floors: integer number of above-ground storeys (default: 1)
- basement_floors: integer number of basement levels (default: 0)
- city: city name in Kazakhstan (default: "Almaty")
- material: primary structural material, one of [Reinforced concrete, Steel, Brick, Wood, Panel, Monolithic, Other]  (default: "Reinforced concrete")
- purpose: brief description of building purpose / intended use (default: "")
- notes: any additional details from the prompt that don't fit above fields (keep in original language)
"""

_EXTRACT_USER = "Extract parameters from:\n\n{prompt}"


def _extract_params(prompt: str) -> ParsedParams:
    """Use LLM to extract structured building parameters from a free-text prompt."""
    llm = get_llm()
    messages = [
        SystemMessage(content=_EXTRACT_SYSTEM),
        HumanMessage(content=_EXTRACT_USER.format(prompt=prompt)),
    ]
    try:
        response = llm.invoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)
        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        data = json.loads(cleaned)

        # Combine basement info into notes if present
        basement = data.get("basement_floors", 0)
        extra_notes = data.get("notes", "")
        if basement and int(basement) > 0:
            extra_notes = f"{basement}-level basement. " + extra_notes

        return ParsedParams(
            building_type=str(data.get("building_type", "Residential")),
            floors=max(1, int(data.get("floors", 1))),
            city=str(data.get("city", "Almaty")),
            material=str(data.get("material", "Reinforced concrete")),
            purpose=str(data.get("purpose", "")),
            notes=(extra_notes + "\n\nOriginal query: " + prompt).strip(),
        )
    except Exception as exc:
        log.warning("param_extraction_failed", error=str(exc))
        # Fallback: pass entire prompt as notes
        return ParsedParams(notes=prompt)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/prompt", response_model=AnalyzeResponse, summary="Free-text compliance query")
@limiter.limit("10/minute")
async def prompt_analysis(request: Request, body: PromptRequest) -> AnalyzeResponse:
    """
    Accept a natural-language construction project description,
    extract parameters, run the multi-agent compliance pipeline,
    and return a human-readable report with document references.
    """
    start = time.monotonic()
    log.info("prompt_request", prompt_length=len(body.prompt))

    # Step 1: Extract structured params from the free-text prompt
    params = _extract_params(body.prompt)
    log.info(
        "params_extracted",
        building_type=params.building_type,
        floors=params.floors,
        city=params.city,
        material=params.material,
    )

    # Step 2: Build initial agent state
    state = build_initial_state(
        building_type=params.building_type,
        floors=params.floors,
        city=params.city,
        material=params.material,
        purpose=params.purpose,
        notes=params.notes,
    )

    # Step 3: Run the multi-agent pipeline
    try:
        final_state = run_pipeline(state)
    except Exception as exc:
        log.exception("prompt_pipeline_error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    duration_ms = int((time.monotonic() - start) * 1000)
    log.info("prompt_complete", duration_ms=duration_ms)

    return _build_response(final_state)


# ---------------------------------------------------------------------------
# Streaming endpoint (SSE) — real-time agent progress
# ---------------------------------------------------------------------------

async def _prompt_sse_generator(body: PromptRequest) -> AsyncGenerator[str, None]:
    """Extract params, then stream agent events + final result via SSE."""
    # Step 1: param extraction (runs before streaming starts)
    params = _extract_params(body.prompt)

    state = build_initial_state(
        building_type=params.building_type,
        floors=params.floors,
        city=params.city,
        material=params.material,
        purpose=params.purpose,
        notes=params.notes,
    )

    try:
        async for msg in stream_pipeline(state):
            if msg["event"] == "agent_update":
                data = json.dumps({"event": "agent_update", "step": msg["step"]})
                yield f"data: {data}\n\n"
            elif msg["event"] == "complete":
                response = _build_response(msg["final_state"])
                data = json.dumps({"event": "complete", "result": response.model_dump()})
                yield f"data: {data}\n\n"
            elif msg["event"] == "error":
                data = json.dumps({"event": "error", "message": msg["message"]})
                yield f"data: {data}\n\n"
    except Exception as exc:
        data = json.dumps({"event": "error", "message": str(exc)})
        yield f"data: {data}\n\n"


@router.post("/prompt/stream", summary="Free-text compliance query (SSE streaming)")
@limiter.limit("10/minute")
async def prompt_stream(request: Request, body: PromptRequest) -> StreamingResponse:
    """
    SSE streaming version of /api/prompt.
    Emits agent_update events as each agent completes, then a complete event
    with the full AnalyzeResponse payload.
    """
    log.info("prompt_stream_request", prompt_length=len(body.prompt))
    return StreamingResponse(
        content=_prompt_sse_generator(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
