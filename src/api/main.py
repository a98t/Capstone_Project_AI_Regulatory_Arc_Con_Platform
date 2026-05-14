"""
FastAPI application factory for DEREK-AI backend.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.middleware import limiter, setup_middleware
from src.api.routers import analyze, feedback, prompt, search
from src.config import settings
from src.qdrant_client_factory import create_qdrant_client

log = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DEREK-AI Regulatory Intelligence API",
        description=(
            "AI-powered compliance analysis for Kazakhstan's construction regulations. "
            "Powered by LangGraph multi-agent pipeline, bge-m3 embeddings, and Qdrant."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Rate limiter state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Middleware (CORS, logging)
    setup_middleware(app)

    # Routers
    app.include_router(analyze.router, prefix="/api", tags=["analysis"])
    app.include_router(prompt.router, prefix="/api", tags=["prompt"])
    app.include_router(search.router, prefix="/api", tags=["search"])
    app.include_router(feedback.router, prefix="/api", tags=["feedback"])

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """Health check endpoint — verifies Qdrant and LLM availability."""
        from src.mcp.tavily_client import is_mcp_available

        qdrant_ok = False
        llm_ok = False

        try:
            client = create_qdrant_client()
            client.get_collections()
            qdrant_ok = True
        except Exception:
            pass

        try:
            from src.agents.llm import get_llm
            llm = get_llm()
            # Cheap probe — just check the object is valid
            llm_ok = llm is not None
        except Exception:
            pass

        mcp_ok = is_mcp_available()

        status = "ok" if (qdrant_ok and llm_ok) else "degraded"
        return {
            "status": status,
            "qdrant": qdrant_ok,
            "llm": llm_ok,
            "mcp": mcp_ok,
            "details": {
                "llm_provider": settings.llm_provider,
                "embedding_model": settings.embedding_model,
                "qdrant_collection": settings.qdrant_collection,
            },
        }

    log.info("app_created", version="0.1.0")
    return app


# WSGI/ASGI entry point
app = create_app()
