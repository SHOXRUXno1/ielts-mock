from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.admin import (
    AdminLogin,
    AdminMe,
    AdminTokenResponse,
    ChangeNameBody,
    ChangePasswordBody,
)
from app.services.admin_sessions import start_session
from app.services.env_writer import update_env_key

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    body: AdminLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if (
        body.email.casefold() != settings.admin_login.casefold()
        or body.password != settings.admin_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )
    sid = await start_session(
        db,
        login=settings.admin_login,
        name=settings.admin_name,
        user_id=None,
        request=request,
    )
    token = create_access_token(
        subject=settings.admin_login,
        extra={"role": "admin", "login": settings.admin_login, "sid": str(sid)},
    )
    return AdminTokenResponse(access_token=token)


@router.get("/me", response_model=AdminMe)
async def admin_me(admin: Actor = Depends(get_current_admin)):
    return AdminMe(login=admin.sub, name=settings.admin_name)


@router.patch("/password")
async def change_password(
    body: ChangePasswordBody,
    _admin: Actor = Depends(get_current_admin),
):
    if body.current_password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    update_env_key("ADMIN_PASSWORD", body.new_password)
    settings.admin_password = body.new_password
    return {"ok": True}


@router.patch("/name")
async def change_name(
    body: ChangeNameBody,
    _admin: Actor = Depends(get_current_admin),
):
    update_env_key("ADMIN_NAME", body.new_name)
    settings.admin_name = body.new_name
    return {"ok": True, "new_name": body.new_name}
