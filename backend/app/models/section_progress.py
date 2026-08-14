import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class SectionState(str, enum.Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    SEALED = "sealed"


class SealedReason(str, enum.Enum):
    MANUAL = "manual"  # student clicked Finish Section
    TIMEOUT = "timeout"  # timer expired
    SUBMIT = "submit"  # test-level submit
    ADVANCE = "advance"  # implicit — entered next section


class SectionProgress(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "section_progress"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "section_type",
            name="uq_section_progress_attempt_type",
        ),
        Index("ix_section_progress_active", "attempt_id", "state"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        index=True,
    )
    section_type: Mapped[str] = mapped_column(String(20))
    state: Mapped[str] = mapped_column(
        String(16),
        default=SectionState.NOT_STARTED.value,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sealed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sealed_reason: Mapped[str | None] = mapped_column(String(16), nullable=True)

    attempt: Mapped["Attempt"] = relationship(back_populates="section_progress")
