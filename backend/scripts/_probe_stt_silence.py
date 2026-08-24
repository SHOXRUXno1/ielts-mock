"""Probe what Groq Whisper returns for audio that carries no speech.

Production transcripts are full of turns reading "." or "Thank you." where the
candidate plainly said nothing, so this asks the real API what it does with
silence and what confidence signals come back alongside the invented words.

Run from backend/:  py scripts/_probe_stt_silence.py
"""

from __future__ import annotations

import asyncio
import io
import json
import math
import os
import random
import struct
import wave

import httpx

from app.core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
RATE = 16000


def wav_bytes(samples: list[int]) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", s) for s in samples))
    return buf.getvalue()


def digital_silence(seconds: float) -> bytes:
    return wav_bytes([0] * int(RATE * seconds))


def room_tone(seconds: float, amplitude: int) -> bytes:
    """What a real microphone records when nobody is speaking."""
    rnd = random.Random(7)
    return wav_bytes(
        [rnd.randint(-amplitude, amplitude) for _ in range(int(RATE * seconds))]
    )


def hum(seconds: float, amplitude: int = 400) -> bytes:
    """Mains/fan hum: periodic, non-speech, the kind of thing AGC lifts up."""
    n = int(RATE * seconds)
    return wav_bytes(
        [int(amplitude * math.sin(2 * math.pi * 50 * i / RATE)) for i in range(n)]
    )


async def synth_speech(text: str) -> bytes | None:
    """Real speech to check the guard will not reject genuine short answers."""
    key = settings.elevenlabs_api_key
    if not key:
        return None
    voice = getattr(settings, "elevenlabs_voice_id", None) or "21m00Tcm4TlvDq8ikWAM"
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
            headers={"xi-api-key": key},
            json={"text": text, "model_id": "eleven_turbo_v2_5"},
        )
        if r.status_code >= 400:
            print(f"  (TTS unavailable: {r.status_code} {r.text[:120]})")
            return None
        return r.content


async def ask_groq(audio: bytes, filename: str, mime: str, verbose: bool) -> dict:
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": (filename, audio, mime)},
            data={
                "model": "whisper-large-v3",
                "response_format": "verbose_json" if verbose else "json",
                "language": "en",
            },
        )
        r.raise_for_status()
        return r.json()


def summarise(tag: str, plain: dict, rich: dict) -> None:
    text = (plain.get("text") or "").strip()
    segments = rich.get("segments") or []
    print(f"\n--- {tag} ---")
    print(f"  current params return : {text!r}")
    if not segments:
        print("  segments              : (none returned)")
        return
    for s in segments:
        print(
            "  no_speech_prob={:<6.3f} avg_logprob={:<7.3f} "
            "compression={:<6.3f} text={!r}".format(
                s.get("no_speech_prob", float("nan")),
                s.get("avg_logprob", float("nan")),
                s.get("compression_ratio", float("nan")),
                (s.get("text") or "").strip()[:70],
            )
        )


async def main() -> None:
    if not settings.groq_api_key:
        raise SystemExit("GROQ_API_KEY is not configured")

    cases: list[tuple[str, bytes, str, str]] = [
        ("digital silence, 3s", digital_silence(3), "s.wav", "audio/wav"),
        ("digital silence, 8s", digital_silence(8), "s.wav", "audio/wav"),
        ("room tone (quiet mic), 5s", room_tone(5, 60), "s.wav", "audio/wav"),
        ("room tone louder, 5s", room_tone(5, 500), "s.wav", "audio/wav"),
        ("50 Hz hum, 5s", hum(5), "s.wav", "audio/wav"),
    ]

    # Genuine speech, including a short intro-style answer, as a control: the
    # guard must not reject these.
    for label, phrase in (
        ("REAL short answer", "My name is Shoxsana Atayeva."),
        ("REAL two words", "Call me Sasha."),
    ):
        audio = await synth_speech(phrase)
        if audio:
            cases.append((f"{label}: {phrase!r}", audio, "s.mp3", "audio/mpeg"))

    for tag, audio, name, mime in cases:
        try:
            plain = await ask_groq(audio, name, mime, verbose=False)
            rich = await ask_groq(audio, name, mime, verbose=True)
        except httpx.HTTPStatusError as e:
            print(f"\n--- {tag} ---\n  HTTP {e.response.status_code}: {e.response.text[:200]}")
            continue
        summarise(tag, plain, rich)

    print("\nRaw verbose_json shape for one silent case (field discovery):")
    rich = await ask_groq(digital_silence(3), "s.wav", "audio/wav", verbose=True)
    print(json.dumps(rich, indent=2)[:1500])


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    asyncio.run(main())
