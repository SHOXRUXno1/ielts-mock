"""Race / reliability coverage for the 15-student readiness work."""

from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.attempts import start_attempt
from app.api.deps import Actor, get_current_actor, get_current_admin
from app.core.config import settings
from app.main import app
from app.models.attempt import Attempt, AttemptMode, AttemptStatus
from app.models.evaluation_job import EvaluationJob, JobStatus
from app.services.section_progress import GRACE_SECONDS
from app.services.worker import _claim_jobs, _requeue_stuck_jobs


@pytest.fixture
def client():
    actor = Actor(
        role="admin",
        sub="concurrency-admin",
        login="concurrency-admin",
        user_id=None,
    )
    app.dependency_overrides[get_current_admin] = lambda: actor
    app.dependency_overrides[get_current_actor] = lambda: actor
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _run_async(coro):
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


def _set_ends_at(attempt_id: str, section_type: str, ends_at: datetime) -> None:
    _run_async(_aset_ends_at(attempt_id, section_type, ends_at))


@pytest.fixture
def listening_attempt(client):
    created = client.post(
        "/admin/tests/",
        json={
            "title": f"Concurrency {uuid.uuid4().hex[:8]}",
            "description": "concurrency",
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
    assert enter.json().get("grace_seconds") == GRACE_SECONDS

    yield client, test_id, attempt_id, question_id
    client.delete(f"/admin/tests/{test_id}")


def _submit(client, attempt_id: str, question_id: str, answer: str = "A"):
    return client.post(
        f"/attempts/{attempt_id}/answers",
        json={
            "answers": [
                {"question_id": question_id, "response": {"answer": answer}},
            ]
        },
    )


class TestAnswerUpsertRace:
    def test_parallel_autosaves_do_not_duplicate(self, listening_attempt):
        client, _tid, attempt_id, qid = listening_attempt

        def _one(value: str):
            return _submit(client, attempt_id, qid, value)

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(_one, f"v{i}") for i in range(8)]
            statuses = [f.result().status_code for f in futures]

        assert all(s == 200 for s in statuses), statuses

        def _count():
            async def _inner():
                eng = create_async_engine(settings.database_url)
                try:
                    async with eng.connect() as conn:
                        result = await conn.execute(
                            text(
                                """
                                SELECT COUNT(*) FROM answers
                                WHERE attempt_id = CAST(:aid AS uuid)
                                  AND question_id = CAST(:qid AS uuid)
                                """
                            ),
                            {"aid": attempt_id, "qid": qid},
                        )
                        return int(result.scalar_one())
                finally:
                    await eng.dispose()

            return _run_async(_inner())

        assert _count() == 1


class TestGraceBoundary:
    def test_submit_one_second_before_grace_ends_ok(self, listening_attempt):
        client, _tid, attempt_id, qid = listening_attempt
        _set_ends_at(
            attempt_id,
            "listening",
            datetime.now(timezone.utc) - timedelta(seconds=GRACE_SECONDS - 1),
        )
        resp = _submit(client, attempt_id, qid)
        assert resp.status_code == 200, resp.text

    def test_submit_one_second_after_grace_expires(self, listening_attempt):
        client, _tid, attempt_id, qid = listening_attempt
        _set_ends_at(
            attempt_id,
            "listening",
            datetime.now(timezone.utc) - timedelta(seconds=GRACE_SECONDS + 1),
        )
        resp = _submit(client, attempt_id, qid)
        assert resp.status_code == 409, resp.text
        assert resp.json()["detail"]["code"] == "SECTION_EXPIRED"


class TestStartAttemptIntegrityError:
    @pytest.mark.asyncio
    async def test_integrity_error_returns_existing_attempt(self):
        test_id = uuid.uuid4()
        user_id = uuid.uuid4()
        existing = Attempt(
            id=uuid.uuid4(),
            test_id=test_id,
            user_id=user_id,
            status=AttemptStatus.IN_PROGRESS,
            mode=AttemptMode.FULL_MOCK.value,
            started_at=datetime.now(timezone.utc),
        )

        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock(side_effect=IntegrityError("stmt", {}, Exception()))
        db.rollback = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        published = MagicMock()
        published.is_published = True
        db.get = AsyncMock(return_value=published)

        # 1) pre-check existing → None; 2) after race → winner row
        calls = {"n": 0}

        async def execute_side_effect(_stmt):
            calls["n"] += 1
            result = MagicMock()
            result.scalar_one_or_none.return_value = (
                None if calls["n"] == 1 else existing
            )
            return result

        db.execute = AsyncMock(side_effect=execute_side_effect)

        # Students no longer create attempts via this endpoint (returns 403
        # "Full mocks are assigned automatically"); the IntegrityError catch
        # branch is now only reachable for non-student actors carrying a
        # user_id — see app/api/attempts.py :: start_attempt.
        actor = Actor(
            role="admin",
            sub=str(user_id),
            login="race-admin",
            user_id=user_id,
        )

        with patch(
            "app.api.attempts._ensure_progress_rows_for_attempt",
            new=AsyncMock(return_value=[]),
        ):
            out = await start_attempt(test_id, db, actor)

        assert out is existing
        db.rollback.assert_awaited()
        db.commit.assert_awaited()


class TestWorkerClaim:
    def test_parallel_claim_does_not_double_assign(self):
        attempt_id = uuid.uuid4()
        job_ids: list[uuid.UUID] = []

        async def _run() -> None:
            eng = create_async_engine(settings.database_url)
            Session = async_sessionmaker(eng, expire_on_commit=False)
            try:
                async with Session() as db:
                    try:
                        await db.execute(
                            text(
                                """
                                INSERT INTO attempts
                                  (id, test_id, status, mode, created_at, updated_at)
                                SELECT
                                  CAST(:aid AS uuid), t.id, 'completed',
                                  'full_mock', NOW(), NOW()
                                FROM tests t
                                LIMIT 1
                                """
                            ),
                            {"aid": str(attempt_id)},
                        )
                        for _ in range(6):
                            jid = uuid.uuid4()
                            job_ids.append(jid)
                            db.add(
                                EvaluationJob(
                                    id=jid,
                                    attempt_id=attempt_id,
                                    section_type="writing",
                                    status=JobStatus.PENDING,
                                    input_data={"answers": {}, "prompts": {}},
                                )
                            )
                        await db.commit()
                    except Exception as exc:  # noqa: BLE001
                        await db.rollback()
                        pytest.skip(f"Cannot seed jobs for claim test: {exc}")

                # Patch worker session factory to this engine for the duration.
                import app.services.worker as worker_mod

                original = worker_mod.async_session
                worker_mod.async_session = Session
                try:
                    batches = await asyncio.gather(
                        _claim_jobs(3),
                        _claim_jobs(3),
                        _claim_jobs(3),
                    )
                finally:
                    worker_mod.async_session = original

                claimed = [jid for batch in batches for jid in batch]
                assert len(claimed) == len(set(claimed))
                assert set(claimed).issubset(set(job_ids))
                assert len(claimed) == 6
            finally:
                async with Session() as db:
                    await db.execute(
                        text(
                            "DELETE FROM evaluation_jobs "
                            "WHERE attempt_id = CAST(:aid AS uuid)"
                        ),
                        {"aid": str(attempt_id)},
                    )
                    await db.execute(
                        text(
                            "DELETE FROM attempts WHERE id = CAST(:aid AS uuid)"
                        ),
                        {"aid": str(attempt_id)},
                    )
                    await db.commit()
                await eng.dispose()

        _run_async(_run())

    def test_requeue_stuck_processing(self):
        """Use a fresh engine/loop — avoid sharing the TestClient event loop."""
        attempt_id = uuid.uuid4()
        job_id = uuid.uuid4()

        async def _run() -> None:
            eng = create_async_engine(settings.database_url)
            Session = async_sessionmaker(eng, expire_on_commit=False)
            try:
                async with Session() as db:
                    try:
                        await db.execute(
                            text(
                                """
                                INSERT INTO attempts
                                  (id, test_id, status, mode, created_at, updated_at)
                                SELECT
                                  CAST(:aid AS uuid), t.id, 'completed',
                                  'full_mock', NOW(), NOW()
                                FROM tests t
                                LIMIT 1
                                """
                            ),
                            {"aid": str(attempt_id)},
                        )
                        db.add(
                            EvaluationJob(
                                id=job_id,
                                attempt_id=attempt_id,
                                section_type="writing",
                                status=JobStatus.PROCESSING,
                                input_data={"answers": {}, "prompts": {}},
                            )
                        )
                        await db.commit()
                        await db.execute(
                            text(
                                """
                                UPDATE evaluation_jobs
                                SET updated_at = NOW() - INTERVAL '30 minutes'
                                WHERE id = CAST(:jid AS uuid)
                                """
                            ),
                            {"jid": str(job_id)},
                        )
                        await db.commit()
                    except Exception as exc:  # noqa: BLE001
                        await db.rollback()
                        pytest.skip(f"Cannot seed stuck job: {exc}")

                async with Session() as db:
                    n = await _requeue_stuck_jobs(db)
                assert n >= 1

                async with eng.connect() as conn:
                    status = (
                        await conn.execute(
                            text(
                                "SELECT status FROM evaluation_jobs "
                                "WHERE id = CAST(:jid AS uuid)"
                            ),
                            {"jid": str(job_id)},
                        )
                    ).scalar_one()
                    assert status == "pending"
            finally:
                async with Session() as db:
                    await db.execute(
                        text(
                            "DELETE FROM evaluation_jobs "
                            "WHERE attempt_id = CAST(:aid AS uuid)"
                        ),
                        {"aid": str(attempt_id)},
                    )
                    await db.execute(
                        text(
                            "DELETE FROM attempts WHERE id = CAST(:aid AS uuid)"
                        ),
                        {"aid": str(attempt_id)},
                    )
                    await db.commit()
                await eng.dispose()

        _run_async(_run())
