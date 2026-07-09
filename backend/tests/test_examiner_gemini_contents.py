"""Tests for Gemini multi-turn payload building in the speaking examiner."""

from app.services.llm import (
    _build_examiner_gemini_contents,
    _merge_gemini_contents,
    _trim_examiner_history,
)


def _roles(contents: list[dict]) -> list[str]:
    return [c["role"] for c in contents]


def _no_consecutive_same_role(contents: list[dict]) -> bool:
    roles = _roles(contents)
    return all(roles[i] != roles[i + 1] for i in range(len(roles) - 1))


class TestMergeGeminiContents:
    def test_merges_consecutive_user_turns(self):
        merged = _merge_gemini_contents([
            {"role": "user", "parts": [{"text": "A"}]},
            {"role": "user", "parts": [{"text": "B"}]},
        ])
        assert len(merged) == 1
        assert "A" in merged[0]["parts"][0]["text"]
        assert "B" in merged[0]["parts"][0]["text"]


class TestBuildExaminerGeminiContents:
    def test_starts_with_user_when_history_begins_with_examiner(self):
        history = [{"role": "examiner", "text": "What is your name?"}]
        contents = _build_examiner_gemini_contents(history, "John Doe", "")
        assert contents[0]["role"] == "user"
        assert _no_consecutive_same_role(contents)

    def test_deduplicates_candidate_already_in_history(self):
        history = [
            {"role": "examiner", "text": "What is your name?"},
            {"role": "candidate", "text": "John Doe"},
        ]
        contents = _build_examiner_gemini_contents(history, "John Doe", "")
        joined = "\n".join(c["parts"][0]["text"] for c in contents)
        assert joined.count("John Doe") == 1
        assert _no_consecutive_same_role(contents)

    def test_long_history_summary_does_not_create_model_model_pair(self):
        history = []
        for i in range(8):
            history.append({"role": "examiner", "text": f"Question {i + 1}?"})
            history.append({"role": "candidate", "text": f"Answer {i + 1}."})

        trimmed = _trim_examiner_history(history)
        assert trimmed[0]["role"] == "user"

        contents = _build_examiner_gemini_contents(history, "Answer 9.", "")
        assert contents[0]["role"] == "user"
        assert _no_consecutive_same_role(contents)
