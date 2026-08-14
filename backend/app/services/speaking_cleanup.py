"""Background cleanup of abandoned speaking sessions."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.speaking_session import SpeakingSession, SpeakingState

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL = 1800  # 30 minutes
ABANDON_AFTER = timedelta(hours=2)


async def cleanup_abandoned_sessions(db: AsyncSession) -> int:
    """Mark in_progress sessions older than 2 hours as abandoned."""
    threshold = datetime.now(timezone.utc) - ABANDON_AFTER
    result = await db.execute(
        update(SpeakingSession)
        .where(
            SpeakingSession.status == "in_progress",
            func.coalesce(
                SpeakingSession.state_entered_at,
                SpeakingSession.started_at,
                SpeakingSession.created_at,
            )
            < threshold,
        )
        .values(
            status="abandoned",
            current_state=SpeakingState.ABANDONED.value,
            finished_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()
    return int(result.rowcount or 0)


async def run_session_cleanup() -> None:
    """Forever loop: abandon stale sessions every CLEANUP_INTERVAL seconds."""
    while True:
        try:
            async with async_session() as db:
                n = await cleanup_abandoned_sessions(db)
                if n:
                    logger.info("Abandoned %d stale speaking sessions", n)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Speaking cleanup iteration failed")
        await asyncio.sleep(CLEANUP_INTERVAL)
