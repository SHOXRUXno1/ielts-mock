import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StudentCreate(BaseModel):
    full_name: str
    phone: str  # required — used as login and initial password
    group_name: str | None = None


class StudentUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    group_name: str | None = None
    is_active: bool | None = None


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    login: str
    full_name: str
    phone: str | None
    group_name: str | None
    role: str
    is_active: bool
    created_at: datetime


class StudentCreated(StudentRead):
    """Returned only once at creation — includes plaintext password."""
    password: str


class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_id: uuid.UUID
    status: str
    overall_band: float | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class StudentDetail(StudentRead):
    attempts: list[AttemptSummary] = []


class ResetPasswordResponse(BaseModel):
    password: str
