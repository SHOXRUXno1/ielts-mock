"""In-process counters for provider usage the providers themselves do not expose.

Google does not publish a "quota remaining" endpoint for Gemini, so the only
way to tell an admin how much of the daily free-tier allowance is left is to
count the calls we make. Groq does report its ceiling, but only in the headers
of a real response, so the last seen values are cached here rather than probed
on demand.

Counters live in the process, not the database: they reset on redeploy, and the
snapshot reports since when it has been counting so the number is never read as
an absolute truth.
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from datetime import date, datetime, timezone
from typing import Any, Mapping

_lock = threading.Lock()

_process_started_at = datetime.now(timezone.utc)

# date -> number of successful Gemini calls on that day
_gemini_calls: dict[date, int] = defaultdict(int)
# date -> number of Gemini calls rejected with 429 RESOURCE_EXHAUSTED
_gemini_rate_limited: dict[date, int] = defaultdict(int)

# STT transcripts our silence-guard threw away. The static list of stock
# hallucinations in llm.py needs to grow as Whisper evolves; without a
# sample we would only find out when a new phrase slips through and is
# stored as a candidate answer.
_stt_discarded: dict[date, int] = defaultdict(int)
_stt_discarded_recent: deque[str] = deque(maxlen=20)

# Last rate-limit headers Groq returned, per endpoint kind ("stt" / "chat")
_groq_limits: dict[str, dict[str, Any]] = {}

_GROQ_HEADERS = (
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-audio-seconds",
    "x-ratelimit-remaining-audio-seconds",
)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _prune(store: dict[date, int]) -> None:
    """Keep only the last two days so the dicts cannot grow without bound."""
    today = _today()
    for key in list(store):
        if (today - key).days > 1:
            del store[key]


def record_gemini_call() -> None:
    with _lock:
        _gemini_calls[_today()] += 1
        _prune(_gemini_calls)


def record_gemini_rate_limited() -> None:
    with _lock:
        _gemini_rate_limited[_today()] += 1
        _prune(_gemini_rate_limited)


def record_stt_discarded(text: str) -> None:
    """Called when the silence-guard drops a suspicious transcript.

    Keeps a per-day count plus a ring of the last 20 samples so an operator
    can see which new phrases Whisper is inventing and extend the guard list.
    """
    sample = (text or "").strip()[:80]
    with _lock:
        _stt_discarded[_today()] += 1
        _prune(_stt_discarded)
        if sample:
            _stt_discarded_recent.append(sample)


def record_groq_headers(headers: Mapping[str, str], kind: str) -> None:
    """Remember Groq's own reported ceiling from a response we already made."""
    seen = {name: headers[name] for name in _GROQ_HEADERS if name in headers}
    if not seen:
        return
    seen["observed_at"] = datetime.now(timezone.utc).isoformat()
    with _lock:
        _groq_limits[kind] = seen


def snapshot() -> dict[str, Any]:
    with _lock:
        today = _today()
        calls = _gemini_calls.get(today, 0)
        throttled = _gemini_rate_limited.get(today, 0)
        groq = {kind: dict(vals) for kind, vals in _groq_limits.items()}
        stt_dropped_today = _stt_discarded.get(today, 0)
        stt_recent = list(_stt_discarded_recent)

    return {
        "counting_since": _process_started_at.isoformat(),
        "gemini": {
            "calls_today": calls,
            "rate_limited_today": throttled,
        },
        "groq": groq,
        "stt_silence_guard": {
            "dropped_today": stt_dropped_today,
            "recent_samples": stt_recent,
        },
    }
