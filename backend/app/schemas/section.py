import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.question_group import QuestionGroupRead
from app.services.scoring import scoring_slots_for_question


class SectionCreate(BaseModel):
    type: str = Field(pattern=r"^(listening|reading|writing|speaking)$")
    audio_url: str | None = None
    passage: str | None = None
    audioscript: str | None = None
    title: str | None = None
    passage_subtitle: str | None = None


class SectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_id: uuid.UUID
    type: str
    order: int
    audio_url: str | None
    passage: str | None = None
    audioscript: str | None = None
    title: str | None = None
    passage_subtitle: str | None = None
    question_count: int = 0
    question_groups: list[QuestionGroupRead] = []
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _compute_fields(cls, data: Any) -> Any:
        # When the input is a SQLAlchemy ORM instance, convert it to a plain
        # dict so Pydantic never calls getattr(section, 'question_count')
        # (which would trigger an async lazy-load and crash).
        if hasattr(data, "_sa_instance_state"):
            try:
                raw_qs = data.__dict__.get("questions")
                if isinstance(raw_qs, list):
                    qc = sum(scoring_slots_for_question(q) for q in raw_qs)
                else:
                    qc = 0
            except Exception:
                qc = 0
            try:
                raw_groups = data.__dict__.get("question_groups") or []
            except Exception:
                raw_groups = []
            return {
                "id": data.id,
                "test_id": data.test_id,
                "type": data.type,
                "order": data.order,
                "audio_url": data.audio_url,
                "passage": data.passage,
                "audioscript": data.audioscript,
                "title": data.title,
                "passage_subtitle": data.passage_subtitle,
                "question_count": qc,
                "question_groups": raw_groups,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class SectionUpdate(BaseModel):
    audio_url: str | None = None
    passage: str | None = None
    audioscript: str | None = None
    title: str | None = None
    passage_subtitle: str | None = None
