from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class SimliSlotLease(UUIDPrimaryKey, TimestampMixin, Base):
    """A claim on one concurrent video-avatar slot.

    The browser asks for a video token before the exam session exists, so
    counting sessions alone lets a simultaneous start wave through far more
    candidates than the plan allows. Handing out a token takes a lease instead,
    which makes the claim visible the instant it is made.

    One lease per candidate: reloading the exam page renews the existing claim
    rather than taking a second slot.
    """

    __tablename__ = "simli_slot_leases"

    actor: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
