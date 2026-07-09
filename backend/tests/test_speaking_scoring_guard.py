"""Tests for speaking examiner scoring guard tiers."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.speaking_examiner import NO_SPEECH_TRANSCRIPT


def _gemini_score(band: float = 6.0) -> dict:
    criterion = {"band": band, "feedback": "Gemini feedback"}
    return {
        "fluency_coherence": dict(criterion),
        "lexical_resource": dict(criterion),
        "grammatical_range": dict(criterion),
        "pronunciation": dict(criterion),
        "overall_band": band,
        "strengths": ["Good effort"],
        "improvements": ["Keep practicing"],
        "corrections": [],
        "example_phrases": ["For example"],
        "transcript": "sample transcript",
    }


def _long_answer(word_count: int = 20) -> str:
    words = [f"word{i}" for i in range(word_count)]
    return " ".join(words)


def _tier5_history() -> list[dict]:
    history: list[dict] = []
    for i in range(5):
        history.append({"role": "examiner", "text": f"Question number {i + 1} please"})
        history.append(
            {
                "role": "candidate",
                "text": _long_answer(16),
            }
        )
    return history


class TestScoringGuardTiers:
    def test_tier0_zero_words(self, auth_client):
        history = [{"role": "examiner", "text": "Tell me about your hometown."}]
        with patch(
            "app.api.speaking_examiner.evaluate_speaking_dialog",
            new=AsyncMock(),
        ) as mock_score:
            resp = auth_client.post(
                "/admin/speaking-examiner/score",
                json={"conversation_history": history},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_band"] == 0.0
        assert data["transcript"] == "(No speech detected)"
        assert data["conversation_history"] == history
        mock_score.assert_not_called()

    def test_tier1_under_10_words(self, auth_client):
        history = [
            {"role": "examiner", "text": "What is your name?"},
            {"role": "candidate", "text": "yes no ok"},
        ]
        with patch(
            "app.api.speaking_examiner.evaluate_speaking_dialog",
            new=AsyncMock(),
        ) as mock_score:
            resp = auth_client.post(
                "/admin/speaking-examiner/score",
                json={"conversation_history": history},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_band"] == 1.0
        assert data["transcript"] == "yes no ok"
        mock_score.assert_not_called()

    def test_tier3_caps_gemini(self, auth_client):
        history = [
            {"role": "examiner", "text": "Tell me about your job."},
            {"role": "candidate", "text": _long_answer(20)},
        ]
        with patch(
            "app.api.speaking_examiner.evaluate_speaking_dialog",
            new=AsyncMock(return_value=_gemini_score(6.0)),
        ) as mock_score:
            resp = auth_client.post(
                "/admin/speaking-examiner/score",
                json={"conversation_history": history},
            )

        assert resp.status_code == 200
        data = resp.json()
        mock_score.assert_awaited_once()
        assert data["fluency_coherence"]["band"] <= 3.0
        assert data["overall_band"] <= 3.0
        assert data["improvements"][0].startswith("Your responses were extremely short")

    def test_tier4_few_turns(self, auth_client):
        history = [
            {"role": "examiner", "text": "Question one"},
            {"role": "candidate", "text": _long_answer(20)},
            {"role": "examiner", "text": "Question two"},
            {"role": "candidate", "text": _long_answer(20)},
        ]
        with patch(
            "app.api.speaking_examiner.evaluate_speaking_dialog",
            new=AsyncMock(return_value=_gemini_score(6.0)),
        ) as mock_score:
            resp = auth_client.post(
                "/admin/speaking-examiner/score",
                json={"conversation_history": history},
            )

        assert resp.status_code == 200
        data = resp.json()
        mock_score.assert_awaited_once()
        assert data["overall_band"] <= 2.0
        for key in (
            "fluency_coherence",
            "lexical_resource",
            "grammatical_range",
            "pronunciation",
        ):
            assert data[key]["band"] <= 2.0

    def test_tier5_full_eval(self, auth_client):
        history = _tier5_history()
        with patch(
            "app.api.speaking_examiner.evaluate_speaking_dialog",
            new=AsyncMock(return_value=_gemini_score(6.5)),
        ) as mock_score:
            resp = auth_client.post(
                "/admin/speaking-examiner/score",
                json={"conversation_history": history},
            )

        assert resp.status_code == 200
        data = resp.json()
        mock_score.assert_awaited_once_with(history)
        assert data["overall_band"] == 6.5
        assert data["conversation_history"] == history


class TestTranscribeEmptySentinel:
    @patch(
        "app.api.speaking_examiner.transcribe_audio_bytes",
        new=AsyncMock(return_value=""),
    )
    def test_transcribe_empty_returns_sentinel(self, auth_client):
        resp = auth_client.post(
            "/admin/speaking-examiner/transcribe",
            files={"file": ("recording.webm", b"x" * 1024, "audio/webm")},
        )
        assert resp.status_code == 200
        assert resp.json()["transcript"] == NO_SPEECH_TRANSCRIPT


class TestScoreHistoryPreference:
    def test_score_prefers_client_history_over_db(self, auth_client):
        session_id = str(uuid.uuid4())
        db_history = [{"role": "examiner", "text": "Stale DB question"}]
        client_history = _tier5_history()

        with patch(
            "app.api.speaking_examiner._get_live_session",
            new=AsyncMock(
                return_value=MagicMock(history_json=db_history),
            ),
        ), patch(
            "app.api.speaking_examiner.evaluate_speaking_dialog",
            new=AsyncMock(return_value=_gemini_score(6.0)),
        ) as mock_score:
            resp = auth_client.post(
                "/admin/speaking-examiner/score",
                json={
                    "conversation_history": client_history,
                    "session_id": session_id,
                },
            )

        assert resp.status_code == 200
        mock_score.assert_awaited_once_with(client_history)
