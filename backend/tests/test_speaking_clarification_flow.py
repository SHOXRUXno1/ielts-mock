"""Integration tests: clarification requests do NOT advance the state machine.

Covers _advance_turn's clarification branch. The core safety property
being tested is: a "Pardon?" (or empty transcript) must repeat the
current question verbatim-ish, not consume the student's question quota,
not change state, and not land in the scored transcript.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.speaking_examiner import (
    INTRO_GREETING,
    _advance_turn,
    strip_for_scoring,
)
from app.models.speaking_session import SpeakingState
from app.services.speaking_clarification import MAX_CLARIFICATION_REPEATS
from app.services.speaking_plan import SpeakingCueCard, SpeakingPlan


def _plan() -> SpeakingPlan:
    return SpeakingPlan(
        part1=[
            "What kinds of fast food have you tried?",
            "Do you ever use a microwave to cook quickly?",
            "How popular are fast food restaurants where you live?",
        ],
        cue_card=SpeakingCueCard(
            topic="a town you enjoyed visiting",
            bullets=["why you went", "who you saw", "what you did"],
            follow_up="and explain why you enjoyed it",
        ),
        part3=[
            "What kinds of computer games do people play in your country?",
            "Why do people enjoy playing computer games?",
            "In what ways can technology in the classroom be helpful?",
        ],
        part1_authored=True,
        part3_authored=True,
        cue_card_authored=True,
    )


def _session(
    state: str = SpeakingState.PART_1_ACTIVE.value,
    idx: int = 2,
    clarif: int = 0,
) -> MagicMock:
    s = MagicMock()
    s.id = uuid4()
    s.current_state = state
    s.candidate_nickname = None
    s.current_question_index = idx
    s.clarification_count = clarif
    s.state_entered_at = datetime.now(timezone.utc)
    s.started_at = s.state_entered_at
    s.created_at = s.state_entered_at
    s.history_json = [
        {"role": "examiner", "text": INTRO_GREETING, "phase": "intro"},
        {
            "role": "examiner",
            "text": "What kinds of fast food have you tried?",
            "phase": "part1",
        },
        {"role": "candidate", "text": "I like pizza.", "phase": "part1"},
        {
            "role": "examiner",
            "text": "I see. Do you ever use a microwave to cook quickly?",
            "phase": "part1",
        },
    ]
    s.status = "in_progress"
    s.finished_at = None
    s.test_id = None
    s.attempt_id = None
    return s


def _db() -> MagicMock:
    db = MagicMock()
    db.commit = AsyncMock()
    return db


class TestClarificationDoesNotAdvance:
    @pytest.mark.asyncio
    async def test_pardon_repeats_current_question(self) -> None:
        plan = _plan()
        session = _session(idx=2)  # Q2 just asked ("Do you ever use a microwave...")
        db = _db()

        r = await _advance_turn(session, "Pardon?", plan, db, include_tts=False)

        # Question is repeated verbatim, no "I see." prefix on first repeat.
        assert r["text"] == "Do you ever use a microwave to cook quickly?"
        assert r["part"] == 1
        # Index did NOT advance.
        assert session.current_question_index == 2
        # State unchanged.
        assert session.current_state == SpeakingState.PART_1_ACTIVE.value
        # Streak incremented.
        assert session.clarification_count == 1

    @pytest.mark.asyncio
    async def test_empty_transcript_also_treated_as_clarification(self) -> None:
        """Whisper hallucination filter returns ''. Treat as 'please repeat'."""
        plan = _plan()
        session = _session(idx=2)
        db = _db()

        r = await _advance_turn(session, "", plan, db, include_tts=False)

        assert r["text"] == "Do you ever use a microwave to cook quickly?"
        assert session.current_question_index == 2
        assert session.clarification_count == 1

    @pytest.mark.asyncio
    async def test_second_repeat_has_sure_filler(self) -> None:
        plan = _plan()
        session = _session(idx=2, clarif=1)
        db = _db()

        r = await _advance_turn(session, "Could you repeat that?", plan, db, include_tts=False)

        assert r["text"].startswith("Sure. ")
        assert "Do you ever use a microwave" in r["text"]
        assert session.clarification_count == 2
        assert session.current_question_index == 2

    @pytest.mark.asyncio
    async def test_third_repeat_rephrases(self) -> None:
        plan = _plan()
        session = _session(idx=2, clarif=2)
        db = _db()

        r = await _advance_turn(session, "Say that again", plan, db, include_tts=False)

        assert r["text"].startswith("Let me rephrase. ")
        assert session.clarification_count == 3
        assert session.current_question_index == 2


class TestClarificationDoesNotPollueteScoring:
    def test_strip_for_scoring_drops_clarification_turns(self) -> None:
        history = [
            {"role": "examiner", "text": "Q1", "phase": "part1"},
            {"role": "candidate", "text": "Answer 1", "phase": "part1"},
            {"role": "examiner", "text": "Q2", "phase": "part1"},
            {
                "role": "candidate",
                "text": "Pardon?",
                "phase": "part1",
                "kind": "clarification_request",
            },
            {
                "role": "examiner",
                "text": "Q2 (repeat)",
                "phase": "part1",
                "kind": "clarification_repeat",
            },
            {"role": "candidate", "text": "Answer 2", "phase": "part1"},
        ]
        scored = strip_for_scoring(history)
        texts = [t["text"] for t in scored]
        assert "Pardon?" not in texts
        assert "Q2 (repeat)" not in texts
        assert texts == ["Q1", "Answer 1", "Q2", "Answer 2"]

    def test_strip_for_scoring_still_removes_intro(self) -> None:
        """Backward compat: intro turns still filtered."""
        history = [
            {"role": "examiner", "text": "Good morning.", "phase": "intro"},
            {"role": "candidate", "text": "Hi.", "phase": "intro"},
            {"role": "examiner", "text": "Q1", "phase": "part1"},
            {"role": "candidate", "text": "A1", "phase": "part1"},
        ]
        scored = strip_for_scoring(history)
        assert len(scored) == 2
        assert all(t.get("phase") != "intro" for t in scored)


class TestClarificationCapBreaksLoop:
    @pytest.mark.asyncio
    async def test_cap_force_advances(self) -> None:
        """After MAX_CLARIFICATION_REPEATS the examiner moves on."""
        plan = _plan()
        session = _session(idx=2, clarif=MAX_CLARIFICATION_REPEATS)
        db = _db()

        # Streak already at the cap — one more clarification triggers
        # the force-advance path.
        r = await _advance_turn(session, "Pardon?", plan, db, include_tts=False)

        # Advanced: idx moved to 3 (next Part 1 question emitted).
        assert session.current_question_index == 3
        assert session.clarification_count == 0
        # The emitted text contains the next question.
        assert "How popular are fast food restaurants" in r["text"]


class TestRealAnswerResetsStreak:
    @pytest.mark.asyncio
    async def test_normal_answer_zeroes_streak(self) -> None:
        plan = _plan()
        session = _session(idx=2, clarif=2)  # mid-streak
        db = _db()

        r = await _advance_turn(
            session,
            "Yes, I use a microwave almost every morning.",
            plan,
            db,
            include_tts=False,
        )

        # Advanced to Q3.
        assert session.current_question_index == 3
        # Streak reset.
        assert session.clarification_count == 0
        # Next question emitted (not a repeat).
        assert "How popular are fast food restaurants" in r["text"]
