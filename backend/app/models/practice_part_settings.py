"""Per-part practice settings — one row per (test, section_type, part_number).

Practice mode ("Single Part Timer") lets a student solve one part in isolation.
Each part has its own duration and can be disabled by the admin. When a row is
absent the API falls back to a proportional default derived from the section
duration (e.g. Listening 30 min / 4 parts = 7.5 min per part).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class PracticePartSettings(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "practice_part_settings"
    __table_args__ = (
        UniqueConstraint(
            "test_id",
            "section_type",
            "part_number",
            name="uq_practice_part_settings",
        ),
    )

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tests.id", ondelete="CASCADE"),
        index=True,
    )
    section_type: Mapped[str] = mapped_column(String(20))
    part_number: Mapped[int] = mapped_column(SmallInteger)
    # NULL means "use proportional default". Speaking may stay NULL forever.
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    test: Mapped["Test"] = relationship(back_populates="practice_part_settings")
