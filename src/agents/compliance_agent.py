"""
Compliance Agent — evaluates building parameters against retrieved regulations
and produces a structured compliance report.

Input:  retrieved_chunks from Search Agent + building parameters
Output: compliance_report, norm_identifiers
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.llm import get_llm
from src.agents.state import AgentState, AgentStep, ComplianceItem, ComplianceReport
from src.rag.quality import filter_confident_chunks, format_chunks_for_llm

log = structlog.get_logger(__name__)

SYSTEM_PROMPT = """Вы — эксперт по строительным нормам и правилам Казахстана.

Ваша задача: проанализировать предоставленные нормативные документы и оценить соответствие описанного объекта строительства действующим нормам.

СТРОГИЕ ПРАВИЛА:
1. Используйте ТОЛЬКО информацию из предоставленных нормативных документов
2. НЕ придумывайте статьи или нормы, которые отсутствуют в контексте
3. Если норма не найдена — укажите "Норма не найдена в базе данных"
4. Каждый пункт должен содержать точную ссылку на источник
5. Отвечайте на языке запроса (русский или английский)

ФОРМАТ ОТВЕТА: Строго JSON, без markdown-блоков, без пояснений вне JSON.

{
  "items": [
    {
      "article_ref": "точная ссылка на статью",
      "doc_name": "название документа",
      "status": "COMPLIANT|VIOLATION|REQUIRES_ACTION|ADVISORY",
      "description": "техническое описание требования",
      "plain_language": "простое объяснение для архитектора",
      "risk_level": "HIGH|MEDIUM|LOW|ADVISORY"
    }
  ],
  "overall_risk": "HIGH|MEDIUM|LOW|CLEAR"
}

Статусы:
- COMPLIANT: объект соответствует норме
- VIOLATION: явное нарушение нормы
- REQUIRES_ACTION: требует дополнительной проверки или документации
- ADVISORY: рекомендация, не обязательное требование"""


def _parse_llm_response(response_text: str) -> List[ComplianceItem]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Strip markdown code blocks if present
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", response_text).strip()

    try:
        data = json.loads(cleaned)
        return data.get("items", []), data.get("overall_risk", "MEDIUM")
    except json.JSONDecodeError:
        # Attempt to extract JSON object from surrounding text
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data.get("items", []), data.get("overall_risk", "MEDIUM")
        raise ValueError(f"Could not parse LLM JSON response: {response_text[:200]}")


def _build_user_prompt(state: AgentState, context: str) -> str:
    return f"""Параметры объекта строительства:
- Тип здания: {state.get('building_type', 'не указан')}
- Этажность: {state.get('floors', 'не указана')}
- Город/регион: {state.get('city', 'не указан')}
- Материал конструкции: {state.get('material', 'не указан')}
- Назначение: {state.get('purpose', 'не указано')}
- Дополнительно: {state.get('notes', '—')}

Нормативные документы из базы данных:
{context}

Проанализируйте соответствие данного объекта приведённым нормам и предоставьте структурированный отчёт в формате JSON."""


def compliance_agent(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Compliance Agent.

    Analyzes the retrieved chunks against the building parameters
    and produces a structured ComplianceReport.
    """
    start = time.monotonic()
    log.info("compliance_agent_start", session_id=state.get("session_id"))

    try:
        chunks = state.get("retrieved_chunks", [])

        if not chunks:
            # No chunks retrieved — cannot perform compliance analysis
            empty_report: ComplianceReport = {
                "items": [],
                "total_norms": 0,
                "violations": 0,
                "requires_action": 0,
                "advisory": 0,
                "compliant": 0,
                "overall_risk": "CLEAR",
            }
            step: AgentStep = {
                "agent": "ComplianceAgent",
                "status": "skipped",
                "message": "No chunks retrieved — skipping compliance analysis",
                "duration_ms": 0,
            }
            return {
                "compliance_report": empty_report,
                "norm_identifiers": [],
                "compliance_error": "Нормативные документы не найдены в базе данных.",
                "agent_trace": state.get("agent_trace", []) + [step],
            }

        # Prefer high-confidence chunks; still include low-confidence with flag
        confident_chunks = filter_confident_chunks(chunks)
        context_chunks = confident_chunks if confident_chunks else chunks
        context = format_chunks_for_llm(context_chunks)

        llm = get_llm()

        # --- RAG-only fallback (no LLM configured) ---
        if llm is None:
            items = []
            for chunk in context_chunks:
                items.append({
                    "article_ref": chunk.article_ref or "—",
                    "doc_name": chunk.doc_name,
                    "status": "ADVISORY",
                    "description": chunk.text[:400],
                    "plain_language": chunk.text[:300],
                    "risk_level": "ADVISORY",
                })
            overall_risk = "REQUIRES_REVIEW"
            report: ComplianceReport = {
                "items": items,
                "total_norms": len(items),
                "violations": 0,
                "requires_action": len(items),
                "advisory": 0,
                "compliant": 0,
                "overall_risk": overall_risk,
            }
            norm_identifiers = list({c.doc_name for c in context_chunks})
            duration_ms = int((time.monotonic() - start) * 1000)
            step: AgentStep = {
                "agent": "ComplianceAgent",
                "status": "done",
                "message": f"RAG-only mode — {len(items)} relevant regulations found (no LLM)",
                "duration_ms": duration_ms,
            }
            return {
                "compliance_report": report,
                "norm_identifiers": norm_identifiers,
                "compliance_error": None,
                "agent_trace": state.get("agent_trace", []) + [step],
            }
        # --- End RAG-only fallback ---

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_prompt(state, context)),
        ]

        response = llm.invoke(messages)
        items, overall_risk = _parse_llm_response(response.content)

        # Compute summary counts
        violations = sum(1 for i in items if i.get("status") == "VIOLATION")
        requires_action = sum(1 for i in items if i.get("status") == "REQUIRES_ACTION")
        advisory = sum(1 for i in items if i.get("status") == "ADVISORY")
        compliant = sum(1 for i in items if i.get("status") == "COMPLIANT")

        report: ComplianceReport = {
            "items": items,
            "total_norms": len(items),
            "violations": violations,
            "requires_action": requires_action,
            "advisory": advisory,
            "compliant": compliant,
            "overall_risk": overall_risk,
        }

        # Collect distinct document names for the Update Agent
        norm_identifiers = list({i.get("doc_name", "") for i in items if i.get("doc_name")})

        duration_ms = int((time.monotonic() - start) * 1000)
        step: AgentStep = {
            "agent": "ComplianceAgent",
            "status": "done",
            "message": f"Analyzed {len(items)} items — {violations} violations, {requires_action} actions required",
            "duration_ms": duration_ms,
        }

        log.info(
            "compliance_agent_done",
            items=len(items),
            violations=violations,
            overall_risk=overall_risk,
            duration_ms=duration_ms,
        )

        return {
            "compliance_report": report,
            "norm_identifiers": norm_identifiers,
            "compliance_error": None,
            "agent_trace": state.get("agent_trace", []) + [step],
        }

    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        log.exception("compliance_agent_error", error=str(exc))
        step: AgentStep = {
            "agent": "ComplianceAgent",
            "status": "error",
            "message": str(exc),
            "duration_ms": duration_ms,
        }
        return {
            "compliance_report": None,
            "norm_identifiers": [],
            "compliance_error": str(exc),
            "agent_trace": state.get("agent_trace", []) + [step],
            "errors": state.get("errors", []) + [f"ComplianceAgent: {exc}"],
        }
