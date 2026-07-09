import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.question import QuestionRead


class QuestionGroupCreate(BaseModel):
    order: int | None = None  # auto-computed as max+1 when omitted
    question_type: str
    instruction: str = ""
    options_shared: dict[str, Any] | None = None


class QuestionGroupUpdate(BaseModel):
    order: int | None = None
    question_type: str | None = None
    instruction: str | None = None
    options_shared: dict[str, Any] | None = None


class QuestionGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_id: uuid.UUID
    order: int
    question_type: str
    instruction: str
    options_shared: dict[str, Any] | None
    questions: list[QuestionRead] = []
    created_at: datetime
    updated_at: datetime
