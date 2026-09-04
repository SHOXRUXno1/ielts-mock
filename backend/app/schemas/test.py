import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.section import SectionRead
from app.schemas.section_settings import SectionSettingsRead


class TestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_published: bool = False
    type: str = "academic"
    book_name: str | None = None
    book_slug: str | None = None
    test_number: int | None = None


class TestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_published: bool | None = None
    type: str | None = None
    book_name: str | None = None
    book_slug: str | None = None
    test_number: int | None = None


class SectionCounts(BaseModel):
    """Scoring slots per skill for a test, so the list page can show an
    accurate 'L 40 · R 40 · W 2 · S 3' summary without a per-row detail
    fetch. Populated by the list endpoint; single-test detail can skip it.
    """
    listening: int = 0
    reading: int = 0
    writing: int = 0
    speaking: int = 0


class TestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    is_published: bool
    type: str
    book_name: str | None = None
    book_slug: str
    test_number: int
    section_counts: SectionCounts | None = None
    created_at: datetime
    updated_at: datetime


class TestDetailRead(TestRead):
    sections: list[SectionRead]
    section_settings: list[SectionSettingsRead] = []
