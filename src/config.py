"""
Central configuration — all settings loaded from .env via pydantic-settings.
Import `settings` anywhere in the codebase.
"""

from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    llm_provider: Literal["ollama", "openai"] = "ollama"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b-instruct"

    # Embeddings
    embedding_model: str = "BAAI/bge-m3"
    embedding_batch_size: int = 32

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "regulations"

    # RAG
    rag_top_k: int = 8
    rag_confidence_threshold: float = 0.40
    rag_max_chunk_size: int = 800
    rag_chunk_overlap: int = 100

    # MCP / Tavily
    tavily_api_key: str = ""
    mcp_cache_ttl_hours: int = 24

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Backend
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_rate_limit: int = 20
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # Security
    secret_key: str = "change-me"

    # Data paths
    regulations_dir: str = "./data/regulations"
    cache_dir: str = "./data/cache"
    sqlite_db_path: str = "./data/derek_ai.db"

    # App
    environment: Literal["development", "production"] = "development"
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
