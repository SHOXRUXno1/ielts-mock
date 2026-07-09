import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test
from app.schemas.test import TestCreate, TestDetailRead, TestRead, TestUpdate
from app.utils.slug import generate_book_slug

router = APIRouter(
    prefix="/admin/tests",
    tags=["Tests"],
    dependencies=[Depends(get_current_admin)],
)

# IELTS standard: (type, order, duration_minutes)
# First section of each type carries the full duration; subsequent parts are 0
# (take-test uses Math.max across sections of the same type for the timer).
DEFAULT_SECTIONS: list[tuple[SectionType, int, int]] = [
    # Listening — 4 parts
    (SectionType.LISTENING, 1,  30),
    (SectionType.LISTENING, 2,  0),
    (SectionType.LISTENING, 3,  0),
    (SectionType.LISTENING, 4,  0),
    # Reading — 3 passages
    (SectionType.READING,  10,  60),
    (SectionType.READING,  11,  0),
    (SectionType.READING,  12,  0),
    # Writing — 1 section (Task 1 + Task 2 are questions within it)
    (SectionType.WRITING,  20,  60),
    # Speaking — 3 parts
    (SectionType.SPEAKING, 30,  0),
    (SectionType.SPEAKING, 31,  0),
    (SectionType.SPEAKING, 32,  0),
]

# Expected section counts per type for a complete IELTS test
STANDARD_COUNTS: dict[SectionType, int] = {
    SectionType.LISTENING: 4,
    SectionType.READING:   3,
    SectionType.WRITING:   1,
    SectionType.SPEAKING:  3,
}


async def _load_test_detail(db: AsyncSession, test_id: uuid.UUID) -> Test:
    stmt = (
        select(Test)
        .options(
            selectinload(Test.sections)
            .selectinload(Section.question_groups)
            .selectinload(QuestionGroup.questions),
            selectinload(Test.sections).selectinload(Section.questions),
        )
        .where(Test.id == test_id)
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    return test


async def _resolve_slug(db: AsyncSession, payload_slug: str | None, book_name: str | None, title: str) -> str:
    """Return the book_slug to use, deriving it from book_name or title if not explicit."""
    if payload_slug:
        return payload_slug
    return generate_book_slug(book_name or title)


@router.get("/", response_model=list[TestRead])
async def list_tests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Test).order_by(Test.created_at.desc()))
    return result.scalars().all()


# ── Slug-based lookup (must be before /{test_id} to avoid UUID parse clash) ──

@router.get("/by-slug/{book_slug}/{test_number}", response_model=TestDetailRead)
async def get_test_by_slug(
    book_slug: str,
    test_number: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Test)
        .options(
            selectinload(Test.sections)
            .selectinload(Section.question_groups)
            .selectinload(QuestionGroup.questions),
            selectinload(Test.sections).selectinload(Section.questions),
        )
        .where(Test.book_slug == book_slug, Test.test_number == test_number)
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    return test


@router.post("/", response_model=TestDetailRead, status_code=status.HTTP_201_CREATED)
async def create_test(payload: TestCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()

    if data.get("type") and data["type"] != "academic":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Academic tests are supported. General Training is temporarily unavailable.",
        )

    # Auto-generate book_slug if not supplied
    if not data.get("book_slug"):
        data["book_slug"] = generate_book_slug(data.get("book_name") or data["title"])

    # Default test_number to 1 if not supplied
    if data.get("test_number") is None:
        data["test_number"] = 1

    test_id = uuid.uuid4()
    test = Test(id=test_id, **data)
    db.add(test)

    for section_type, order, duration in DEFAULT_SECTIONS:
        db.add(
            Section(
                test_id=test_id,
                type=section_type,
                order=order,
                duration_minutes=duration,
            )
        )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A test with this book name and test number already exists. Choose a different test number.",
        )
    return await _load_test_detail(db, test_id)


