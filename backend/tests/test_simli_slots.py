"""Video slots are claimed when the token is granted, not counted afterwards.

The browser asks for a token before its exam session exists, so counting
sessions alone let a simultaneous start admit everybody at once. These tests
pin the admission decision; the cross-process atomicity of the claim is proved
against real Postgres by scripts/_verify_simli_slots.py.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.core.config import settings
from app.services import simli_slots

ACTOR = "candidate@example.test"


def _db() -> MagicMock:
    db = MagicMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.commit = AsyncMock()
    return db


def _executed_sql(db: MagicMock) -> str:
    return " ".join(str(call.args[0]) for call in db.execute.await_args_list).lower()


@pytest.fixture(autouse=True)
def _plan(monkeypatch):
    monkeypatch.setattr(settings, "simli_max_concurrent", 8)
    monkeypatch.setattr(settings, "simli_lease_minutes", 3)


def _occupancy(monkeypatch, *, taken: int, actor_holds: bool = False):
    monkeypatch.setattr(
        simli_slots, "occupied_slots", AsyncMock(return_value=taken)
    )
    monkeypatch.setattr(
        simli_slots, "_holds_slot", AsyncMock(return_value=actor_holds)
    )


class TestClaimSlot:
    @pytest.mark.asyncio
    async def test_grants_a_slot_while_the_plan_has_room(self, monkeypatch):
        _occupancy(monkeypatch, taken=3)
        db = _db()

        granted, taken = await simli_slots.claim_slot(db, ACTOR)

        assert granted is True
        assert taken == 3
        assert "insert into simli_slot_leases" in _executed_sql(db)

    @pytest.mark.asyncio
    async def test_refuses_once_every_slot_is_held(self, monkeypatch):
        _occupancy(monkeypatch, taken=8)
        db = _db()

        granted, taken = await simli_slots.claim_slot(db, ACTOR)

        assert granted is False
        assert taken == 8
        assert "insert into simli_slot_leases" not in _executed_sql(db)

    @pytest.mark.asyncio
    async def test_a_reload_renews_the_claim_even_at_capacity(self, monkeypatch):
        """A candidate already on video must not lose it by refreshing the page,
        which would strand them on audio while their own slot sat occupied."""
        _occupancy(monkeypatch, taken=8, actor_holds=True)
        db = _db()

        granted, _ = await simli_slots.claim_slot(db, ACTOR)

        assert granted is True
        sql = _executed_sql(db)
        assert "insert into simli_slot_leases" in sql
        assert "on conflict" in sql

    @pytest.mark.asyncio
    async def test_serialises_the_decision_across_workers(self, monkeypatch):
        """Counting and claiming must be one indivisible step, or a burst of
        requests all read the same free count and all get in."""
        _occupancy(monkeypatch, taken=0)
        db = _db()

        await simli_slots.claim_slot(db, ACTOR)

        assert "pg_advisory_xact_lock" in _executed_sql(db)

    @pytest.mark.asyncio
    async def test_releases_the_lock_even_when_refused(self, monkeypatch):
        """The lock lives until the transaction ends, so a refusal that skipped
        the commit would freeze every later request."""
        _occupancy(monkeypatch, taken=99)
        db = _db()

        await simli_slots.claim_slot(db, ACTOR)

        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_commits_before_returning_so_simli_is_called_unlocked(
        self, monkeypatch
    ):
        _occupancy(monkeypatch, taken=1)
        db = _db()

        await simli_slots.claim_slot(db, ACTOR)

        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_broken_cap_still_admits_one_candidate(self, monkeypatch):
        """A misconfigured zero or negative cap should not switch video off for
        everyone with no way to tell why."""
        monkeypatch.setattr(settings, "simli_max_concurrent", 0)
        _occupancy(monkeypatch, taken=0)

        granted, _ = await simli_slots.claim_slot(_db(), ACTOR)
        assert granted is True


class TestOccupancyQuery:
    @pytest.mark.asyncio
    async def test_counts_claims_and_live_sessions_without_double_counting(self):
        db = _db()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one=lambda: 0))

        await simli_slots.occupied_slots(db)

        stmt = db.execute.await_args.args[0]
        sql = str(stmt.compile(dialect=postgresql.dialect())).lower()
        assert "simli_slot_leases" in sql
        assert "speaking_sessions" in sql
        # UNION, not UNION ALL: a candidate holding both a claim and a live
        # session occupies one slot, not two.
        assert "union" in sql
        assert "union all" not in sql

    @pytest.mark.asyncio
    async def test_ignores_expired_claims_and_silent_sessions(self):
        db = _db()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one=lambda: 0))

        await simli_slots.occupied_slots(db)

        stmt = db.execute.await_args.args[0]
        sql = str(stmt.compile(dialect=postgresql.dialect())).lower()
        assert "expires_at >" in sql
        assert "updated_at >=" in sql
        assert "current_state not in" in sql


class TestReleaseSlot:
    @pytest.mark.asyncio
    async def test_hands_the_slot_back(self):
        db = _db()
        await simli_slots.release_slot(db, ACTOR)

        assert "delete from simli_slot_leases" in _executed_sql(db)
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_survives_a_failing_database(self):
        """Releasing is a courtesy — the claim expires on its own — so it must
        never turn into an error on a request that already succeeded."""
        db = _db()
        db.execute = AsyncMock(side_effect=RuntimeError("connection lost"))

        await simli_slots.release_slot(db, ACTOR)


class TestPurgeExpiredLeases:
    @pytest.mark.asyncio
    async def test_reports_how_many_it_cleared(self):
        result = MagicMock()
        result.rowcount = 4
        db = _db()
        db.execute = AsyncMock(return_value=result)

        assert await simli_slots.purge_expired_leases(db) == 4
        assert "delete from simli_slot_leases" in _executed_sql(db)
