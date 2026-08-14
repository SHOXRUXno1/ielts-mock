import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class WritingFeedback(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "writing_feedback"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    task_number: Mapped[int] = mapped_column(Integer)
    prompt_hash: Mapped[str] = mapped_column(String(64))
    text_hash: Mapped[str] = mapped_column(String(64))
    essay_text: Mapped[str] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSONB)
    overall_band: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        Index("ix_writing_feedback_cache", "prompt_hash", "text_hash"),
    )
