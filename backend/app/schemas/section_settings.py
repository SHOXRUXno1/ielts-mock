import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


DurationMode = Literal["standard", "custom"]


class SectionSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_id: uuid.UUID
    section_type: str
    duration_minutes: int | None
    duration_mode: str = "standard"


class SectionSettingsUpdate(BaseModel):
    # Range checks live in services.section_duration.check_duration because
    # section_type comes from the URL path, not this body.
    duration_minutes: int | None = None
    duration_mode: DurationMode | None = None

    @model_validator(mode="after")
    def require_something(self) -> "SectionSettingsUpdate":
        fields_set = self.model_fields_set
        if "duration_minutes" not in fields_set and "duration_mode" not in fields_set:
            raise ValueError("Provide duration_mode and/or duration_minutes")
        return self


class SectionSettingsUpdateResponse(BaseModel):
    settings: SectionSettingsRead
    warning: str | None = None
