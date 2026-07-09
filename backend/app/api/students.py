import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.student import (
    ResetPasswordResponse,
    StudentCreate,
    StudentCreated,
    StudentDetail,
    StudentRead,
    StudentUpdate,
)

router = APIRouter(
    prefix="/admin/students",
    tags=["Students"],
    dependencies=[Depends(get_current_admin)],
)


def _generate_password() -> str:
    return secrets.token_urlsafe(6)


@router.get("/", response_model=list[StudentRead])
async def list_students(
    search: str | None = None,
    group: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.role == "student")
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                func.lower(User.full_name).like(func.lower(pattern)),
                func.lower(User.login).like(func.lower(pattern)),
            )
        )
    if group:
        stmt = stmt.where(User.group_name == group)
    stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=StudentCreated, status_code=status.HTTP_201_CREATED)
async def create_student(
    body: StudentCreate,
    db: AsyncSession = Depends(get_db),
):
    login = body.phone.strip()
    plain_password = body.phone.strip()

    existing = await db.execute(select(User.id).where(User.login == login))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A student with phone '{login}' already exists.",
        )

    user = User(
        login=login,
        hashed_password=hash_password(plain_password),
        full_name=body.full_name.strip(),
        phone=body.phone,
        group_name=body.group_name,
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    data = {
        "id": user.id,
        "login": user.login,
        "full_name": user.full_name,
        "phone": user.phone,
        "group_name": user.group_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "password": plain_password,
    }
    return StudentCreated.model_validate(data)


@router.get("/{student_id}", response_model=StudentDetail)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.attempts))
        .where(User.id == student_id, User.role == "student")
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return user


@router.put("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.phone is not None:
        user.phone = body.phone
    if body.group_name is not None:
        user.group_name = body.group_name
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{student_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_student_password(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    plain_password = _generate_password()
    user.hashed_password = hash_password(plain_password)
    await db.commit()
    return ResetPasswordResponse(password=plain_password)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    user.is_active = False
    await db.commit()
