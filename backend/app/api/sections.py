import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.section import Section, SectionType
from app.models.test import Test
from app.schemas.section import SectionCreate, SectionRead, SectionUpdate

router = APIRouter(
    prefix="/admin",
    tags=["Sections"],
    dependencies=[Depends(get_current_admin)],
)

# IELTS standard maximum sections per type.
# create_section rejects requests that would exceed these counts.
STANDARD_COUNTS: dict[SectionType, int] = {
    SectionType.LISTENING: 4,
    SectionType.READING:   3,
    SectionType.WRITING:   1,
    SectionType.SPEAKING:  3,
}

# order bands: listening 1-9, reading 10-19, writing 20-29, speaking 30-39
_BAND_START: dict[SectionType, int] = {
    SectionType.LISTENING: 1,
    SectionType.READING: 10,
    SectionType.WRITING: 20,
    SectionType.SPEAKING: 30,
}


@router.post(
    "/tests/{test_id}/sections",
    response_model=SectionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_section(
    test_id: uuid.UUID,
    payload: SectionCreate,
    db: AsyncSession = Depends(get_db),
):
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    section_type = SectionType(payload.type)
    standard_max = STANDARD_COUNTS[section_type]

    # Count existing sections of this type
    count_result = await db.execute(
        select(func.count()).where(Section.test_id == test_id, Section.type == section_type)
    )
    current_count = count_result.scalar_one()

    if current_count >= standard_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"IELTS standard allows exactly {standard_max} "
                f"{section_type.value} section(s). "
                f"This test already has {current_count}."
            ),
        )

    band_start = _BAND_START[section_type]
    band_end = band_start + 9

    result = await db.execute(
        select(Section.order)
        .where(Section.test_id == test_id, Section.type == section_type)
        .order_by(Section.order.desc())
        .limit(1)
    )
    max_order = result.scalar_one_or_none()
    new_order = max(band_start, (max_order or band_start - 1) + 1)

    if new_order > band_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum sections for type '{payload.type}' reached",
        )

    section = Section(
        test_id=test_id,
        type=section_type,
        order=new_order,
        duration_minutes=payload.duration_minutes,
        audio_url=payload.audio_url,
        passage=payload.passage,
        audioscript=payload.audioscript,
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


@router.patch("/sections/{section_id}", response_model=SectionRead)
async def update_section(
    section_id: uuid.UUID,
    payload: SectionUpdate,
    db: AsyncSession = Depends(get_db),
):
    section = await db.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, field, value)

    await db.commit()
    await db.refresh(section)
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    section = await db.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    await db.execute(delete(Section).where(Section.id == section_id))
    await db.commit()
