import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_QUESTION_TYPE_RE = r"^(mcq|gap_fill|matching|map_labeling|true_false_ng|multi_select|essay|speaking_part|matching_headings|matching_information|matching_features|yes_no_ng|sentence_completion|short_answer|table_completion|note_completion|form_completion|summary_completion|flow_chart_completion|diagram_labeling)$"

EssayType = Literal[
    "opinion",
    "discussion",
    "problem_solution",
    "advantages_disadvantages",
    "double_question",
]

_ALLOWED_ESSAY_TYPES = {
    "opinion",
    "discussion",
    "problem_solution",
    "advantages_disadvantages",
    "double_question",
}

_LEGACY_CONTENT_KEYS = ("task_type", "min_words", "image_url")


def _strip_legacy_content(content: dict[str, Any] | None) -> dict[str, Any] | None:
    if content is None:
        return None
    cleaned = {k: v for k, v in content.items() if k not in _LEGACY_CONTENT_KEYS}
    return cleaned


def validate_multi_select_answers(
    question_type: str | None,
    content: dict[str, Any] | None,
    answer_key: dict[str, Any] | None,
) -> None:
    """Require exactly choose_n correct answers for multi_select."""
    if question_type != "multi_select":
        return
    content = content or {}
    choose_n = content.get("choose_n", 2)
    if not isinstance(choose_n, int) or choose_n < 1:
        choose_n = 2
    raw = (answer_key or {}).get("correct")
    if isinstance(raw, list):
        selected = [str(x).strip() for x in raw if str(x).strip()]
    elif raw is not None and str(raw).strip():
        selected = [str(raw).strip()]
    else:
        selected = []
    if len(selected) != choose_n:
        raise ValueError(f"Select exactly {choose_n} correct answers")


class QuestionCreate(BaseModel):
    order: int = Field(ge=1)
    question_type: str = Field(pattern=_QUESTION_TYPE_RE)
    content: dict[str, Any]
    answer_key: dict[str, Any] | None = None
    question_group_id: uuid.UUID | None = None
    # Writing-task metadata (populated by API from task_number, not sent raw by client)
    task_number: int | None = Field(default=None, ge=1, le=2)
    min_words: int | None = Field(default=None, ge=50)
    image_url: str | None = None
    essay_type: EssayType | None = None

    @field_validator("content", mode="before")
    @classmethod
    def _clean_content(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return _strip_legacy_content(v)
        return v

    @model_validator(mode="after")
    def _validate_writing_fields(self) -> "QuestionCreate":
        if self.essay_type is not None:
            if self.task_number == 1:
                raise ValueError("essay_type is only allowed for Task 2 (task_number=2)")
            if self.task_number is not None and self.task_number != 2:
                raise ValueError("essay_type requires task_number=2")
            if self.essay_type not in _ALLOWED_ESSAY_TYPES:
                raise ValueError(f"Invalid essay_type: {self.essay_type}")
        validate_multi_select_answers(self.question_type, self.content, self.answer_key)
        return self


class QuestionCreateInGroup(BaseModel):
    """Used by POST /admin/question-groups/{id}/questions.

    question_type is optional — when omitted the endpoint inherits it from the group.
    If provided it must match the group's question_type.
    """
    order: int | None = Field(default=None, ge=1)
    question_type: str | None = Field(default=None, pattern=_QUESTION_TYPE_RE)
    content: dict[str, Any] = Field(default_factory=dict)
    answer_key: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_multi_select(self) -> "QuestionCreateInGroup":
        # When type omitted, API validates after resolving group type.
        if self.question_type is not None:
            validate_multi_select_answers(
                self.question_type, self.content, self.answer_key
            )
        return self


class QuestionUpdate(BaseModel):
    order: int | None = Field(default=None, ge=1)
    question_type: str | None = Field(default=None, pattern=_QUESTION_TYPE_RE)
    content: dict[str, Any] | None = None
    answer_key: dict[str, Any] | None = None
    task_number: int | None = Field(default=None, ge=1, le=2)
    min_words: int | None = Field(default=None, ge=50)
    image_url: str | None = None
    essay_type: EssayType | None = None

    @field_validator("content", mode="before")
    @classmethod
    def _clean_content(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return _strip_legacy_content(v)
        return v

    @model_validator(mode="after")
    def _validate_writing_fields(self) -> "QuestionUpdate":
        if self.essay_type is not None:
            if self.task_number == 1:
                raise ValueError("essay_type is only allowed for Task 2 (task_number=2)")
            if self.essay_type not in _ALLOWED_ESSAY_TYPES:
                raise ValueError(f"Invalid essay_type: {self.essay_type}")
        # Full multi_select check needs merged type/content from DB — done in API.
        return self


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_id: uuid.UUID
    question_group_id: uuid.UUID | None = None
    order: int
    question_type: str
    content: dict[str, Any]
    answer_key: dict[str, Any] | None
    task_number: int | None = None
    min_words: int | None = None
    image_url: str | None = None
    essay_type: str | None = None
    # Transient IELTS display numbers (set by annotate_question_numbers; not DB columns)
    computed_number: int | None = None
    computed_number_end: int | None = None
    created_at: datetime
    updated_at: datetime
