import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    response: dict[str, Any]


class AnswersBulkSubmit(BaseModel):
    answers: list[AnswerSubmit]


class SectionSnapshot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    order: int


class QuestionSnapshot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_id: uuid.UUID
    order: int
    question_type: str
    content: dict[str, Any]
    answer_key: dict[str, Any] | None


class AnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    response: dict[str, Any]
    is_correct: bool | None
    score: float | None
    question: QuestionSnapshot | None = None
    section: SectionSnapshot | None = None


class EvaluationJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_type: str
    status: str
    band_score: float | None
    result: dict[str, Any] | None
    teacher_override_band: float | None
    processed_at: datetime | None
    error_message: str | None


class AttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_id: uuid.UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    overall_band: float | None
    listening_band: float | None
    reading_band: float | None
    writing_band: float | None
    speaking_band: float | None
    listening_raw: int | None
    reading_raw: int | None
    flagged_overtime: bool
    created_at: datetime
    updated_at: datetime


class AttemptDetailRead(AttemptRead):
    answers: list[AnswerRead]
    evaluation_jobs: list[EvaluationJobRead]
