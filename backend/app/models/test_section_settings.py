import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class TestSectionSettings(UUIDPrimaryKey, TimestampMixin, Base):
    """Per-test, per-section-type settings. Source of truth for section duration."""

    __tablename__ = "test_section_settings"
    __table_args__ = (
        UniqueConstraint("test_id", "section_type", name="uq_test_section_settings"),
    )

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tests.id", ondelete="CASCADE"),
        index=True,
    )
    section_type: Mapped[str] = mapped_column(String(20))
    # NULL means untimed (speaking is AI-paced by default).
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # standard | custom — source of how duration_minutes was set.
    duration_mode: Mapped[str] = mapped_column(
        String(20),
        default="standard",
        server_default="standard",
    )

    test: Mapped["Test"] = relationship(back_populates="section_settings")
