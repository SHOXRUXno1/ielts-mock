import uuid
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _parse_session_id(payload: dict) -> uuid.UUID | None:
    raw = payload.get("sid")
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except (ValueError, AttributeError, TypeError):
        return None


@dataclass
class Actor:
    """Decoded JWT principal — works for both .env admin and DB users."""

    role: str
    sub: str  # login string for .env admin; user UUID string for DB users
    login: str
    user_id: uuid.UUID | None = field(default=None)
    db_user: object = field(default=None, repr=False)  # User model or None
    session_id: uuid.UUID | None = field(default=None)


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Actor:
    """Decode JWT and return an Actor. Works for admin (.env) and students (DB)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    role = payload.get("role", "student")
    sub = payload.get("sub", "")
    login = payload.get("login", sub)
    session_id = _parse_session_id(payload)

    async def _require_live_admin_session() -> None:
        if session_id is None:
            return
        from app.models.admin_session import AdminSession

        sess = await db.get(AdminSession, session_id)
        if sess is None or sess.ended_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin session revoked or expired",
            )

    # .env admin: sub is the login string (not a UUID)
    if role == "admin" and sub.casefold() == settings.admin_login.casefold():
        await _require_live_admin_session()
        return Actor(
            role="admin",
            sub=sub,
            login=sub,
            user_id=None,
            db_user=None,
            session_id=session_id,
        )

    # DB user: sub is a UUID
    try:
        user_id = uuid.UUID(sub)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    from app.models.user import User  # avoid circular at module level

    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if db_user is None or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if db_user.role == "admin":
        await _require_live_admin_session()

    return Actor(
        role=db_user.role,
        sub=sub,
        login=db_user.login,
        user_id=user_id,
        db_user=db_user,
        session_id=session_id,
    )


async def get_current_admin(
    actor: Actor = Depends(get_current_actor),
) -> Actor:
    """Require admin role (.env admin or DB user with role='admin')."""
    if actor.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return actor


async def get_current_student(
    actor: Actor = Depends(get_current_actor),
) -> Actor:
    """Require student role."""
    if actor.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return actor
