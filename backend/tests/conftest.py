import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_admin
from app.main import app

TEST_ADMIN = {"sub": "test@example.com", "role": "admin"}


@pytest.fixture
def auth_client():
    app.dependency_overrides[get_current_admin] = lambda: TEST_ADMIN
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    with TestClient(app) as client:
        yield client
