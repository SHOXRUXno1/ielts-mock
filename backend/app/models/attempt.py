import enum
import uuid
from datetime import datetime

from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AUTO_SCORED = "auto_scored"
    SPEAKING_IN_PROGRESS = "speaking_in_progress"
    FULLY_SCORED = "fully_scored"
    COMPLETED_WITHOUT_SPEAKING = "completed_without_speaking"
    PARTIAL = "partial"
    ABANDONED = "abandoned"


class AttemptMode(str, enum.Enum):
    FULL_MOCK = "full_mock"
    SINGLE_PART = "single_part"
    SINGLE_SECTION = "single_section"


# Modes that isolate a skill (or part of a skill) from the full mock.
PRACTICE_MODES = frozenset({
    AttemptMode.SINGLE_PART.value,
    AttemptMode.SINGLE_SECTION.value,
})


class Attempt(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "attempts"

    user_id: Mapped["uuid.UUID | None"] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    test_id: Mapped["uuid.UUID"] = mapped_column(UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"))
    status: Mapped[AttemptStatus] = mapped_column(String(32), default=AttemptStatus.IN_PROGRESS)
    # full_mock | single_part | single_section
    mode: Mapped[str] = mapped_column(
        String(16),
        default=AttemptMode.FULL_MOCK.value,
        server_default=AttemptMode.FULL_MOCK.value,
    )
    # True when a full mock was started on a paper the student deliberately
    # chose (practice picker → "Start this paper"), so the exam screen names
    # the paper ("Practice set #N") instead of the anonymous "Mock #N".
    # False for random-rotation mocks and all practice attempts.
    picked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Practice-mode scope. NULL for full_mock attempts.
    practice_section_id: Mapped["uuid.UUID | None"] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    practice_part_number: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    # Target skill for practice (listening/reading/writing/speaking).
    # Required for single_section; backfilled for single_part.
    practice_section_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    # Raw correct / total for practice results.
    practice_correct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    practice_total: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    overall_band: Mapped[float | None] = mapped_column(Float)
    listening_band: Mapped[float | None] = mapped_column(Float)
    reading_band: Mapped[float | None] = mapped_column(Float)
    writing_band: Mapped[float | None] = mapped_column(Float)
    speaking_band: Mapped[float | None] = mapped_column(Float)
    # Raw correct-answer counts (e.g. 32 out of 40) for display in results
    listening_raw: Mapped[int | None] = mapped_column(nullable=True)
    reading_raw: Mapped[int | None] = mapped_column(nullable=True)
    # TODO: remove after all clients updated — legacy cumulative-deadline flag.
    # No longer written on finish; timing is enforced via SectionProgress.
    flagged_overtime: Mapped[bool] = mapped_column(default=False)

    # Append-only log of exam-integrity events (e.g. leaving fullscreen mid-exam).
    # JSONB, not a pair of counters, so future event kinds cost no migration.
    # Shape: [{"type": str, "at": ISO8601 str, ...}]
    integrity_events: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True
    )

    user: Mapped["User | None"] = relationship(back_populates="attempts")
    test: Mapped["Test"] = relationship(back_populates="attempts")
    answers: Mapped[list["Answer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")
    evaluation_jobs: Mapped[list["EvaluationJob"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")
    section_progress: Mapped[list["SectionProgress"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
