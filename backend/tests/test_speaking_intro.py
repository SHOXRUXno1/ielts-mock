"""Unit + HTTP tests for hardcoded IELTS Speaking INTRO phase."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.speaking_examiner import (
    INTRO_FRAME,
    INTRO_GREETING,
    INTRO_NICKNAME_Q,
    _extract_nickname,
    _format_intro_to_part1,
    _handle_intro_turn,
    count_questions_by_part,
    strip_intro,
)
from app.models.speaking_session import SpeakingState
from app.services.speaking_plan import DEFAULT_PART1, SpeakingPlan


FIRST_Q = DEFAULT_PART1[0]


class TestExtractNickname:
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
    def test_with_nickname_and_question(self):
        text = _format_intro_to_part1("Alibek", FIRST_Q)
        assert text.startswith("Alright, Alibek.")
        assert FIRST_Q in text
        assert "Let's talk about what you do" not in text

    def test_without_nickname(self):
        text = _format_intro_to_part1("", FIRST_Q)
        assert text.startswith("Alright.")
        assert "Alright, ." not in text
        assert FIRST_Q in text

    def test_frame_only(self):
        text = _format_intro_to_part1("Alibek")
        assert text == INTRO_FRAME.format(nickname="Alibek")


class TestCountQuestionsSkipsIntro:
    def test_intro_turns_excluded(self):
        history = [
            {"role": "examiner", "text": INTRO_GREETING, "phase": "intro"},
            {"role": "candidate", "text": "My name is Alibek", "phase": "intro"},
            {"role": "examiner", "text": INTRO_NICKNAME_Q, "phase": "intro"},
            {"role": "candidate", "text": "Alibek", "phase": "intro"},
            {
                "role": "examiner",
                "text": _format_intro_to_part1("Alibek", FIRST_Q),
                "phase": "part1",
            },
        ]
        counts = count_questions_by_part(history)
        assert counts["part1"] == 1
        assert counts["current_part"] == 1


class TestStripIntro:
    def test_strips_phase_markers(self):
        q1 = _format_intro_to_part1("Alibek", FIRST_Q)
        history = [
            {"role": "examiner", "text": INTRO_GREETING, "phase": "intro"},
            {"role": "candidate", "text": "Full name", "phase": "intro"},
            {"role": "examiner", "text": INTRO_NICKNAME_Q, "phase": "intro"},
            {"role": "candidate", "text": "Alibek", "phase": "intro"},
            {"role": "examiner", "text": q1, "phase": "part1"},
            {"role": "candidate", "text": "I am a student", "phase": "part1"},
        ]
        stripped = strip_intro(history)
        assert len(stripped) == 2
        assert stripped[0]["text"] == q1
        assert stripped[1]["text"] == "I am a student"

    def test_positional_fallback_without_phase(self):
        q1 = _format_intro_to_part1("Alibek", FIRST_Q)
        history = [
            {"role": "examiner", "text": INTRO_GREETING},
            {"role": "candidate", "text": "Full name"},
            {"role": "examiner", "text": INTRO_NICKNAME_Q},
            {"role": "candidate", "text": "Alibek"},
            {"role": "examiner", "text": q1},
            {"role": "candidate", "text": "I work"},
        ]
        stripped = strip_intro(history)
        assert len(stripped) == 2
        assert stripped[0]["text"] == q1

    def test_no_intro_unchanged(self):
        history = [
            {"role": "examiner", "text": "Where are you from?"},
            {"role": "candidate", "text": "Almaty"},
        ]
        assert strip_intro(history) == history


class TestStartEndpointIntro:
    def test_start_returns_hardcoded_greeting(self, auth_client):
        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.current_state = SpeakingState.INTRO_GREETING.value

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
                "app.api.speaking_examiner.generate_examiner_turn",
                new=AsyncMock(),
            ) as mock_gemini,
        ):
            resp = auth_client.post("/admin/speaking-examiner/start", json={})

        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == INTRO_GREETING
        assert data["part"] == 1
        assert data["question_number"] == 1
        assert data["is_end"] is False
        assert data["session_id"] == str(mock_session.id)
        assert data["audio_base64"] == "YmFzZTY0"
        mock_create.assert_awaited_once()
        mock_gemini.assert_not_called()


class TestIntroRespondFlow:
    @pytest.mark.asyncio
    async def test_nickname_then_transition_with_part1_q1(self):
        session = MagicMock()
        session.id = uuid4()
        session.current_state = SpeakingState.INTRO_GREETING.value
        session.candidate_nickname = None
        session.current_question_index = 0
        session.state_entered_at = None
        session.history_json = [
            {"role": "examiner", "text": INTRO_GREETING, "phase": "intro"},
        ]
        session.status = "in_progress"
        session.finished_at = None

        db = MagicMock()
        db.commit = AsyncMock()

        plan = SpeakingPlan(
            part1=[FIRST_Q, "Second question?"],
            cue_card=None,
            part3=[],
            part1_authored=True,
            part3_authored=False,
            cue_card_authored=False,
        )

        p1 = await _handle_intro_turn(
            session, "My name is Alibek Sattarov", db, include_tts=False, plan=plan
        )
        assert p1 is not None
        assert p1["text"] == INTRO_NICKNAME_Q
        assert session.current_state == SpeakingState.INTRO_NICKNAME.value

        p2 = await _handle_intro_turn(
            session, "Alibek", db, include_tts=False, plan=plan
        )
        assert p2 is not None
        assert p2["text"] == _format_intro_to_part1("Alibek", FIRST_Q)
        assert FIRST_Q in p2["text"]
        assert session.current_state == SpeakingState.PART_1_ACTIVE.value
        assert session.candidate_nickname == "Alibek"
        assert session.current_question_index == 1

        # After INTRO, helper returns None (state is PART_1_ACTIVE)
        p3 = await _handle_intro_turn(
            session, "I am a student", db, include_tts=False, plan=plan
        )
        assert p3 is None
        assert db.commit.await_count == 2
