"""Tests for GET /tests/{test_id}/attempts/current."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.main import app
from app.models.attempt import Attempt, AttemptStatus
from app.models.test import Test as TestModel


def _session_returning(value):
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    session.execute = AsyncMock(return_value=result)
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def student_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def test_id() -> uuid.UUID:
    return uuid.uuid4()


def test_current_attempt_404_when_none(student_id, test_id):
    published = MagicMock(spec=TestModel)
    published.id = test_id
    published.is_published = True

    session = _session_returning(None)
    session.get = AsyncMock(return_value=published)

    actor = Actor(
        role="student",
        sub=str(student_id),
        login="student1",
        user_id=student_id,
    )
    app.dependency_overrides[get_current_actor] = lambda: actor
    app.dependency_overrides[get_db] = lambda: session

    with TestClient(app) as client:
        resp = client.get(f"/tests/{test_id}/attempts/current")
    app.dependency_overrides.clear()

    assert resp.status_code == 404


def test_current_attempt_returns_in_progress(student_id, test_id):
    published = MagicMock(spec=TestModel)
    published.id = test_id
    published.is_published = True

    attempt = MagicMock(spec=Attempt)
    attempt.id = uuid.uuid4()
    attempt.test_id = test_id
    attempt.user_id = student_id
    attempt.status = AttemptStatus.IN_PROGRESS
    attempt.started_at = datetime.now(timezone.utc)
    attempt.finished_at = None
    attempt.overall_band = None
    attempt.listening_band = None
    attempt.reading_band = None
    attempt.writing_band = None
    attempt.speaking_band = None
    attempt.listening_raw = None
    attempt.reading_raw = None
    attempt.flagged_overtime = False
    attempt.created_at = datetime.now(timezone.utc)
    attempt.updated_at = datetime.now(timezone.utc)

    # First get() is Test; execute returns Attempt
    session = MagicMock()
    session.get = AsyncMock(return_value=published)
    result = MagicMock()
    result.scalar_one_or_none.return_value = attempt
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()

    actor = Actor(
        role="student",
        sub=str(student_id),
        login="student1",
        user_id=student_id,
    )
    app.dependency_overrides[get_current_actor] = lambda: actor
    app.dependency_overrides[get_db] = lambda: session

    with TestClient(app) as client:
        resp = client.get(f"/tests/{test_id}/attempts/current")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["id"] == str(attempt.id)
    assert resp.json()["status"] == "in_progress"


def test_current_attempt_403_unpublished_for_student(student_id, test_id):
    unpublished = MagicMock(spec=TestModel)
    unpublished.id = test_id
    unpublished.is_published = False

    session = _session_returning(None)
    session.get = AsyncMock(return_value=unpublished)

    actor = Actor(
        role="student",
        sub=str(student_id),
        login="student1",
        user_id=student_id,
    )
    app.dependency_overrides[get_current_actor] = lambda: actor
    app.dependency_overrides[get_db] = lambda: session

    with TestClient(app) as client:
        resp = client.get(f"/tests/{test_id}/attempts/current")
    app.dependency_overrides.clear()

    assert resp.status_code == 403
