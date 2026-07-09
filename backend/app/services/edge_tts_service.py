"""Edge TTS fallback service using Microsoft Edge's free TTS."""
from __future__ import annotations

import logging

import edge_tts

logger = logging.getLogger(__name__)

# High-quality English voice for IELTS examiner persona
_EDGE_VOICE = "en-GB-RyanNeural"


async def text_to_speech_edge(text: str) -> bytes:
    """Convert text to speech using Edge TTS (no API key required).

    Returns MP3 audio bytes or empty bytes on failure.
    """
    if not text.strip():
        return b""

    try:
        communicate = edge_tts.Communicate(text, _EDGE_VOICE)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        audio = b"".join(chunks)
        if audio:
            logger.info("TTS: Edge TTS OK voice=%s bytes=%d", _EDGE_VOICE, len(audio))
        else:
            logger.warning("TTS: Edge TTS returned empty audio voice=%s", _EDGE_VOICE)
        return audio
    except Exception:
        logger.exception("TTS: Edge TTS failed voice=%s", _EDGE_VOICE)
        return b""
