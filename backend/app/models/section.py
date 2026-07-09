import enum
import uuid

from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class SectionType(str, enum.Enum):
    LISTENING = "listening"
    READING = "reading"
    WRITING = "writing"
    SPEAKING = "speaking"


class Section(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "sections"

    test_id: Mapped["uuid.UUID"] = mapped_column(UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"))
    type: Mapped[SectionType] = mapped_column(String(20))
    order: Mapped[int] = mapped_column(SmallInteger)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    audio_url: Mapped[str | None] = mapped_column(String(500))
    passage: Mapped[str | None] = mapped_column(Text, nullable=True)
    audioscript: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    test: Mapped["Test"] = relationship(back_populates="sections")
    questions: Mapped[list["Question"]] = relationship(back_populates="section", order_by="Question.order", passive_deletes=True)
    question_groups: Mapped[list["QuestionGroup"]] = relationship(  # type: ignore[name-defined]
        back_populates="section",
        order_by="QuestionGroup.order",
        passive_deletes=True,
    )
