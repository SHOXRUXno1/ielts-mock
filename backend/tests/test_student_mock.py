"""Blind full-mock assignment and anonymous student labels."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.main import app
from app.models.test import Test as TestModel
from app.schemas.test import TestDetailRead
from app.models.section_progress import SectionProgress, SectionState
from app.services import section_progress as sp
from app.services.student_mock import (
    cloak_test_read,
    pick_next_id,
    pick_unused_id,
    practice_set_label,
    start_next_full_mock,
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


def test_pick_next_id_recycles_when_every_paper_is_used():
    a, b = uuid.uuid4(), uuid.uuid4()
    recycled = pick_next_id([a, b], {a, b})
    assert recycled in {a, b}
    assert pick_next_id([], {a}) is None


def test_labels():
    assert student_mock_label(None) == "Full mock"
    assert student_mock_label(3) == "Mock #3"
    assert practice_set_label(None) == "Practice set"
    assert practice_set_label(2) == "Practice set #2"


@pytest.mark.asyncio
async def test_student_facing_title_picked_shows_practice_set(monkeypatch):
    """A deliberately-picked full mock is named by its catalogue number, even
    when the student already has a Mock #N slot for the same paper."""
    from app.services import student_mock as m

    uid = uuid.uuid4()
    tid = uuid.uuid4()

    async def _picked(_db, _uid, _tid):
        return True

    async def _practice(_db, _tid):
        return "Practice set #29"

    async def _slots(_db, _uid):
        return {tid: 14}  # would have been "Mock #14" without the pick

    monkeypatch.setattr(m, "latest_full_mock_picked", _picked)
    monkeypatch.setattr(m, "practice_label_for_test", _practice)
    monkeypatch.setattr(m, "slot_map_for_user", _slots)

    title = await m.student_facing_title(None, uid, tid)  # type: ignore[arg-type]
    assert title == "Practice set #29"


@pytest.mark.asyncio
async def test_student_facing_title_random_stays_mock(monkeypatch):
    """A random-rotation mock (not picked) keeps the anonymous Mock #N."""
    from app.services import student_mock as m

    uid = uuid.uuid4()
    tid = uuid.uuid4()

    async def _not_picked(_db, _uid, _tid):
        return False

    async def _slots(_db, _uid):
        return {tid: 14}

    monkeypatch.setattr(m, "latest_full_mock_picked", _not_picked)
    monkeypatch.setattr(m, "slot_map_for_user", _slots)

    title = await m.student_facing_title(None, uid, tid)  # type: ignore[arg-type]
    assert title == "Mock #14"


def _progress(stype: str, state: SectionState) -> SectionProgress:
    return SectionProgress(
        id=uuid.uuid4(),
        attempt_id=uuid.uuid4(),
        section_type=stype,
        state=state.value,
    )


def test_resume_section_prefers_active():
    rows = [
        _progress("listening", SectionState.SEALED),
        _progress("reading", SectionState.ACTIVE),
        _progress("writing", SectionState.NOT_STARTED),
        _progress("speaking", SectionState.NOT_STARTED),
    ]
    assert sp.resume_section_type(rows) == "reading"


def test_resume_section_first_not_started_when_none_active():
    rows = [
        _progress("listening", SectionState.NOT_STARTED),
        _progress("reading", SectionState.NOT_STARTED),
    ]
    assert sp.resume_section_type(rows) == "listening"


def test_resume_section_all_sealed_is_none():
    rows = [
        _progress("listening", SectionState.SEALED),
        _progress("reading", SectionState.SEALED),
        _progress("writing", SectionState.SEALED),
        _progress("speaking", SectionState.SEALED),
    ]
    assert sp.resume_section_type(rows) is None


def test_resume_part_first_unanswered():
    a, b, c, d = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    assert (
        sp.resume_part_number("listening", [[a, b], [c, d]], {a, b}) == 2
    )
    assert sp.resume_part_number("reading", [[a], [b], [c]], {a, b}) == 3


def test_resume_part_all_answered_returns_last():
    a, b = uuid.uuid4(), uuid.uuid4()
    assert sp.resume_part_number("writing", [[a], [b]], {a, b}) == 2


def test_resume_part_speaking_is_none():
    a = uuid.uuid4()
    assert sp.resume_part_number("speaking", [[a]], {a}) is None


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


def test_start_next_does_not_import_settings_service():
    from app.services import student_mock as module

    assert not hasattr(module, "settings_service")


@pytest.mark.asyncio
async def test_start_next_full_mock_does_not_touch_section_settings():
    user_id = uuid.uuid4()
    test_id = uuid.uuid4()

    user = MagicMock()
    user.id = user_id

    test = MagicMock(spec=TestModel)
    test.id = test_id
    test.is_published = True

    def _boom(_self):
        raise RuntimeError("lazy section_settings must not be loaded")

    type(test).section_settings = property(_boom)

    lock_result = MagicMock()
    lock_result.scalar_one_or_none.return_value = user
    live_result = MagicMock()
    live_result.scalar_one_or_none.return_value = None
    used_result = MagicMock()
    used_result.all.return_value = []
    published_result = MagicMock()
    published_result.all.return_value = [(test_id,)]

    session = MagicMock()
    session.execute = AsyncMock(
        side_effect=[lock_result, live_result, used_result, published_result]
    )
    session.get = AsyncMock(return_value=test)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    attempt = await start_next_full_mock(session, user_id)

    session.flush.assert_awaited()
    session.commit.assert_awaited()
    session.refresh.assert_awaited()
    assert attempt.test_id == test_id
    assert attempt.user_id == user_id
