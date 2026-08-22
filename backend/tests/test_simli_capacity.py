"""The /simli-token endpoint: what a candidate gets once admission is decided.

The decision itself lives in app.services.simli_slots and is covered by
test_simli_slots.py; here we pin how the endpoint acts on it, including giving
the slot back when Simli turns out to be unreachable.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api import speaking_examiner
from app.api.speaking_examiner import get_simli_token
from app.core.config import settings

ACTOR = MagicMock(sub="candidate@example.test")


def _stub_simli_client(*_args, **_kwargs) -> AsyncMock:
    """Stand in for Simli so the endpoint can be exercised without egress."""
    ok = MagicMock()
    ok.status_code = 200
    ok.json = MagicMock(return_value={"session_token": "tok-123"})
    ok.raise_for_status = MagicMock()

    client = AsyncMock()
    client.post = AsyncMock(return_value=ok)
    client.get = AsyncMock(return_value=ok)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


def _unreachable_simli_client(*_args, **_kwargs) -> AsyncMock:
    client = AsyncMock()
    client.post = AsyncMock(side_effect=RuntimeError("simli is down"))
    client.get = AsyncMock(side_effect=RuntimeError("simli is down"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "simli_api_key", "key")
    monkeypatch.setattr(settings, "simli_face_id", "face-id-123")
    monkeypatch.setattr(settings, "simli_max_concurrent", 8)


@pytest.fixture
def admitted(monkeypatch):
    monkeypatch.setattr(
        speaking_examiner, "claim_slot", AsyncMock(return_value=(True, 2))
    )


@pytest.fixture
def released(monkeypatch):
    release = AsyncMock()
    monkeypatch.setattr(speaking_examiner, "release_slot", release)
    return release


class TestAdmission:
    @pytest.mark.asyncio
    async def test_admitted_candidate_gets_a_video_token(
        self, configured, admitted, monkeypatch
    ):
        monkeypatch.setattr(
            speaking_examiner.httpx, "AsyncClient", _stub_simli_client
        )
        payload = await get_simli_token(_actor=ACTOR, db=MagicMock())

        assert payload["enabled"] is True
        assert payload["session_token"] == "tok-123"
        assert payload["face_id"] == "face-id-123"

    @pytest.mark.asyncio
    async def test_refused_candidate_falls_back_to_audio_only(
        self, configured, monkeypatch
    ):
        monkeypatch.setattr(
            speaking_examiner, "claim_slot", AsyncMock(return_value=(False, 8))
        )
        payload = await get_simli_token(_actor=ACTOR, db=MagicMock())

        assert payload["enabled"] is False
        assert payload["reason"] == "capacity"
        assert "8/8" in payload["detail"]

    @pytest.mark.asyncio
    async def test_missing_credentials_claim_nothing(self, monkeypatch):
        """No video is possible, so the candidate must not consume a slot."""
        monkeypatch.setattr(settings, "simli_api_key", "")
        claim = AsyncMock()
        monkeypatch.setattr(speaking_examiner, "claim_slot", claim)

        payload = await get_simli_token(_actor=ACTOR, db=MagicMock())

        assert payload == {"enabled": False, "reason": "not_configured"}
        claim.assert_not_awaited()


class TestSlotIsReturnedOnFailure:
    @pytest.mark.asyncio
    async def test_unreachable_simli_gives_the_slot_back(
        self, configured, admitted, released, monkeypatch
    ):
        """No stream was ever established, so holding the claim would only deny
        the next candidate for nothing."""
        monkeypatch.setattr(
            speaking_examiner.httpx, "AsyncClient", _unreachable_simli_client
        )
        payload = await get_simli_token(_actor=ACTOR, db=MagicMock())

        assert payload["enabled"] is False
        released.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_exhausted_credits_give_the_slot_back(
        self, configured, admitted, released, monkeypatch
    ):
        def _out_of_credits(*_args, **_kwargs) -> AsyncMock:
            resp = MagicMock()
            resp.status_code = 402
            resp.json = MagicMock(
                return_value={"detail": "Free credits ran out, upgrade plan"}
            )
            client = AsyncMock()
            client.post = AsyncMock(return_value=resp)
            client.get = AsyncMock(return_value=resp)
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            return client

        monkeypatch.setattr(
            speaking_examiner.httpx, "AsyncClient", _out_of_credits
        )
        payload = await get_simli_token(_actor=ACTOR, db=MagicMock())

        assert payload["enabled"] is False
        released.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_successful_token_keeps_the_slot(
        self, configured, admitted, released, monkeypatch
    ):
        monkeypatch.setattr(
            speaking_examiner.httpx, "AsyncClient", _stub_simli_client
        )
        await get_simli_token(_actor=ACTOR, db=MagicMock())

        released.assert_not_awaited()
