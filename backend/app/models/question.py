import enum
import uuid

from sqlalchemy import ForeignKey, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    GAP_FILL = "gap_fill"
    MATCHING = "matching"
    MAP_LABELING = "map_labeling"
    TRUE_FALSE_NG = "true_false_ng"
    MULTI_SELECT = "multi_select"
    ESSAY = "essay"
    SPEAKING_PART = "speaking_part"
    MATCHING_HEADINGS = "matching_headings"
    MATCHING_INFORMATION = "matching_information"
    MATCHING_FEATURES = "matching_features"
    YES_NO_NG = "yes_no_ng"
    SENTENCE_COMPLETION = "sentence_completion"
    SHORT_ANSWER = "short_answer"


class Question(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "questions"

    section_id: Mapped["uuid.UUID"] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"))
    question_group_id: Mapped["uuid.UUID | None"] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_groups.id", ondelete="CASCADE"),
        nullable=True,
    )
    order: Mapped[int] = mapped_column(SmallInteger)
    question_type: Mapped[QuestionType] = mapped_column(String(50))
    content: Mapped[dict] = mapped_column(JSONB)
    answer_key: Mapped[dict | None] = mapped_column(JSONB)

    # Writing-task specific columns (NULL for all other question types)
    task_number: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    min_words: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    section: Mapped["Section"] = relationship(back_populates="questions")
    group: Mapped["QuestionGroup | None"] = relationship(back_populates="questions")  # type: ignore[name-defined]
    answers: Mapped[list["Answer"]] = relationship(back_populates="question")
