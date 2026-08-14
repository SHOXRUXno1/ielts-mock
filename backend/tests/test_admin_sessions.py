"""Unit + HTTP tests for admin session tracking."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.models.admin_session import AdminSession
from app.services.admin_sessions import (
    ONLINE_WINDOW,
    client_ip,
    close_stale_sessions,
    end_session,
    is_online,
    start_session,
)


def _request(
    *,
    ip: str = "10.0.0.5",
    forwarded: str | None = None,
    ua: str = "Mozilla/5.0 Chrome/138.0",
):
    headers = {"user-agent": ua}
    if forwarded:
        headers["x-forwarded-for"] = forwarded
    return SimpleNamespace(
        headers=headers,
        client=SimpleNamespace(host=ip),
    )


class TestClientIp:
    def test_prefers_forwarded_for(self):
        req = _request(forwarded="203.0.113.9, 10.0.0.1")
        assert client_ip(req) == "203.0.113.9"

    def test_falls_back_to_client_host(self):
        req = _request(ip="192.168.1.10")
        assert client_ip(req) == "192.168.1.10"


class TestIsOnline:
    def test_online_when_recent(self):
        now = datetime.now(timezone.utc)
        session = SimpleNamespace(
            ended_at=None,
            last_seen_at=now - timedelta(minutes=5),
        )
        assert is_online(session, now=now) is True

    def test_offline_when_stale(self):
        now = datetime.now(timezone.utc)
        session = SimpleNamespace(
            ended_at=None,
            last_seen_at=now - ONLINE_WINDOW - timedelta(minutes=1),
        )
        assert is_online(session, now=now) is False

    def test_offline_when_ended(self):
        now = datetime.now(timezone.utc)
        session = SimpleNamespace(
            ended_at=now,
            last_seen_at=now,
        )
        assert is_online(session, now=now) is False


class TestStartSession:
    @pytest.mark.asyncio
    async def test_writes_forwarded_ip_and_parses_ua(self):
        captured: list[AdminSession] = []

        db = MagicMock()
        db.add = MagicMock(side_effect=lambda obj: captured.append(obj))
        db.commit = AsyncMock()

        async def _refresh(obj):
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

        db.refresh = AsyncMock(side_effect=_refresh)

        req = _request(
            forwarded="198.51.100.7",
            ua=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            ),
        )
        sid = await start_session(
            db,
            login="admin@example.com",
            name="Demo Bob",
            user_id=None,
            request=req,
        )
        assert sid is not None
        assert len(captured) == 1
        row = captured[0]
        assert row.ip_address == "198.51.100.7"
        assert row.actor_login == "admin@example.com"
        assert row.device_type == "desktop"
        assert row.browser and row.browser.startswith("Chrome")
        assert row.os_name == "Windows"
        assert row.ended_at is None


class TestEndSession:
    @pytest.mark.asyncio
    async def test_idempotent_update(self):
        result = MagicMock()
        result.rowcount = 1
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()

        sid = uuid4()
        assert await end_session(db, sid, "logout") is True
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

        # None / invalid sid
        assert await end_session(db, None, "logout") is False
        assert await end_session(db, "not-a-uuid", "logout") is False


class TestCloseStaleSessions:
    @pytest.mark.asyncio
    async def test_runs_two_updates_and_commits(self):
        idle = MagicMock(rowcount=2)
        expired = MagicMock(rowcount=1)
        db = MagicMock()
        db.execute = AsyncMock(side_effect=[idle, expired])
        db.commit = AsyncMock()

        n = await close_stale_sessions(db)
        assert n == 3
        assert db.execute.await_count == 2
        db.commit.assert_awaited_once()

        # First update should set end_reason=timeout using last_seen_at
        first_stmt = db.execute.await_args_list[0].args[0]
        compiled = first_stmt.compile(dialect=postgresql.dialect())
        params = compiled.params
        assert params.get("end_reason") == "timeout"

        second_stmt = db.execute.await_args_list[1].args[0]
        compiled2 = second_stmt.compile(dialect=postgresql.dialect())
        assert compiled2.params.get("end_reason") == "expired"


class TestDevicesApiAuth:
    def test_list_requires_auth(self, anon_client):
        resp = anon_client.get("/admin/devices/")
        assert resp.status_code in (401, 403)

    def test_summary_requires_auth(self, anon_client):
        resp = anon_client.get("/admin/devices/summary")
        assert resp.status_code in (401, 403)

    def test_list_marks_current_session(self, auth_client):
        now = datetime.now(timezone.utc)
        sid = uuid4()
        session = AdminSession(
            id=sid,
            actor_login="test@example.com",
            actor_name="Demo",
            ip_address="127.0.0.1",
            user_agent="Chrome",
            device_type="desktop",
            browser="Chrome 138",
            os_name="Windows",
            login_at=now,
            last_seen_at=now,
        )

        from app.api.deps import Actor

        actor = Actor(
            role="admin",
            sub="test@example.com",
            login="test@example.com",
            session_id=sid,
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [session]
        db = MagicMock()
        db.execute = AsyncMock(return_value=result)

        from app.api.deps import get_current_admin
        from app.core.database import get_db
        from app.main import app

        app.dependency_overrides[get_current_admin] = lambda: actor
        app.dependency_overrides[get_db] = lambda: db
        try:
            resp = auth_client.get("/admin/devices/")
        finally:
            app.dependency_overrides.pop(get_current_admin, None)
            # auth_client fixture clears all overrides after yield; keep consistent
            pass

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["is_current"] is True
        assert data[0]["is_online"] is True
        assert data[0]["id"] == str(sid)
