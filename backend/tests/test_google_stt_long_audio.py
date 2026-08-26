"""Chirp sync Recognize stops at 60s. Longer takes must be split, not failed."""

import httpx
import pytest

from app.services import google_stt


def _http_error(message: str, status: int = 400) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://us-speech.googleapis.com/v2/recognize")
    response = httpx.Response(status, request=request, text=message)
    return httpx.HTTPStatusError("boom", request=request, response=response)


class TestDurationLimitDetection:
    def test_reads_google_s_own_wording(self):
        exc = _http_error("Audio can be of a maximum of 60 seconds.")
        assert google_stt.is_duration_limit_error(exc) is True

    def test_ignores_other_400s(self):
        exc = _http_error("Invalid audio encoding")
        assert google_stt.is_duration_limit_error(exc) is False

    def test_ignores_non_http_errors(self):
        assert google_stt.is_duration_limit_error(RuntimeError("60 seconds")) is False


class TestJoinChunks:
    def test_joins_non_empty_parts(self):
        text = google_stt._join_chunk_transcripts(
            ["I live in a city.", "  It is busy.  ", ""]
        )
        assert text == "I live in a city. It is busy."


class TestRecognizeSplitsLongAudio:
    @pytest.mark.asyncio
    async def test_a_long_take_is_recognized_in_parallel_chunks(self, monkeypatch):
        calls: list[int] = []

        async def fake_split(audio_bytes, *, force=False, duration_hint=None):
            return [b"a" * 2048, b"b" * 2048]

        async def fake_once(audio_bytes):
            calls.append(len(audio_bytes))
            return "first half" if audio_bytes.startswith(b"a") else "second half"

        monkeypatch.setattr(google_stt, "ffmpeg_available", lambda: True)
        monkeypatch.setattr(google_stt, "split_for_sync_recognize", fake_split)
        monkeypatch.setattr(google_stt, "recognize_once", fake_once)

        text = await google_stt.recognize(b"x" * 4096)

        assert text == "first half second half"
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_a_short_take_stays_on_one_call(self, monkeypatch):
        async def fake_split(audio_bytes, *, force=False, duration_hint=None):
            return [audio_bytes]

        async def fake_once(audio_bytes):
            return "one take"

        monkeypatch.setattr(google_stt, "ffmpeg_available", lambda: True)
        monkeypatch.setattr(google_stt, "split_for_sync_recognize", fake_split)
        monkeypatch.setattr(google_stt, "recognize_once", fake_once)

        assert await google_stt.recognize(b"x" * 4096) == "one take"

    @pytest.mark.asyncio
    async def test_a_60s_refusal_retries_as_chunks(self, monkeypatch):
        async def fake_split(audio_bytes, *, force=False, duration_hint=None):
            if not force:
                return [audio_bytes]
            return [b"a" * 2048, b"b" * 2048]

        async def fake_once(audio_bytes):
            if audio_bytes.startswith(b"x"):
                raise _http_error("Audio can be of a maximum of 60 seconds.")
            return "chunk"

        monkeypatch.setattr(google_stt, "ffmpeg_available", lambda: True)
        monkeypatch.setattr(google_stt, "split_for_sync_recognize", fake_split)
        monkeypatch.setattr(google_stt, "recognize_once", fake_once)

        text = await google_stt.recognize(b"x" * 4096)
        assert text == "chunk chunk"

    @pytest.mark.asyncio
    async def test_other_errors_are_not_swallowed(self, monkeypatch):
        async def fake_once(audio_bytes):
            raise _http_error("Invalid audio encoding")

        monkeypatch.setattr(google_stt, "ffmpeg_available", lambda: False)
        monkeypatch.setattr(google_stt, "recognize_once", fake_once)

        with pytest.raises(httpx.HTTPStatusError):
            await google_stt.recognize(b"x" * 4096)

    @pytest.mark.asyncio
    async def test_a_known_long_take_is_split_before_the_first_call(
        self, monkeypatch
    ):
        hints: list[float | None] = []

        async def fake_split(audio_bytes, *, force=False, duration_hint=None):
            hints.append(duration_hint)
            return [b"a" * 2048, b"b" * 2048]

        async def fake_once(audio_bytes):
            return "chunk"

        monkeypatch.setattr(google_stt, "ffmpeg_available", lambda: True)
        monkeypatch.setattr(google_stt, "split_for_sync_recognize", fake_split)
        monkeypatch.setattr(google_stt, "recognize_once", fake_once)

        text = await google_stt.recognize(b"x" * 4096, duration_seconds=120)

        assert text == "chunk chunk"
        assert hints == [120]

    @pytest.mark.asyncio
    async def test_a_known_short_take_skips_the_splitter(self, monkeypatch):
        split_calls = {"n": 0}

        async def fake_split(*_args, **_kwargs):
            split_calls["n"] += 1
            return [b"nope"]

        async def fake_once(audio_bytes):
            return "short"

        monkeypatch.setattr(google_stt, "split_for_sync_recognize", fake_split)
        monkeypatch.setattr(google_stt, "recognize_once", fake_once)

        text = await google_stt.recognize(b"x" * 4096, duration_seconds=20)

        assert text == "short"
        assert split_calls["n"] == 0
