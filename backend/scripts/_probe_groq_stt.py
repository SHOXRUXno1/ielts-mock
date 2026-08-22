"""Probe Groq STT from the backend container. Never prints secrets."""

from __future__ import annotations

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
    key = (settings.groq_api_key or "").strip()
    print(f"GROQ_KEY_SET={bool(key)} GROQ_KEY_LEN={len(key)} PREFIX={key[:7] + '…' if key else '-'}")
    if not key:
        raise SystemExit("no groq key")

    headers = {"Authorization": f"Bearer {key}"}
    wav = _silent_wav()
    print(f"WAV_BYTES={len(wav)}")

    with httpx.Client(timeout=30.0) as client:
        models = client.get("https://api.groq.com/openai/v1/models", headers=headers)
        print(f"MODELS_STATUS={models.status_code}")
        if models.status_code == 200:
            ids = [m.get("id") for m in models.json().get("data", [])]
            whisper = [i for i in ids if i and "whisper" in i]
            print(f"WHISPER_MODELS={whisper[:8]}")
        else:
            print(f"MODELS_BODY={models.text[:200]}")

        for model in ("whisper-large-v3", "whisper-large-v3-turbo"):
            resp = client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files={"file": ("probe.wav", wav, "audio/wav")},
                data={"model": model, "response_format": "json", "language": "en"},
            )
            print(f"STT_{model}={resp.status_code} BODY={resp.text[:180]}")


if __name__ == "__main__":
    main()
