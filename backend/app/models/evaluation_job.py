import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class EvaluationJob(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "evaluation_jobs"

    attempt_id: Mapped["uuid.UUID"] = mapped_column(UUID(as_uuid=True), ForeignKey("attempts.id", ondelete="CASCADE"))
    section_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[JobStatus] = mapped_column(String(20), default=JobStatus.PENDING, index=True)
    input_data: Mapped[dict] = mapped_column(JSONB)
    result: Mapped[dict | None] = mapped_column(JSONB)
    band_score: Mapped[float | None] = mapped_column(Float)
    teacher_override_band: Mapped[float | None] = mapped_column(Float)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    attempt: Mapped["Attempt"] = relationship(back_populates="evaluation_jobs")
