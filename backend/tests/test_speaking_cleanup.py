"""Unit tests for abandoned speaking-session cleanup."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.models.speaking_session import SpeakingState
from app.services.speaking_cleanup import (
    ABANDON_AFTER,
    CLEANUP_INTERVAL,
    cleanup_abandoned_sessions,
    idle_since,
)


class TestCleanupAbandonedSessions:
    @pytest.mark.asyncio
    async def test_marks_old_sessions_and_commits(self):
        result = MagicMock()
        result.rowcount = 3
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()

        n = await cleanup_abandoned_sessions(db)
        assert n == 3
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

        stmt = db.execute.await_args.args[0]
        compiled = stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
        sql = str(compiled).lower()
        assert "speaking_sessions" in sql
        assert "status" in sql
        assert "current_state" in sql
        # Staleness is judged by last activity, not by when the state was
        # entered — a candidate can spend several turns inside one state.
        assert "updated_at" in sql

        params = compiled.params
        assert params.get("status") == "abandoned"
        assert params.get("current_state") == SpeakingState.ABANDONED.value

        # finished_at ≈ now, the staleness cutoff is older — pick the older one
        datetimes = [v for v in params.values() if isinstance(v, datetime)]
        assert datetimes
        threshold = min(datetimes)
        expected = datetime.now(timezone.utc) - ABANDON_AFTER
        assert abs((threshold - expected).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_zero_rowcount(self):
        result = MagicMock()
        result.rowcount = 0
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()
        assert await cleanup_abandoned_sessions(db) == 0


class TestReclaimTiming:
    """A dead session used to keep its Simli video slot for over two hours,
    which downgraded every later candidate to audio-only."""

    def test_sweep_reclaims_well_within_one_exam_sitting(self):
        assert ABANDON_AFTER <= timedelta(minutes=30)
        # The sweep must run often enough that reclaim is bounded by the
        # threshold rather than by how rarely the loop wakes up.
        assert CLEANUP_INTERVAL <= ABANDON_AFTER.total_seconds()

    def test_abandon_window_outlasts_a_real_exam(self):
        # A full Speaking exam is roughly fifteen minutes; the window has to
        # clear that so a slow candidate is never dropped mid-answer.
        assert ABANDON_AFTER >= timedelta(minutes=20)

    def test_idle_since_counts_back_from_now(self):
        cutoff = idle_since(timedelta(minutes=5))
        expected = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert abs((cutoff - expected).total_seconds()) < 5
