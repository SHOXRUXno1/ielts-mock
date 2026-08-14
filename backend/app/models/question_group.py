import uuid

from sqlalchemy import ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class QuestionGroup(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "question_groups"

    section_id: Mapped["uuid.UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), index=True
    )
    order: Mapped[int] = mapped_column(SmallInteger)
    question_type: Mapped[str] = mapped_column(String(50))
    instruction: Mapped[str] = mapped_column(Text, default="", server_default="")
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    options_shared: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    section: Mapped["Section"] = relationship(back_populates="question_groups")  # type: ignore[name-defined]
    questions: Mapped[list["Question"]] = relationship(  # type: ignore[name-defined]
        back_populates="group",
        order_by="Question.order",
        passive_deletes=True,
    )
