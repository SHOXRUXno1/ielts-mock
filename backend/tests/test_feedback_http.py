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
            json={
                "task": 1,
                "task_description": "Describe the chart.",
                "task_instruction": "Summarise the information.",
                "text": "The chart shows...",
            },
        )
        assert resp.status_code in (401, 403)

    def test_rejects_empty_text(self, auth_client):
        with patch(
            "app.api.feedback.evaluate_writing",
            new=AsyncMock(return_value=MOCK_RESULT),
        ):
            resp = auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 1,
                    "task_description": "Describe the chart.",
                    "task_instruction": "Summarise the information.",
                    "text": "   ",
                },
            )
        assert resp.status_code == 422

    def test_rejects_invalid_task_number(self, auth_client):
        resp = auth_client.post(
            "/admin/feedback/writing",
            json={
                "task": 3,
                "task_description": "Topic.",
                "task_instruction": "Write about it.",
                "text": "Some text here.",
            },
        )
        assert resp.status_code == 422


class TestWritingFeedbackSuccess:
    def test_task1_returns_band_and_criteria(self, auth_client):
        essay = "The line graph illustrates employment trends across four sectors in the US. " * 4
        essay += "There were more informations about the service sector than manufacturing. "
        with patch(
            "app.api.feedback.evaluate_writing",
            new=AsyncMock(return_value=MOCK_RESULT),
        ):
            resp = auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 1,
                    "task_description": "The graph below shows employment in four US sectors.",
                    "task_instruction": "Summarise the information by selecting and reporting the main features.",
                    "text": essay,
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

    def test_task2_reads_task_response_criterion(self, auth_client):
        """Task 2 results use task_response; endpoint must map it into task_achievement field."""
        task2_result = {
            "tasks": {
                "task_2": {
                    "overall_band": 7.0,
                    "task_response": {"band": 7.5, "feedback": "Clear position throughout."},
                    "coherence_cohesion": {"band": 7.0, "feedback": "Well organised."},
                    "lexical_resource": {"band": 7.0, "feedback": "Good range."},
                    "grammatical_range": {"band": 6.5, "feedback": "Variety of structures."},
                    "strengths": ["Clear argument"],
                    "improvements": [],
                    "errors": [],
                    "word_count": 260,
                }
            },
            "overall_band": 7.0,
        }
        with patch(
            "app.api.feedback.evaluate_writing",
            new=AsyncMock(return_value=task2_result),
        ):
            resp = auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 2,
                    "task_statement": "Some people believe technology has made our lives more complex.",
                    "task_question": "To what extent do you agree or disagree with this statement?",
                    "task_instruction": "Give reasons for your answer and include any relevant examples.",
                    "text": "Undeniably, modern technology has transformed daily life in many ways. " * 5,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["task_achievement"] is not None
        assert data["task_achievement"]["band"] == pytest.approx(7.5)
        assert "Clear position" in data["task_achievement"]["feedback"]

    def test_task2_calls_evaluate_with_statement_question(self, auth_client):
        """Verify evaluate_writing receives task_statements and task_questions."""
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
                    "task_statement": "Technology has changed our lives.",
                    "task_question": "To what extent do you agree or disagree?",
                    "task_instruction": "Give reasons for your answer.",
                    "text": "Undeniably, modern technology has transformed daily life in many ways. " * 5,
                },
            )

        assert resp.status_code == 200
        call_kwargs = mock_evaluate.call_args.kwargs
        assert "task_2" in call_kwargs["answers"]
        assert call_kwargs["task_statements"] == {"task_2": "Technology has changed our lives."}
        assert call_kwargs["task_questions"] == {"task_2": "To what extent do you agree or disagree?"}
        assert call_kwargs["task_instructions"] == {"task_2": "Give reasons for your answer."}
        combined = "Technology has changed our lives.\n\nTo what extent do you agree or disagree?"
        assert call_kwargs["task_descriptions"] == {"task_2": combined}

    def test_task2_legacy_without_statement_question(self, auth_client):
        """Legacy Task 2 payload without task_statement/task_question should still work."""
        task2_result = {
            "tasks": {
                "task_2": {
                    "overall_band": 7.0,
                    "task_achievement": {"band": 7.0, "feedback": "Good."},
                    "coherence_cohesion": {"band": 7.0, "feedback": "Good."},
                    "lexical_resource": {"band": 7.0, "feedback": "Good."},
                    "grammatical_range": {"band": 7.0, "feedback": "Good."},
                    "strengths": [],
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
                    "task_description": "Technology is great. Do you agree?",
                    "task_instruction": "Give reasons.",
                    "text": "Undeniably, modern technology has transformed daily life in many ways. " * 5,
                },
            )

        assert resp.status_code == 200
        call_kwargs = mock_evaluate.call_args.kwargs
        assert call_kwargs["task_statements"] == {"task_2": "Technology is great. Do you agree?"}
        assert call_kwargs["task_questions"] == {"task_2": ""}

    def test_legacy_prompt_field_still_works(self, auth_client):
        """Legacy clients sending only 'prompt' (no task_description/task_instruction) should still work."""
        mock_evaluate = AsyncMock(return_value=MOCK_RESULT)

        with patch("app.api.feedback.evaluate_writing", new=mock_evaluate):
            resp = auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 1,
                    "prompt": "The chart below shows... Summarise the information.",
                    "text": "The chart illustrates data about various sectors. " * 8,
                },
            )

        assert resp.status_code == 200
        call_kwargs = mock_evaluate.call_args.kwargs
        assert call_kwargs["task_descriptions"] == {
            "task_1": "The chart below shows... Summarise the information."
        }
        assert call_kwargs["task_instructions"] == {"task_1": ""}

    def test_image_url_forwarded_for_task1(self, auth_client):
        mock_evaluate = AsyncMock(return_value=MOCK_RESULT)

        with patch("app.api.feedback.evaluate_writing", new=mock_evaluate):
            auth_client.post(
                "/admin/feedback/writing",
                json={
                    "task": 1,
                    "task_description": "The chart below shows...",
                    "task_instruction": "Summarise the information.",
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
                    "task_description": "Describe the graph.",
                    "task_instruction": "Summarise the information.",
                    "text": "The graph shows employment trends over time. " * 5,
                },
            )

        call_kwargs = mock_evaluate.call_args.kwargs
        assert call_kwargs.get("images") is None


