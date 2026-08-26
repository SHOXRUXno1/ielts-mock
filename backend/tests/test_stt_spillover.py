"""Groq Whisper allows only ~20 requests per minute account-wide, which a
single burst of live Speaking sessions exhausts within seconds. A spent budget
or a 429 must reroute the turn to Gemini STT, never fail the candidate.
"""

import httpx
import pytest

from app.core import rate_limiter
from app.core.rate_limiter import TokenBucket
from app.services import llm

AUDIO = b"x" * 4096


@pytest.fixture(autouse=True)
def _reset_stt_state(monkeypatch):
    rate_limiter._groq_stt_bucket = None
    monkeypatch.setattr(llm, "_groq_stt_blocked", False)
    monkeypatch.setattr(llm.settings, "stt_google_only", False)
    monkeypatch.setattr(llm.settings, "groq_api_key", "gsk_test")
    monkeypatch.setattr(llm.settings, "gemini_api_keys", "key-a")
    yield
    rate_limiter._groq_stt_bucket = None


def _http_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request(
        "POST", "https://api.groq.com/openai/v1/audio/transcriptions"
    )
    response = httpx.Response(status, request=request, text="rate limit reached")
    return httpx.HTTPStatusError("boom", request=request, response=response)


def _record_calls(monkeypatch, *, groq_result, gemini_text="from gemini"):
    calls = {"groq": 0, "gemini": 0}

    async def fake_groq(audio_bytes, content_type):
        calls["groq"] += 1
        if isinstance(groq_result, Exception):
            raise groq_result
        return groq_result

    async def fake_gemini(audio_bytes, content_type):
        calls["gemini"] += 1
        return gemini_text

    monkeypatch.setattr(llm, "_transcribe_with_groq", fake_groq)
    monkeypatch.setattr(llm, "_transcribe_with_gemini", fake_gemini)
    return calls


class TestTokenBucketTryAcquire:
    def test_hands_out_capacity_then_refuses(self):
        bucket = TokenBucket(rate=5 / 60.0, capacity=5)
        assert sum(bucket.try_acquire() for _ in range(5)) == 5
        assert bucket.try_acquire() is False

    def test_refills_over_time(self, monkeypatch):
        bucket = TokenBucket(rate=1.0, capacity=1)
        assert bucket.try_acquire() is True
        assert bucket.try_acquire() is False

        now = bucket.last_refill + 2.0
        monkeypatch.setattr(rate_limiter.time, "monotonic", lambda: now)
        assert bucket.try_acquire() is True


class TestSpillover:
    @pytest.mark.asyncio
    async def test_uses_groq_while_budget_lasts(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 5)
        calls = _record_calls(monkeypatch, groq_result="from groq")

        assert await llm.transcribe_audio_bytes(AUDIO) == "from groq"
        assert calls == {"groq": 1, "gemini": 0}

    @pytest.mark.asyncio
    async def test_spent_budget_routes_to_gemini_without_calling_groq(
        self, monkeypatch
    ):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 2)
        calls = _record_calls(monkeypatch, groq_result="from groq")

        results = [await llm.transcribe_audio_bytes(AUDIO) for _ in range(4)]

        assert results == ["from groq", "from groq", "from gemini", "from gemini"]
        assert calls == {"groq": 2, "gemini": 2}

    @pytest.mark.asyncio
    async def test_rate_limited_turn_falls_back_instead_of_failing(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 5)
        calls = _record_calls(monkeypatch, groq_result=_http_error(429))

        assert await llm.transcribe_audio_bytes(AUDIO) == "from gemini"
        assert calls == {"groq": 1, "gemini": 1}
        assert llm._groq_stt_blocked is False

    @pytest.mark.asyncio
    async def test_auth_failure_still_trips_the_circuit(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 5)
        calls = _record_calls(monkeypatch, groq_result=_http_error(403))

        assert await llm.transcribe_audio_bytes(AUDIO) == "from gemini"
        assert llm._groq_stt_blocked is True
        assert calls == {"groq": 1, "gemini": 1}

    @pytest.mark.asyncio
    async def test_without_gemini_the_groq_error_still_surfaces(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 5)
        monkeypatch.setattr(llm.settings, "gemini_api_keys", "")
        _record_calls(monkeypatch, groq_result=_http_error(429))

        with pytest.raises(httpx.HTTPStatusError):
            await llm.transcribe_audio_bytes(AUDIO)


class TestTheEngineIsOnTheRecord:
    """Spilling over is correct, but it must also be visible afterwards.

    The spillover above is silent by design, which left "recognition is
    sometimes wrong" with no denominator: a sitting's turns can be split between
    two models with different failure habits, and nobody could tell which one
    had heard a given answer. Naming the engine, and why it ran, is what makes
    the complaint countable.
    """

    @pytest.mark.asyncio
    async def test_a_groq_turn_names_groq_and_needs_no_excuse(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 5)
        _record_calls(monkeypatch, groq_result="from groq")

        result = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert result.text == "from groq"
        assert result.provider == "groq"
        assert result.reason is None
        assert result.audio_bytes == len(AUDIO)

    @pytest.mark.asyncio
    async def test_a_busy_minute_is_named_as_the_reason(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 1)
        _record_calls(monkeypatch, groq_result="from groq")

        first = await llm.transcribe_audio_bytes_detailed(AUDIO)
        second = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert (first.provider, first.reason) == ("groq", None)
        assert (second.provider, second.reason) == ("gemini", "groq_budget_spent")

    @pytest.mark.asyncio
    async def test_an_http_failure_carries_its_status(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 5)
        _record_calls(monkeypatch, groq_result=_http_error(429))

        result = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert (result.provider, result.reason) == ("gemini", "groq_http_429")

    @pytest.mark.asyncio
    async def test_a_dead_provider_reads_differently_from_a_busy_one(
        self, monkeypatch
    ):
        """Both route to Gemini; only one of them means Groq needs attention."""
        monkeypatch.setattr(llm, "_groq_stt_blocked", True)
        calls = _record_calls(monkeypatch, groq_result="from groq")

        result = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert (result.provider, result.reason) == ("gemini", "groq_blocked")
        assert calls["groq"] == 0

    @pytest.mark.asyncio
    async def test_a_missing_key_reads_differently_again(self, monkeypatch):
        monkeypatch.setattr(llm.settings, "groq_api_key", "")
        _record_calls(monkeypatch, groq_result="from groq")

        result = await llm.transcribe_audio_bytes_detailed(AUDIO)

        assert (result.provider, result.reason) == ("gemini", "groq_not_configured")

    @pytest.mark.asyncio
    async def test_callers_that_only_want_the_words_still_get_a_string(
        self, monkeypatch
    ):
        monkeypatch.setattr(llm.settings, "groq_stt_rpm_limit", 5)
        _record_calls(monkeypatch, groq_result="from groq")

        assert await llm.transcribe_audio_bytes(AUDIO) == "from groq"
