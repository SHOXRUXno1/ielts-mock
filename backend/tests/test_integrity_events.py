"""Unit tests for /attempts/{id}/integrity-event.

The full-mock scoring path is exercised by other tests; here the focus is on
the four behaviours the endpoint uniquely owns:
    * unknown event types are rejected,
    * a foreign attempt cannot be touched,
    * a non-terminal call records without closing the attempt,
    * a terminal call closes the attempt exactly once.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api import attempts as attempts_api
from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.main import app
from app.models.attempt import Attempt, AttemptStatus


def _attempt(status: AttemptStatus = AttemptStatus.IN_PROGRESS) -> MagicMock:
    a = MagicMock(spec=Attempt)
    a.id = uuid.uuid4()
    a.user_id = uuid.uuid4()
    a.status = status
    a.mode = "full_mock"
    a.integrity_events = None
    return a


def _install(session: MagicMock, actor: Actor) -> None:
    app.dependency_overrides[get_current_actor] = lambda: actor
    app.dependency_overrides[get_db] = lambda: session


def _teardown() -> None:
    app.dependency_overrides.clear()


def test_unknown_event_type_rejected():
    a = _attempt()
    session = MagicMock()
    session.get = AsyncMock(return_value=a)
    session.commit = AsyncMock()
    _install(
        session,
        Actor(role="student", sub=str(a.user_id), login="s", user_id=a.user_id),
    )
    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/attempts/{a.id}/integrity-event",
                json={"type": "tab_switch", "terminal": False},
            )
    finally:
        _teardown()

    assert resp.status_code == 400
    session.get.assert_not_called()  # rejected before any DB work


def test_finished_attempt_rejected():
    a = _attempt(status=AttemptStatus.COMPLETED)
    session = MagicMock()
    session.get = AsyncMock(return_value=a)
    _install(
        session,
        Actor(role="student", sub=str(a.user_id), login="s", user_id=a.user_id),
    )
    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/attempts/{a.id}/integrity-event",
                json={"type": "fullscreen_exit", "terminal": True},
            )
    finally:
        _teardown()

    assert resp.status_code == 400
    assert "already finished" in resp.json()["detail"].lower()


def test_non_terminal_appends_event_without_scoring():
    a = _attempt()
    session = MagicMock()
    session.get = AsyncMock(return_value=a)
    session.commit = AsyncMock()
    _install(
        session,
        Actor(role="student", sub=str(a.user_id), login="s", user_id=a.user_id),
    )
    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/attempts/{a.id}/integrity-event",
                json={"type": "fullscreen_exit", "terminal": False},
            )
    finally:
        _teardown()

    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is True
    assert body["terminated"] is False
    assert body["events_count"] == 1
    assert a.integrity_events is not None
    assert a.integrity_events[0]["type"] == "fullscreen_exit"
    assert "at" in a.integrity_events[0]
    # Attempt must stay open — scoring is only for terminal calls.
    assert a.status == AttemptStatus.IN_PROGRESS
    session.commit.assert_awaited_once()


def test_terminal_call_delegates_to_finish_helper(monkeypatch):
    """The terminal branch must go through _finish_full_mock_attempt so the
    seal/score path stays single-sourced."""
    a = _attempt()
    calls: list[Attempt] = []

    async def fake_finish(db, attempt):
        calls.append(attempt)
        attempt.status = AttemptStatus.COMPLETED
        return attempt

    monkeypatch.setattr(attempts_api, "_finish_full_mock_attempt", fake_finish)

    session = MagicMock()
    session.get = AsyncMock(return_value=a)
    session.commit = AsyncMock()
    _install(
        session,
        Actor(role="student", sub=str(a.user_id), login="s", user_id=a.user_id),
    )
    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/attempts/{a.id}/integrity-event",
                json={"type": "fullscreen_exit", "terminal": True},
            )
    finally:
        _teardown()

    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is True
    assert body["terminated"] is True
    assert calls == [a], "must call the shared finish helper once"
    assert a.integrity_events[0]["type"] == "fullscreen_exit"


def test_reload_event_is_accepted_and_never_terminal():
    """A page that loads outside fullscreen is logged but must not end the
    attempt — a browser cannot restore fullscreen without a user gesture, so
    this also covers an honest student returning after a crash."""
    a = _attempt()
    session = MagicMock()
    session.get = AsyncMock(return_value=a)
    session.commit = AsyncMock()
    _install(
        session,
        Actor(role="student", sub=str(a.user_id), login="s", user_id=a.user_id),
    )
    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/attempts/{a.id}/integrity-event",
                json={"type": "fullscreen_reload", "terminal": False},
            )
    finally:
        _teardown()

    assert resp.status_code == 200
    assert resp.json()["terminated"] is False
    assert a.integrity_events[0]["type"] == "fullscreen_reload"
    assert a.status == AttemptStatus.IN_PROGRESS


def test_other_students_attempt_forbidden():
    a = _attempt()
    session = MagicMock()
    session.get = AsyncMock(return_value=a)
    intruder = Actor(
        role="student", sub="other", login="other", user_id=uuid.uuid4()
    )
    _install(session, intruder)
    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/attempts/{a.id}/integrity-event",
                json={"type": "fullscreen_exit", "terminal": False},
            )
    finally:
        _teardown()

    assert resp.status_code == 403
