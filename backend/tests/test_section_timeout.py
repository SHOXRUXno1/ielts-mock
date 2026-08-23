"""Phase 2: server-side section deadline enforcement on answer submit."""

from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.deps import Actor, get_current_actor, get_current_admin
from app.core.config import settings
from app.main import app
from app.services.section_progress import GRACE_SECONDS


@pytest.fixture
def client():
    actor = Actor(
        role="admin",
        sub="timeout-admin",
        login="timeout-admin",
        user_id=None,
    )
    app.dependency_overrides[get_current_admin] = lambda: actor
    app.dependency_overrides[get_current_actor] = lambda: actor
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _run_async(coro):
    """Run async DB helpers on a fresh loop in a worker thread.

    TestClient binds the shared async engine to its own loop; a separate
    engine + thread avoids 'Future attached to a different loop'.
    """

    def _runner():
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_runner).result()


async def _aset_ends_at(attempt_id: str, section_type: str, ends_at: datetime) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text(
                    """
                    UPDATE section_progress
                    SET ends_at = :ends_at, state = 'active'
                    WHERE attempt_id = CAST(:aid AS uuid)
                      AND section_type = :stype
                    """
                ),
                {
                    "ends_at": ends_at,
                    "aid": attempt_id,
                    "stype": section_type,
                },
            )
    finally:
        await eng.dispose()


