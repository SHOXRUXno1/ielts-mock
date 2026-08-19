"""Regression tests for speaking examiner bug fixes."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.llm import (
    _groq_upload_file,
    _normalize_stt_text,
    generate_examiner_turn,
    reset_groq_stt_circuit,
    transcribe_audio_bytes,
)


@pytest.fixture(autouse=True)
def _reset_groq_stt():
    reset_groq_stt_circuit()
    yield
    reset_groq_stt_circuit()


class TestScoreHistoryPreference:
    def test_score_prefers_client_history_over_db(self, auth_client):
        session_id = str(uuid.uuid4())
        db_history = [{"role": "examiner", "text": "Stale DB question"}]
        client_history = [
            {"role": "examiner", "text": f"Question {i + 1}"}
            if i % 2 == 0
            else {
                "role": "candidate",
                "text": " ".join(f"word{i}{j}" for j in range(16)),
            }
            for i in range(10)
        ]
        gemini_result = {
            "fluency_coherence": {"band": 6.0, "feedback": "ok"},
            "lexical_resource": {"band": 6.0, "feedback": "ok"},
            "grammatical_range": {"band": 6.0, "feedback": "ok"},
            "pronunciation": {"band": 6.0, "feedback": "ok"},
            "overall_band": 6.0,
            "strengths": [],
            "improvements": [],
            "corrections": [],
            "example_phrases": [],
            "transcript": "Fresh answer",
        }

        with patch(
            "app.api.speaking_examiner._get_live_session",
            new=AsyncMock(
                return_value=MagicMock(history_json=db_history),
            ),
        ), patch(
            "app.api.speaking_examiner.evaluate_speaking_dialog",
            new=AsyncMock(return_value=gemini_result),
        ) as mock_score:
            resp = auth_client.post(
                "/admin/speaking-examiner/score",
                json={
                    "conversation_history": client_history,
                    "session_id": session_id,
                },
            )

        assert resp.status_code == 200
        mock_score.assert_awaited_once_with(client_history)


class TestGroqUploadFile:
    def test_normalizes_webm_codecs_suffix(self):
        name, mime = _groq_upload_file("audio/webm;codecs=opus")
        assert name == "recording.webm"
        assert mime == "audio/webm"

    def test_maps_wav(self):
        name, mime = _groq_upload_file("audio/wav")
        assert name == "recording.wav"
        assert mime == "audio/wav"


class TestGroqTranscribeRetry:
    @pytest.mark.asyncio
    @patch("app.services.llm.settings")
    @patch("app.services.llm.get_http_client")
    async def test_retries_on_429(self, mock_get_client, mock_settings):
        mock_settings.groq_api_key = "gsk_test"

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json = MagicMock(return_value={"text": "hello there"})
        ok_resp.raise_for_status = MagicMock()

        fail_resp = MagicMock()
        fail_resp.status_code = 429
        fail_resp.text = "rate limit"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[fail_resp, ok_resp])
        mock_get_client.return_value = mock_client

        with patch("app.services.llm.asyncio.sleep", new=AsyncMock()):
            text = await transcribe_audio_bytes(b"x" * 1024)

        assert text == "hello there"
        assert mock_client.post.await_count == 2

    @pytest.mark.asyncio
    @patch("app.services.llm.settings")
    @patch("app.services.llm.get_http_client")
    async def test_falls_back_to_gemini_on_403(self, mock_get_client, mock_settings):
        mock_settings.groq_api_key = "gsk_test"
        mock_settings.gemini_key_list = ["gem-test"]

        request = httpx.Request(
            "POST", "https://api.groq.com/openai/v1/audio/transcriptions"
        )
        fail_resp = httpx.Response(403, request=request, text='{"error":{"message":"Forbidden"}}')

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=fail_resp)
        mock_get_client.return_value = mock_client

        with patch(
            "app.services.llm._transcribe_with_gemini",
            new=AsyncMock(return_value="gemini transcript"),
        ) as mock_gemini:
            first = await transcribe_audio_bytes(b"x" * 1024)
            second = await transcribe_audio_bytes(b"y" * 1024)

        assert first == "gemini transcript"
        assert second == "gemini transcript"
        assert mock_gemini.await_count == 2
        assert mock_client.post.await_count == 1


class TestNormalizeSttText:
    def test_empty_markers_become_blank(self):
        assert _normalize_stt_text("EMPTY") == ""
        assert _normalize_stt_text('"empty"') == ""
        assert _normalize_stt_text("  Hello there  ") == "Hello there"


class TestGroqExaminerFallback:
    @pytest.mark.asyncio
    async def test_falls_back_on_gemini_429(self):
        response = MagicMock()
        response.status_code = 429
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch(
                "app.services.llm._call_groq_examiner_turn",
                new=AsyncMock(return_value="Groq reply [PART:1]"),
            ) as mock_groq,
            patch("app.services.llm._call_gemini_text", new=AsyncMock()) as mock_gemini,
        ):
            mock_settings.groq_api_key = "gsk_test"
            mock_gemini.side_effect = httpx.HTTPStatusError(
                "rate limit",
                request=MagicMock(),
                response=response,
            )

            result = await generate_examiner_turn([], None)

        assert result == "Groq reply [PART:1]"
        mock_groq.assert_awaited_once()
