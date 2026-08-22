"""Guard against Gemini collapsing Writing criteria onto task relevance.

A well-written but off-topic response must keep its language bands; only the
task criterion may be capped. Without this guard an identical essay scored
5.0 on one run and 3.5 on the next.
"""

import pytest

from app.services.llm import (
    WritingEvaluationError,
    _validate_writing_criteria,
)


def _result(task: int, coherence: int, lexical: int, grammar: int) -> dict:
    return {
        "task_achievement": {"band": task, "feedback": ""},
        "coherence_cohesion": {"band": coherence, "feedback": ""},
        "lexical_resource": {"band": lexical, "feedback": ""},
        "grammatical_range": {"band": grammar, "feedback": ""},
    }


class TestValidateWritingCriteria:
    def test_rejects_all_language_criteria_zeroed(self):
        result = _result(0, 0, 0, 0)
        with pytest.raises(WritingEvaluationError, match="language criterion"):
            _validate_writing_criteria(result, word_count=206)

    def test_accepts_off_topic_with_intact_language_bands(self):
        result = _result(0, 6, 6, 6)
        _validate_writing_criteria(result, word_count=206)
        # Band 0 is only for a blank script — a written answer floors at 1.
        assert result["task_achievement"]["band"] == 1
        assert result["coherence_cohesion"]["band"] == 6

    def test_leaves_normal_bands_untouched(self):
        result = _result(6, 7, 6, 7)
        _validate_writing_criteria(result, word_count=280)
        assert [
            result[k]["band"]
            for k in (
                "task_achievement",
                "coherence_cohesion",
                "lexical_resource",
                "grammatical_range",
            )
        ] == [6, 7, 6, 7]

    def test_short_response_may_legitimately_score_zero(self):
        # Too short to distinguish model failure from a real near-zero score,
        # so floor it rather than burning retries.
        result = _result(0, 0, 0, 0)
        _validate_writing_criteria(result, word_count=8)
        assert result["lexical_resource"]["band"] == 1

    def test_task_2_criterion_key_is_floored_too(self):
        result = {
            "task_response": {"band": 0, "feedback": ""},
            "coherence_cohesion": {"band": 5, "feedback": ""},
            "lexical_resource": {"band": 5, "feedback": ""},
            "grammatical_range": {"band": 5, "feedback": ""},
        }
        _validate_writing_criteria(result, word_count=300)
        assert result["task_response"]["band"] == 1

    def test_partial_zeroes_are_not_a_collapse(self):
        # One weak criterion is a plausible score, not a structural failure.
        result = _result(4, 0, 5, 5)
        _validate_writing_criteria(result, word_count=260)
        assert result["coherence_cohesion"]["band"] == 1
