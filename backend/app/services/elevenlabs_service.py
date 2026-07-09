"""ElevenLabs Text-to-Speech service with retries and structured errors."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.services.shared_http import get_http_client

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_RETRIES = 3


@dataclass(frozen=True)
class TTSResult:
    audio: bytes
    error: str | None = None

    @property
    def ok(self) -> bool:
        return bool(self.audio)


def _voice_url() -> str:
    return f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"


def _tts_payload(text: str) -> dict:
    return {
        "model_id": settings.elevenlabs_model_id,
        "text": text,
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.85,
            "speed": 0.9,
        },
    }


def _error_from_response(resp: httpx.Response) -> str:
    body = (resp.text or "").strip()
    if resp.status_code == 401:
        return "Invalid ElevenLabs API key"
    if resp.status_code == 404:
        return f"Voice not found: {settings.elevenlabs_voice_id}"
    if resp.status_code == 422:
        return "ElevenLabs rejected request — check voice/model settings"
    if resp.status_code == 429:
        return "ElevenLabs rate limit exceeded"
    if body:
        return f"ElevenLabs HTTP {resp.status_code}: {body[:180]}"
    return f"ElevenLabs HTTP {resp.status_code}"


async def validate_voice_config() -> tuple[bool, str]:
    """Verify API key and voice id before serving examiner audio."""
    if not settings.elevenlabs_api_key:
        return False, "ELEVENLABS_API_KEY is not set"

    url = f"https://api.elevenlabs.io/v1/voices/{settings.elevenlabs_voice_id}"
    try:
        client = get_http_client()
        resp = await client.get(
            url,
            headers={"xi-api-key": settings.elevenlabs_api_key},
            timeout=15.0,
        )
        if resp.status_code == 200:
            name = resp.json().get("name", settings.elevenlabs_voice_id)
            return True, f"voice={name} model={settings.elevenlabs_model_id}"
        return False, _error_from_response(resp)
    except httpx.TimeoutException:
        return False, "ElevenLabs voice lookup timed out"
    except Exception as exc:
        logger.exception("ElevenLabs voice validation failed")
        return False, f"ElevenLabs validation failed: {type(exc).__name__}"


async def text_to_speech(text: str) -> TTSResult:
    """Convert text to speech via ElevenLabs API with retries."""
    if not settings.elevenlabs_api_key:
        return TTSResult(audio=b"", error="ELEVENLABS_API_KEY is not set")

    if not text.strip():
        return TTSResult(audio=b"", error="Empty TTS text")

    last_error = "Unknown ElevenLabs error"

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            client = get_http_client()
            resp = await client.post(
                _voice_url(),
                json=_tts_payload(text),
                headers={
                    "xi-api-key": settings.elevenlabs_api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                timeout=30.0,
            )
            if resp.status_code == 200 and resp.content:
                return TTSResult(audio=resp.content)

            last_error = _error_from_response(resp)
            if resp.status_code not in _RETRYABLE_STATUS:
                logger.error(
                    "ElevenLabs TTS failed voice=%s attempt=%d: %s",
                    settings.elevenlabs_voice_id[:8],
                    attempt,
                    last_error,
                )
                return TTSResult(audio=b"", error=last_error)

            logger.warning(
                "ElevenLabs TTS retryable failure voice=%s attempt=%d/%d: %s",
                settings.elevenlabs_voice_id[:8],
                attempt,
                _MAX_RETRIES,
                last_error,
            )
        except httpx.TimeoutException:
            last_error = "ElevenLabs request timed out"
            logger.warning(
                "ElevenLabs TTS timeout voice=%s attempt=%d/%d",
                settings.elevenlabs_voice_id[:8],
                attempt,
                _MAX_RETRIES,
            )
        except Exception as exc:
            last_error = f"ElevenLabs error: {type(exc).__name__}"
            logger.exception(
                "ElevenLabs TTS unexpected failure voice=%s attempt=%d/%d",
                settings.elevenlabs_voice_id[:8],
                attempt,
                _MAX_RETRIES,
            )

        if attempt < _MAX_RETRIES:
            await asyncio.sleep(0.6 * attempt)

    logger.error(
        "ElevenLabs TTS exhausted retries voice=%s: %s",
        settings.elevenlabs_voice_id[:8],
        last_error,
    )
    return TTSResult(audio=b"", error=last_error)
