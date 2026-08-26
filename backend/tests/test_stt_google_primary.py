"""Chirp is the first ear when a service account is present.

Groq Whisper and Gemini stay as overflow. These tests pin that order, and
the reasons written on a turn when Chirp cannot take it, so a sitting
split across engines remains countable.
"""

import httpx
import pytest

from app.core import rate_limiter
from app.services import google_stt, llm

AUDIO = b"x" * 4096


@pytest.fixture(autouse=True)
def _reset_stt_state(monkeypatch):
    rate_limiter._groq_stt_bucket = None
    monkeypatch.setattr(llm, "_groq_stt_blocked", False)
    monkeypatch.setattr(llm.settings, "stt_google_only", False)
    monkeypatch.setattr(llm.settings, "groq_api_key", "gsk_test")
    monkeypatch.setattr(llm.settings, "gemini_api_keys", "key-a")
    google_stt.reset()
    yield
    rate_limiter._groq_stt_bucket = None
    google_stt.reset()


def _http_error(url: str, status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", url)
    response = httpx.Response(status, request=request, text="no")
    return httpx.HTTPStatusError("boom", request=request, response=response)


def _record_calls(monkeypatch, *, google_result, groq_result="from groq"):
    calls = {"google": 0, "groq": 0, "gemini": 0}

    async def fake_google(audio_bytes):
        calls["google"] += 1
        if isinstance(google_result, Exception):
            raise google_result
        return google_result

    async def fake_groq(audio_bytes, content_type):
        calls["groq"] += 1
        if isinstance(groq_result, Exception):
            raise groq_result
        return groq_result

    async def fake_gemini(audio_bytes, content_type):
        calls["gemini"] += 1
        return "from gemini"

    monkeypatch.setattr(google_stt, "is_configured", lambda: True)
    monkeypatch.setattr(llm, "_transcribe_with_google", fake_google)
    monkeypatch.setattr(llm, "_transcribe_with_groq", fake_groq)
    monkeypatch.setattr(llm, "_transcribe_with_gemini", fake_gemini)
    return calls


class TestTranscriptFromResponse:
    def test_joins_every_result(self):
        text = google_stt.transcript_from_response(
            {
                "results": [
                    {"alternatives": [{"transcript": "I am a student."}]},
                    {"alternatives": [{"transcript": " I live in Tashkent."}]},
                ]
            }
        )
        assert text == "I am a student. I live in Tashkent."

    def test_empty_results_are_silence(self):
        assert google_stt.transcript_from_response({}) == ""
        assert google_stt.transcript_from_response({"results": []}) == ""


class TestChirpGoesFirst:
    @pytest.mark.asyncio
    async def test_a_configured_account_does_not_call_groq(self, monkeypatch):
        calls = _record_calls(monkeypatch, google_result="from chirp")

        result = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert result.text == "from chirp"
        assert result.provider == "google"
        assert result.reason is None
        assert calls == {"google": 1, "groq": 0, "gemini": 0}

    @pytest.mark.asyncio
    async def test_an_http_failure_falls_through_to_groq(self, monkeypatch):
        calls = _record_calls(
            monkeypatch,
            google_result=_http_error(
                "https://us-speech.googleapis.com/v2/recognize", 429
            ),
        )

        result = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert (result.provider, result.reason) == ("groq", "google_http_429")
        assert result.text == "from groq"
        assert calls == {"google": 1, "groq": 1, "gemini": 0}

    @pytest.mark.asyncio
    async def test_auth_failure_trips_the_circuit(self, monkeypatch):
        calls = _record_calls(
            monkeypatch,
            google_result=_http_error(
                "https://oauth2.googleapis.com/token", 403
            ),
        )

        first = await llm.transcribe_audio_bytes_detailed(AUDIO)
        second = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert (first.provider, first.reason) == ("groq", "google_http_403")
        assert (second.provider, second.reason) == ("groq", "google_blocked")
        assert calls["google"] == 1
        assert calls["groq"] == 2
        assert google_stt.is_blocked() is True

    @pytest.mark.asyncio
    async def test_without_a_fallback_the_google_error_still_surfaces(
        self, monkeypatch
    ):
        monkeypatch.setattr(llm.settings, "groq_api_key", "")
        monkeypatch.setattr(llm.settings, "gemini_api_keys", "")
        _record_calls(
            monkeypatch,
            google_result=_http_error(
                "https://us-speech.googleapis.com/v2/recognize", 500
            ),
        )

        with pytest.raises(httpx.HTTPStatusError):
            await llm.transcribe_audio_bytes(AUDIO)


class TestChirpOnlyProbe:
    """Live sittings can pin the ear to Chirp so the 60s cliff is visible."""

    @pytest.mark.asyncio
    async def test_a_google_failure_does_not_call_groq_or_gemini(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "stt_google_only", True)
        calls = _record_calls(
            monkeypatch,
            google_result=_http_error(
                "https://us-speech.googleapis.com/v2/recognize", 400
            ),
        )

        with pytest.raises(httpx.HTTPStatusError):
            await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert calls == {"google": 1, "groq": 0, "gemini": 0}

    @pytest.mark.asyncio
    async def test_without_google_there_is_no_whisper_rescue(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "stt_google_only", True)
        calls = _record_calls(monkeypatch, google_result="unused")
        monkeypatch.setattr(google_stt, "is_configured", lambda: False)

        with pytest.raises(RuntimeError, match="Chirp-only"):
            await llm.transcribe_audio_bytes(AUDIO)

        assert calls["google"] == 0
        assert calls["groq"] == 0
        assert calls["gemini"] == 0
