"""Admin Devices API — list and summarize login sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_admin
from app.core.database import get_db
from app.models.admin_session import AdminSession
from app.schemas.devices import AdminSessionRead, DevicesSummary
from app.services.admin_sessions import ONLINE_WINDOW, end_session, is_online

router = APIRouter(
    prefix="/admin/devices",
    tags=["Devices"],
    dependencies=[Depends(get_current_admin)],
)


def _duration_seconds(session: AdminSession, *, now: datetime) -> int:
    end = session.ended_at or now
    start = session.login_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return max(0, int((end - start).total_seconds()))


def _to_read(
    session: AdminSession,
    *,
    current_sid,
    now: datetime,
) -> AdminSessionRead:
    online = is_online(session, now=now)
    return AdminSessionRead(
        id=session.id,
        actor_login=session.actor_login,
        actor_name=session.actor_name,
        ip_address=session.ip_address,
        device_type=session.device_type,
        browser=session.browser,
        os_name=session.os_name,
        login_at=session.login_at,
        last_seen_at=session.last_seen_at,
        ended_at=session.ended_at,
        end_reason=session.end_reason,
        is_online=online,
        is_current=bool(current_sid and session.id == current_sid),
        duration_seconds=_duration_seconds(session, now=now),
    )


@router.get("/", response_model=list[AdminSessionRead])
async def list_devices(
    status: str = Query("all", pattern="^(all|online|ended)$"),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    actor: Actor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    online_cutoff = now - ONLINE_WINDOW

    stmt = (
        select(AdminSession)
        .where(AdminSession.login_at >= since)
        .order_by(AdminSession.login_at.desc())
        .limit(limit)
    )

    if status == "online":
        stmt = stmt.where(
            AdminSession.ended_at.is_(None),
            AdminSession.last_seen_at > online_cutoff,
        )
    elif status == "ended":
        stmt = stmt.where(
            (AdminSession.ended_at.is_not(None))
            | (AdminSession.last_seen_at <= online_cutoff)
        )

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return [
        _to_read(row, current_sid=actor.session_id, now=now) for row in rows
    ]


@router.get("/summary", response_model=DevicesSummary)
async def devices_summary(
    _actor: Actor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    online_cutoff = now - ONLINE_WINDOW
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    online_q = await db.execute(
        select(func.count())
        .select_from(AdminSession)
        .where(
            AdminSession.ended_at.is_(None),
            AdminSession.last_seen_at > online_cutoff,
        )
    )
    today_q = await db.execute(
        select(func.count())
        .select_from(AdminSession)
        .where(AdminSession.login_at >= today_start)
    )
    # Unique devices ≈ distinct (browser, os_name, device_type, ip_address) in 7d
    unique_q = await db.execute(
        select(
            func.count(
                func.distinct(
                    func.concat(
                        func.coalesce(AdminSession.browser, ""),
                        "|",
                        func.coalesce(AdminSession.os_name, ""),
                        "|",
                        AdminSession.device_type,
                        "|",
                        func.coalesce(AdminSession.ip_address, ""),
                    )
                )
            )
        ).where(AdminSession.login_at >= week_ago)
    )
    last_q = await db.execute(
        select(AdminSession.login_at)
        .order_by(AdminSession.login_at.desc())
        .limit(1)
    )

    return DevicesSummary(
        online_now=int(online_q.scalar() or 0),
        logins_today=int(today_q.scalar() or 0),
        unique_devices_7d=int(unique_q.scalar() or 0),
        last_login_at=last_q.scalar_one_or_none(),
    )


@router.delete("/{session_id}", status_code=204)
async def revoke_session(
    session_id: uuid.UUID,
    actor: Actor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """End a single admin session (cannot revoke your own current session)."""
    if actor.session_id and uuid.UUID(str(actor.session_id)) == session_id:
        raise HTTPException(400, "Cannot revoke your own current session")
    closed = await end_session(db, session_id, reason="revoked")
    if not closed:
        raise HTTPException(404, "Session not found or already ended")


@router.post("/revoke-all", status_code=200)
async def revoke_all_sessions(
    actor: Actor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """End all other active admin sessions except the caller's current one."""
    now = datetime.now(timezone.utc)
    stmt = (
        update(AdminSession)
        .where(
            AdminSession.ended_at.is_(None),
            AdminSession.id != uuid.UUID(str(actor.session_id))
            if actor.session_id
            else True,
        )
        .values(ended_at=now, end_reason="revoked")
    )
    result = await db.execute(stmt)
    await db.commit()
    return {"revoked": int(result.rowcount or 0)}
