"""Atomic state transitions for the AI Speaking Examiner."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.speaking_session import SpeakingSession, SpeakingState

logger = logging.getLogger(__name__)

PREP_MIN_SECONDS = 45.0

# Entering these states resets the in-part question index.
_PART_ENTRY_STATES = frozenset(
    {
        SpeakingState.PART_1_ACTIVE,
        SpeakingState.PART_2_CUE,
        SpeakingState.PART_2_PREP,
        SpeakingState.PART_3_ACTIVE,
    }
)

_TERMINAL_ADVANCE_BLOCKED = frozenset(
    {
        SpeakingState.ENDED.value,
        SpeakingState.SCORING.value,
        SpeakingState.ABANDONED.value,
    }
)

ROUNDING_QUESTIONS = (
    "Did you enjoy that experience?",
    "Would you like to do that again?",
    "Was that difficult to talk about?",
)


class InvalidStateTransition(Exception):
    """Raised when a turn is requested from a non-advanceable state."""


def transition_state(
    session: SpeakingSession,
    new_state: SpeakingState | str,
    *,
    reset_index: bool | None = None,
) -> None:
    """Atomically update current_state + state_entered_at.

    Commit is the caller's responsibility. When entering a part-entry state
    the question index is reset to 0 unless ``reset_index`` overrides.
    """
    if isinstance(new_state, str):
        new_state_enum = SpeakingState(new_state)
    else:
        new_state_enum = new_state

    old_state = session.current_state
    session.current_state = new_state_enum.value
    session.state_entered_at = datetime.now(timezone.utc)

    should_reset = (
        reset_index
        if reset_index is not None
        else new_state_enum in _PART_ENTRY_STATES
    )
    if should_reset:
        session.current_question_index = 0

    logger.info(
        "Session %s: %s → %s",
        getattr(session, "id", "?"),
        old_state,
        new_state_enum.value,
    )


def seconds_in_state(session: SpeakingSession) -> float:
    """Seconds since state_entered_at (falls back to started_at / created_at)."""
    entered = (
        getattr(session, "state_entered_at", None)
        or getattr(session, "started_at", None)
        or getattr(session, "created_at", None)
    )
    if entered is None:
        return 0.0
    if entered.tzinfo is None:
        entered = entered.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - entered).total_seconds()


def rounding_question(session: SpeakingSession) -> str:
    """Pick a short Part-2 rounding-off question (stable per session)."""
    sid = getattr(session, "id", None)
    if sid is None:
        return ROUNDING_QUESTIONS[0]
    try:
        idx = int(sid.int % len(ROUNDING_QUESTIONS))  # type: ignore[attr-defined]
    except (AttributeError, TypeError, ValueError):
        idx = hash(str(sid)) % len(ROUNDING_QUESTIONS)
    return ROUNDING_QUESTIONS[idx]


def assert_can_advance(session: SpeakingSession) -> None:
    """Raise InvalidStateTransition for terminal / scoring states."""
    state = session.current_state
    if state in _TERMINAL_ADVANCE_BLOCKED:
        raise InvalidStateTransition(f"Cannot advance from {state}")


def http_detail_for_blocked_state(state: str) -> tuple[int, str]:
    """Map a blocked state to (status_code, detail) for API responses."""
    if state == SpeakingState.SCORING.value:
        return 409, "Scoring in progress"
    if state in (
        SpeakingState.ENDED.value,
        SpeakingState.ABANDONED.value,
    ):
        return 400, "Test already ended"
    return 400, f"Invalid session state: {state}"
