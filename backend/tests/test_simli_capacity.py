"""The video avatar has only a handful of concurrent slots, so the capacity
gate must count candidates who are actually mid-exam. Sessions whose browser
died used to keep their slot until the abandon sweep ran, which silently
downgraded every later candidate to audio-only.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.api import speaking_examiner
from app.api.speaking_examiner import get_simli_token
from app.core.config import settings


def _db_returning(count: int) -> MagicMock:
    result = MagicMock()
    result.scalar_one = MagicMock(return_value=count)
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    return db


def _stub_simli_client(*_args, **_kwargs) -> AsyncMock:
    """Stand in for Simli so the gate can be exercised without egress."""
    ok = MagicMock()
    ok.status_code = 200
    ok.json = MagicMock(return_value={"session_token": "tok-123"})
    ok.raise_for_status = MagicMock()

    client = AsyncMock()
    client.post = AsyncMock(return_value=ok)
    client.get = AsyncMock(return_value=ok)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "simli_api_key", "key")
    monkeypatch.setattr(settings, "simli_face_id", "face-id-123")
    monkeypatch.setattr(settings, "simli_max_concurrent", 8)
    monkeypatch.setattr(settings, "simli_slot_idle_minutes", 5)


class TestCapacityGate:
    @pytest.mark.asyncio
    async def test_counts_only_recently_active_sessions(self, configured):
        db = _db_returning(8)
        await get_simli_token(_actor=None, db=db)

        stmt = db.execute.await_args.args[0]
        compiled = stmt.compile(dialect=postgresql.dialect())
        sql = str(compiled).lower()
        assert "updated_at" in sql
        assert "current_state" in sql

        cutoffs = [v for v in compiled.params.values() if isinstance(v, datetime)]
        assert len(cutoffs) == 1
        expected = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert abs((cutoffs[0] - expected).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_full_house_falls_back_to_audio_only(self, configured):
        payload = await get_simli_token(_actor=None, db=_db_returning(8))
        assert payload["enabled"] is False
        assert payload["reason"] == "capacity"
        assert "8/8" in payload["detail"]

    @pytest.mark.asyncio
    async def test_idle_sessions_leave_room_for_a_new_candidate(
        self, configured, monkeypatch
    ):
        """With the stale sessions excluded the count drops below the cap, so
        the gate lets the candidate through to a real video token."""
        monkeypatch.setattr(
            speaking_examiner.httpx, "AsyncClient", _stub_simli_client
        )
        payload = await get_simli_token(_actor=None, db=_db_returning(3))
        assert payload["enabled"] is True
        assert payload["session_token"] == "tok-123"

    @pytest.mark.asyncio
    async def test_missing_credentials_short_circuit(self, monkeypatch):
        monkeypatch.setattr(settings, "simli_api_key", "")
        payload = await get_simli_token(_actor=None, db=_db_returning(0))
        assert payload == {"enabled": False, "reason": "not_configured"}
