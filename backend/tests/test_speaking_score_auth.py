"""Regression: students must not forge speaking bands on attempts."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.main import app
from app.models.attempt import Attempt, AttemptStatus


STUDENT = Actor(
    role="student",
    sub="student@example.com",
    login="student@example.com",
    user_id=uuid.uuid4(),
)


def _attempt(user_id: uuid.UUID) -> MagicMock:
    now = datetime.now(timezone.utc)
    att = MagicMock(spec=Attempt)
    att.id = uuid.uuid4()
    att.user_id = user_id
    att.test_id = uuid.uuid4()
    att.status = AttemptStatus.COMPLETED.value
    att.speaking_band = None
    att.listening_band = 7.0
    att.reading_band = 7.0
    att.writing_band = 7.0
    att.overall_band = None
    att.started_at = now
    att.finished_at = now
    att.created_at = now
    att.updated_at = now
    att.flagged_overtime = False
    att.listening_raw = None
    att.reading_raw = None
    return att


@pytest.fixture
def student_client():
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()

    empty = MagicMock()
    empty.scalars.return_value.all.return_value = []
    empty.all.return_value = []
    session.execute = AsyncMock(return_value=empty)

    app.dependency_overrides[get_current_actor] = lambda: STUDENT
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as client:
        yield client, session
    app.dependency_overrides.clear()


class TestSpeakingScoreForgeBlocked:
    def test_rejects_student_without_session_id(self, student_client):
        client, session = student_client
        att = _attempt(STUDENT.user_id)
        session.get = AsyncMock(return_value=att)

        resp = client.post(
            f"/attempts/{att.id}/speaking-score",
            json={"speaking_band": 9.0},
        )
        assert resp.status_code == 400
        assert "session_id" in resp.json()["detail"].lower()
        assert att.speaking_band is None

    def test_rejects_student_when_session_unscored(self, student_client):
        client, session = student_client
        att = _attempt(STUDENT.user_id)
        sess = MagicMock()
        sess.id = uuid.uuid4()
        sess.admin_email = STUDENT.sub
        sess.overall_band = None
        sess.score_json = None

        async def _get(model, pk):
            table = getattr(model, "__tablename__", "")
            return att if table == "attempts" else sess

        session.get = AsyncMock(side_effect=_get)

        resp = client.post(
            f"/attempts/{att.id}/speaking-score",
            json={
                "speaking_band": 9.0,
                "session_id": str(sess.id),
            },
        )
        assert resp.status_code == 400
        assert "not been scored" in resp.json()["detail"]
        assert att.speaking_band is None

    def test_uses_server_band_not_client_band(self, student_client):
        client, session = student_client
        att = _attempt(STUDENT.user_id)
        sess = MagicMock()
        sess.id = uuid.uuid4()
        sess.admin_email = STUDENT.sub
        sess.overall_band = 5.5
        sess.score_json = {"overall_band": 5.5, "transcript": "ok"}

        async def _get(model, pk):
            table = getattr(model, "__tablename__", "")
            return att if table == "attempts" else sess

        session.get = AsyncMock(side_effect=_get)

        resp = client.post(
            f"/attempts/{att.id}/speaking-score",
            json={
                "speaking_band": 9.0,
                "session_id": str(sess.id),
                "score_json": {"overall_band": 9.0},
            },
        )
        assert resp.status_code == 200
        assert att.speaking_band == 5.5
