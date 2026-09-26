"""LRU cache for ElevenLabs TTS base64 payloads."""

from __future__ import annotations

from collections import OrderedDict

_MAX_ENTRIES = 200

_cache: OrderedDict[str, str] = OrderedDict()


def get_cached_tts(text: str) -> str | None:
    encoded = _cache.get(text)
    if encoded is not None:
        _cache.move_to_end(text)
    return encoded


def set_cached_tts(text: str, encoded: str) -> None:
    _cache[text] = encoded
    _cache.move_to_end(text)
    while len(_cache) > _MAX_ENTRIES:
        _cache.popitem(last=False)


def clear_tts_cache() -> None:
    _cache.clear()
