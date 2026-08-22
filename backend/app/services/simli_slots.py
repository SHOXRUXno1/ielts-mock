"""Admission control for concurrent video-avatar slots.

The Simli plan allows a fixed number of simultaneous WebRTC sessions. Counting
speaking sessions cannot enforce that on its own: the browser asks for a video
token while the exam page loads, before any session row exists, so a wave of
candidates starting together all see an empty house and all get in.

A slot is therefore claimed the moment a token is granted, and a candidate
occupies a slot while either that claim or a live session says so. Claims are
short-lived, because a candidate who never starts must not hold video hostage.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, text, union
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.simli_lease import SimliSlotLease
from app.models.speaking_session import SpeakingSession, SpeakingState
from app.services.speaking_cleanup import idle_since

logger = logging.getLogger(__name__)

# Serialises the count-then-claim window across every worker process. Distinct
# from BACKGROUND_LOCK_KEY so the two never contend.
SLOT_LOCK_KEY = 874_512_04

TERMINAL_STATES = (
    SpeakingState.ENDED.value,
    SpeakingState.SCORING.value,
    SpeakingState.ABANDONED.value,
)


def _live_session_actors():
    """Candidates mid-exam. A session that stopped taking turns has lost its
    browser and no longer holds a stream."""
    cutoff = idle_since(timedelta(minutes=settings.simli_slot_idle_minutes))
    return select(SpeakingSession.admin_email.label("actor")).where(
        SpeakingSession.status == "in_progress",
        SpeakingSession.current_state.notin_(TERMINAL_STATES),
        SpeakingSession.updated_at >= cutoff,
    )


def _lease_actors(now: datetime):
    return select(SimliSlotLease.actor.label("actor")).where(
        SimliSlotLease.expires_at > now
    )


def _occupants(now: datetime):
    """One row per candidate holding a slot. UNION rather than UNION ALL, so a
    candidate counts once whether they hold a claim, a live session, or both."""
    return union(_lease_actors(now), _live_session_actors()).subquery()


async def occupied_slots(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    return (
        await db.execute(select(func.count()).select_from(_occupants(now)))
    ).scalar_one()


async def _holds_slot(db: AsyncSession, actor: str, now: datetime) -> bool:
    occupants = _occupants(now)
    return bool(
        (
            await db.execute(
                select(func.count())
                .select_from(occupants)
                .where(occupants.c.actor == actor)
            )
        ).scalar_one()
    )


async def claim_slot(db: AsyncSession, actor: str) -> tuple[bool, int]:
    """Take a video slot for `actor`, if the plan has room.

    Returns whether the slot was granted and how many were occupied at decision
    time. Commits before returning, which also drops the advisory lock — the
    caller must never hold it across the call out to Simli.
    """
    cap = max(1, settings.simli_max_concurrent)
    lease = timedelta(minutes=max(1, settings.simli_lease_minutes))

    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SLOT_LOCK_KEY})
    try:
        now = datetime.now(timezone.utc)
        taken = await occupied_slots(db)

        # Renewing an existing claim is always allowed: a candidate who reloads
        # the exam page already occupies their slot and must not lose video.
        if not await _holds_slot(db, actor, now) and taken >= cap:
            return False, taken

        stmt = pg_insert(SimliSlotLease).values(
            id=uuid.uuid4(),
            actor=actor,
            expires_at=now + lease,
        )
        await db.execute(
            stmt.on_conflict_do_update(
                index_elements=["actor"],
                set_={"expires_at": now + lease, "updated_at": func.now()},
            )
        )
        return True, taken
    finally:
        await db.commit()


async def release_slot(db: AsyncSession, actor: str) -> None:
    """Give the slot back, for when the token could not be obtained after all.
    Best effort: an orphaned claim expires on its own shortly."""
    try:
        await db.execute(
            delete(SimliSlotLease).where(SimliSlotLease.actor == actor)
        )
        await db.commit()
    except Exception:
        logger.exception("Failed to release Simli slot for %s", actor)


async def purge_expired_leases(db: AsyncSession) -> int:
    """Expired claims are already ignored when counting; this only stops the
    table from growing without bound."""
    result = await db.execute(
        delete(SimliSlotLease).where(
            SimliSlotLease.expires_at < datetime.now(timezone.utc)
        )
    )
    await db.commit()
    return int(result.rowcount or 0)
