import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_QUESTION_TYPE_RE = r"^(mcq|gap_fill|matching|map_labeling|true_false_ng|multi_select|essay|speaking_part|matching_headings|matching_information|matching_features|yes_no_ng|sentence_completion|short_answer)$"


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


class QuestionCreateInGroup(BaseModel):
    """Used by POST /admin/question-groups/{id}/questions.

    question_type is optional — when omitted the endpoint inherits it from the group.
    If provided it must match the group's question_type.
    """
    order: int = Field(default=1, ge=1)
    question_type: str | None = Field(default=None, pattern=_QUESTION_TYPE_RE)
    content: dict[str, Any] = Field(default_factory=dict)
    answer_key: dict[str, Any] | None = None


class QuestionUpdate(BaseModel):
    order: int | None = Field(default=None, ge=1)
    question_type: str | None = Field(default=None, pattern=_QUESTION_TYPE_RE)
    content: dict[str, Any] | None = None
    answer_key: dict[str, Any] | None = None
    task_number: int | None = Field(default=None, ge=1, le=2)
    min_words: int | None = Field(default=None, ge=50)
    image_url: str | None = None


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
    created_at: datetime
    updated_at: datetime
