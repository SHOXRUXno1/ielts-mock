"""Unit tests for ElevenLabs TTS service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.elevenlabs_service import TTSResult, text_to_speech, validate_voice_config


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
            mock_settings.elevenlabs_api_key = "key"
            mock_settings.elevenlabs_voice_id = "voice123456"
            mock_settings.elevenlabs_model_id = "eleven_turbo_v2"
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
            mock_settings.elevenlabs_api_key = "key"
            mock_settings.elevenlabs_voice_id = "bad-voice"
            mock_settings.elevenlabs_model_id = "eleven_turbo_v2"
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
            mock_settings.elevenlabs_api_key = "key"
            mock_settings.elevenlabs_voice_id = "voice123456"
            mock_settings.elevenlabs_model_id = "eleven_turbo_v2"
            ok, detail = await validate_voice_config()

        assert ok is True
        assert "Charlie" in detail
