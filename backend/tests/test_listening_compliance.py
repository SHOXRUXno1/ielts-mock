"""Tests for Listening IELTS compliance Layer 1 (publish counts, delete guard, defaults)."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.api.deps import Actor, get_current_admin
from app.api.tests import _collect_publish_errors
from app.main import app
from app.models.section import SectionType


# ── Helpers for unit-testing publish validation ───────────────────────────────

def _q(**kwargs):
    defaults = {
        "task_number": None,
        "image_url": None,
        "content": {},
        "answer_key": {"correct": "A"},
        "question_type": "mcq",
        "order": 1,
        # Non-null keeps the orphan-question publish check quiet.
        "question_group_id": uuid.uuid4(),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _section(stype: SectionType, order: int, n_questions: int = 0, questions=None, **extra):
    if questions is None:
        questions = [_q() for _ in range(n_questions)]
    return SimpleNamespace(
        type=stype,
        order=order,
        questions=questions,
        question_groups=extra.get("question_groups", []),
    )


def _writing_section():
    """Minimal valid Academic writing section (2 tasks with prompts + Task1 image)."""
    return SimpleNamespace(
        type=SectionType.WRITING,
        order=20,
        questions=[
            _q(task_number=1, image_url="/media/images/chart.png", content={"prompt": "Describe the chart."}),
            _q(task_number=2, content={"prompt": "Discuss both views."}),
        ],
        question_groups=[],
    )


def _full_skeleton(*, listening_counts=(10, 10, 10, 10), reading_qs=1):
    """Build a FakeTest with standard section counts."""
    sections = [
        _section(SectionType.LISTENING, i + 1, n)
        for i, n in enumerate(listening_counts)
    ]
    # 3 reading passages — put questions on first
    sections.append(_section(SectionType.READING, 10, reading_qs))
    sections.append(_section(SectionType.READING, 11, 0))
    sections.append(_section(SectionType.READING, 12, 0))
    sections.append(_writing_section())
    sections.append(_section(SectionType.SPEAKING, 30, 0))
    sections.append(_section(SectionType.SPEAKING, 31, 0))
    sections.append(_section(SectionType.SPEAKING, 32, 0))
    return SimpleNamespace(sections=sections, type="academic")


class TestPublishListeningCounts:
    def test_exactly_40_ok(self):
        errors = _collect_publish_errors(_full_skeleton(listening_counts=(10, 10, 10, 10)))
        listening_errors = [e for e in errors if e.startswith("Listening Part") or "40 questions" in e]
        assert listening_errors == []

    def test_41_questions_rejects(self):
        errors = _collect_publish_errors(_full_skeleton(listening_counts=(10, 11, 10, 10)))
        joined = "\n".join(errors)
        assert "Listening Part 2 must have exactly 10 questions, got 11." in joined
        assert "Listening must have exactly 40 questions total, got 41." in joined

    def test_two_parts_wrong_count(self):
        errors = _collect_publish_errors(_full_skeleton(listening_counts=(9, 10, 10, 11)))
        joined = "\n".join(errors)
        assert "Listening Part 1 must have exactly 10 questions, got 9." in joined
        assert "Listening Part 4 must have exactly 10 questions, got 11." in joined
        assert "Listening must have exactly 40 questions total, got 40." not in joined
        # total is still 40 (9+10+10+11) — only per-part errors
        assert "40 questions total" not in joined

    def test_multi_select_slots_count_as_n(self):
        """8 Question rows with 2× choose-two multi_select → 10 scoring slots."""
        part2_qs = [
            *[_q(question_type="mcq", answer_key={"correct": "A"}) for _ in range(6)],
            _q(
                question_type="multi_select",
                content={"choose_n": 2, "options": ["a", "b", "c", "d", "e"]},
                answer_key={"correct": ["A", "C"]},
            ),
            _q(
                question_type="multi_select",
                content={"choose_n": 2, "options": ["a", "b", "c", "d", "e"]},
                answer_key={"correct": ["B", "D"]},
            ),
        ]
        sections = [
            _section(SectionType.LISTENING, 1, 10),
            _section(SectionType.LISTENING, 2, questions=part2_qs),
            _section(SectionType.LISTENING, 3, 10),
            _section(SectionType.LISTENING, 4, 10),
            _section(SectionType.READING, 10, 1),
            _section(SectionType.READING, 11, 0),
            _section(SectionType.READING, 12, 0),
            _writing_section(),
            _section(SectionType.SPEAKING, 30, 0),
            _section(SectionType.SPEAKING, 31, 0),
            _section(SectionType.SPEAKING, 32, 0),
        ]
        errors = _collect_publish_errors(SimpleNamespace(sections=sections, type="academic"))
        listening_errors = [
            e for e in errors if e.startswith("Listening Part") or "40 questions" in e
        ]
        assert listening_errors == []
        assert len(part2_qs) == 8  # rows
        from app.services.scoring import count_questions_in_section

        assert count_questions_in_section(sections[1]) == 10


@pytest.fixture
def admin_actor_client():
    app.dependency_overrides[get_current_admin] = lambda: Actor(
        role="admin",
        sub="test-admin",
        login="test-admin",
        user_id=None,
    )
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


class TestDeleteSectionGuard:
    def test_delete_listening_returns_400(self, admin_actor_client):
        client = admin_actor_client
        title = f"Delete Guard {uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/admin/tests/",
            json={"title": title, "description": "delete guard", "type": "academic"},
        )
        assert resp.status_code == 201, resp.text
        test = resp.json()
        listening = next(s for s in test["sections"] if s["type"] == "listening")

        delete_resp = client.delete(f"/admin/sections/{listening['id']}")
        assert delete_resp.status_code == 400, delete_resp.text
        assert "Cannot delete listening part" in delete_resp.json()["detail"]

        client.delete(f"/admin/tests/{test['id']}")

    def test_delete_reading_returns_400(self, admin_actor_client):
        client = admin_actor_client
        title = f"Delete Guard R {uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/admin/tests/",
            json={"title": title, "description": "delete guard", "type": "academic"},
        )
        assert resp.status_code == 201, resp.text
        test = resp.json()
        reading = next(s for s in test["sections"] if s["type"] == "reading")

        delete_resp = client.delete(f"/admin/sections/{reading['id']}")
        assert delete_resp.status_code == 400, delete_resp.text
        assert "Cannot delete reading passage" in delete_resp.json()["detail"]

        client.delete(f"/admin/tests/{test['id']}")


class TestListeningDefaults:
    def test_create_test_duration_lives_on_settings(self, admin_actor_client):
        client = admin_actor_client
        title = f"Duration Default {uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/admin/tests/",
            json={"title": title, "description": "duration", "type": "academic"},
        )
        assert resp.status_code == 201, resp.text
        test = resp.json()
        listening = [s for s in test["sections"] if s["type"] == "listening"]
        assert len(listening) == 4
        assert all("duration_minutes" not in s for s in listening)

        settings = {s["section_type"]: s["duration_minutes"] for s in test["section_settings"]}
        assert settings == {
            "listening": 30,
            "reading": 60,
            "writing": 60,
            "speaking": None,
        }

        client.delete(f"/admin/tests/{test['id']}")

    def test_patch_listening_passage_redirects_to_audioscript(self, admin_actor_client):
        client = admin_actor_client
        title = f"Audioscript Redirect {uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/admin/tests/",
            json={"title": title, "description": "audioscript", "type": "academic"},
        )
        assert resp.status_code == 201, resp.text
        test_data = resp.json()
        listening = next(s for s in test_data["sections"] if s["type"] == "listening")

        patch = client.patch(
            f"/admin/sections/{listening['id']}",
            json={"passage": "Hello from legacy passage field."},
        )
        assert patch.status_code == 200, patch.text
        data = patch.json()
        assert data["audioscript"] == "Hello from legacy passage field."
        assert data["passage"] is None or data["passage"] == ""

        client.delete(f"/admin/tests/{test_data['id']}")