@router.get("/{test_id}", response_model=TestDetailRead)
async def get_test(test_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await _load_test_detail(db, test_id)


@router.patch("/{test_id}", response_model=TestRead)
async def update_test(
    test_id: uuid.UUID,
    payload: TestUpdate,
    db: AsyncSession = Depends(get_db),
):
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    updates = payload.model_dump(exclude_unset=True)

    # Reject attempts to change type to general
    if updates.get("type") and updates["type"] != "academic":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Academic tests are supported. General Training is temporarily unavailable.",
        )

    # Re-derive book_slug when book_name changes but slug was not explicitly set
    if "book_name" in updates and "book_slug" not in updates:
        new_name = updates["book_name"] or test.title
        updates["book_slug"] = generate_book_slug(new_name)

    for field, value in updates.items():
        setattr(test, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A test with this book name and test number already exists. Choose a different test number.",
        )
    await db.refresh(test)
    return test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test(test_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    # Use SQL-level DELETE so PostgreSQL ON DELETE CASCADE fires properly
    # (ORM-level db.delete() tries to nullify FKs on loaded related objects first)
    await db.execute(delete(Test).where(Test.id == test_id))
    await db.commit()


@router.get("/{test_id}/slug-redirect")
async def get_slug_redirect(test_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return the slug coordinates for a UUID-keyed test (for backward-compat redirects)."""
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    return {"book_slug": test.book_slug, "test_number": test.test_number}


@router.post("/{test_id}/normalize-sections", response_model=TestDetailRead)
async def normalize_sections(test_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Bring an existing test's sections in line with IELTS standard counts.

    - Backfills missing sections (old tests that have fewer than the standard count).
    - Deletes extra sections beyond the standard count (highest order first;
      cascade removes their questions and question groups).
    - Returns the refreshed test detail.
    """
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    for section_type, required_count in STANDARD_COUNTS.items():
        result = await db.execute(
            select(Section)
            .where(Section.test_id == test_id, Section.type == section_type)
            .order_by(Section.order)
        )
        existing = list(result.scalars().all())

        # Delete extras (highest order first to minimise FK conflicts)
        while len(existing) > required_count:
            extra = existing.pop()
            await db.delete(extra)

        # Backfill missing sections using the DEFAULT_SECTIONS order values
        defaults_for_type = [(o, d) for (t, o, d) in DEFAULT_SECTIONS if t == section_type]
        for i in range(len(existing), required_count):
            order, duration = defaults_for_type[i]
            db.add(Section(
                test_id=test_id,
                type=section_type,
                order=order,
                duration_minutes=duration,
            ))

    await db.commit()
    return await _load_test_detail(db, test_id)


@router.post("/{test_id}/publish", response_model=TestDetailRead)
async def publish_test(test_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    test = await _load_test_detail(db, test_id)

    errors: list[str] = []

    # Validate exact section counts per type
    for section_type, required in STANDARD_COUNTS.items():
        sections_of_type = [s for s in test.sections if s.type == section_type]
        actual = len(sections_of_type)
        if actual != required:
            errors.append(
                f"{section_type.value.capitalize()}: expected {required} section(s), found {actual}. "
                "Run 'Migrate to IELTS standard' to fix."
            )

    # Validate content presence for L/R/W
    for section_type in (SectionType.LISTENING, SectionType.READING, SectionType.WRITING):
        sections_of_type = [s for s in test.sections if s.type == section_type]
        total_questions = sum(len(s.questions) for s in sections_of_type)
        if total_questions == 0:
            errors.append(f"{section_type.value.capitalize()} has no questions.")

    # Writing must have exactly 2 tasks with task_number 1 and 2
    writing_sections = [s for s in test.sections if s.type == SectionType.WRITING]
    if writing_sections:
        writing_qs = [q for s in writing_sections for q in s.questions]
        writing_task_numbers = {q.task_number for q in writing_qs if q.task_number is not None}
        if len(writing_qs) != 2 or writing_task_numbers != {1, 2}:
            errors.append(
                f"Writing must have exactly 2 tasks with task_number 1 and 2; "
                f"found {len(writing_qs)} question(s) with task numbers {sorted(writing_task_numbers) or 'none'}."
            )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )

    test.is_published = True
    await db.commit()
    return await _load_test_detail(db, test_id)
