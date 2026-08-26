"""Blind full-mock assignment and anonymous student labels."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.main import app
from app.models.test import Test as TestModel
from app.schemas.test import TestDetailRead
from app.services.student_mock import (
    cloak_test_read,
    pick_unused_id,
    practice_set_label,
    student_mock_label,
)


def test_pick_unused_id_skips_used():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    unused = pick_unused_id([a, b, c], {a, c})
    assert unused == b


def test_pick_unused_id_empty_pool():
    a = uuid.uuid4()
    assert pick_unused_id([a], {a}) is None
    assert pick_unused_id([], set()) is None


def test_labels():
    assert student_mock_label(None) == "Full mock"
    assert student_mock_label(3) == "Mock #3"
    assert practice_set_label(None) == "Practice set"
    assert practice_set_label(2) == "Practice set #2"


def test_cloak_test_read_strips_cambridge():
    tid = uuid.uuid4()
    raw = TestDetailRead(
        id=tid,
        title="Cambridge IELTS 18 – Test 2",
        description="Official booklet",
        is_published=True,
        type="academic",
        book_name="Cambridge IELTS 18",
        book_slug="cambridge-ielts-18",
        test_number=2,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        sections=[],
        section_settings=[],
    )
    cloaked = cloak_test_read(raw, "Mock #1")
    assert cloaked.title == "Mock #1"
    assert cloaked.description is None
    assert cloaked.book_name is None
    assert cloaked.book_slug == "mock"
    assert cloaked.test_number == 0
    assert raw.title.startswith("Cambridge")


def _session_returning(value):
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    session.execute = AsyncMock(return_value=result)
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


def test_student_cannot_start_chosen_full_mock():
    student_id = uuid.uuid4()
    test_id = uuid.uuid4()
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
        resp = client.post(f"/tests/{test_id}/attempts")
    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert "assigned automatically" in resp.json()["detail"]


def test_student_slug_redirect_is_hidden():
    student_id = uuid.uuid4()
    test_id = uuid.uuid4()
    published = MagicMock(spec=TestModel)
    published.id = test_id
    published.is_published = True
    published.book_slug = "cambridge-ielts-18"
    published.test_number = 2

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
        resp = client.get(f"/tests/{test_id}/slug-redirect")
    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert "cambridge" not in resp.text.lower()
