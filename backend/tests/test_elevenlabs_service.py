"""Unit tests for ElevenLabs TTS service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.elevenlabs_service import (
    TTSResult,
    _tts_payload,
    _voice_url,
    text_to_speech,
    validate_voice_config,
)


def _configure_settings(mock_settings) -> None:
    """Fill mock settings with the full TTS config surface so f-string /
    dict formatting inside the service don't leak MagicMock reprs."""
    mock_settings.elevenlabs_api_key = "key"
    mock_settings.elevenlabs_voice_id = "voice123456"
    mock_settings.elevenlabs_model_id = "eleven_turbo_v2_5"
    mock_settings.elevenlabs_stability = 0.5
    mock_settings.elevenlabs_similarity_boost = 0.75
    mock_settings.elevenlabs_style = 0.3
    mock_settings.elevenlabs_use_speaker_boost = True
    mock_settings.elevenlabs_speed = 0.9
    mock_settings.elevenlabs_output_format = "mp3_44100_192"


class TestTTSPayload:
    def test_payload_carries_all_tuned_voice_settings(self):
        with patch("app.services.elevenlabs_service.settings") as mock_settings:
            _configure_settings(mock_settings)
            payload = _tts_payload("Hello there.")

        assert payload["model_id"] == "eleven_turbo_v2_5"
        assert payload["text"] == "Hello there."
        assert payload["voice_settings"] == {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
            "speed": 0.9,
        }

    def test_voice_url_pins_output_format_and_streaming_latency(self):
        with patch("app.services.elevenlabs_service.settings") as mock_settings:
            _configure_settings(mock_settings)
            url = _voice_url()

        assert "text-to-speech/voice123456" in url
        assert "output_format=mp3_44100_192" in url
        # We fetch the whole blob, so ask for the highest-quality synth.
        assert "optimize_streaming_latency=0" in url


class TestTextToSpeech:
    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        with patch("app.services.elevenlabs_service.settings") as mock_settings:
            mock_settings.elevenlabs_api_key = ""
            result = await text_to_speech("Hello")
        assert result.ok is False
        assert result.error == "ELEVENLABS_API_KEY is not set"

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit(self):
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.content = b"mp3-bytes"

        rate_resp = MagicMock()
        rate_resp.status_code = 429
        rate_resp.text = "rate limited"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[rate_resp, ok_resp])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.elevenlabs_service.settings") as mock_settings,
            patch(
                "app.services.elevenlabs_service.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("app.services.elevenlabs_service.asyncio.sleep", new=AsyncMock()),
        ):
            _configure_settings(mock_settings)
            result = await text_to_speech("Hello")

        assert result == TTSResult(audio=b"mp3-bytes")
        assert mock_client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_invalid_voice_returns_error(self):
        resp = MagicMock()
        resp.status_code = 404
        resp.text = "voice not found"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.elevenlabs_service.settings") as mock_settings,
            patch(
                "app.services.elevenlabs_service.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            _configure_settings(mock_settings)
            mock_settings.elevenlabs_voice_id = "bad-voice"
            result = await text_to_speech("Hello")

        assert result.ok is False
        assert "Voice not found" in (result.error or "")


class TestValidateVoiceConfig:
    @pytest.mark.asyncio
    async def test_valid_voice(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.json = MagicMock(return_value={"name": "Charlie"})

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.elevenlabs_service.settings") as mock_settings,
            patch(
                "app.services.elevenlabs_service.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            _configure_settings(mock_settings)
            ok, detail = await validate_voice_config()

        assert ok is True
        assert "Charlie" in detail
