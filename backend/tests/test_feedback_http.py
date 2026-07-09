"""HTTP tests for POST /admin/feedback/writing."""

from unittest.mock import AsyncMock, patch

import pytest


MOCK_RESULT = {
    "tasks": {
        "task_1": {
            "overall_band": 6.5,
            "task_achievement": {"band": 7.0, "feedback": "Task addressed well."},
            "coherence_cohesion": {"band": 6.0, "feedback": "Generally organised."},
            "lexical_resource": {"band": 6.5, "feedback": "Adequate vocabulary."},
            "grammatical_range": {"band": 6.5, "feedback": "Mix of structures."},
            "strengths": ["Clear overview", "Good range of vocabulary"],
            "improvements": ["More precise data", "Fewer repetitions"],
            "errors": [
                {
                    "quote": "informations",
                    "type": "grammar",
                    "correction": "information",
                    "explanation": "'information' is uncountable in English.",
                }
            ],
            "word_count": 162,
        }
    },
    "overall_band": 6.5,
}


class TestWritingFeedbackAuth:
    def test_requires_auth(self, anon_client):
        resp = anon_client.post(
            "/admin/feedback/writing",
            json={"task": 1, "prompt": "Describe the chart.", "text": "The chart shows..."},
        )
        assert resp.status_code == 403

    def test_rejects_empty_text(self, auth_client):
        with patch(
            "app.api.feedback.evaluate_writing",
            new=AsyncMock(return_value=MOCK_RESULT),
        ):
            resp = auth_client.post(
                "/admin/feedback/writing",
                json={"task": 1, "prompt": "Describe the chart.", "text": "   "},
            )
        assert resp.status_code == 422

    def test_rejects_invalid_task_number(self, auth_client):
        resp = auth_client.post(
            "/admin/feedback/writing",
            json={"task": 3, "prompt": "Topic.", "text": "Some text here."},
        )
        assert resp.status_code == 422


class TestWritingFeedbackSuccess:
    def test_task1_returns_band_and_criteria(self, auth_client):
        with patch(
            "app.api.feedback.evaluate_writing",
            new=AsyncMock(return_value=MOCK_RESULT),
        ):
            resp = auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 1,
                    "prompt": "The graph below shows employment in four US sectors.",
                    "text": "The line graph illustrates employment trends across four sectors in the US. " * 5,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_band"] == pytest.approx(6.5)
        assert data["task_achievement"]["band"] == pytest.approx(7.0)
        assert data["coherence_cohesion"]["band"] == pytest.approx(6.0)
        assert data["lexical_resource"]["band"] == pytest.approx(6.5)
        assert data["grammatical_range"]["band"] == pytest.approx(6.5)
        assert "Clear overview" in data["strengths"]
        assert len(data["errors"]) == 1
        assert data["errors"][0]["quote"] == "informations"
        assert data["word_count"] == 162

    def test_task2_calls_evaluate_with_correct_key(self, auth_client):
        task2_result = {
            "tasks": {
                "task_2": {
                    "overall_band": 7.0,
                    "task_achievement": {"band": 7.0, "feedback": "Position is clear."},
                    "coherence_cohesion": {"band": 7.0, "feedback": "Well organised."},
                    "lexical_resource": {"band": 7.0, "feedback": "Good range."},
                    "grammatical_range": {"band": 7.0, "feedback": "Variety of structures."},
                    "strengths": ["Clear argument"],
                    "improvements": [],
                    "errors": [],
                    "word_count": 260,
                }
            },
            "overall_band": 7.0,
        }
        mock_evaluate = AsyncMock(return_value=task2_result)

        with patch("app.api.feedback.evaluate_writing", new=mock_evaluate):
            resp = auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 2,
                    "prompt": "Some people believe technology has made our lives more complex.",
                    "text": "Undeniably, modern technology has transformed daily life in many ways. " * 5,
                },
            )

        assert resp.status_code == 200
        # Verify the mock was called with task_2 key
        call_kwargs = mock_evaluate.call_args.kwargs
        assert "task_2" in call_kwargs["answers"]
        assert "task_2" in call_kwargs["prompts"]

    def test_image_url_forwarded_for_task1(self, auth_client):
        mock_evaluate = AsyncMock(return_value=MOCK_RESULT)

        with patch("app.api.feedback.evaluate_writing", new=mock_evaluate):
            auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 1,
                    "prompt": "The chart below shows...",
                    "text": "The chart illustrates data. " * 8,
                    "image_url": "/media/charts/graph1.png",
                },
            )

        call_kwargs = mock_evaluate.call_args.kwargs
        assert call_kwargs.get("images") == {"task_1": "/media/charts/graph1.png"}

    def test_no_image_url_passes_none_images(self, auth_client):
        mock_evaluate = AsyncMock(return_value=MOCK_RESULT)

        with patch("app.api.feedback.evaluate_writing", new=mock_evaluate):
            auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 1,
                    "prompt": "Describe the graph.",
                    "text": "The graph shows employment trends over time. " * 5,
                },
            )

        call_kwargs = mock_evaluate.call_args.kwargs
        assert call_kwargs.get("images") is None
