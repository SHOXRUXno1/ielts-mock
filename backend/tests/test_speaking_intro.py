"""Unit + HTTP tests for IELTS Speaking INTRO phase.

The name-exchange intro (INTRO_GREETING → INTRO_NICKNAME) has been removed.
New sessions start directly in PART_1_ACTIVE with Q1 in the greeting.
These tests cover the remaining helpers and the new /start behavior.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.speaking_examiner import (
    INTRO_GREETING,
    _extract_nickname,
    _format_intro_to_part1,
    count_questions_by_part,
    strip_intro,
)
from app.models.speaking_session import SpeakingState
from app.services.speaking_plan import DEFAULT_PART1, SpeakingPlan


FIRST_Q = DEFAULT_PART1[0]


class TestExtractNickname:
    """Legacy helper — kept for backward compatibility."""

    def test_simple_name(self):
        assert _extract_nickname("Alibek") == "Alibek"

    def test_call_me_prefix(self):
        assert _extract_nickname("You can call me Alex") == "Alex"

    def test_my_name_is_prefix(self):
        assert _extract_nickname("My name is Alibek Sattarov") == "Alibek"

    def test_im_prefix(self):
        assert _extract_nickname("I'm Bek") == "Bek"

    def test_empty(self):
        assert _extract_nickname("") == ""
        assert _extract_nickname("   ") == ""

    def test_truncates_to_30(self):
        long = "abcdefghijabcdefghijabcdefghijXXXX"
        assert len(_extract_nickname(long)) == 30
        assert _extract_nickname(long) == "Abcdefghijabcdefghijabcdefghij"


class TestFormatIntroToPart1:
    """Legacy helper — kept for backward compatibility."""

    def test_with_nickname_and_question(self):
        text = _format_intro_to_part1("Alibek", FIRST_Q)
        assert text.startswith("Alright, Alibek.")
        assert FIRST_Q in text

    def test_without_nickname(self):
        text = _format_intro_to_part1("", FIRST_Q)
        assert text.startswith("Alright.")
        assert "Alright, ." not in text
        assert FIRST_Q in text


class TestCountQuestionsSkipsIntro:
    def test_intro_turns_excluded(self):
        history = [
            {"role": "examiner", "text": "Good morning.", "phase": "intro"},
            {
                "role": "examiner",
                "text": f"Some frame. {FIRST_Q}",
                "phase": "part1",
            },
        ]
        counts = count_questions_by_part(history)
        assert counts["part1"] == 1
        assert counts["current_part"] == 1


class TestStripIntro:
    def test_strips_phase_markers(self):
        history = [
            {"role": "examiner", "text": "Good morning. ...", "phase": "intro"},
            {"role": "candidate", "text": "I am a student", "phase": "part1"},
        ]
        stripped = strip_intro(history)
        assert len(stripped) == 1
        assert stripped[0]["text"] == "I am a student"

    def test_no_intro_unchanged(self):
        history = [
            {"role": "examiner", "text": "Where are you from?"},
            {"role": "candidate", "text": "Almaty"},
        ]
        assert strip_intro(history) == history


class TestStartEndpointIntro:
    def test_start_returns_greeting_with_first_question(self, auth_client):
        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.current_state = SpeakingState.PART_1_ACTIVE.value

        with (
            patch(
                "app.api.speaking_examiner._tts_base64",
                new=AsyncMock(return_value=("YmFzZTY0", None, True)),
            ),
            patch(
                "app.api.speaking_examiner._create_start_session",
                new=AsyncMock(return_value=mock_session),
            ) as mock_create,
            patch(
                "app.api.speaking_examiner.load_speaking_plan",
                new=AsyncMock(
                    return_value=SpeakingPlan(
                        part1=list(DEFAULT_PART1),
                        cue_card=None,
                        part3=[],
                        part1_authored=False,
                        part3_authored=False,
                        cue_card_authored=False,
                    )
                ),
            ),
            patch(
                "app.api.speaking_examiner.generate_examiner_turn",
                new=AsyncMock(),
            ) as mock_gemini,
        ):
            resp = auth_client.post("/admin/speaking-examiner/start", json={})

        assert resp.status_code == 200
        data = resp.json()
        assert data["part"] == 1
        assert data["question_number"] == 1
        assert data["is_end"] is False
        assert data["session_id"] == str(mock_session.id)
        assert data["audio_base64"] == "YmFzZTY0"
        assert DEFAULT_PART1[0] in data["text"]
        mock_create.assert_awaited_once()
        mock_gemini.assert_not_called()
