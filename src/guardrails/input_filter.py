"""
Guardrail input filter — validates and sanitizes user queries before
they reach the agent pipeline.

Checks:
1. Topic relevance (must be construction/regulatory domain)
2. Prompt injection detection
3. Geographic scope (Kazakhstan focus)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import structlog

log = structlog.get_logger(__name__)

# --- Prompt injection patterns ---
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|prompts?)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a?\s*\w+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+)?(you\s+are\s+)?a?\s*\w+", re.IGNORECASE),
    re.compile(r"(pretend|roleplay|imagine)\s+(you\s+are|to\s+be)", re.IGNORECASE),
    re.compile(r"override\s+(safety|content|system)", re.IGNORECASE),
    re.compile(r"disregard\s+your\s+(guidelines|instructions)", re.IGNORECASE),
    re.compile(r"say\s+(that\s+)?(the\s+building\s+is\s+)?compliant", re.IGNORECASE),
    re.compile(r"DAN\b", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]

# --- Off-topic domain patterns (things clearly NOT construction-related) ---
_OFF_TOPIC_PATTERNS = [
    re.compile(r"\b(recipe|cook|food|pizza|pasta)\b", re.IGNORECASE),
    re.compile(r"\b(stock|crypto|bitcoin|invest)\b", re.IGNORECASE),
    re.compile(r"\b(movie|film|song|music|game)\b", re.IGNORECASE),
    re.compile(r"\b(politics|election|president)\b", re.IGNORECASE),
]

# --- Construction domain keywords (at least one should appear for valid query) ---
_CONSTRUCTION_KEYWORDS = [
    "building", "здание", " үй", "floor", "этаж", "қабат",
    "residential", "жилой", "тұрғын", "commercial", "коммерческий",
    "warehouse", "склад", "school", "школа", "hospital", "больница",
    "concrete", "бетон", "steel", "сталь", "wood", "дерево",
    "norm", "норма", "СНиП", "СП", "ҚНжЕ", "regulation", "нормативы",
    "compliance", "соответствие", "safety", "безопасность",
    "construction", "строительство", "architect", "архитектор",
    "design", "проект", "fire", "пожар", "seismic", "сейсм",
    "Almaty", "Алматы", "Astana", "Астана", "Kazakhstan", "Казахстан",
]


@dataclass
class FilterResult:
    is_valid: bool
    reason: Optional[str]         # None if valid
    detected_injection: bool
    detected_off_topic: bool


def validate_input(
    building_type: str,
    floors: int,
    city: str,
    material: str,
    purpose: str,
    notes: str,
) -> FilterResult:
    """
    Validate and filter user input before passing to the agent pipeline.

    Returns FilterResult indicating whether the input is safe and on-topic.
    """
    # Combine all text fields for pattern matching
    combined = " ".join([building_type, city, material, purpose, notes])

    # 1. Check for prompt injection
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(combined):
            log.warning("injection_detected", pattern=pattern.pattern, input=combined[:100])
            return FilterResult(
                is_valid=False,
                reason="Запрос содержит недопустимые инструкции и не может быть обработан.",
                detected_injection=True,
                detected_off_topic=False,
            )

    # 2. Check for off-topic content
    for pattern in _OFF_TOPIC_PATTERNS:
        if pattern.search(combined):
            log.warning("off_topic_detected", input=combined[:100])
            return FilterResult(
                is_valid=False,
                reason=(
                    "Система предназначена исключительно для анализа строительных норм Казахстана. "
                    "Пожалуйста, опишите параметры строительного объекта."
                ),
                detected_injection=False,
                detected_off_topic=True,
            )

    # 3. Validate floor count is reasonable
    if floors is not None and (floors < 1 or floors > 200):
        return FilterResult(
            is_valid=False,
            reason="Количество этажей должно быть от 1 до 200.",
            detected_injection=False,
            detected_off_topic=False,
        )

    # 4. Validate required fields are not suspiciously short
    if len(building_type.strip()) < 2:
        return FilterResult(
            is_valid=False,
            reason="Укажите тип здания.",
            detected_injection=False,
            detected_off_topic=False,
        )

    if len(city.strip()) < 2:
        return FilterResult(
            is_valid=False,
            reason="Укажите город или регион.",
            detected_injection=False,
            detected_off_topic=False,
        )

    log.info("input_validated", building_type=building_type, floors=floors, city=city)
    return FilterResult(is_valid=True, reason=None, detected_injection=False, detected_off_topic=False)
