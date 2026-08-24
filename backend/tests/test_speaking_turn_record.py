"""The engine that heard an answer is kept beside the answer.

Knowing the split only in aggregate is not enough. When a band looks wrong the
question is always about one particular reply — "she did say her name, why does
the transcript say Thank" — and that can only be answered if the turn itself
remembers which model produced it and why that model was the one asked.

The stamp is additive on purpose: every existing reader of history_json walks
turns looking for role and text, and a sitting recorded before this existed must
keep working unchanged.
"""

from app.api.speaking_examiner import _history_turn
from app.services.llm import Transcription


def _stt(provider: str, reason: str | None = None) -> Transcription:
    return Transcription(
        text="I live in Tashkent with my family.",
        provider=provider,
        reason=reason,
        latency_ms=912,
        audio_bytes=41_000,
    )


class TestCandidateTurnsCarryTheEngine:
    def test_the_engine_and_its_reason_are_both_kept(self):
        turn = _history_turn(
            "candidate",
            "I live in Tashkent with my family.",
            "part1",
            _stt("gemini", "groq_budget_spent"),
        )

        assert turn["stt"]["provider"] == "gemini"
        assert turn["stt"]["reason"] == "groq_budget_spent"
        assert turn["stt"]["latency_ms"] == 912
        assert turn["stt"]["audio_bytes"] == 41_000

    def test_the_ordinary_case_records_no_reason(self):
        turn = _history_turn("candidate", "Yes, I do.", "part1", _stt("groq"))

        assert turn["stt"]["provider"] == "groq"
        assert turn["stt"]["reason"] is None

    def test_the_words_and_phase_are_untouched(self):
        """The stamp sits alongside the turn, it does not rewrite it."""
        turn = _history_turn("candidate", "Yes, I do.", "part1", _stt("groq"))

        assert turn["role"] == "candidate"
        assert turn["text"] == "Yes, I do."
        assert turn["phase"] == "part1"


class TestTurnsWithoutAnEngineAreUnchanged:
    """An examiner's line has no transcript, and neither has an older sitting."""

    def test_an_examiner_turn_gains_nothing(self):
        turn = _history_turn("examiner", "Where do you live?", "part1")

        assert turn == {
            "role": "examiner",
            "text": "Where do you live?",
            "phase": "part1",
        }

    def test_a_turn_recorded_without_one_stays_the_old_shape(self):
        turn = _history_turn("candidate", "Yes, I do.", "part1", None)

        assert "stt" not in turn
