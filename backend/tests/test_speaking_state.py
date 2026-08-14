"""Unit tests for speaking state machine helpers."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.api.speaking_examiner import _get_live_session
from app.models.speaking_session import SpeakingState
from app.services.speaking_state import (
    InvalidStateTransition,
    assert_can_advance,
    http_detail_for_blocked_state,
    rounding_question,
    seconds_in_state,
    transition_state,
)


def _session(
    state: str = SpeakingState.INTRO_GREETING.value,
    *,
    index: int = 0,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        current_state=state,
        current_question_index=index,
        state_entered_at=now,
        started_at=now,
        created_at=now,
        candidate_nickname=None,
    )


class TestTransitionState:
    def test_updates_state_and_timestamp(self):
        session = _session()
        before = session.state_entered_at
        transition_state(session, SpeakingState.INTRO_NICKNAME)
        assert session.current_state == SpeakingState.INTRO_NICKNAME.value
        assert session.state_entered_at >= before

    def test_resets_index_on_part_entry(self):
        session = _session(SpeakingState.INTRO_NICKNAME.value, index=3)
        transition_state(session, SpeakingState.PART_1_ACTIVE)
        assert session.current_question_index == 0

        session.current_question_index = 2
        transition_state(session, SpeakingState.PART_2_PREP)
        assert session.current_question_index == 0

        session.current_question_index = 4
        transition_state(session, SpeakingState.PART_3_ACTIVE)
        assert session.current_question_index == 0

    def test_no_reset_on_intra_part_transition(self):
        session = _session(SpeakingState.PART_2_PREP.value, index=0)
        transition_state(session, SpeakingState.PART_2_ROUNDING)
        assert session.current_question_index == 0

        session.current_question_index = 2
        transition_state(session, SpeakingState.ENDED)
        assert session.current_question_index == 2

    def test_reset_index_override(self):
        session = _session(SpeakingState.PART_1_ACTIVE.value, index=3)
        transition_state(
            session, SpeakingState.PART_1_ACTIVE, reset_index=False
        )
        assert session.current_question_index == 3


class TestAssertCanAdvance:
    def test_raises_for_terminal_states(self):
        for state in (
            SpeakingState.ENDED.value,
            SpeakingState.SCORING.value,
            SpeakingState.ABANDONED.value,
        ):
            session = _session(state)
            with pytest.raises(InvalidStateTransition):
                assert_can_advance(session)

    def test_allows_active_states(self):
        assert_can_advance(_session(SpeakingState.PART_1_ACTIVE.value))


class TestHttpDetail:
    def test_scoring_is_409(self):
        assert http_detail_for_blocked_state(SpeakingState.SCORING.value) == (
            409,
            "Scoring in progress",
        )

    def test_ended_is_400(self):
        assert http_detail_for_blocked_state(SpeakingState.ENDED.value) == (
            400,
            "Test already ended",
        )


class TestSecondsInState:
    def test_elapsed_from_state_entered_at(self):
        session = _session()
        session.state_entered_at = datetime.now(timezone.utc) - timedelta(seconds=90)
        assert 89 <= seconds_in_state(session) <= 95


class TestRoundingQuestion:
    def test_stable_for_session(self):
        session = _session()
        assert rounding_question(session) == rounding_question(session)
        assert rounding_question(session).endswith("?")


class TestForUpdateLock:
    @pytest.mark.asyncio
    async def test_get_live_session_compiles_for_update(self):
        captured: list = []

        class FakeResult:
            def scalar_one_or_none(self):
                return None

        class FakeDb:
            async def execute(self, stmt):
                captured.append(stmt)
                return FakeResult()

        await _get_live_session(
            uuid4(), "test@example.com", FakeDb(), for_update=True  # type: ignore[arg-type]
        )
        assert len(captured) == 1
        compiled = captured[0].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
        sql = str(compiled).upper()
        assert "FOR UPDATE" in sql