async def _aprogress_row(attempt_id: str, section_type: str) -> dict:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT state, sealed_reason, sealed_at, ends_at
                    FROM section_progress
                    WHERE attempt_id = CAST(:aid AS uuid)
                      AND section_type = :stype
                    """
                ),
                {"aid": attempt_id, "stype": section_type},
            )
            row = result.mappings().one()
            return dict(row)
    finally:
        await eng.dispose()


def _set_ends_at(attempt_id: str, section_type: str, ends_at: datetime) -> None:
    _run_async(_aset_ends_at(attempt_id, section_type, ends_at))


def _progress_row(attempt_id: str, section_type: str) -> dict:
    return _run_async(_aprogress_row(attempt_id, section_type))


@pytest.fixture
def listening_attempt(client):
    """Create test + listening MCQ + attempt; enter listening."""
    created = client.post(
        "/admin/tests/",
        json={
            "title": f"Timeout {uuid.uuid4().hex[:8]}",
            "description": "timeout",
            "type": "academic",
        },
    )
    assert created.status_code == 201, created.text
    test = created.json()
    test_id = test["id"]
    listening = next(s for s in test["sections"] if s["type"] == "listening")

    q = client.post(
        f"/admin/sections/{listening['id']}/questions",
        json={
            "order": 1,
            "question_type": "mcq",
            "content": {"prompt": "Pick one", "options": ["A", "B", "C"]},
            "answer_key": {"correct": "A"},
        },
    )
    assert q.status_code == 201, q.text
    question_id = q.json()["id"]

    attempt = client.post(f"/tests/{test_id}/attempts")
    assert attempt.status_code == 201, attempt.text
    attempt_id = attempt.json()["id"]

    enter = client.post(f"/attempts/{attempt_id}/sections/listening/enter")
    assert enter.status_code == 200, enter.text

    yield client, test_id, attempt_id, question_id

    client.delete(f"/admin/tests/{test_id}")


def _submit(client, attempt_id: str, question_id: str):
    return client.post(
        f"/attempts/{attempt_id}/answers",
        json={
            "answers": [
                {"question_id": question_id, "response": {"answer": "A"}},
            ]
        },
    )


class TestSectionDeadlineEnforcement:
    def test_submit_during_active_ok(self, listening_attempt):
        client, _tid, attempt_id, qid = listening_attempt
        resp = _submit(client, attempt_id, qid)
        assert resp.status_code == 200, resp.text
        assert resp.json()["saved"] == 1

    def test_submit_5s_before_deadline_ok(self, listening_attempt):
        client, _tid, attempt_id, qid = listening_attempt
        _set_ends_at(
            attempt_id,
            "listening",
            datetime.now(timezone.utc) + timedelta(seconds=5),
        )
        resp = _submit(client, attempt_id, qid)
        assert resp.status_code == 200, resp.text

    def test_submit_10s_into_grace_ok(self, listening_attempt):
        client, _tid, attempt_id, qid = listening_attempt
        # deadline + 10s is still inside GRACE_SECONDS (30)
        assert 10 < GRACE_SECONDS
        _set_ends_at(
            attempt_id,
            "listening",
            datetime.now(timezone.utc) - timedelta(seconds=10),
        )
        resp = _submit(client, attempt_id, qid)
        assert resp.status_code == 200, resp.text

    def test_submit_60s_past_deadline_expires(self, listening_attempt):
        client, _tid, attempt_id, qid = listening_attempt
        ends = datetime.now(timezone.utc) - timedelta(seconds=60)
        _set_ends_at(attempt_id, "listening", ends)

        resp = _submit(client, attempt_id, qid)
        assert resp.status_code == 409, resp.text
        detail = resp.json()["detail"]
        assert detail["code"] == "SECTION_EXPIRED"
        assert detail["next_section"] == "reading"
        assert detail["sealed_at"] is not None

        row = _progress_row(attempt_id, "listening")
        assert row["state"] == "sealed"
        assert row["sealed_reason"] == "timeout"
        # sealed_at should match the official ends_at (within 1s)
        sealed_at = row["sealed_at"]
        if sealed_at.tzinfo is None:
            sealed_at = sealed_at.replace(tzinfo=timezone.utc)
        stored_ends = row["ends_at"]
        if stored_ends.tzinfo is None:
            stored_ends = stored_ends.replace(tzinfo=timezone.utc)
        assert abs((sealed_at - stored_ends).total_seconds()) < 1

    def test_second_submit_after_timeout_still_409(self, listening_attempt):
        """Concurrent/late submits: after one seals, others get sealed 409."""
        client, _tid, attempt_id, qid = listening_attempt
        _set_ends_at(
            attempt_id,
            "listening",
            datetime.now(timezone.utc) - timedelta(seconds=60),
        )
        first = _submit(client, attempt_id, qid)
        assert first.status_code == 409
        assert first.json()["detail"]["code"] == "SECTION_EXPIRED"

        second = _submit(client, attempt_id, qid)
        assert second.status_code == 409
        # Already sealed — plain conflict, not a second timeout seal.
        assert second.json()["detail"] == "Section already completed"

    def test_speaking_past_safety_cap_expires(self, client, caplog):
        created = client.post(
            "/admin/tests/",
            json={
                "title": f"SpeakCap {uuid.uuid4().hex[:8]}",
                "description": "cap",
                "type": "academic",
            },
        )
        assert created.status_code == 201, created.text
        test = created.json()
        test_id = test["id"]
        speaking = next(s for s in test["sections"] if s["type"] == "speaking")

        q = client.post(
            f"/admin/sections/{speaking['id']}/questions",
            json={
                "order": 1,
                "question_type": "short_answer",
                "content": {"prompt": "Tell me about yourself."},
                "answer_key": {"correct": "x"},
            },
        )
        assert q.status_code == 201, q.text
        question_id = q.json()["id"]

        attempt = client.post(f"/tests/{test_id}/attempts")
        assert attempt.status_code == 201
        attempt_id = attempt.json()["id"]

        enter = client.post(f"/attempts/{attempt_id}/sections/speaking/enter")
        assert enter.status_code == 200, enter.text
        # Simulate a session that overran the safety cap (past grace).
        _set_ends_at(
            attempt_id,
            "speaking",
            datetime.now(timezone.utc) - timedelta(seconds=60),
        )

        with caplog.at_level("WARNING", logger="app.api.attempts"):
            resp = _submit(client, attempt_id, question_id)

        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "SECTION_EXPIRED"
        row = _progress_row(attempt_id, "speaking")
        assert row["state"] == "sealed"
        assert row["sealed_reason"] == "timeout"
        assert any(
            "Speaking session exceeded safety cap" in r.message for r in caplog.records
        )

        client.delete(f"/admin/tests/{test_id}")
