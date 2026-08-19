"""Test import API: template download, preview, confirm, and per-section audio upload."""

from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test
from app.services import section_settings as settings_service
from app.services.storage import save_audio
from app.services.test_import_service import (
    ParsedSection,
    PreviewResult,
    SectionSummary,
    _build_answer_key,
    _build_content,
    build_preview,
    parse_xlsx,
)
from app.services.test_template import build_template_workbook

router = APIRouter(
    prefix="/admin/tests",
    tags=["Test Import"],
    dependencies=[Depends(get_current_admin)],
)

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class SectionSummaryOut(BaseModel):
    sheet_name: str
    kind: str
    passage_word_count: int | None
    questions_count: int
    tasks_count: int | None
    audio_filename: str | None


class PreviewResultOut(BaseModel):
    title: str
    description: str | None
    type: str
    sections: list[SectionSummaryOut]
    total_questions: int
    warnings: list[str]
    errors: list[str]


class ListeningSectionInfo(BaseModel):
    id: uuid.UUID
    name: str
    audio_filename: str | None


class ConfirmResultOut(BaseModel):
    test_id: uuid.UUID
    sections_created: int
    questions_created: int
    listening_sections: list[ListeningSectionInfo]


class AudioUploadOut(BaseModel):
    url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _preview_to_out(pr: PreviewResult) -> PreviewResultOut:
    return PreviewResultOut(
        title=pr.title,
        description=pr.description,
        type=pr.type,
        sections=[
            SectionSummaryOut(
                sheet_name=s.sheet_name,
                kind=s.kind,
                passage_word_count=s.passage_word_count,
                questions_count=s.questions_count,
                tasks_count=s.tasks_count,
                audio_filename=s.audio_filename,
            )
            for s in pr.sections
        ],
        total_questions=pr.total_questions,
        warnings=pr.warnings,
        errors=pr.errors,
    )


def _section_order_for(kind: str, part_or_idx: int) -> int:
    """Assign canonical section order: reading 1-3, writing 4, listening 5-8."""
    if kind == "reading":
        return part_or_idx           # 1, 2, 3
    if kind == "writing":
        return 4
    # listening
    return 4 + part_or_idx           # 5, 6, 7, 8


def _resolve_qtype(qtype_str: str) -> QuestionType:
    try:
        return QuestionType(qtype_str)
    except ValueError:
        return QuestionType.GAP_FILL


def _build_questions_for_section(sec: ParsedSection) -> list[dict]:
    """Build list of dicts ready to construct Question ORM objects."""
    rows = []
    for q in sec.questions:
        content = _build_content(
            q.question_type, q.question, q.options, q.instruction
        )
        answer_key = _build_answer_key(q.question_type, q.answer, q.options)
        row: dict = {
            "order": q.order,
            "question_type": _resolve_qtype(q.question_type),
            "content": content,
            "answer_key": answer_key,
            "group": q.group,
            "_instruction": q.instruction,
            "_options": q.options,
        }
        # Carry writing metadata so confirm_import can set the DB columns
        if sec.section_kind == "writing":
            # Derive task_number from field or fall back to order
            task_num = q.task_number if q.task_number in (1, 2) else (q.order if q.order in (1, 2) else None)
            row["_task_number"] = task_num
            row["_min_words"] = 150 if task_num == 1 else (250 if task_num == 2 else q.min_words)
            row["_essay_type"] = q.essay_type if task_num == 2 else None
            # Writing questions are always stored as essay
            row["question_type"] = QuestionType.ESSAY
        rows.append(row)
    return rows


def _group_question_rows(
    q_rows: list[dict],
) -> list[tuple[str, str | None, list[dict]]]:
    """
    Return (question_type, instruction, [q_row, ...]) tuples, one per logical group.

    Groups are determined by:
    1. Explicit `group` number in the row (from Excel `group` column).
    2. Fallback: contiguous runs of the same `question_type`.

    Also hoists `options_shared` when all questions in the group have identical options.
    """
    if not q_rows:
        return []

    # Determine if explicit group numbers are present
    has_explicit = any(r["group"] is not None for r in q_rows)

    groups: list[tuple[str, str | None, list[dict]]] = []

    if has_explicit:
        # Group by explicit number; use first row's type/instruction for the group
        group_map: dict[int, list[dict]] = {}
        group_order: list[int] = []
        for r in q_rows:
            gnum = r["group"] if r["group"] is not None else -id(r)
            if gnum not in group_map:
                group_map[gnum] = []
                group_order.append(gnum)
            group_map[gnum].append(r)
        for gnum in group_order:
            rows = group_map[gnum]
            qt = rows[0]["question_type"]
            inst = rows[0]["_instruction"] or ""
            groups.append((qt, inst, rows))
    else:
        # Contiguous runs of same question_type (via shared utility)
        from app.services.question_grouping import group_questions_by_contiguous_type
        for run in group_questions_by_contiguous_type(q_rows, lambda r: r["question_type"]):
            groups.append((run[0]["question_type"], run[0]["_instruction"] or "", run))

    return groups


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/template")
async def download_template():
    """Stream the styled IELTS test template as an xlsx attachment."""
    wb = build_template_workbook()
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type=XLSX_MIME,
        headers={
            "Content-Disposition": 'attachment; filename="ielts_test_template.xlsx"'
        },
    )


