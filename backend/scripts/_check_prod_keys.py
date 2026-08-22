#!/usr/bin/env python3
"""Test the production API keys from wherever this runs.

The production VPS sits in Russia, where Google and Groq refuse requests. Run
this from a non-blocked network to tell the two causes apart:

  * key works here      -> the key and quota are fine, the VPS is geo-blocked
  * key fails here too  -> the key itself is revoked / out of quota

Keys are read from the environment so they never live in the repo:

  $env:PROD_GEMINI_KEY='...'; $env:PROD_GROQ_KEY='...'
  $env:PROD_ELEVENLABS_KEY='...'; $env:PROD_SIMLI_KEY='...'
  python scripts/_check_prod_keys.py
"""

from __future__ import annotations

import asyncio
import json
import os

import httpx

GEMINI_MODEL = "gemini-3.1-flash-lite"


def show(label: str, status: int | str, detail: str = "") -> None:
    print(f"{label:26s} {str(status):>6}  {detail}")


async def check_gemini(client: httpx.AsyncClient, key: str) -> None:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    try:
        resp = await client.post(
            url,
            params={"key": key},
            json={"contents": [{"parts": [{"text": "Reply with the word OK"}]}]},
        )
    except Exception as exc:  # noqa: BLE001
        show("Gemini generateContent", "ERR", f"{type(exc).__name__}: {exc}")
        return

    if resp.status_code == 200:
        try:
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:  # noqa: BLE001
            text = "(200 but unexpected shape)"
        show("Gemini generateContent", 200, f"reply={text.strip()[:40]!r}")
    else:
        body = resp.json() if resp.headers.get("content-type", "").startswith(
            "application/json"
        ) else {}
        err = (body.get("error") or {})
        show(
            "Gemini generateContent",
            resp.status_code,
            f"{err.get('status', '')} {err.get('message', resp.text[:120])}",
        )


async def check_groq(client: httpx.AsyncClient, key: str) -> None:
    headers = {"Authorization": f"Bearer {key}"}
    try:
        resp = await client.get(
            "https://api.groq.com/openai/v1/models", headers=headers
        )
    except Exception as exc:  # noqa: BLE001
        show("Groq models", "ERR", f"{type(exc).__name__}: {exc}")
        return

    if resp.status_code == 200:
        ids = [m.get("id") for m in resp.json().get("data", [])]
        whisper = [i for i in ids if i and "whisper" in i]
        show("Groq models", 200, f"whisper models: {whisper}")
    else:
        show("Groq models", resp.status_code, resp.text[:140])


async def check_elevenlabs(client: httpx.AsyncClient, key: str) -> None:
    """Read the quota, then do a real synthesis — the quota route needs a
    permission the prod key may not carry, but synthesis is what actually
    matters, and it is where an exhausted plan surfaces."""
    headers = {"xi-api-key": key}
    try:
        resp = await client.get(
            "https://api.elevenlabs.io/v1/user/subscription", headers=headers
        )
    except Exception as exc:  # noqa: BLE001
        show("ElevenLabs quota", "ERR", f"{type(exc).__name__}: {exc}")
    else:
        if resp.status_code == 200:
            body = resp.json()
            used = body.get("character_count")
            limit = body.get("character_limit")
            left = (
                limit - used
                if isinstance(used, int) and isinstance(limit, int)
                else "?"
            )
            show(
                "ElevenLabs quota",
                200,
                f"tier={body.get('tier')} used={used}/{limit} left={left}",
            )
        else:
            show("ElevenLabs quota", resp.status_code, resp.text[:160])

    voice = os.getenv("PROD_ELEVENLABS_VOICE_ID", "IKne3meq5aSn9XLyUdCD")
    model = os.getenv("PROD_ELEVENLABS_MODEL_ID", "eleven_turbo_v2")
    try:
        tts = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
            json={"model_id": model, "text": "Good morning."},
            headers={
                "xi-api-key": key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
        )
    except Exception as exc:  # noqa: BLE001
        show("ElevenLabs synth", "ERR", f"{type(exc).__name__}: {exc}")
        return
    if tts.status_code == 200:
        show("ElevenLabs synth", 200, f"{len(tts.content)} bytes of mp3 returned")
    else:
        show("ElevenLabs synth", tts.status_code, tts.text[:200])


async def check_simli(client: httpx.AsyncClient, key: str) -> None:
    face = os.getenv("PROD_SIMLI_FACE_ID", "")
    headers = {"Content-Type": "application/json", "x-simli-api-key": key}
    try:
        resp = await client.post(
            "https://api.simli.ai/compose/token",
            json={
                "faceId": face,
                "handleSilence": True,
                "maxSessionLength": 1800,
                "maxIdleTime": 1800,
            },
            headers=headers,
        )
    except Exception as exc:  # noqa: BLE001
        show("Simli token", "ERR", f"{type(exc).__name__}: {exc}")
        return
    detail = resp.text[:180]
    if resp.status_code == 402:
        detail = "PAYMENT REQUIRED - credits exhausted: " + detail
    elif resp.status_code == 200:
        detail = "token issued, credits available"
    show("Simli token", resp.status_code, detail)


async def main() -> None:
    keys = {
        "gemini": os.getenv("PROD_GEMINI_KEY", ""),
        "groq": os.getenv("PROD_GROQ_KEY", ""),
        "elevenlabs": os.getenv("PROD_ELEVENLABS_KEY", ""),
        "simli": os.getenv("PROD_SIMLI_KEY", ""),
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            who = await client.get("https://ipinfo.io/json")
            info = who.json()
            print(
                f"Running from {info.get('ip')} "
                f"({info.get('city')}, {info.get('country')})\n"
            )
        except Exception:  # noqa: BLE001
            print("Could not determine local egress IP\n")

        print(f"{'service':26s} {'status':>6}  detail")
        print("-" * 100)
        if keys["gemini"]:
            await check_gemini(client, keys["gemini"])
        if keys["groq"]:
            await check_groq(client, keys["groq"])
        if keys["elevenlabs"]:
            await check_elevenlabs(client, keys["elevenlabs"])
        if keys["simli"]:
            await check_simli(client, keys["simli"])
        missing = [name for name, val in keys.items() if not val]
        if missing:
            print(f"\nSkipped (no env var set): {json.dumps(missing)}")


if __name__ == "__main__":
    asyncio.run(main())
