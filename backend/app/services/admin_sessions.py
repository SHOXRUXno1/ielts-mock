"""Admin login session tracking: start/end/touch + cleanup + heartbeat."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.database import async_session
from app.core.security import decode_access_token
from app.models.admin_session import AdminSession
from app.services.user_agent import parse_user_agent

logger = logging.getLogger(__name__)

ONLINE_WINDOW = timedelta(minutes=15)
TOUCH_THROTTLE_SECONDS = 60.0
CLEANUP_INTERVAL = 300  # 5 minutes

# In-memory throttle: sid -> monotonic timestamp of last touch attempt
_touch_throttle: dict[str, float] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def client_ip(request: Request) -> str | None:
    """Prefer first X-Forwarded-For hop, fall back to request.client.host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first[:45]
    if request.client and request.client.host:
        return request.client.host[:45]
    return None


async def start_session(
    db: AsyncSession,
    *,
    login: str,
    name: str | None,
    user_id: uuid.UUID | None,
    request: Request,
) -> uuid.UUID:
    """Create an admin_sessions row and return its id (JWT sid)."""
    now = _utcnow()
    ua = request.headers.get("user-agent") or ""
    device_type, browser, os_name = parse_user_agent(ua)
    session = AdminSession(
        actor_login=login,
        actor_name=name,
        user_id=user_id,
        ip_address=client_ip(request),
        user_agent=ua[:2000] if ua else None,
        device_type=device_type,
        browser=browser,
        os_name=os_name,
        login_at=now,
        last_seen_at=now,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session.id


async def end_session(
    db: AsyncSession,
    sid: uuid.UUID | str | None,
    reason: str,
) -> bool:
    """Idempotently close a session. Returns True if a row was updated."""
    if sid is None:
        return False
    try:
        session_id = uuid.UUID(str(sid))
    except (ValueError, AttributeError, TypeError):
        return False

    now = _utcnow()
    result = await db.execute(
        update(AdminSession)
        .where(
            AdminSession.id == session_id,
            AdminSession.ended_at.is_(None),
        )
        .values(ended_at=now, end_reason=reason)
    )
    await db.commit()
    return bool(result.rowcount)


async def touch_session(sid: uuid.UUID | str) -> None:
    """Update last_seen_at at most once per TOUCH_THROTTLE_SECONDS."""
    key = str(sid)
    now_mono = time.monotonic()
    last = _touch_throttle.get(key)
    if last is not None and (now_mono - last) < TOUCH_THROTTLE_SECONDS:
        return
    _touch_throttle[key] = now_mono

    try:
        session_id = uuid.UUID(key)
    except (ValueError, AttributeError, TypeError):
        return

    try:
        async with async_session() as db:
            await db.execute(
                update(AdminSession)
                .where(
                    AdminSession.id == session_id,
                    AdminSession.ended_at.is_(None),
                )
                .values(last_seen_at=_utcnow())
            )
            await db.commit()
    except Exception:
        logger.debug("touch_session failed for %s", key, exc_info=True)


async def close_stale_sessions(db: AsyncSession) -> int:
    """Close idle and expired open sessions. Returns number of rows closed."""
    now = _utcnow()
    idle_threshold = now - ONLINE_WINDOW
    token_ttl = timedelta(minutes=settings.access_token_expire_minutes)
    expired_threshold = now - token_ttl
    closed = 0

    # Idle timeout: ended_at = last_seen_at (not now)
    idle_result = await db.execute(
        update(AdminSession)
        .where(
            AdminSession.ended_at.is_(None),
            AdminSession.last_seen_at < idle_threshold,
            AdminSession.login_at >= expired_threshold,
        )
        .values(
            ended_at=AdminSession.last_seen_at,
            end_reason="timeout",
        )
    )
    closed += int(idle_result.rowcount or 0)

    # Token lifetime exceeded
    expired_result = await db.execute(
        update(AdminSession)
        .where(
            AdminSession.ended_at.is_(None),
            AdminSession.login_at < expired_threshold,
        )
        .values(
            ended_at=AdminSession.last_seen_at,
            end_reason="expired",
        )
    )
    closed += int(expired_result.rowcount or 0)

    await db.commit()
    return closed


async def run_admin_session_cleanup() -> None:
    """Forever loop: close stale admin sessions every CLEANUP_INTERVAL seconds."""
    while True:
        try:
            async with async_session() as db:
                n = await close_stale_sessions(db)
                if n:
                    logger.info("Closed %d stale admin sessions", n)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Admin session cleanup iteration failed")
        await asyncio.sleep(CLEANUP_INTERVAL)


def is_online(session: AdminSession, *, now: datetime | None = None) -> bool:
    """Online = not ended and last_seen within ONLINE_WINDOW."""
    if session.ended_at is not None:
        return False
    ref = now or _utcnow()
    last = session.last_seen_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last > ref - ONLINE_WINDOW


class AdminSessionHeartbeatMiddleware(BaseHTTPMiddleware):
    """Touch admin session last_seen_at from Bearer sid (best-effort)."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.method != "OPTIONS":
            try:
                auth = request.headers.get("authorization") or ""
                if auth.lower().startswith("bearer "):
                    token = auth[7:].strip()
                    payload = decode_access_token(token)
                    if payload and payload.get("role") == "admin":
                        sid = payload.get("sid")
                        if sid:
                            await touch_session(sid)
            except Exception:
                logger.debug("Heartbeat middleware skipped", exc_info=True)
        return await call_next(request)


async def get_session_by_id(
    db: AsyncSession, sid: uuid.UUID
) -> AdminSession | None:
    result = await db.execute(
        select(AdminSession).where(AdminSession.id == sid)
    )
    return result.scalar_one_or_none()
