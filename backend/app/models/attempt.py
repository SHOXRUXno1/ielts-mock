import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SCORED = "scored"
    ABANDONED = "abandoned"


class Attempt(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "attempts"

    user_id: Mapped["uuid.UUID | None"] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    test_id: Mapped["uuid.UUID"] = mapped_column(UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"))
    status: Mapped[AttemptStatus] = mapped_column(String(20), default=AttemptStatus.IN_PROGRESS)
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
    # Flagged if the attempt took significantly longer than the allowed duration
    flagged_overtime: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User | None"] = relationship(back_populates="attempts")
    test: Mapped["Test"] = relationship(back_populates="attempts")
    answers: Mapped[list["Answer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")
    evaluation_jobs: Mapped[list["EvaluationJob"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")
