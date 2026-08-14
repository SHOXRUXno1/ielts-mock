"""Unit tests for abandoned speaking-session cleanup."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.models.speaking_session import SpeakingState
from app.services.speaking_cleanup import (
    ABANDON_AFTER,
    cleanup_abandoned_sessions,
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
        assert "coalesce" in sql

        params = compiled.params
        assert params.get("status") == "abandoned"
        assert params.get("current_state") == SpeakingState.ABANDONED.value

        # finished_at ≈ now, coalesce threshold ≈ now-2h — pick the older one
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
