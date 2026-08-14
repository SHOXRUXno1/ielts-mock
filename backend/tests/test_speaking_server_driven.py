"""Server-driven speaking examiner: authored questions drive the flow."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.speaking_examiner import (
    FORCED_END_TEXT,
    INTRO_GREETING,
    INTRO_NICKNAME_Q,
    MAX_EXAMINER_TURNS,
    PART3_TRANSITION,
    REACTIONS,
    _advance_turn,
    _format_intro_to_part1,
    _reaction,
)
from app.models.speaking_session import SpeakingState
from app.services.speaking_plan import (
    DEFAULT_PART1,
    SpeakingCueCard,
    SpeakingPlan,
    format_cue_card,
    parse_part1_or_3,
    parse_part2_cue,
    plan_from_sections,
    sanitize_question,
)
from app.services.speaking_state import ROUNDING_QUESTIONS


class TestSanitizeQuestion:
    def test_strips_why_hint(self):
        assert (
            sanitize_question("Do you watch cookery programmes on TV? [Why/Why not?]")
            == "Do you watch cookery programmes on TV?"
        )

    def test_strips_mid_sentence_hint(self):
        assert (
            sanitize_question("Who does the cooking [Why?] at home?")
            == "Who does the cooking at home?"
        )

    def test_collapses_whitespace(self):
        assert sanitize_question("What  sorts   of food?") == "What sorts of food?"

    def test_text_without_hints_unchanged(self):
        text = "Do you work or are you a student?"
        assert sanitize_question(text) == text

    def test_empty_after_strip(self):
        assert sanitize_question("[Why?]") == ""


class TestPlanDropsAdminHints:
    def test_part1_questions_sanitized(self):
        assert parse_part1_or_3(
            {"questions": ["A? [Why?]", "[Why/Why not?]", "B?"]}
        ) == ["A?", "B?"]

    def test_cue_card_sanitized(self):
        cue = parse_part2_cue(
            {
                "cue_card": {
                    "topic": "a trip [tell candidate to elaborate]",
                    "bullets": ["where you went [Why?]"],
                    "follow_up": "why it mattered [probe]",
                }
            }
        )
        assert cue is not None
        assert cue.topic == "a trip"
        assert cue.bullets == ["where you went"]
        assert cue.follow_up == "why it mattered"


def _plan_authored() -> SpeakingPlan:
    return SpeakingPlan(
        part1=[
            "What sorts of food do you like eating most?",
            "Who normally does the cooking in your home?",
            "Do you watch cookery programmes on TV?",
            "In general, do you prefer eating out or eating at home?",
        ],
        cue_card=SpeakingCueCard(
            topic="a house/apartment that someone you know lives in",
            bullets=[
                "whose house/apartment this is",
                "where the house/apartment is",
                "what it looks like inside",
            ],
            follow_up="what you like or dislike about this person's house/apartment",
        ),
        part3=[
            "What kinds of home are most popular in your country?",
            "Do you think it is better to rent or to buy?",
            "Is there a right age to leave home?",
        ],
        part1_authored=True,
        part3_authored=True,
        cue_card_authored=True,
    )


def _session(state: str = SpeakingState.INTRO_GREETING.value) -> MagicMock:
    session = MagicMock()
    session.id = uuid4()
    session.current_state = state
    session.candidate_nickname = None
    session.current_question_index = 0
    session.state_entered_at = datetime.now(timezone.utc)
    session.started_at = session.state_entered_at
    session.created_at = session.state_entered_at
    session.history_json = [
        {"role": "examiner", "text": INTRO_GREETING, "phase": "intro"},
    ]
    session.status = "in_progress"
    session.finished_at = None
    session.test_id = None
    return session


def _db() -> MagicMock:
    db = MagicMock()
    db.commit = AsyncMock()
    empty = MagicMock()
    empty.scalars.return_value.all.return_value = []
    empty.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=empty)
    return db


class TestSpeakingPlanParsers:
    def test_legacy_prompt_shape(self):
        assert parse_part1_or_3({"prompt": "Where are you from?"}) == [
            "Where are you from?"
        ]

    def test_legacy_cue_string(self):
        cue = parse_part2_cue({"cue_card": "a memorable journey"})
        assert cue is not None
        assert cue.topic == "a memorable journey"

    def test_plan_from_sections_authored(self):
        def _sec(order: int, content: dict) -> SimpleNamespace:
            q = SimpleNamespace(
                order=1, question_type="speaking_part", content=content
            )
            return SimpleNamespace(order=order, type="speaking", questions=[q])

        plan = plan_from_sections(
            [
                _sec(30, {"part": 1, "questions": ["Q1", "Q2"]}),
                _sec(
                    31,
                    {
                        "part": 2,
                        "cue_card": {
                            "topic": "a trip",
                            "bullets": ["where"],
                            "follow_up": "why",
                        },
                    },
                ),
                _sec(32, {"part": 3, "questions": ["P3Q1"]}),
            ]
        )
        assert plan.part1_authored is True
        assert plan.part1 == ["Q1", "Q2"]
        assert plan.cue_card is not None
        assert plan.cue_card.topic == "a trip"
        assert plan.part3 == ["P3Q1"]
        assert plan.part3_target == 1

    def test_empty_sections_use_defaults(self):
        plan = plan_from_sections([])
        assert plan.part1 == DEFAULT_PART1
        assert plan.part1_authored is False
        assert plan.cue_card is None
        assert plan.part3_target == 4


class TestReactions:
    def test_rotates_without_adjacent_repeat_in_sequence(self):
        # Deterministic rotation — consecutive indices map to different strings
        # except when list length is 1. With 5 reactions, idx and idx+1 differ.
        for i in range(20):
            assert _reaction(i) != _reaction(i + 1) or len(REACTIONS) == 1
            assert _reaction(i) in REACTIONS


class TestAuthoredFullFlow:
    @pytest.mark.asyncio
    async def test_authored_4_cue_3_no_gemini(self):
        plan = _plan_authored()
        session = _session()
        db = _db()
        cue_text = format_cue_card(plan.cue_card)

        with (
            patch(
                "app.api.speaking_examiner.generate_cue_card",
                new=AsyncMock(),
            ) as mock_cue,
            patch(
                "app.api.speaking_examiner.generate_part3_question",
                new=AsyncMock(),
            ) as mock_p3,
            patch(
                "app.api.speaking_examiner.generate_examiner_turn",
                new=AsyncMock(),
            ) as mock_turn,
        ):
            # INTRO greeting → nickname question
            r = await _advance_turn(
                session, "My name is Alibek Sattarov", plan, db, include_tts=False
            )
            assert r["text"] == INTRO_NICKNAME_Q
            assert session.current_state == SpeakingState.INTRO_NICKNAME.value

            # Nickname → frame + Part 1 Q1
            r = await _advance_turn(session, "Alibek", plan, db, include_tts=False)
            expected_q1 = _format_intro_to_part1("Alibek", plan.part1[0])
            assert r["text"] == expected_q1
            assert plan.part1[0] in r["text"]
            assert "Do you work or are you a student?" not in r["text"]
            assert r["part"] == 1
            assert r["question_number"] == 1
            assert r["questions_total"] == 4
            assert session.current_state == SpeakingState.PART_1_ACTIVE.value
            assert session.current_question_index == 1

            # Part 1 Q2–Q4
            for i, question in enumerate(plan.part1[1:], start=2):
                r = await _advance_turn(
                    session, f"Answer {i}", plan, db, include_tts=False
                )
                assert question in r["text"]
                assert r["part"] == 1
                assert r["question_number"] == i
                assert r["questions_total"] == 4

            # After last Part 1 answer → cue card from DB (prep state)
            r = await _advance_turn(
                session, "Answer last p1", plan, db, include_tts=False
            )
            assert r["part"] == 2
            assert r["cue_card"] == cue_text
            assert r["text"] == cue_text
            assert session.current_state == SpeakingState.PART_2_PREP.value

            # Monologue → rounding-off question (still part 2, no cue_card)
            r = await _advance_turn(
                session, "Long monologue about a house", plan, db, include_tts=False
            )
            assert r["part"] == 2
            assert r.get("cue_card") in (None, "")
            assert r["text"].startswith("Thank you.")
            assert any(q in r["text"] for q in ROUNDING_QUESTIONS)
            assert session.current_state == SpeakingState.PART_2_ROUNDING.value

            # Rounding answer → Part 3 Q1
            r = await _advance_turn(
                session, "Yes I enjoyed it", plan, db, include_tts=False
            )
            assert r["part"] == 3
            assert PART3_TRANSITION in r["text"]
            assert plan.part3[0] in r["text"]
            assert r["question_number"] == 1
            assert r["questions_total"] == 3
            assert session.current_state == SpeakingState.PART_3_ACTIVE.value

            # Part 3 Q2–Q3
            for i, question in enumerate(plan.part3[1:], start=2):
                r = await _advance_turn(
                    session, f"P3 answer {i}", plan, db, include_tts=False
                )
                assert question in r["text"]
                assert r["part"] == 3
                assert r["question_number"] == i

            # After last Part 3 answer → end
            r = await _advance_turn(
                session, "Final answer", plan, db, include_tts=False
            )
            assert r["is_end"] is True
            assert r["text"] == FORCED_END_TEXT
            assert session.current_state == SpeakingState.ENDED.value

            mock_cue.assert_not_called()
            mock_p3.assert_not_called()
            mock_turn.assert_not_called()


class TestFallbackPool:
    @pytest.mark.asyncio
    async def test_default_part1_and_gemini_cue_part3(self):
        plan = SpeakingPlan(
            part1=list(DEFAULT_PART1),
            cue_card=None,
            part3=[],
            part1_authored=False,
            part3_authored=False,
            cue_card_authored=False,
        )
        session = _session()
        db = _db()

        with (
            patch(
                "app.api.speaking_examiner.generate_cue_card",
                new=AsyncMock(
                    return_value=(
                        "Describe a memorable journey. You should say:\n"
                        "- where you went\n"
                        "- who you went with\n"
                        "- what you did\n"
                        "and explain why it was memorable. [PART:2]"
                    )
                ),
            ) as mock_cue,
            patch(
                "app.api.speaking_examiner.generate_part3_question",
                new=AsyncMock(return_value="Why do people travel? [PART:3]"),
            ) as mock_p3,
        ):
            await _advance_turn(session, "Full name", plan, db, include_tts=False)
            r = await _advance_turn(session, "Alex", plan, db, include_tts=False)
            assert DEFAULT_PART1[0] in r["text"]
            assert r["questions_total"] == 5

            # Ask remaining 4 Part 1 questions
            for i in range(1, 5):
                r = await _advance_turn(
                    session, f"A{i}", plan, db, include_tts=False
                )
                assert DEFAULT_PART1[i] in r["text"]

            # Cue via Gemini
            r = await _advance_turn(session, "last p1", plan, db, include_tts=False)
            assert r["part"] == 2
            assert r["cue_card"]
            assert session.current_state == SpeakingState.PART_2_PREP.value
            mock_cue.assert_awaited_once()

            # Monologue → rounding (no Gemini yet)
            r = await _advance_turn(session, "monologue", plan, db, include_tts=False)
            assert r["part"] == 2
            assert any(q in r["text"] for q in ROUNDING_QUESTIONS)
            assert session.current_state == SpeakingState.PART_2_ROUNDING.value
            mock_p3.assert_not_called()

            # Rounding answer → Part 3 Q1 via Gemini
            r = await _advance_turn(session, "yes", plan, db, include_tts=False)
            assert r["part"] == 3
            assert "Why do people travel?" in r["text"]
            assert r["questions_total"] == 4
            assert session.current_state == SpeakingState.PART_3_ACTIVE.value

            for i in range(3):
                r = await _advance_turn(
                    session, f"p3-{i}", plan, db, include_tts=False
                )
                assert r["part"] == 3
                assert r["is_end"] is False

            r = await _advance_turn(session, "done", plan, db, include_tts=False)
            assert r["is_end"] is True
            assert mock_p3.await_count == 4


class TestMaxTurns:
    @pytest.mark.asyncio
    async def test_forced_end_at_max_turns(self):
        plan = _plan_authored()
        session = _session(SpeakingState.PART_1_ACTIVE.value)
        # Fill history with enough non-intro examiner turns
        history = [{"role": "examiner", "text": INTRO_GREETING, "phase": "intro"}]
        for i in range(MAX_EXAMINER_TURNS):
            history.append({"role": "examiner", "text": f"Q{i}", "phase": "part1"})
            history.append({"role": "candidate", "text": f"A{i}", "phase": "part1"})
        session.history_json = history
        db = _db()

        r = await _advance_turn(session, "more", plan, db, include_tts=False)
        assert r["is_end"] is True
        assert r["text"] == FORCED_END_TEXT
        assert session.current_state == SpeakingState.ENDED.value


class TestInvalidStateApi:
    def test_respond_rejects_ended_session(self, auth_client):
        session = MagicMock()
        session.id = uuid4()
        session.current_state = SpeakingState.ENDED.value
        session.history_json = []
        session.admin_email = "test@example.com"
        session.test_id = None

        with patch(
            "app.api.speaking_examiner._get_live_session",
            new=AsyncMock(return_value=session),
        ):
            resp = auth_client.post(
                "/admin/speaking-examiner/respond",
                json={
                    "candidate_text": "hello",
                    "conversation_history": [],
                    "session_id": str(session.id),
                },
            )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Test already ended"

    def test_respond_rejects_scoring_session(self, auth_client):
        session = MagicMock()
        session.id = uuid4()
        session.current_state = SpeakingState.SCORING.value
        session.history_json = []
        session.admin_email = "test@example.com"
        session.test_id = None

        with patch(
            "app.api.speaking_examiner._get_live_session",
            new=AsyncMock(return_value=session),
        ):
            resp = auth_client.post(
                "/admin/speaking-examiner/respond",
                json={
                    "candidate_text": "hello",
                    "conversation_history": [],
                    "session_id": str(session.id),
                },
            )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Scoring in progress"

    @pytest.mark.asyncio
    async def test_advance_raises_from_ended(self):
        plan = _plan_authored()
        session = _session(SpeakingState.ENDED.value)
        db = _db()
        from app.services.speaking_state import InvalidStateTransition

        with pytest.raises(InvalidStateTransition):
            await _advance_turn(session, "x", plan, db, include_tts=False)
