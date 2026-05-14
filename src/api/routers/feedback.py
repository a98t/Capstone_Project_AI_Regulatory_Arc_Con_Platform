"""
/api/feedback — stores user star ratings and optional comments in SQLite.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Request

from src.api.middleware import limiter
from src.api.models import FeedbackRequest
from src.config import settings
from src.monitoring.tracer import log_user_feedback

log = structlog.get_logger(__name__)
router = APIRouter()


async def _save_feedback(session_id: str, rating: int, comment: str) -> None:
    """Persist feedback to SQLite using aiosqlite."""
    import aiosqlite

    async with aiosqlite.connect(settings.sqlite_db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL,
                rating      INTEGER NOT NULL,
                comment     TEXT    DEFAULT '',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            "INSERT INTO feedback (session_id, rating, comment) VALUES (?, ?, ?)",
            (session_id, rating, comment),
        )
        await db.commit()


@router.post("/feedback", status_code=201)
@limiter.limit("10/minute")
async def submit_feedback(request: Request, body: FeedbackRequest) -> dict:
    """Store user star rating and optional comment for a session."""
    try:
        await _save_feedback(
            session_id=body.session_id,
            rating=body.rating,
            comment=body.comment,
        )
    except Exception as exc:
        log.exception("feedback_db_error", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to save feedback.")

    # Also record in Langfuse observability
    log_user_feedback(
        session_id=body.session_id,
        rating=body.rating,
        comment=body.comment,
    )

    log.info("feedback_saved", session_id=body.session_id, rating=body.rating)
    return {"status": "ok", "message": "Thank you for your feedback!"}
