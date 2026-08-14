"""Section duration rules and the admin section-settings endpoints."""

from __future__ import annotations

import logging
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import Actor, get_current_admin
from app.main import app
from app.services import section_settings as settings_service
from app.services.section_duration import (
    DurationRangeError,
    check_duration,
    recommended_for,
    total_minutes,
)


# ── Pure rules ────────────────────────────────────────────────────────────────

def test_recommended_values():
    assert recommended_for("listening") == 30
    assert recommended_for("reading") == 60
    assert recommended_for("writing") == 60
    assert recommended_for("speaking") is None


def test_check_duration_silent_at_recommended():
    assert check_duration("listening", 30) is None
    assert check_duration("reading", 60) is None


def test_check_duration_silent_within_tolerance():
    assert check_duration("listening", 29) is None
    assert check_duration("listening", 31) is None
    assert check_duration("listening", 27) is None
    assert check_duration("listening", 33) is None
    assert check_duration("reading", 58) is None
    assert check_duration("reading", 62) is None
    assert check_duration("writing", 55) is None
    assert check_duration("writing", 65) is None


def test_check_duration_warns_beyond_tolerance():
    warning = check_duration("listening", 40)
    assert warning is not None
    assert "30 min" in warning
    assert check_duration("listening", 35) is not None
    assert check_duration("reading", 70) is not None


def test_check_duration_rejects_out_of_range():
    with pytest.raises(DurationRangeError) as exc:
        check_duration("listening", 5)
    assert "20-45" in str(exc.value)
    assert "Recommended: 30" in str(exc.value)


def test_check_duration_rejects_null_for_timed_sections():
    with pytest.raises(DurationRangeError) as exc:
        check_duration("listening", None)
    assert "cannot be null" in str(exc.value)
    assert "Recommended: 30" in str(exc.value)

    with pytest.raises(DurationRangeError):
        check_duration("reading", None)
    with pytest.raises(DurationRangeError):
        check_duration("writing", None)


def test_speaking_untimed_is_silent_but_cap_warns():
    assert check_duration("speaking", None) is None
    assert check_duration("speaking", 15) is not None
    with pytest.raises(DurationRangeError):
        check_duration("speaking", 25)


def test_total_minutes_estimates_untimed_speaking():
    assert total_minutes(
        {"listening": 30, "reading": 60, "writing": 60, "speaking": None}
    ) == 162


