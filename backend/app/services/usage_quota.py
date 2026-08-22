"""Read remaining quota and spend straight from the providers that expose it.

Each provider is queried independently and a failure is reported as a status on
that provider's card rather than failing the whole request, so one revoked key
cannot blank the admin's usage page.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.services import usage_meter

logger = logging.getLogger(__name__)

_TIMEOUT = 12.0


def _card(
    name: str,
    configured: bool,
    status: str,
    **extra: Any,
) -> dict[str, Any]:
    """One provider's tile. `status` is 'ok' | 'warning' | 'error' | 'unknown'."""
    return {"name": name, "configured": configured, "status": status, **extra}


async def _elevenlabs(client: httpx.AsyncClient) -> dict[str, Any]:
    if not settings.elevenlabs_api_key:
        return _card("ElevenLabs", False, "unknown", detail="No API key configured")

    try:
        resp = await client.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": settings.elevenlabs_api_key},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("ElevenLabs quota lookup failed: %s", exc)
        return _card("ElevenLabs", True, "error", detail=f"Unreachable: {type(exc).__name__}")

    if resp.status_code != 200:
        return _card(
            "ElevenLabs",
            True,
            "error",
            detail=f"HTTP {resp.status_code}",
        )

    body = resp.json()
    used = body.get("character_count")
    limit = body.get("character_limit")
    remaining = limit - used if isinstance(used, int) and isinstance(limit, int) else None
    percent_left = (
        round(remaining / limit * 100) if remaining is not None and limit else None
    )

    status = "ok"
    if percent_left is not None and percent_left <= 5:
        status = "error"
    elif percent_left is not None and percent_left <= 20:
        status = "warning"

    reset_unix = body.get("next_character_count_reset_unix")
    resets_at = None
    if isinstance(reset_unix, (int, float)) and reset_unix > 0:
        resets_at = datetime.fromtimestamp(reset_unix, tz=timezone.utc).isoformat()

    return _card(
        "ElevenLabs",
        True,
        status,
        tier=body.get("tier"),
        used=used,
        limit=limit,
        remaining=remaining,
        percent_left=percent_left,
        unit="characters",
        resets_at=resets_at,
    )


async def _digitalocean(client: httpx.AsyncClient) -> dict[str, Any]:
    if not settings.digitalocean_api_token:
        return _card(
            "DigitalOcean",
            False,
            "unknown",
            detail="No API token configured",
        )

    headers = {"Authorization": f"Bearer {settings.digitalocean_api_token}"}
    try:
        resp = await client.get(
            "https://api.digitalocean.com/v2/customers/my/balance",
            headers=headers,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("DigitalOcean balance lookup failed: %s", exc)
        return _card(
            "DigitalOcean", True, "error", detail=f"Unreachable: {type(exc).__name__}"
        )

    if resp.status_code != 200:
        return _card("DigitalOcean", True, "error", detail=f"HTTP {resp.status_code}")

    body = resp.json()
    # DO returns these as decimal strings, e.g. "23.44".
    #   account_balance      - carried over, excludes this month's usage
    #   month_to_date_usage  - spent so far this billing period
    #   month_to_date_balance- the two combined, i.e. the real amount due
    month_to_date = body.get("month_to_date_usage")
    balance = body.get("account_balance")
    due = body.get("month_to_date_balance")

    # A negative balance is prepaid credit; a positive one is money owed, and
    # only that is worth flagging.
    status = "ok"
    try:
        if due is not None and float(due) > 0:
            status = "warning"
    except (TypeError, ValueError):
        pass

    return _card(
        "DigitalOcean",
        True,
        status,
        month_to_date_usage=month_to_date,
        account_balance=balance,
        month_to_date_balance=due,
        generated_at=body.get("generated_at"),
        unit="USD",
    )


def _gemini() -> dict[str, Any]:
    keys = settings.gemini_key_list
    if not keys:
        return _card("Gemini", False, "unknown", detail="No API keys configured")

    meter = usage_meter.snapshot()
    g = meter["gemini"]
    daily_budget = g["free_tier_daily_per_key"] * len(keys)
    used = g["calls_today"]
    remaining = max(0, daily_budget - used)
    percent_left = round(remaining / daily_budget * 100) if daily_budget else None

    status = "ok"
    if g["rate_limited_today"] > 0:
        status = "warning"
    if percent_left is not None and percent_left <= 5:
        status = "error"

    return _card(
        "Gemini",
        True,
        status,
        model=settings.gemini_model,
        key_count=len(keys),
        rpm_per_key=settings.gemini_rpm_limit,
        used=used,
        limit=daily_budget,
        remaining=remaining,
        percent_left=percent_left,
        rate_limited_today=g["rate_limited_today"],
        unit="requests/day",
        counting_since=meter["counting_since"],
        estimated=True,
    )


def _groq() -> dict[str, Any]:
    if not settings.groq_api_key:
        return _card("Groq", False, "unknown", detail="No API key configured")

    observed = usage_meter.snapshot()["groq"]
    if not observed:
        return _card(
            "Groq",
            True,
            "unknown",
            detail="No request made yet since restart",
            stt_rpm_budget=settings.groq_stt_rpm_limit,
        )

    stt = observed.get("stt", {})
    remaining_req = stt.get("x-ratelimit-remaining-requests")
    limit_req = stt.get("x-ratelimit-limit-requests")

    status = "ok"
    try:
        if remaining_req is not None and int(remaining_req) == 0:
            status = "warning"
    except (TypeError, ValueError):
        pass

    return _card(
        "Groq",
        True,
        status,
        model=settings.groq_examiner_model,
        stt_model="whisper-large-v3",
        remaining_requests=remaining_req,
        limit_requests=limit_req,
        remaining_audio_seconds=stt.get("x-ratelimit-remaining-audio-seconds"),
        limit_audio_seconds=stt.get("x-ratelimit-limit-audio-seconds"),
        observed_at=stt.get("observed_at"),
        stt_rpm_budget=settings.groq_stt_rpm_limit,
        unit="requests/min",
    )


def _simli() -> dict[str, Any]:
    """Simli exposes no quota endpoint, only a 402 when credits run out.

    Minting a probe token would consume a concurrency slot a live candidate may
    need, so the card reports configuration rather than calling out.
    """
    if not settings.simli_api_key:
        return _card("Simli", False, "unknown", detail="No API key configured")
    return _card(
        "Simli",
        True,
        "unknown",
        detail="Simli has no quota API; credits show up only when a session fails",
        max_concurrent=settings.simli_max_concurrent,
    )


async def collect_usage() -> dict[str, Any]:
    """Gather every provider tile, querying the remote ones concurrently."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        elevenlabs, digitalocean = await asyncio.gather(
            _elevenlabs(client),
            _digitalocean(client),
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "providers": [
            digitalocean,
            _gemini(),
            _groq(),
            elevenlabs,
            _simli(),
        ],
    }
