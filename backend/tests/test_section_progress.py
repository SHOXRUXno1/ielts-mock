"""Unit + integration tests for section_progress Phase 1."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import Actor, get_current_actor, get_current_admin
from app.core.database import get_db
from app.main import app
from app.models.attempt import Attempt, AttemptStatus
from app.models.section_progress import SectionProgress, SectionState
from app.models.test_section_settings import (
    TestSectionSettings as SectionSettingsRow,  # aliased: pytest collects Test* classes
)
from app.services import section_progress as sp


def _settings(stype: str, duration: int | None) -> SectionSettingsRow:
    return SectionSettingsRow(
        id=uuid.uuid4(),
        test_id=uuid.uuid4(),
        section_type=stype,
        duration_minutes=duration,
    )


def _row(
    stype: str,
    state: SectionState = SectionState.NOT_STARTED,
    *,
    started_at: datetime | None = None,
    ends_at: datetime | None = None,
) -> SectionProgress:
    return SectionProgress(
        id=uuid.uuid4(),
        attempt_id=uuid.uuid4(),
        section_type=stype,
        state=state.value,
        started_at=started_at,
        ends_at=ends_at,
    )


# ── Pure unit tests ───────────────────────────────────────────────────────────


def test_type_duration_reads_settings():
    settings = [
        _settings("listening", 30),
        _settings("reading", 60),
    ]
    assert sp.type_duration_minutes(settings, "listening") == 30
    assert sp.type_duration_minutes(settings, "reading") == 60


def test_compute_ends_at_listening():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [_settings("listening", 30)]
    ends = sp.compute_ends_at(now, settings, "listening")
    assert ends == now + timedelta(minutes=30)


def test_speaking_null_gets_hard_cap():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [_settings("speaking", None)]
    ends = sp.compute_ends_at(now, settings, "speaking")
    assert ends == now + timedelta(minutes=sp.SPEAKING_HARD_CAP_MINUTES)


def test_apply_enter_sets_started_and_ends():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [_settings("listening", 30)]
    rows = [
        _row("listening"),
        _row("reading"),
    ]
    entered, sealed = sp.apply_enter(rows, settings, "listening", now)
    assert sealed is None
    assert entered.state == SectionState.ACTIVE.value
    assert entered.started_at == now
    assert entered.ends_at == now + timedelta(minutes=30)


def test_apply_enter_idempotent_when_active():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [_settings("listening", 30)]
    started = now - timedelta(minutes=5)
    ends = started + timedelta(minutes=30)
    rows = [
        _row("listening", SectionState.ACTIVE, started_at=started, ends_at=ends),
    ]
    entered, sealed = sp.apply_enter(rows, settings, "listening", now)
    assert sealed is None
    assert entered.started_at == started
    assert entered.ends_at == ends


def test_apply_enter_sealed_raises_conflict():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [_settings("listening", 30)]
    rows = [_row("listening", SectionState.SEALED)]
    with pytest.raises(sp.SectionConflictError):
        sp.apply_enter(rows, settings, "listening", now)


def test_apply_enter_speaking_hard_cap():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [_settings("speaking", None)]
    rows = [_row("speaking")]
    entered, _ = sp.apply_enter(rows, settings, "speaking", now)
    assert entered.started_at == now
    assert entered.ends_at == now + timedelta(
        minutes=sp.SPEAKING_HARD_CAP_MINUTES
    )


def test_apply_enter_seals_previous_with_advance():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [_settings("listening", 30), _settings("reading", 60)]
    rows = [
        _row(
            "listening",
            SectionState.ACTIVE,
            started_at=now - timedelta(minutes=10),
            ends_at=now + timedelta(minutes=30),
        ),
        _row("reading"),
    ]
    entered, sealed = sp.apply_enter(rows, settings, "reading", now)
    assert entered.section_type == "reading"
    assert entered.state == SectionState.ACTIVE.value
    assert sealed is not None
    assert sealed.section_type == "listening"
    assert sealed.state == SectionState.SEALED.value
    assert sealed.sealed_reason == sp.SEAL_REASON_ADVANCE


def test_apply_enter_rejects_skip_ahead():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    settings = [
        _settings("listening", 30),
        _settings("reading", 60),
        _settings("writing", 60),
    ]
    rows = [
        _row("listening", SectionState.ACTIVE),
        _row("reading"),
        _row("writing"),
    ]
    with pytest.raises(sp.SectionConflictError, match="Previous sections"):
        sp.apply_enter(rows, settings, "writing", now)


def test_next_not_started_type():
    rows = [
        _row("listening", SectionState.SEALED),
        _row("reading", SectionState.ACTIVE),
        _row("writing"),
        _row("speaking"),
    ]
    # ACTIVE is not suggested — only NOT_STARTED.
    assert sp.next_not_started_type(rows) == "writing"
    rows[1].state = SectionState.SEALED.value
    assert sp.next_not_started_type(rows) == "writing"


def test_ensure_progress_rows_always_four():
    rows = sp.ensure_progress_rows(uuid.uuid4())
    assert [r.section_type for r in rows] == list(sp.TYPE_ORDER)
    assert all(r.state == SectionState.NOT_STARTED.value for r in rows)


def test_is_expired_respects_grace():
    now = datetime(2026, 7, 27, 10, 0, tzinfo=timezone.utc)
    ends = now - timedelta(seconds=10)
    row = _row("listening", SectionState.ACTIVE, ends_at=ends)
    assert sp.is_expired(row, now) is False
    assert sp.is_expired(row, now + timedelta(seconds=25)) is True


def test_all_sealed():
    rows = [
        _row("listening", SectionState.SEALED),
        _row("reading", SectionState.SEALED),
    ]
    assert sp.all_sealed(rows) is True
    rows.append(_row("writing"))
    assert sp.all_sealed(rows) is False


def test_all_sealed_respects_present_types():
    rows = [
        _row("listening", SectionState.SEALED),
        _row("reading", SectionState.SEALED),
        _row("writing", SectionState.SEALED),
        _row("speaking"),  # orphan not_started
    ]
    assert (
        sp.all_sealed(rows, ["listening", "reading", "writing"]) is True
    )
    assert sp.all_sealed(rows) is False


# ── HTTP: submit_answers 409 (existing Phase-2-ish paths left untouched) ─────


def test_submit_answers_409_when_section_sealed():
    attempt_id = uuid.uuid4()
    qid = uuid.uuid4()

    attempt = MagicMock(spec=Attempt)
    attempt.id = attempt_id
    attempt.user_id = uuid.uuid4()
    attempt.status = AttemptStatus.IN_PROGRESS

    progress = MagicMock(spec=SectionProgress)
    progress.section_type = "listening"
    progress.state = SectionState.SEALED.value
    progress.ends_at = None

    session = MagicMock()
    session.get = AsyncMock(return_value=attempt)

    q_result = MagicMock()
    q_result.all.return_value = [(qid, "listening")]
    prog_result = MagicMock()
    prog_result.scalars.return_value.all.return_value = [progress]

    session.execute = AsyncMock(side_effect=[q_result, prog_result])
    session.commit = AsyncMock()

    actor = Actor(
        role="student",
        sub=str(attempt.user_id),
        login="s1",
        user_id=attempt.user_id,
    )
    app.dependency_overrides[get_current_actor] = lambda: actor
    app.dependency_overrides[get_db] = lambda: session

    with TestClient(app) as client:
        resp = client.post(
            f"/attempts/{attempt_id}/answers",
            json={"answers": [{"question_id": str(qid), "response": {"answer": "a"}}]},
        )
    app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Section already completed"


def test_submit_answers_409_structured_when_expired():
    attempt_id = uuid.uuid4()
    qid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    ends = now - timedelta(seconds=60)

    attempt = MagicMock(spec=Attempt)
    attempt.id = attempt_id
    attempt.user_id = uuid.uuid4()
    attempt.status = AttemptStatus.IN_PROGRESS
    attempt.test_id = uuid.uuid4()

    progress = MagicMock(spec=SectionProgress)
    progress.attempt_id = attempt_id
    progress.section_type = "listening"
    progress.state = SectionState.ACTIVE.value
    progress.ends_at = ends
    progress.sealed_at = None
    progress.sealed_reason = None

    reading = MagicMock(spec=SectionProgress)
    reading.section_type = "reading"
    reading.state = SectionState.NOT_STARTED.value

    session = MagicMock()
    session.get = AsyncMock(return_value=attempt)

    q_result = MagicMock()
    q_result.all.return_value = [(qid, "listening")]
    prog_result = MagicMock()
    prog_result.scalars.return_value.all.return_value = [progress, reading]
    sections_result = MagicMock()
    sections_result.scalars.return_value.all.return_value = [
        MagicMock(type="listening"),
        MagicMock(type="reading"),
    ]

    session.execute = AsyncMock(
        side_effect=[q_result, prog_result, sections_result]
    )
    session.commit = AsyncMock()

    actor = Actor(
        role="student",
        sub=str(attempt.user_id),
        login="s1",
        user_id=attempt.user_id,
    )
    app.dependency_overrides[get_current_actor] = lambda: actor
    app.dependency_overrides[get_db] = lambda: session

    with TestClient(app) as client:
        resp = client.post(
            f"/attempts/{attempt_id}/answers",
            json={"answers": [{"question_id": str(qid), "response": {"answer": "a"}}]},
        )
    app.dependency_overrides.clear()

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["code"] == "SECTION_EXPIRED"
    assert detail["next_section"] == "reading"
    assert progress.state == SectionState.SEALED.value
    assert progress.sealed_reason == sp.SEAL_REASON_TIMEOUT
    assert progress.sealed_at == ends


def test_apply_timeout_seal_uses_ends_at():
    now = datetime(2026, 7, 27, 11, 0, tzinfo=timezone.utc)
    ends = datetime(2026, 7, 27, 10, 55, tzinfo=timezone.utc)
    row = _row("listening", SectionState.ACTIVE, ends_at=ends)
    sp.apply_timeout_seal(row, now)
    assert row.state == SectionState.SEALED.value
    assert row.sealed_reason == sp.SEAL_REASON_TIMEOUT
    assert row.sealed_at == ends


def test_expired_detail_shape():
    ends = datetime(2026, 8, 15, 10, 55, tzinfo=timezone.utc)
    row = _row("listening", SectionState.SEALED, ends_at=ends)
    row.sealed_at = ends
    detail = sp.expired_detail(row, "reading")
    assert detail["code"] == "SECTION_EXPIRED"
    assert detail["next_section"] == "reading"
    assert "10:55:00" in detail["message"]
    assert detail["sealed_at"] is not None


# ── Integration (real DB) ─────────────────────────────────────────────────────


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_admin] = lambda: Actor(
        role="admin",
        sub="test-admin",
        login="test-admin",
        user_id=None,
    )
    app.dependency_overrides[get_current_actor] = lambda: Actor(
        role="admin",
        sub="test-admin",
        login="test-admin",
        user_id=None,
    )
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def attempt_ctx(admin_client):
    """Create a published-ready test + attempt; yield (client, test_id, attempt_id)."""
    title = f"SP Phase1 {uuid.uuid4().hex[:8]}"
    created = admin_client.post(
        "/admin/tests/",
        json={"title": title, "description": "sp", "type": "academic"},
    )
    assert created.status_code == 201, created.text
    test = created.json()
    test_id = test["id"]

    # Ensure section settings have listening=30, speaking=null
    admin_client.patch(
        f"/admin/tests/{test_id}/section-settings/listening",
        json={"duration_minutes": 30},
    )
    admin_client.patch(
        f"/admin/tests/{test_id}/section-settings/speaking",
        json={"duration_minutes": None},
    )

    attempt_resp = admin_client.post(f"/tests/{test_id}/attempts")
    assert attempt_resp.status_code == 201, attempt_resp.text
    attempt_id = attempt_resp.json()["id"]

    yield admin_client, test_id, attempt_id

    admin_client.delete(f"/admin/tests/{test_id}")


class TestSectionProgressIntegration:
    def test_create_attempt_has_four_not_started(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        resp = client.get(f"/attempts/{attempt_id}/progress")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "server_now" in body
        assert len(body["sections"]) == 4
        by_type = {s["section_type"]: s for s in body["sections"]}
        assert set(by_type) == {"listening", "reading", "writing", "speaking"}
        assert all(s["state"] == "not_started" for s in body["sections"])

    def test_enter_listening_sets_active_and_ends_at(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        resp = client.post(f"/attempts/{attempt_id}/sections/listening/enter")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["section_type"] == "listening"
        assert body["state"] == "active"
        assert body["started_at"] is not None
        assert body["ends_at"] is not None
        started = datetime.fromisoformat(body["started_at"].replace("Z", "+00:00"))
        ends = datetime.fromisoformat(body["ends_at"].replace("Z", "+00:00"))
        assert ends - started == timedelta(minutes=30)

    def test_enter_listening_idempotent(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        first = client.post(f"/attempts/{attempt_id}/sections/listening/enter").json()
        second = client.post(f"/attempts/{attempt_id}/sections/listening/enter").json()
        assert second["started_at"] == first["started_at"]
        assert second["ends_at"] == first["ends_at"]
        assert second["state"] == "active"

    def test_enter_reading_seals_listening_with_advance(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        client.post(f"/attempts/{attempt_id}/sections/listening/enter")
        resp = client.post(f"/attempts/{attempt_id}/sections/reading/enter")
        assert resp.status_code == 200, resp.text
        assert resp.json()["state"] == "active"
        assert resp.json()["section_type"] == "reading"

        progress = client.get(f"/attempts/{attempt_id}/progress").json()
        by_type = {s["section_type"]: s for s in progress["sections"]}
        assert by_type["listening"]["state"] == "sealed"
        assert by_type["listening"]["sealed_reason"] == "advance"
        assert by_type["reading"]["state"] == "active"

    def test_enter_writing_skips_reading_returns_409(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        client.post(f"/attempts/{attempt_id}/sections/listening/enter")
        resp = client.post(f"/attempts/{attempt_id}/sections/writing/enter")
        assert resp.status_code == 409, resp.text
        assert resp.json()["detail"] == "Previous sections must be completed first"

    def test_enter_sealed_returns_409(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        client.post(f"/attempts/{attempt_id}/sections/listening/enter")
        client.post(f"/attempts/{attempt_id}/sections/reading/enter")
        resp = client.post(f"/attempts/{attempt_id}/sections/listening/enter")
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Section already completed"

    def test_seal_active_returns_next_section(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        client.post(f"/attempts/{attempt_id}/sections/listening/enter")
        resp = client.post(
            f"/attempts/{attempt_id}/sections/listening/seal",
            json={"answers": [], "reason": "manual"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["sealed"]["section_type"] == "listening"
        assert body["sealed"]["sealed_reason"] == "manual"
        assert body["next_section"] == "reading"

    def test_seal_not_started_returns_409(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        resp = client.post(
            f"/attempts/{attempt_id}/sections/listening/seal",
            json={"answers": []},
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Section not active"

    def test_enter_on_finished_attempt_returns_409(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        # Finish without answers — may still complete scoring path.
        finish = client.post(f"/attempts/{attempt_id}/finish")
        assert finish.status_code == 200, finish.text
        resp = client.post(f"/attempts/{attempt_id}/sections/listening/enter")
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Test not in progress"

    def test_get_progress_includes_server_now(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        resp = client.get(f"/attempts/{attempt_id}/progress")
        assert resp.status_code == 200
        body = resp.json()
        assert body["server_now"]
        assert len(body["sections"]) == 4

    def test_enter_speaking_null_duration_hard_cap(self, attempt_ctx):
        client, _test_id, attempt_id = attempt_ctx
        for stype in ("listening", "reading", "writing"):
            enter = client.post(f"/attempts/{attempt_id}/sections/{stype}/enter")
            assert enter.status_code == 200, enter.text
            seal = client.post(
                f"/attempts/{attempt_id}/sections/{stype}/seal",
                json={"answers": [], "reason": "manual"},
            )
            assert seal.status_code == 200, seal.text
        resp = client.post(f"/attempts/{attempt_id}/sections/speaking/enter")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        started = datetime.fromisoformat(body["started_at"].replace("Z", "+00:00"))
        ends = datetime.fromisoformat(body["ends_at"].replace("Z", "+00:00"))
        assert ends - started == timedelta(minutes=sp.SPEAKING_HARD_CAP_MINUTES)

    def test_concurrent_enter_second_is_idempotent(self, attempt_ctx):
        """Two sequential ENTER calls (simulating a race after lock) stay idempotent."""
        client, _test_id, attempt_id = attempt_ctx
        a = client.post(f"/attempts/{attempt_id}/sections/listening/enter").json()
        b = client.post(f"/attempts/{attempt_id}/sections/listening/enter").json()
        assert a["started_at"] == b["started_at"]
        assert a["ends_at"] == b["ends_at"]

        progress = client.get(f"/attempts/{attempt_id}/progress").json()
        active = [s for s in progress["sections"] if s["state"] == "active"]
        assert len(active) == 1
        assert active[0]["section_type"] == "listening"
