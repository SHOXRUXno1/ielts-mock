import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.section import Section, SectionType
from app.models.test import Test
from app.schemas.section import SectionCreate, SectionRead, SectionUpdate
from app.schemas.section_settings import (
    SectionSettingsRead,
    SectionSettingsUpdate,
    SectionSettingsUpdateResponse,
)
from app.services import section_settings as settings_service
from app.services.section_duration import (
    DurationRangeError,
    check_duration,
    recommended_for,
)

logger = logging.getLogger(__name__)

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

    updates = payload.model_dump(exclude_unset=True)

    # Listening: passage is deprecated — redirect into audioscript.
    if section.type == SectionType.LISTENING and "passage" in updates:
        passage_val = updates.pop("passage")
        if passage_val is not None:
            logger.warning(
                "Deprecated: PATCH listening section %s with 'passage'; "
                "redirecting to audioscript",
                section_id,
            )
            # Prefer explicit audioscript if both were sent.
            if "audioscript" not in updates:
                updates["audioscript"] = passage_val

    for field, value in updates.items():
        setattr(section, field, value)

    await db.commit()
    await db.refresh(section)
    return section


@router.get(
    "/tests/{test_id}/section-settings",
    response_model=list[SectionSettingsRead],
)
async def list_section_settings(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    rows = await settings_service.ensure_settings(db, test_id)
    await db.commit()
    return rows


@router.patch(
    "/tests/{test_id}/section-settings/{section_type}",
    response_model=SectionSettingsUpdateResponse,
)
async def update_section_settings(
    test_id: uuid.UUID,
    section_type: str,
    payload: SectionSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    if section_type not in {t.value for t in SectionType}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid section type",
        )

    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    rows = await settings_service.ensure_settings(db, test_id)
    row = next((r for r in rows if r.section_type == section_type), None)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section settings not found",
        )

    fields_set = payload.model_fields_set
    mode = payload.duration_mode
    # Legacy: duration_minutes alone implies custom (or standard when speaking null).
    if mode is None and "duration_minutes" in fields_set:
        if section_type == SectionType.SPEAKING.value and payload.duration_minutes is None:
            mode = "standard"
        else:
            mode = "custom"
    if mode is None:
        # Treat legacy audio_length as custom.
        raw = row.duration_mode or "standard"
        mode = "standard" if raw == "standard" else "custom"

    warning: str | None = None

    if mode == "standard":
        minutes = recommended_for(section_type)
        try:
            warning = check_duration(section_type, minutes)
        except DurationRangeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        row.duration_mode = "standard"
        row.duration_minutes = minutes
    else:
        # custom — keep existing minutes when only switching mode.
        if "duration_minutes" in fields_set:
            minutes = payload.duration_minutes
        else:
            minutes = row.duration_minutes
        try:
            warning = check_duration(section_type, minutes)
        except DurationRangeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        row.duration_mode = "custom"
        row.duration_minutes = minutes

    await db.commit()
    await db.refresh(row)
    return SectionSettingsUpdateResponse(
        settings=SectionSettingsRead.model_validate(row),
        warning=warning,
    )


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
