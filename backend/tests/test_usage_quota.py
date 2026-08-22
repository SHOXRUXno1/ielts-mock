"""Usage page must degrade gracefully: one dead provider cannot blank the page."""

from __future__ import annotations

import httpx
import pytest

from app.services import usage_meter, usage_quota


@pytest.fixture(autouse=True)
def _reset_meter():
    usage_meter._gemini_calls.clear()
    usage_meter._gemini_rate_limited.clear()
    usage_meter._groq_limits.clear()
    yield
    usage_meter._gemini_calls.clear()
    usage_meter._gemini_rate_limited.clear()
    usage_meter._groq_limits.clear()


def test_gemini_card_scales_budget_with_key_count(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "gemini_api_keys", "a,b,c")

    card = usage_quota._gemini()

    assert card["configured"] is True
    assert card["key_count"] == 3
    assert card["limit"] == 3 * usage_meter.GEMINI_FREE_TIER_DAILY_PER_KEY
    assert card["estimated"] is True


def test_gemini_card_counts_calls_and_throttles(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "gemini_api_keys", "a")

    usage_meter.record_gemini_call()
    usage_meter.record_gemini_call()
    usage_meter.record_gemini_rate_limited()

    card = usage_quota._gemini()

    assert card["used"] == 2
    assert card["remaining"] == usage_meter.GEMINI_FREE_TIER_DAILY_PER_KEY - 2
    # A throttle today is worth surfacing even while plenty of budget is left.
    assert card["rate_limited_today"] == 1
    assert card["status"] == "warning"


def test_unconfigured_providers_report_rather_than_raise(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "gemini_api_keys", "")
    monkeypatch.setattr(usage_quota.settings, "groq_api_key", "")
    monkeypatch.setattr(usage_quota.settings, "simli_api_key", "")

    for card in (usage_quota._gemini(), usage_quota._groq(), usage_quota._simli()):
        assert card["configured"] is False
        assert card["status"] == "unknown"
        assert card["detail"]


def test_groq_card_uses_last_seen_headers(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "groq_api_key", "gsk_test")

    # Before any request there is nothing to report, and that must not look
    # like an exhausted quota.
    assert usage_quota._groq()["status"] == "unknown"

    usage_meter.record_groq_headers(
        {
            "x-ratelimit-limit-requests": "20",
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-remaining-audio-seconds": "120",
        },
        "stt",
    )

    card = usage_quota._groq()
    assert card["remaining_requests"] == "0"
    assert card["limit_requests"] == "20"
    assert card["status"] == "warning"


@pytest.mark.asyncio
async def test_elevenlabs_low_balance_is_flagged(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "elevenlabs_api_key", "xi_test")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "tier": "creator",
                "character_count": 99_000,
                "character_limit": 100_000,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        card = await usage_quota._elevenlabs(client)

    assert card["remaining"] == 1_000
    assert card["percent_left"] == 1
    assert card["status"] == "error"


@pytest.mark.asyncio
async def test_elevenlabs_unreachable_does_not_raise(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "elevenlabs_api_key", "xi_test")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        card = await usage_quota._elevenlabs(client)

    assert card["status"] == "error"
    assert "Unreachable" in card["detail"]


@pytest.mark.asyncio
async def test_digitalocean_flags_money_owed(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "digitalocean_api_token", "dop_test")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer dop_test"
        return httpx.Response(
            200,
            json={
                "month_to_date_usage": "11.21",
                "account_balance": "12.23",
                "month_to_date_balance": "23.44",
                "generated_at": "2026-08-23T00:00:00Z",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        card = await usage_quota._digitalocean(client)

    assert card["month_to_date_usage"] == "11.21"
    assert card["month_to_date_balance"] == "23.44"
    assert card["status"] == "warning"


@pytest.mark.asyncio
async def test_digitalocean_credit_balance_is_healthy(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "digitalocean_api_token", "dop_test")

    def handler(request: httpx.Request) -> httpx.Response:
        # DigitalOcean reports prepaid credit as a negative balance.
        return httpx.Response(
            200,
            json={
                "month_to_date_usage": "8.10",
                "account_balance": "-40.00",
                "month_to_date_balance": "-31.90",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        card = await usage_quota._digitalocean(client)

    assert card["status"] == "ok"


@pytest.mark.asyncio
async def test_collect_usage_returns_every_provider(monkeypatch):
    monkeypatch.setattr(usage_quota.settings, "elevenlabs_api_key", "")
    monkeypatch.setattr(usage_quota.settings, "digitalocean_api_token", "")

    payload = await usage_quota.collect_usage()

    names = [p["name"] for p in payload["providers"]]
    assert names == ["DigitalOcean", "Gemini", "Groq", "ElevenLabs", "Simli"]
    assert payload["generated_at"]
