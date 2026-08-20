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
from app.services import section_settings as settings_service
from app.services.compound import check_compound_group_completeness, is_compound_type
from app.services.question_integrity import orphan_question_errors
from app.services.question_numbering import annotate_question_numbers
from app.services.scoring import count_questions_in_section
from app.services.speaking_plan import plan_from_sections
from app.utils.slug import generate_book_slug

router = APIRouter(
    prefix="/admin/tests",
    tags=["Tests"],
    dependencies=[Depends(get_current_admin)],
)

# IELTS standard: (type, order). Timing lives in test_section_settings.
DEFAULT_SECTIONS: list[tuple[SectionType, int]] = [
    # Listening — 4 parts
    (SectionType.LISTENING, 1),
    (SectionType.LISTENING, 2),
    (SectionType.LISTENING, 3),
    (SectionType.LISTENING, 4),
    # Reading — 3 passages
    (SectionType.READING,  10),
    (SectionType.READING,  11),
    (SectionType.READING,  12),
    # Writing — 1 section (Task 1 + Task 2 are questions within it)
    (SectionType.WRITING,  20),
    # Speaking — 3 parts
    (SectionType.SPEAKING, 30),
    (SectionType.SPEAKING, 31),
    (SectionType.SPEAKING, 32),
]

# Expected section counts per type for a complete IELTS test
STANDARD_COUNTS: dict[SectionType, int] = {
    SectionType.LISTENING: 4,
    SectionType.READING:   3,
    SectionType.WRITING:   1,
    SectionType.SPEAKING:  3,
}


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
        .options(*_DETAIL_OPTIONS)
        .where(Test.book_slug == book_slug, Test.test_number == test_number)
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    annotate_question_numbers(test)
    await settings_service.ensure_loaded(db, test)
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

    for section_type, order in DEFAULT_SECTIONS:
        db.add(
            Section(
                test_id=test_id,
                type=section_type,
                order=order,
            )
        )

    db.add_all(settings_service.build_default_rows(test_id))

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


@router.get(
    "/{test_id}/preview",
    response_model=TestDetailRead,
    summary="Teacher preview of a test",
)
async def preview_test(test_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return full test detail for admin preview (no attempt created).

    Same shape as GET /admin/tests/{id}. Includes questions with answer_key
    so the frontend can render correct answers in preview mode. Does not
    write analytics or create an attempt.
    """
    return await _load_test_detail(db, test_id)


def _collect_publish_errors(test: Test) -> list[str]:
    """IELTS Academic publish checks (shared by POST /publish and PATCH is_published)."""
    errors: list[str] = []

    for section_type, required in STANDARD_COUNTS.items():
        sections_of_type = [s for s in test.sections if s.type == section_type]
        actual = len(sections_of_type)
        if actual != required:
            errors.append(
                f"{section_type.value.capitalize()}: expected {required} section(s), found {actual}. "
                "Run 'Migrate to IELTS standard' to fix."
            )

    for section_type in (SectionType.LISTENING, SectionType.READING, SectionType.WRITING):
        sections_of_type = [s for s in test.sections if s.type == section_type]
        total_questions = sum(len(s.questions) for s in sections_of_type)
        if total_questions == 0:
            errors.append(f"{section_type.value.capitalize()} has no questions.")

    # Listening: exactly 10 scoring slots per part and 40 total.
    # multi_select with N correct answers counts as N slots.
    listening = sorted(
        (s for s in test.sections if s.type == SectionType.LISTENING),
        key=lambda s: s.order,
    )
    total_listening = 0
    for i, section in enumerate(listening, 1):
        qc = count_questions_in_section(section)
        total_listening += qc
        if qc != 10:
            errors.append(
                f"Listening Part {i} must have exactly 10 questions, got {qc}."
            )
    if listening and total_listening != 40:
        errors.append(
            f"Listening must have exactly 40 questions total, got {total_listening}."
        )

    writing_sections = [s for s in test.sections if s.type == SectionType.WRITING]
    if writing_sections:
        writing_qs = [q for s in writing_sections for q in s.questions]
        writing_task_numbers = {q.task_number for q in writing_qs if q.task_number is not None}
        if len(writing_qs) != 2 or writing_task_numbers != {1, 2}:
            errors.append(
                f"Writing must have exactly 2 tasks with task_number 1 and 2; "
                f"found {len(writing_qs)} question(s) with task numbers {sorted(writing_task_numbers) or 'none'}."
            )
        else:
            task1 = next((q for q in writing_qs if q.task_number == 1), None)
            if (
                task1 is not None
                and (test.type or "").lower() == "academic"
                and not task1.image_url
            ):
                errors.append("Academic Writing Task 1 requires a chart/diagram image")
            for q in writing_qs:
                content = q.content if isinstance(q.content, dict) else {}
                prompt = (content.get("prompt") or "").strip()
                if not prompt:
                    errors.append(f"Writing Task {q.task_number} is missing a prompt.")

    speaking = [s for s in test.sections if s.type == SectionType.SPEAKING]
    if speaking:
        plan = plan_from_sections(speaking)
        missing: list[str] = []
        if not plan.part1_authored:
            missing.append("Part 1 questions")
        if not plan.cue_card_authored:
            missing.append("a Part 2 cue card")
        if not plan.part3_authored:
            missing.append("Part 3 questions")
        if missing:
            errors.append("Speaking is missing " + ", ".join(missing) + ".")

    for section in test.sections:
        for group in getattr(section, "question_groups", []) or []:
            if not is_compound_type(group.question_type):
                continue
            errors.extend(
                check_compound_group_completeness(
                    group.question_type,
                    group.options_shared,
                    list(group.questions or []),
                )
            )

    errors.extend(orphan_question_errors(test))

    return errors


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

    # Publishing via PATCH must run the same IELTS checks as POST /publish
    publishing = updates.get("is_published") is True and not test.is_published
    if publishing:
        detail = await _load_test_detail(db, test_id)
        errors = _collect_publish_errors(detail)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"errors": errors},
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
        defaults_for_type = [o for (t, o) in DEFAULT_SECTIONS if t == section_type]
        for i in range(len(existing), required_count):
            order = defaults_for_type[i]
            db.add(Section(
                test_id=test_id,
                type=section_type,
                order=order,
            ))

    await settings_service.ensure_settings(db, test_id)
    await db.commit()
    return await _load_test_detail(db, test_id)


@router.post("/{test_id}/publish", response_model=TestDetailRead)
async def publish_test(
    test_id: uuid.UUID,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
):
    test = await _load_test_detail(db, test_id)

    errors = _collect_publish_errors(test)
    if errors and not force:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )

    test.is_published = True
    await db.commit()
    return await _load_test_detail(db, test_id)