class TestWritingPresets:
    def test_get_presets_returns_all_sections(self, auth_client):
        resp = auth_client.get("/admin/writing-presets")
        assert resp.status_code == 200
        data = resp.json()
        assert "task_1" in data
        assert "task_2" in data
        assert "task_2_questions" in data
        assert "Summarise" in data["task_1"]
        assert isinstance(data["task_2"], dict)
        assert "discussion" in data["task_2"]
        assert isinstance(data["task_2_questions"], dict)
        assert "opinion" in data["task_2_questions"]
        assert "agree or disagree" in data["task_2_questions"]["opinion"]

    def test_task1_preset_instruction(self):
        from app.services.writing_presets import get_default_instruction
        instr = get_default_instruction(1)
        assert "Summarise" in instr
        assert "main features" in instr

    def test_task2_discussion_preset_instruction_no_duplicate(self):
        from app.services.writing_presets import get_default_instruction
        instr = get_default_instruction(2, "discussion")
        assert "Give reasons" in instr
        assert "Discuss both" not in instr

    def test_task2_default_preset_instruction(self):
        from app.services.writing_presets import get_default_instruction
        instr = get_default_instruction(2)
        assert "Give reasons" in instr

    def test_task2_unknown_type_falls_back_to_default(self):
        from app.services.writing_presets import get_default_instruction
        instr = get_default_instruction(2, "unknown_type")
        default = get_default_instruction(2, None)
        assert instr == default

    def test_get_default_question_opinion(self):
        from app.services.writing_presets import get_default_question
        q = get_default_question("opinion")
        assert q is not None
        assert "agree or disagree" in q

    def test_get_default_question_discussion(self):
        from app.services.writing_presets import get_default_question
        q = get_default_question("discussion")
        assert q is not None
        assert "Discuss both" in q

    def test_get_default_question_none_type(self):
        from app.services.writing_presets import get_default_question
        assert get_default_question(None) is None

    def test_get_default_question_unknown_type(self):
        from app.services.writing_presets import get_default_question
        assert get_default_question("unknown") is None
