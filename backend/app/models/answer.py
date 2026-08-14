import uuid

from sqlalchemy import Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Answer(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_answers_attempt_question"),
    )

    attempt_id: Mapped["uuid.UUID"] = mapped_column(UUID(as_uuid=True), ForeignKey("attempts.id", ondelete="CASCADE"))
    question_id: Mapped["uuid.UUID"] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"))
    response: Mapped[dict] = mapped_column(JSONB)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    score: Mapped[float | None] = mapped_column(Float)

    attempt: Mapped["Attempt"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="answers")
