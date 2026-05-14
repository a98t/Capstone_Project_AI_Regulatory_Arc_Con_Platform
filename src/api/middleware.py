"""
FastAPI middleware — CORS, rate limiting, request logging.
"""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

log = structlog.get_logger(__name__)

# Rate limiter — shared instance imported by routers
limiter = Limiter(key_func=get_remote_address)


def setup_middleware(app: FastAPI) -> None:
    """Attach all middleware to the FastAPI app."""

    # CORS — allow React dev server and production origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        log.info(
            "request_start",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        log.info(
            "request_end",
            request_id=request_id,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Duration-Ms"] = str(duration_ms)
        return response
