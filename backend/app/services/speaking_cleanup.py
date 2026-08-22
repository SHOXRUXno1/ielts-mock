"""Background cleanup of abandoned speaking sessions."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.speaking_session import SpeakingSession, SpeakingState

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL = 300  # 5 minutes
# A full Speaking exam runs about fifteen minutes, so half an hour without a
# single turn means the candidate is gone. The old two-hour window let dead
# sessions hold Simli video slots for most of an exam sitting.
ABANDON_AFTER = timedelta(minutes=30)


def idle_since(idle: timedelta) -> datetime:
    """Cutoff for `updated_at` below which a session is no longer live.

    Every examiner turn rewrites the session row, so `updated_at` tracks real
    candidate activity — unlike `state_entered_at`, which stands still while a
    candidate works through several questions inside one state.
    """
    return datetime.now(timezone.utc) - idle


async def cleanup_abandoned_sessions(db: AsyncSession) -> int:
    """Mark sessions with no activity for ABANDON_AFTER as abandoned."""
    result = await db.execute(
        update(SpeakingSession)
        .where(
            SpeakingSession.status == "in_progress",
            SpeakingSession.updated_at < idle_since(ABANDON_AFTER),
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
    # Imported here because the slot service depends on this module.
    from app.services.simli_slots import purge_expired_leases

    while True:
        try:
            async with async_session() as db:
                n = await cleanup_abandoned_sessions(db)
                if n:
                    logger.info("Abandoned %d stale speaking sessions", n)
                leases = await purge_expired_leases(db)
                if leases:
                    logger.info("Cleared %d expired Simli slot leases", leases)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Speaking cleanup iteration failed")
        await asyncio.sleep(CLEANUP_INTERVAL)
