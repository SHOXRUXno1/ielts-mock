"""Shared take-test read endpoints for admin and student.

Students may only access published tests, and never receive answer_key.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test
from app.schemas.question import QuestionRead
from app.schemas.test import TestDetailRead
from app.services import section_settings as settings_service
from app.services.question_numbering import (
    annotate_question_numbers,
    annotate_questions_list,
    question_numbers_for_test,
)

router = APIRouter(tags=["Take Test"])


class SlugRedirectRead(BaseModel):
    book_slug: str
    test_number: int


def _assert_take_access(test: Test, actor: Actor) -> None:
    if actor.role == "student" and not test.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test is not published",
        )


def _strip_answer_keys(test: Test) -> Test:
    """Mutate loaded ORM graph so student responses never leak answer_key."""
    for section in test.sections:
        for q in section.questions:
            q.answer_key = None
        for group in section.question_groups:
            for q in group.questions:
                q.answer_key = None
    return test


_DETAIL_OPTIONS = (
    selectinload(Test.sections)
    .selectinload(Section.question_groups)
    .selectinload(QuestionGroup.questions),
    selectinload(Test.sections).selectinload(Section.questions),
    selectinload(Test.section_settings),
)


async def _load_test_detail(db: AsyncSession, test_id: uuid.UUID) -> Test:
    stmt = select(Test).options(*_DETAIL_OPTIONS).where(Test.id == test_id)
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    annotate_question_numbers(test)
    await settings_service.ensure_loaded(db, test)
    return test


@router.get("/tests/{test_id}/slug-redirect", response_model=SlugRedirectRead)
async def take_slug_redirect(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    _assert_take_access(test, actor)
    return {"book_slug": test.book_slug, "test_number": test.test_number}


@router.get("/tests/by-slug/{book_slug}/{test_number}", response_model=TestDetailRead)
async def take_test_by_slug(
    book_slug: str,
    test_number: int,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    stmt = (
        select(Test)
        .options(*_DETAIL_OPTIONS)
        .where(Test.book_slug == book_slug, Test.test_number == test_number)
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    _assert_take_access(test, actor)
    annotate_question_numbers(test)
    await settings_service.ensure_loaded(db, test)
    if actor.role == "student":
        _strip_answer_keys(test)
    return test


@router.get("/tests/{test_id}", response_model=TestDetailRead)
async def take_test_detail(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    test = await _load_test_detail(db, test_id)
    _assert_take_access(test, actor)
    if actor.role == "student":
        _strip_answer_keys(test)
    return test


@router.get(
    "/sections/{section_id}/questions",
    response_model=list[QuestionRead],
)
async def take_section_questions(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    section = await db.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    test = await _load_test_detail(db, section.test_id)
    _assert_take_access(test, actor)

    result = await db.execute(
        select(Question).where(Question.section_id == section_id).order_by(Question.order)
    )
    questions = list(result.scalars().all())
    # Numbers already annotated on the loaded test graph; copy onto this flat list.
    ranges = question_numbers_for_test(test)
    annotate_questions_list(questions, ranges)
    if actor.role == "student":
        for q in questions:
            q.answer_key = None
    return questions
