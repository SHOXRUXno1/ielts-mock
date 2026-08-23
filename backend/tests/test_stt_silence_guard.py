"""Whisper's inventions over silence must never reach a candidate's transcript.

Live sittings produced Part 1 answers reading "." and "Thank you." from students
who had said nothing audible; one such reply was parsed as a name, so the
examiner called her "Thank" for the rest of the exam. These cases were measured
against the real Groq API (see scripts/_probe_stt_silence.py) before the guard
was written.
"""

import pytest

from app.services.llm import _normalize_stt_text


class TestSilenceIsNotAnAnswer:
    @pytest.mark.parametrize(
        "transcript",
        [
            ".",
            "...",
            "…",
            " . ",
            "you",  # what digital silence returns
            "You.",
            "Thank you.",
            "thank you",
            "Thank you. Thank you.",  # the same filler, repeated
            "Thank you. Thank you. Thank you.",
            "Thanks for watching!",
            "Please subscribe.",
            "Bye.",
            '"Thank you."',
        ],
    )
    def test_stock_filler_becomes_empty(self, transcript):
        assert _normalize_stt_text(transcript) == ""

    @pytest.mark.parametrize(
        "transcript",
        [
            "My name is Shoxsana Atayeva.",
            "Call me Sasha.",  # three words, genuinely short, must survive
            "Sasha",
            "Thank you, my name is Laylo.",  # filler plus a real answer
            "Yes, I did.",
            "No.",
            "Thank you for the question. I would say rich people are famous.",
        ],
    )
    def test_real_speech_survives(self, transcript):
        assert _normalize_stt_text(transcript) == transcript.strip().strip('"').strip()


class TestTranscriptsAreNotRewritten:
    """The guard only ever discards; it must not edit what a candidate said."""

    def test_repetition_is_left_alone(self):
        """Speakers repeat themselves, and that is evidence an examiner may use."""
        text = "I like it. I like it. It is very good."
        assert _normalize_stt_text(text) == text

    def test_ordinary_answer_is_untouched(self):
        text = (
            "Well, from my perspective, it largely depends on each person. "
            "Firstly, it depends on character. "
            "The second reason is that it is not about everyone."
        )
        assert _normalize_stt_text(text) == text
