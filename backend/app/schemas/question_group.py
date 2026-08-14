import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.question import QuestionRead


def _normalize_subtitle(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


class QuestionGroupCreate(BaseModel):
    order: int | None = None  # auto-computed as max+1 when omitted
    question_type: str
    instruction: str = ""
    subtitle: str | None = Field(default=None, max_length=500)
    options_shared: dict[str, Any] | None = None

    @field_validator("subtitle", mode="before")
    @classmethod
    def empty_subtitle_to_none(cls, v: object) -> object:
        if isinstance(v, str):
            return _normalize_subtitle(v)
        return v


class QuestionGroupUpdate(BaseModel):
    order: int | None = None
    question_type: str | None = None
    instruction: str | None = None
    subtitle: str | None = Field(default=None, max_length=500)
    options_shared: dict[str, Any] | None = None

    @field_validator("subtitle", mode="before")
    @classmethod
    def empty_subtitle_to_none(cls, v: object) -> object:
        if isinstance(v, str):
            return _normalize_subtitle(v)
        return v


class QuestionGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_id: uuid.UUID
    order: int
    question_type: str
    instruction: str
    subtitle: str | None = None
    options_shared: dict[str, Any] | None
    questions: list[QuestionRead] = []
    created_at: datetime
    updated_at: datetime
