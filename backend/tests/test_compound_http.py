"""HTTP integration tests for compound completion question groups."""

from __future__ import annotations

import uuid

import pytest

from app.api.deps import Actor, get_current_admin
from app.main import app

TABLE_STRUCTURE = {
    "variant": "table",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "headers": ["Name", "Location"],
    "rows": [
        [
            {"type": "text", "value": "Cafe"},
            {"type": "gap", "gap_id": "g1"},
        ],
        [
            {"type": "gap", "gap_id": "g2"},
            {"type": "text", "value": "City"},
        ],
        [
            {"type": "text", "value": "Park"},
            {"type": "gap", "gap_id": "g3"},
        ],
    ],
}


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


def _create_test_with_listening_section(client):
    title = f"Compound IT {uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/admin/tests/",
        json={"title": title, "description": "compound integration", "type": "academic"},
    )
    assert resp.status_code == 201, resp.text
    test = resp.json()
    sections = test.get("sections") or []
    listening = next((s for s in sections if s["type"] == "listening"), None)
    assert listening is not None, "expected auto-created listening section"
    return test, listening


class TestCompoundTableGroupHttp:
    def test_create_group_questions_and_reject_bad_gap(self, admin_actor_client):
        client = admin_actor_client
        test, section = _create_test_with_listening_section(client)
        section_id = section["id"]

        # POST group table_completion → 201
        group_resp = client.post(
            f"/admin/sections/{section_id}/question-groups",
            json={
                "question_type": "table_completion",
                "instruction": "Complete the table.",
                "options_shared": TABLE_STRUCTURE,
            },
        )
        assert group_resp.status_code == 201, group_resp.text
        group = group_resp.json()
        assert group["question_type"] == "table_completion"
        assert group["options_shared"]["variant"] == "table"
        group_id = group["id"]

        # POST question with gap_id=g1 → 201
        q1 = client.post(
            f"/admin/question-groups/{group_id}/questions",
            json={
                "order": 1,
                "content": {"gap_id": "g1"},
                "answer_key": {"correct": ["Audley"], "max_words": 2},
            },
        )
        assert q1.status_code == 201, q1.text
        assert q1.json()["content"]["gap_id"] == "g1"

        # POST question with gap_id=wrong → 400
        bad = client.post(
            f"/admin/question-groups/{group_id}/questions",
            json={
                "order": 2,
                "content": {"gap_id": "wrong"},
                "answer_key": {"correct": ["x"]},
            },
        )
        assert bad.status_code == 400, bad.text
        assert "gap_id" in bad.json()["detail"]

        # Add remaining gaps
        for order, gap_id, ans in ((2, "g2", "North"), (3, "g3", "Lake")):
            resp = client.post(
                f"/admin/question-groups/{group_id}/questions",
                json={
                    "order": order,
                    "content": {"gap_id": gap_id},
                    "answer_key": {"correct": [ans], "max_words": 2},
                },
            )
            assert resp.status_code == 201, resp.text

        # GET group → structure + questions
        groups = client.get(f"/admin/sections/{section_id}/question-groups")
        assert groups.status_code == 200
        found = next(g for g in groups.json() if g["id"] == group_id)
        assert found["options_shared"]["headers"] == ["Name", "Location"]
        assert len(found["questions"]) == 3
        gap_ids = {q["content"]["gap_id"] for q in found["questions"]}
        assert gap_ids == {"g1", "g2", "g3"}

        # Cleanup
        client.delete(f"/admin/tests/{test['id']}")

    def test_invalid_structure_rejected(self, admin_actor_client):
        client = admin_actor_client
        _test, section = _create_test_with_listening_section(client)
        resp = client.post(
            f"/admin/sections/{section['id']}/question-groups",
            json={
                "question_type": "table_completion",
                "instruction": "x",
                "options_shared": {
                    "variant": "notes",
                    "instruction_words": "ONE WORD",
                    "max_words_per_gap": 1,
                    "sections": [],
                },
            },
        )
        assert resp.status_code == 400
        client.delete(f"/admin/tests/{_test['id']}")
