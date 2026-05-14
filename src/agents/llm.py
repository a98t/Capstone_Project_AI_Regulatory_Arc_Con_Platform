"""
LLM factory — returns a configured LangChain chat model based on settings.

Centralised here so all agents use the same model instance and tracing wrapper.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from src.config import settings


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.0,
            max_tokens=1500,
        )
    elif settings.llm_provider == "demo":
        # No external LLM — agents will run in RAG-only fallback mode
        return None  # type: ignore
    else:
        # Ollama via LangChain community integration
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            num_predict=1500,
        )


def llm_available() -> bool:
    """Return True if an LLM is configured and reachable."""
    if settings.llm_provider == "demo":
        return False
    try:
        llm = get_llm()
        return llm is not None
    except Exception:
        return False
