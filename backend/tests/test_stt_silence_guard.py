"""Whisper's inventions over silence must never reach a candidate's transcript.

Live sittings produced Part 1 answers reading "." and "Thank you." from students
who had said nothing audible; one such reply was parsed as a name, so the
examiner called her "Thank" for the rest of the exam. These cases were measured
against the real Groq API (see scripts/_probe_stt_silence.py) before the guard
was written.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services import google_stt, llm
from app.services.llm import _normalize_stt_text, transcribe_audio_bytes_detailed


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

    @pytest.mark.parametrize(
        "transcript",
        [
            # Padded stock outros — the frozenset misses these but the regex
            # catches them.
            "Thank you so much for watching this video.",
            "Thanks so much for watching!",
            "Please subscribe to the channel.",
            "Please like and subscribe.",
            "Like and subscribe, thanks!",
            "See you in the next video.",
            "See you next time.",
            "Thanks for listening!",
        ],
    )
    def test_padded_youtube_outros_are_dropped(self, transcript):
        assert _normalize_stt_text(transcript) == ""

    @pytest.mark.parametrize(
        "transcript",
        [
            # Long real answers that happen to contain a matching phrase
            # (the >8-word guardrail keeps them).
            "In our village people often watch videos and thank the presenter "
            "for watching, which I always find funny",
            "I would tell my friend to like and subscribe to my favourite "
            "channel because it teaches useful vocabulary every week",
        ],
    )
    def test_long_answers_containing_outro_phrases_survive(self, transcript):
        assert _normalize_stt_text(transcript) == transcript.strip()


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


class TestNoSpeechProbGuard:
    """The Whisper-only guard on the aggregate no_speech_prob is what stops
    a phrase Whisper accepted as speech from being stored as the candidate's
    answer when its own probability of "no speech" is high. Numbers here
    come from the synthetic bad-audio probe on this stack — see the docstring
    of ``_WHISPER_NO_SPEECH_GUARD`` in llm.py.
    """

    AUDIO = b"x" * 4096

    @pytest.fixture(autouse=True)
    def _isolate_stt_state(self, monkeypatch):
        # Force Whisper as the ear so the guard is exercised on its metrics.
        monkeypatch.setattr(google_stt, "is_configured", lambda: False)
        monkeypatch.setattr(llm.settings, "stt_google_only", False)
        monkeypatch.setattr(llm.settings, "groq_api_key", "gsk_test")
        monkeypatch.setattr(llm.settings, "gemini_api_keys", "")
        monkeypatch.setattr(llm, "_groq_stt_blocked", False)
        from app.core import rate_limiter

        rate_limiter._groq_stt_bucket = None
        yield
        rate_limiter._groq_stt_bucket = None

    @pytest.mark.asyncio
    async def test_high_no_speech_prob_empties_the_transcript(self, monkeypatch):
        """A model that says both "words" AND "probably silent" is disbelieved."""
        fake = AsyncMock(
            return_value=(
                "In my opinion, environmental protection matters.",
                {
                    "no_speech_prob": 0.42,  # cheap-mic room tone territory
                    "avg_logprob": -0.30,
                    "compression_ratio": 0.9,
                },
            )
        )
        monkeypatch.setattr(llm, "_transcribe_with_groq", fake)

        result = await transcribe_audio_bytes_detailed(self.AUDIO)

        assert result.text == ""
        assert result.provider == "groq"
        # The metric that gated the guard is preserved on the record so
        # /admin/usage snapshots can still see why the turn came back empty.
        assert result.no_speech_prob == pytest.approx(0.42)

    @pytest.mark.asyncio
    async def test_low_no_speech_prob_lets_a_real_answer_through(self, monkeypatch):
        fake = AsyncMock(
            return_value=(
                "Yes, I did.",
                {
                    "no_speech_prob": 0.004,  # clean-speech floor
                    "avg_logprob": -0.05,
                    "compression_ratio": 1.2,
                },
            )
        )
        monkeypatch.setattr(llm, "_transcribe_with_groq", fake)

        result = await transcribe_audio_bytes_detailed(self.AUDIO)

        assert result.text == "Yes, I did."
        assert result.no_speech_prob == pytest.approx(0.004)

    @pytest.mark.asyncio
    async def test_no_metric_means_no_guard(self, monkeypatch):
        """Chirp does not report no_speech_prob; a Chirp turn must not be
        empty-ed by a guard that has nothing to weigh."""
        fake = AsyncMock(return_value=("Yes, I did.", {}))
        monkeypatch.setattr(llm, "_transcribe_with_groq", fake)

        result = await transcribe_audio_bytes_detailed(self.AUDIO)

        assert result.text == "Yes, I did."
        assert result.no_speech_prob is None

    @pytest.mark.asyncio
    async def test_threshold_is_inclusive_at_the_boundary(self, monkeypatch):
        """The declared threshold is the edge; a signal at exactly the floor
        of "no speech" territory is not treated as speech."""
        from app.services.llm import _WHISPER_NO_SPEECH_GUARD

        fake = AsyncMock(
            return_value=(
                "Some answer here.",
                {"no_speech_prob": _WHISPER_NO_SPEECH_GUARD},
            )
        )
        monkeypatch.setattr(llm, "_transcribe_with_groq", fake)

        result = await transcribe_audio_bytes_detailed(self.AUDIO)

        assert result.text == ""
