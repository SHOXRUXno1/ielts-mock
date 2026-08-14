import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class SpeakingState(str, enum.Enum):
    INTRO_GREETING = "intro_greeting"
    INTRO_NICKNAME = "intro_nickname"

    # Part 1 — dynamic question count via current_question_index
    PART_1_ACTIVE = "part_1_active"

    # Part 2 — rigid sequence (prep/talk mostly client-driven)
    PART_2_CUE = "part_2_cue"
    PART_2_PREP = "part_2_prep"
    PART_2_TALK = "part_2_talk"
    PART_2_ROUNDING = "part_2_rounding"

    # Part 3 — dynamic question count
    PART_3_ACTIVE = "part_3_active"

    # Terminal
    ENDED = "ended"
    SCORING = "scoring"
    ABANDONED = "abandoned"


class SpeakingSession(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "speaking_sessions"

    admin_email: Mapped[str] = mapped_column(String(255), index=True)
    # Link to a student test attempt (nullable for legacy / standalone admin sessions)
    attempt_id: Mapped["uuid.UUID | None"] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Test whose speaking sections supply examiner question context
    test_id: Mapped["uuid.UUID | None"] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    overall_band: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    history_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    current_state: Mapped[str] = mapped_column(
        String(32), default=SpeakingState.ENDED.value, index=True
    )
    candidate_nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state_entered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_question_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
