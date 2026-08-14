"""Schemas for admin Devices / login sessions API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AdminSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_login: str
    actor_name: str | None = None
    ip_address: str | None = None
    device_type: str
    browser: str | None = None
    os_name: str | None = None
    login_at: datetime
    last_seen_at: datetime
    ended_at: datetime | None = None
    end_reason: str | None = None
    is_online: bool
    is_current: bool
    duration_seconds: int


class DevicesSummary(BaseModel):
    online_now: int
    logins_today: int
    unique_devices_7d: int
    last_login_at: datetime | None = None
