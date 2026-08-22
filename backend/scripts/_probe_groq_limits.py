#!/usr/bin/env python3
"""Read Groq's own rate-limit headers for both Whisper models.

Groq reports the account's real ceiling on every response, so one small
transcription per model tells us exactly how much headroom Speaking has and
whether the turbo model is more generous than the one in use.

  $env:PROD_GROQ_KEY='...'; py scripts/_probe_groq_limits.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx

AUDIO = sorted((Path(__file__).parent / "_speaking_audio").glob("turn_*.mp3"))
MODELS = ["whisper-large-v3", "whisper-large-v3-turbo"]
INTERESTING = (
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-audio-seconds",
    "x-ratelimit-remaining-audio-seconds",
    "retry-after",
)


async def probe(client: httpx.AsyncClient, key: str, model: str, clip: bytes) -> None:
    resp = await client.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {key}"},
        files={"file": ("answer.mp3", clip, "audio/mpeg")},
        data={"model": model, "response_format": "json", "language": "en"},
    )
    print(f"\n{model}  -> HTTP {resp.status_code}")
    for name in INTERESTING:
        val = resp.headers.get(name)
        if val is not None:
            print(f"  {name:38s} {val}")
    if resp.status_code != 200:
        print(f"  body: {resp.text[:200]}")


async def main() -> None:
    key = os.getenv("PROD_GROQ_KEY", "")
    if not key:
        raise SystemExit("Set PROD_GROQ_KEY first")
    if not AUDIO:
        raise SystemExit("No audio clips found; run scripts/_gen_speaking_audio.py")

    clip = AUDIO[0].read_bytes()
    print(f"probe clip: {AUDIO[0].name} ({len(clip) / 1024:.0f} KB)")
    async with httpx.AsyncClient(timeout=120.0) as client:
        for model in MODELS:
            await probe(client, key, model, clip)


if __name__ == "__main__":
    asyncio.run(main())
