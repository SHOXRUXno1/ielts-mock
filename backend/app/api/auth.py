from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_actor
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginBody, LoginResponse, MeResponse, TokenUser
from app.services.admin_sessions import end_session, start_session

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # 1. Check .env admin first
    if body.login == settings.admin_login and body.password == settings.admin_password:
        sid = await start_session(
            db,
            login=settings.admin_login,
            name=settings.admin_name,
            user_id=None,
            request=request,
        )
        token = create_access_token(
            subject=settings.admin_login,
            extra={
                "role": "admin",
                "login": settings.admin_login,
                "sid": str(sid),
            },
        )
        return LoginResponse(
            access_token=token,
            user=TokenUser(
                id=None,
                login=settings.admin_login,
                full_name=settings.admin_name,
                role="admin",
            ),
        )

    # 2. DB lookup
    result = await db.execute(
        select(User).where(User.login == body.login, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    extra: dict = {"role": user.role, "login": user.login}
    if user.role == "admin":
        sid = await start_session(
            db,
            login=user.login,
            name=user.full_name or user.login,
            user_id=user.id,
            request=request,
        )
        extra["sid"] = str(sid)

    token = create_access_token(subject=str(user.id), extra=extra)
    return LoginResponse(
        access_token=token,
        user=TokenUser(
            id=str(user.id),
            login=user.login,
            full_name=user.full_name,
            role=user.role,
        ),
    )


@router.post("/logout")
async def logout(
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Close the current admin session if present. Always succeeds."""
    if actor.session_id is not None:
        await end_session(db, actor.session_id, reason="logout")
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(actor: Actor = Depends(get_current_actor)):
    # .env admin
    if actor.db_user is None:
        return MeResponse(
            id=None,
            login=actor.login,
            full_name=settings.admin_name,
            name=settings.admin_name,
            role="admin",
        )
    # DB user
    u = actor.db_user
    return MeResponse(
        id=str(u.id),
        login=u.login,
        full_name=u.full_name,
        name=u.full_name,
        role=u.role,
    )
