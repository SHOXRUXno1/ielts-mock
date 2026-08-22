"""Run the abandoned-session sweep once and report the video-slot picture
before and after. Handy after a load test leaves dead sessions behind.

    python scripts/_reclaim_simli_slots.py
"""

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import async_session  # noqa: E402
from app.models.speaking_session import SpeakingSession, SpeakingState  # noqa: E402
from app.services.speaking_cleanup import (  # noqa: E402
    ABANDON_AFTER,
    cleanup_abandoned_sessions,
    idle_since,
)

TERMINAL = (
    SpeakingState.ENDED.value,
    SpeakingState.SCORING.value,
    SpeakingState.ABANDONED.value,
)


async def _slots_taken(db, *, live_only: bool) -> int:
    """Sessions the capacity gate would count, with and without the liveness
    filter — the gap is how many slots dead sessions were squatting on."""
    stmt = (
        select(func.count())
        .select_from(SpeakingSession)
        .where(
            SpeakingSession.status == "in_progress",
            SpeakingSession.current_state.notin_(TERMINAL),
        )
    )
    if live_only:
        stmt = stmt.where(
            SpeakingSession.updated_at
            >= idle_since(timedelta(minutes=settings.simli_slot_idle_minutes))
        )
    return (await db.execute(stmt)).scalar_one()


async def main() -> None:
    async with async_session() as db:
        stale = await _slots_taken(db, live_only=False)
        live = await _slots_taken(db, live_only=True)
        print(f"capacity            : {settings.simli_max_concurrent} video slots")
        print(f"counted without fix : {stale}")
        print(f"counted with fix    : {live}  (idle cutoff "
              f"{settings.simli_slot_idle_minutes} min)")

        reclaimed = await cleanup_abandoned_sessions(db)
        print(f"sweep marked        : {reclaimed} abandoned "
              f"(threshold {ABANDON_AFTER})")

        after = await _slots_taken(db, live_only=False)
        print(f"counted after sweep : {after}")


if __name__ == "__main__":
    asyncio.run(main())
