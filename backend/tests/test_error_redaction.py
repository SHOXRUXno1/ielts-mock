"""Gemini takes its API key as a query parameter, so an httpx error quotes a
live credential. That text is logged, stored on the evaluation job and shown in
the admin panel, so the key has to be stripped before it travels anywhere.
"""

import httpx
import pytest

from app.services.llm import _gemini_request_with_rotation, redact_api_keys

# Shaped like a Gemini key, deliberately not one.
KEY = "AQ.Ab8" + "0" * 45
URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    f"/gemini-3.1-flash-lite:generateContent?key={KEY}"
)


def test_redacts_a_key_carried_in_a_url():
    message = f"Client error '400 Bad Request' for url '{URL}'"

    cleaned = redact_api_keys(message)

    assert KEY not in cleaned
    assert "key=REDACTED" in cleaned
    assert "400 Bad Request" in cleaned


def test_leaves_text_without_a_key_alone():
    message = "No Gemini API keys configured"

    assert redact_api_keys(message) == message


def test_keeps_other_query_parameters():
    cleaned = redact_api_keys(f"GET {URL}&alt=sse failed")

    assert "alt=sse" in cleaned
    assert KEY not in cleaned


@pytest.mark.asyncio
async def test_a_rejected_request_reports_without_the_key(monkeypatch):
    """The 400 that ends the retry loop must surface a redacted message."""
    monkeypatch.setattr(
        "app.services.llm.settings.gemini_api_keys", "key-a", raising=False
    )

    async def always_rejected(api_key: str) -> httpx.Response:
        request = httpx.Request("POST", URL)
        response = httpx.Response(400, request=request, text="Bad Request")
        raise httpx.HTTPStatusError(
            f"Client error '400 Bad Request' for url '{URL}'",
            request=request,
            response=response,
        )

    with pytest.raises(httpx.HTTPStatusError) as caught:
        await _gemini_request_with_rotation(always_rejected)

    reported = str(caught.value)
    assert KEY not in reported
    assert "key=REDACTED" in reported
    # A chained exception is printed with the traceback, so it must be clean too.
    assert caught.value.__context__ is None or KEY not in str(
        caught.value.__context__
    )
