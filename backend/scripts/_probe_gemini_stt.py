"""Probe Gemini audio transcription. Never prints secrets."""

from __future__ import annotations

import base64
import io
import struct
import wave

import httpx

from app.core.config import settings


def _silent_wav(seconds: float = 0.4) -> bytes:
    rate = 16000
    n = int(rate * seconds)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack("<" + "h" * n, *([0] * n)))
    return buf.getvalue()


def main() -> None:
    keys = settings.gemini_key_list
    print(f"GEMINI_KEYS={len(keys)} MODEL={settings.gemini_model}")
    if not keys:
        raise SystemExit("no gemini keys")
    key = keys[0]
    print(f"GEMINI_KEY_LEN={len(key)} PREFIX={key[:6] + '…'}")

    wav = _silent_wav()
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "audio/wav",
                            "data": base64.b64encode(wav).decode(),
                        }
                    },
                    {
                        "text": (
                            "Transcribe this spoken English recording verbatim. "
                            "Return only the transcript text. "
                            "If there is no speech, return EMPTY."
                        )
                    },
                ]
            }
        ],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 256},
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/{settings.gemini_model}:generateContent"
    )
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(url, json=payload, params={"key": key})
        print(f"GEMINI_STT_STATUS={resp.status_code}")
        print(f"GEMINI_STT_BODY={resp.text[:400]}")


if __name__ == "__main__":
    main()
