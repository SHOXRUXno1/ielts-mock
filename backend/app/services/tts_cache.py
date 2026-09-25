"""LRU cache for ElevenLabs TTS base64 payloads.

The cache key includes a fingerprint of the current TTS configuration
(model, voice, voice_settings, output_format). Any change to those settings
produces a fresh fingerprint, so entries synthesized under the old settings
are naturally shadowed by new writes and evicted by the LRU without any
manual clear_tts_cache() call on deploy.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict

from app.core.config import settings

_MAX_ENTRIES = 200

_cache: OrderedDict[str, str] = OrderedDict()


def _fingerprint() -> str:
    parts = (
        settings.elevenlabs_model_id,
        settings.elevenlabs_voice_id,
        f"{settings.elevenlabs_stability:.3f}",
        f"{settings.elevenlabs_similarity_boost:.3f}",
        f"{settings.elevenlabs_style:.3f}",
        "1" if settings.elevenlabs_use_speaker_boost else "0",
        f"{settings.elevenlabs_speed:.3f}",
        settings.elevenlabs_output_format,
    )
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:8]


def _cache_key(text: str) -> str:
    return f"{_fingerprint()}:{text}"


def get_cached_tts(text: str) -> str | None:
    key = _cache_key(text)
    encoded = _cache.get(key)
    if encoded is not None:
        _cache.move_to_end(key)
    return encoded


def set_cached_tts(text: str, encoded: str) -> None:
    key = _cache_key(text)
    _cache[key] = encoded
    _cache.move_to_end(key)
    while len(_cache) > _MAX_ENTRIES:
        _cache.popitem(last=False)


def clear_tts_cache() -> None:
    _cache.clear()
