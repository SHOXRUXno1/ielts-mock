from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import Actor, get_current_actor, get_current_admin
from app.core.database import get_db
from app.main import app

TEST_ADMIN = {"sub": "test@example.com", "role": "admin"}

TEST_ACTOR = Actor(role="admin", sub="test@example.com", login="test@example.com")


def _mock_db():
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear per-user rate limiter between tests so cooldown doesn't leak."""
    from app.api import feedback
    feedback._user_last_request.clear()


@pytest.fixture(autouse=True)
def _disable_google_stt(monkeypatch):
    """A local service-account JSON must not change Groq/Gemini STT tests."""
    from app.core.config import settings
    from app.services import google_stt

    monkeypatch.setattr(settings, "google_stt_credentials_json", "")
    monkeypatch.setattr(settings, "google_application_credentials", "")
    monkeypatch.setattr(settings, "google_cloud_project", "")
    google_stt.reset()
    yield
    google_stt.reset()


@pytest.fixture
def auth_client():
    app.dependency_overrides[get_current_admin] = lambda: TEST_ADMIN
    app.dependency_overrides[get_current_actor] = lambda: TEST_ACTOR
    app.dependency_overrides[get_db] = _mock_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    with TestClient(app) as client:
        yield client
