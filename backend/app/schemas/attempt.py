import logging
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

logger = logging.getLogger(__name__)


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
    question_group_id: uuid.UUID | None = None
    order: int
    question_type: str
    content: dict[str, Any]
    answer_key: dict[str, Any] | None
    task_number: int | None = None
    computed_number: int | None = None
    computed_number_end: int | None = None


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
    created_at: datetime | None = None
    retry_count: int = 0


class AttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_id: uuid.UUID
    status: str
    mode: str = "full_mock"
    practice_section_id: uuid.UUID | None = None
    practice_part_number: int | None = None
    practice_section_type: str | None = None
    practice_correct: int | None = None
    practice_total: int | None = None
    started_at: datetime | None
    finished_at: datetime | None
    overall_band: float | None
    listening_band: float | None
    reading_band: float | None
    writing_band: float | None
    speaking_band: float | None
    listening_raw: int | None
    reading_raw: int | None
    # TODO: remove after all clients updated — legacy cumulative-deadline flag.
    flagged_overtime: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("flagged_overtime")
    @classmethod
    def _warn_legacy_overtime(cls, v: bool) -> bool:
        if v:
            logger.warning(
                "Legacy flagged_overtime=True accessed; cumulative deadline "
                "is deprecated — timing is enforced via SectionProgress"
            )
        return v


class SpeakingSessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    overall_band: float | None = None
    score_json: dict[str, Any] | None = None
    history_json: list[Any] | None = None


class AttemptDetailRead(AttemptRead):
    answers: list[AnswerRead]
    evaluation_jobs: list[EvaluationJobRead]
    speaking_session: SpeakingSessionSummary | None = None
    test_title: str | None = None


class SectionProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_type: str
    state: str
    started_at: datetime | None = None
    ends_at: datetime | None = None
    sealed_at: datetime | None = None
    sealed_reason: str | None = None


class EnterSectionResponse(BaseModel):
    state: str
    started_at: datetime | None = None
    ends_at: datetime | None = None
    sealed_at: datetime | None = None
    sealed_reason: str | None = None
    section_type: str
    server_now: datetime
    grace_seconds: int = 30


class AttemptProgressRead(BaseModel):
    server_now: datetime
    grace_seconds: int = 30
    sections: list[SectionProgressRead]


class SealSectionRequest(BaseModel):
    answers: list[AnswerSubmit] = []
    reason: str = "manual"


class SealSectionResponse(BaseModel):
    sealed: SectionProgressRead
    next_section: str | None = None
    all_sealed: bool = False
    server_now: datetime
