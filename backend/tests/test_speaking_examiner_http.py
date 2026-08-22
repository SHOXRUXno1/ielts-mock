"""HTTP tests for speaking examiner endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.speaking_examiner import (
    FORCED_END_TEXT,
    MAX_EXAMINER_TURNS,
    PART2_BEGIN_SPEAKING,
    _simli_credits_response,
)


class TestAuth:
    def test_part2_begin_phrase_requires_auth(self, anon_client):
        resp = anon_client.get("/admin/speaking-examiner/part2-begin-phrase")
        assert resp.status_code == 403


class TestPart2BeginPhrase:
    def test_returns_cached_phrase(self, auth_client):
        with patch(
            "app.api.speaking_examiner._tts_base64",
            new=AsyncMock(return_value=("YmFzZTY0", None, True)),
        ):
            resp = auth_client.get("/admin/speaking-examiner/part2-begin-phrase")
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == PART2_BEGIN_SPEAKING
        assert data["audio_base64"] == "YmFzZTY0"


class TestSimliCredits:
    def test_parses_402_response(self):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 402
        resp.json = MagicMock(
            return_value={
                "session_token": "token",
                "detail": "Free credits ran out, upgrade plan on https://app.simli.com",
            }
        )
        payload = _simli_credits_response(resp)
        assert payload is not None
        assert payload["enabled"] is False
        assert payload["reason"] == "simli_credits_exhausted"
        assert "Free credits ran out" in payload["detail"]


class TestTranscribeValidation:
    def test_rejects_short_file(self, auth_client):
        resp = auth_client.post(
            "/admin/speaking-examiner/transcribe",
            files={"file": ("recording.webm", b"tiny", "audio/webm")},
        )
        assert resp.status_code == 400
        assert "too short" in resp.json()["detail"].lower()

    def test_rejects_unsupported_mime(self, auth_client):
        resp = auth_client.post(
            "/admin/speaking-examiner/transcribe",
            files={"file": ("recording.txt", b"x" * 1024, "text/plain")},
        )
        assert resp.status_code == 400
        assert "unsupported" in resp.json()["detail"].lower()

    @patch("app.api.speaking_examiner.transcribe_audio_bytes", new=AsyncMock(return_value="hello"))
    def test_accepts_webm_with_codecs_suffix(self, auth_client):
        resp = auth_client.post(
            "/admin/speaking-examiner/transcribe",
            files={
                "file": (
                    "recording.webm",
                    b"x" * 1024,
                    "audio/webm;codecs=opus",
                )
            },
        )
        assert resp.status_code == 200
        assert resp.json()["transcript"] == "hello"

    def test_rejects_oversized_file(self, auth_client):
        resp = auth_client.post(
            "/admin/speaking-examiner/transcribe",
            files={
                "file": (
                    "recording.webm",
                    b"x" * (10 * 1024 * 1024 + 1),
                    "audio/webm",
                )
            },
        )
        assert resp.status_code == 400
        assert "too large" in resp.json()["detail"].lower()


class TestRespondForcedEnd:
    def test_forced_end_at_max_turns(self, auth_client):
        history = [
            {"role": "examiner", "text": f"Q{i}"} for i in range(MAX_EXAMINER_TURNS)
        ]
        with patch(
            "app.api.speaking_examiner._tts_base64",
            new=AsyncMock(return_value=("audio", None, False)),
        ):
            resp = auth_client.post(
                "/admin/speaking-examiner/respond",
                json={"candidate_text": "Answer", "conversation_history": history},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == FORCED_END_TEXT
        assert data["is_end"] is True


class TestSessionCrud:
    def test_respond_unknown_session_returns_404(self, auth_client):
        resp = auth_client.post(
            "/admin/speaking-examiner/respond",
            json={
                "candidate_text": "Answer",
                "conversation_history": [],
                "session_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 404

    def test_list_sessions_returns_array(self, auth_client):
        resp = auth_client.get("/admin/speaking-examiner/sessions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