# ── HTTP ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_admin] = lambda: Actor(
        role="admin",
        sub="test-admin",
        login="test-admin",
        user_id=None,
    )
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def created_test(admin_client):
    resp = admin_client.post(
        "/admin/tests/",
        json={
            "title": f"Durations {uuid.uuid4().hex[:8]}",
            "description": "durations",
            "type": "academic",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    yield body
    admin_client.delete(f"/admin/tests/{body['id']}")


class TestSectionSettingsApi:
    def test_create_test_returns_four_settings_with_defaults(
        self, admin_client, created_test
    ):
        settings = created_test["section_settings"]
        assert len(settings) == 4
        by_type = {r["section_type"]: r["duration_minutes"] for r in settings}
        assert by_type == {
            "listening": 30,
            "reading": 60,
            "writing": 60,
            "speaking": None,
        }
        assert all(r.get("duration_mode", "standard") == "standard" for r in settings)

    def test_get_settings_matches_create_defaults(self, admin_client, created_test):
        resp = admin_client.get(
            f"/admin/tests/{created_test['id']}/section-settings"
        )
        assert resp.status_code == 200, resp.text
        by_type = {r["section_type"]: r["duration_minutes"] for r in resp.json()}
        assert by_type == {
            "listening": 30,
            "reading": 60,
            "writing": 60,
            "speaking": None,
        }

    def test_out_of_range_low_returns_422(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": 10},
        )
        assert resp.status_code == 422, resp.text
        assert "20-45" in resp.json()["detail"]

    def test_out_of_range_high_returns_422(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": 100},
        )
        assert resp.status_code == 422, resp.text
        assert "20-45" in resp.json()["detail"]

    def test_null_listening_returns_422(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": None},
        )
        assert resp.status_code == 422, resp.text
        assert "cannot be null" in resp.json()["detail"]

    def test_omit_duration_rejected(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={},
        )
        assert resp.status_code == 422, resp.text

    def test_within_tolerance_no_warning(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": 31, "duration_mode": "custom"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["settings"]["duration_minutes"] == 31
        assert body["settings"]["duration_mode"] == "custom"
        assert body["warning"] is None

    def test_beyond_tolerance_returns_warning(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": 40, "duration_mode": "custom"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["settings"]["duration_minutes"] == 40
        assert body["warning"] is not None

    def test_recommended_returns_no_warning(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": 30},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["settings"]["duration_minutes"] == 30
        assert body["warning"] is None

    def test_standard_mode_resets_to_recommended(self, admin_client, created_test):
        admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": 40, "duration_mode": "custom"},
        )
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_mode": "standard"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["settings"]["duration_minutes"] == 30
        assert body["settings"]["duration_mode"] == "standard"
        assert body["warning"] is None

    def test_audio_length_mode_rejected(self, admin_client, created_test):
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_mode": "audio_length"},
        )
        assert resp.status_code == 422, resp.text

    def test_custom_keeps_value_when_switching_mode_only(
        self, admin_client, created_test
    ):
        admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_minutes": 31, "duration_mode": "custom"},
        )
        resp = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/listening",
            json={"duration_mode": "custom"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["settings"]["duration_minutes"] == 31
        assert resp.json()["settings"]["duration_mode"] == "custom"

    def test_speaking_cap_limits(self, admin_client, created_test):
        over = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/speaking",
            json={"duration_minutes": 25},
        )
        assert over.status_code == 422, over.text

        untimed = admin_client.patch(
            f"/admin/tests/{created_test['id']}/section-settings/speaking",
            json={"duration_minutes": None},
        )
        assert untimed.status_code == 200, untimed.text
        assert untimed.json()["settings"]["duration_minutes"] is None
        assert untimed.json()["warning"] is None

    def test_section_patch_ignores_duration(self, admin_client, created_test):
        listening = next(
            s for s in created_test["sections"] if s["type"] == "listening"
        )

        resp = admin_client.patch(
            f"/admin/sections/{listening['id']}",
            json={"duration_minutes": 99},
        )
        assert resp.status_code == 200, resp.text
        assert "duration_minutes" not in resp.json()

    def test_delete_test_cascades_settings(self, admin_client):
        """DELETE succeeds with settings present — requires ON DELETE CASCADE."""
        resp = admin_client.post(
            "/admin/tests/",
            json={
                "title": f"Cascade {uuid.uuid4().hex[:8]}",
                "description": "cascade",
                "type": "academic",
            },
        )
        assert resp.status_code == 201, resp.text
        test_id = resp.json()["id"]
        assert len(resp.json()["section_settings"]) == 4

        deleted = admin_client.delete(f"/admin/tests/{test_id}")
        assert deleted.status_code == 204, deleted.text
        assert admin_client.get(f"/admin/tests/{test_id}").status_code == 404
        assert (
            admin_client.get(f"/admin/tests/{test_id}/section-settings").status_code
            == 404
        )


@pytest.mark.asyncio
async def test_ensure_settings_auto_heals_with_warning(caplog):
    test_id = uuid.uuid4()
    empty = MagicMock()
    empty.scalars.return_value.all.return_value = []
    db = AsyncMock()
    db.execute = AsyncMock(return_value=empty)
    db.add_all = MagicMock()
    db.flush = AsyncMock()

    with caplog.at_level(logging.WARNING, logger="app.services.section_settings"):
        rows = await settings_service.ensure_settings(db, test_id)

    assert len(rows) == 4
    assert {r.section_type: r.duration_minutes for r in rows} == {
        "listening": 30,
        "reading": 60,
        "writing": 60,
        "speaking": None,
    }
    assert all(r.duration_mode == "standard" for r in rows)
    db.add_all.assert_called_once()
    assert "Missing TestSectionSettings" in caplog.text
    assert str(test_id) in caplog.text
