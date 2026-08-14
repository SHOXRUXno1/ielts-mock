"""Unit tests for writing essay_type schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.question import QuestionCreate, QuestionUpdate


class TestEssayTypeValidation:
    def test_task2_accepts_opinion(self):
        q = QuestionCreate(
            order=2,
            question_type="essay",
            content={"prompt": "Do you agree?"},
            task_number=2,
            essay_type="opinion",
        )
        assert q.essay_type == "opinion"

    def test_task1_rejects_essay_type(self):
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                order=1,
                question_type="essay",
                content={"prompt": "Describe the chart."},
                task_number=1,
                essay_type="opinion",
            )
        assert "essay_type" in str(exc.value)

    def test_invalid_essay_type(self):
        with pytest.raises(ValidationError):
            QuestionCreate(
                order=2,
                question_type="essay",
                content={"prompt": "Discuss."},
                task_number=2,
                essay_type="argument",  # type: ignore[arg-type]
            )

    def test_legacy_content_keys_stripped(self):
        q = QuestionCreate(
            order=1,
            question_type="essay",
            content={
                "prompt": "x",
                "task_type": "task_1",
                "min_words": 150,
                "image_url": "/media/x.png",
            },
            task_number=1,
        )
        assert "task_type" not in q.content
        assert "min_words" not in q.content
        assert "image_url" not in q.content
        assert q.content["prompt"] == "x"

    def test_update_task1_rejects_essay_type(self):
        with pytest.raises(ValidationError):
            QuestionUpdate(task_number=1, essay_type="discussion")