@router.post("/import/preview", response_model=PreviewResultOut)
async def preview_import(file: UploadFile):
    """Parse the uploaded xlsx and return a preview (never touches DB)."""
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .xlsx files are accepted.",
        )
    file_bytes = await file.read()
    try:
        parsed = parse_xlsx(file_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse workbook: {exc}",
        ) from exc

    preview = build_preview(parsed)
    return _preview_to_out(preview)


@router.post("/import/confirm", response_model=ConfirmResultOut)
async def confirm_import(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    """Parse xlsx, validate, then transactionally create Test + Sections + Questions."""
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .xlsx files are accepted.",
        )
    file_bytes = await file.read()
    try:
        parsed = parse_xlsx(file_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse workbook: {exc}",
        ) from exc

    preview = build_preview(parsed)
    if preview.errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": preview.errors},
        )

    try:
        # --- create Test ---
        test = Test(
            title=parsed.title,
            description=parsed.description,
            type=parsed.type,
            is_published=False,
        )
        db.add(test)
        await db.flush()
        db.add_all(settings_service.build_default_rows(test.id))

        sections_created = 0
        questions_created = 0
        listening_sections: list[ListeningSectionInfo] = []

        # Track per-kind counter for ordering
        reading_idx = 0
        listening_idx = 0

        _IELTS_MAX_LISTENING = 4
        _IELTS_MAX_READING = 3

        for sec in parsed.sections:
            # Cap to IELTS standard counts; skip excess sheets
            if sec.section_kind == "reading" and reading_idx >= _IELTS_MAX_READING:
                continue
            if sec.section_kind == "listening" and listening_idx >= _IELTS_MAX_LISTENING:
                continue

            # (section processing continues below)
            audioscript = None
            if sec.section_kind == "reading":
                reading_idx += 1
                order = 9 + reading_idx      # 10, 11, 12 — band-order
                stype = SectionType.READING
                passage = sec.passage

            elif sec.section_kind == "writing":
                order = 20                   # band-order
                stype = SectionType.WRITING
                passage = None

            else:  # listening
                listening_idx += 1
                order = listening_idx        # 1, 2, 3, 4 — band-order
                stype = SectionType.LISTENING
                passage = None
                # A2 audioscript is parsed into ParsedSection.passage; store in audioscript.
                audioscript = sec.passage

            section_obj = Section(
                test_id=test.id,
                type=stype,
                order=order,
                passage=passage,
                audioscript=audioscript,
                audio_url=None,
            )
            db.add(section_obj)
            await db.flush()
            sections_created += 1

            q_rows = _build_questions_for_section(sec)
            grouped = _group_question_rows(q_rows)
            for group_order_idx, (qtype, instruction, group_rows) in enumerate(grouped, 1):
                # Detect shared options (word bank) across the group
                all_options = [tuple(r["_options"]) for r in group_rows if r["_options"]]
                options_shared = None
                if all_options and len(set(all_options)) == 1 and all_options[0]:
                    options_shared = {"options": list(all_options[0])}

                group_obj = QuestionGroup(
                    section_id=section_obj.id,
                    order=group_order_idx,
                    question_type=qtype,
                    instruction=instruction or "",
                    options_shared=options_shared,
                )
                db.add(group_obj)
                await db.flush()

                for local_idx, qd in enumerate(group_rows, start=1):
                    clean = {
                        k: v
                        for k, v in qd.items()
                        if not k.startswith("_") and k != "group"
                    }
                    # Order is always group-local 1..N (ignore absolute Excel order).
                    clean["order"] = local_idx
                    # Extract writing-task DB columns from private keys
                    task_number = qd.get("_task_number")
                    min_words = qd.get("_min_words")
                    essay_type = qd.get("_essay_type")
                    q = Question(
                        section_id=section_obj.id,
                        question_group_id=group_obj.id,
                        task_number=task_number,
                        min_words=min_words,
                        essay_type=essay_type,
                        **clean,
                    )
                    db.add(q)
                    questions_created += 1

            if sec.section_kind == "listening":
                listening_sections.append(
                    ListeningSectionInfo(
                        id=section_obj.id,
                        name=sec.sheet_name,
                        audio_filename=sec.audio_filename,
                    )
                )

        await db.commit()

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {exc}",
        ) from exc

    return ConfirmResultOut(
        test_id=test.id,
        sections_created=sections_created,
        questions_created=questions_created,
        listening_sections=listening_sections,
    )


MAX_AUDIO_BYTES = 50 * 1024 * 1024
_ALLOWED_AUDIO_EXTS = {".mp3", ".ogg", ".mp4", ".m4a", ".wav", ".webm", ".aac"}


@router.post("/{test_id}/audio", response_model=AudioUploadOut)
async def upload_section_audio(
    test_id: uuid.UUID,
    section_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload audio for a listening section; sets section.audio_url."""
    content_type = file.content_type or ""
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if not (
        ext in _ALLOWED_AUDIO_EXTS
        or content_type.lower().startswith("audio/")
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported audio format '{ext or content_type}'. Accepted: MP3, OGG, MP4, WAV, WebM, AAC.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file.",
        )
    if len(file_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio is too large (max 50 MB).",
        )

    section = await db.get(Section, section_id)
    if section is None or section.test_id != test_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found for this test.",
        )

    url, _ = save_audio(
        file_bytes,
        content_type=content_type or "audio/mpeg",
        filename=filename,
    )

    section.audio_url = url
    await db.commit()
    return AudioUploadOut(url=url)
