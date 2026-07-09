import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class SpeakingSession(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "speaking_sessions"

    admin_email: Mapped[str] = mapped_column(String(255), index=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    overall_band: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    history_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
