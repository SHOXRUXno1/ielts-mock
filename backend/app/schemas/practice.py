"""Schemas for single-part and whole-section practice endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PracticeUnitRead(BaseModel):
    section_type: str
    part_number: int
    section_id: uuid.UUID
    label: str
    question_count: int
    # Effective duration for a practice run (settings override or proportional
    # default). None means AI-paced (speaking).
    duration_minutes: int | None = None
    # True when duration_minutes is a proportional default (no admin override).
    duration_is_default: bool
    is_enabled: bool
    last_attempt: "PracticeUnitLastAttempt | None" = None


class PracticeSectionUnitRead(BaseModel):
    section_type: str
    label: str
    part_count: int
    question_count: int
    duration_minutes: int | None = None
    is_enabled: bool
    last_attempt: "PracticeUnitLastAttempt | None" = None


class PracticeUnitLastAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    status: str
    finished_at: datetime | None = None
    correct: int | None = None
    total: int | None = None
    band: float | None = None


class PracticeUnitsResponse(BaseModel):
    test_id: uuid.UUID
    units: list[PracticeUnitRead]
    sections: list[PracticeSectionUnitRead] = []


class StartPracticeAttemptRequest(BaseModel):
    section_type: str
    scope: Literal["part", "section"] = "part"
    part_number: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def _require_part_number_for_part_scope(self) -> "StartPracticeAttemptRequest":
        if self.scope == "part" and self.part_number is None:
            raise ValueError("part_number is required when scope is 'part'")
        return self


class PracticePartSettingsUpdate(BaseModel):
    """PATCH body. ``duration_minutes=None`` reverts to proportional default."""

    duration_minutes: int | None = None
    is_enabled: bool = True


class PracticePartSettingsRead(BaseModel):
    section_type: str
    part_number: int
    duration_minutes: int | None
    is_enabled: bool
    effective_duration_minutes: int | None


PracticeUnitRead.model_rebuild()
PracticeSectionUnitRead.model_rebuild()
