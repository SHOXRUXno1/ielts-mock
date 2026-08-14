"""Per-task Writing feedback endpoint — calls Gemini immediately and returns feedback."""

import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.models.writing_feedback import WritingFeedback
from app.services.llm import evaluate_writing
from app.services.writing_presets import (
    TASK1_DEFAULT_INSTRUCTION,
    TASK2_DEFAULT_INSTRUCTIONS,
    TASK2_QUESTION_PRESETS,
    get_default_instruction,
)

logger = logging.getLogger(__name__)

# ── Per-user rate limiting (in-memory) ─────────────────────────────────────────
_user_last_request: dict[str, float] = {}
_FEEDBACK_COOLDOWN = 30  # seconds

router = APIRouter(
    prefix="/admin",
    tags=["Feedback"],
)

@router.get("/writing-presets")
async def writing_presets():
    return {
        "task_1": TASK1_DEFAULT_INSTRUCTION,
        "task_2": TASK2_DEFAULT_INSTRUCTIONS,
        "task_2_questions": TASK2_QUESTION_PRESETS,
    }


_KNOWN_ERROR_TYPES = frozenset(
    {"grammar", "lexical", "spelling", "cohesion", "punctuation"}
)

_CRITERION_KEYS = (
    "task_achievement",
    "task_response",
    "coherence_cohesion",
    "lexical_resource",
    "grammatical_range",
)


def _round_band(band: float) -> float:
    return round(band * 2) / 2


def _resolve_task_overall_band(task_data: dict) -> float | None:
    """Prefer task overall_band; if missing/0, average criterion bands.

    Returns None when no valid band data can be extracted (caller should 503).
    """
    raw = task_data.get("overall_band")
    try:
        if raw is not None:
            band = float(raw)
            if 0.5 <= band <= 9.0:
                return _round_band(band)
    except (TypeError, ValueError):
        pass

    bands: list[float] = []
    for key in _CRITERION_KEYS:
        val = task_data.get(key)
        if isinstance(val, dict) and val.get("band") is not None:
            try:
                b = float(val["band"])
                if 0.5 <= b <= 9.0:
                    bands.append(b)
            except (TypeError, ValueError):
                continue
    if not bands:
        return None
    return _round_band(sum(bands) / len(bands))


def _find_fuzzy_quote(quote: str, essay_text: str) -> str | None:
    """Try to find *quote* in *essay_text* with normalised whitespace/case.

    Returns the original-cased substring from essay_text, or None.
    """
    norm_quote = re.sub(r"\s+", " ", quote.strip().lower())
    if len(norm_quote) < 2:
        return None
    pattern = re.escape(norm_quote).replace(r"\ ", r"\s+")
    m = re.search(pattern, essay_text, re.IGNORECASE)
    return m.group(0) if m else None


def _sanitize_errors(raw: object, essay_text: str) -> list[dict]:
    """Drop junk Gemini errors that would break client-side highlighting.

    Uses fuzzy matching (normalised whitespace/case) so minor Gemini
    quotation inaccuracies don't discard otherwise valid errors.
    """
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        quote = item.get("quote")
        err_type = item.get("type")
        if not isinstance(quote, str) or len(quote) < 2:
            continue
        if not isinstance(err_type, str) or err_type not in _KNOWN_ERROR_TYPES:
            continue

        # Strict match (fast path)
        if quote in essay_text:
            resolved = quote
        else:
            resolved = _find_fuzzy_quote(quote, essay_text)
            if resolved is None:
                logger.debug("Dropped error quote (not in essay): %.50s", quote)
                continue

        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(
            {
                "quote": resolved,
                "type": err_type,
                "correction": str(item.get("correction") or ""),
                "explanation": str(item.get("explanation") or ""),
            }
        )
        if len(out) >= 12:
            break
    return out


class WritingFeedbackRequest(BaseModel):
    task: int = Field(..., ge=1, le=2, description="1 or 2")
    task_description: str | None = None
    task_statement: str | None = None
    task_question: str | None = None
    task_instruction: str | None = None
    prompt: str | None = None
    text: str
    image_url: str | None = None
    essay_type: str | None = None
    attempt_id: str | None = None

    def resolved_statement(self) -> str:
        if self.task_statement is not None:
            return self.task_statement
        if self.task_description is not None:
            return self.task_description
        return self.prompt or ""

    def resolved_question(self) -> str:
        if self.task_question is not None:
            return self.task_question
        return ""

    def resolved_description(self) -> str:
        stmt = self.resolved_statement()
        q = self.resolved_question()
        if q:
            return f"{stmt}\n\n{q}"
        return stmt

    def resolved_instruction(self) -> str:
        if self.task_instruction is not None:
            return self.task_instruction
        return ""

    def resolved_full_prompt(self) -> str:
        """Combine description + instruction for hashing and legacy callers."""
        desc = self.resolved_description()
        instr = self.resolved_instruction()
        if instr:
            return f"{desc}\n\n{instr}"
        return desc


class CriterionResult(BaseModel):
    band: float
    feedback: str


class WritingFeedbackResponse(BaseModel):
    overall_band: float
    task_achievement: CriterionResult | None = None
    coherence_cohesion: CriterionResult | None = None
    lexical_resource: CriterionResult | None = None
    grammatical_range: CriterionResult | None = None
    strengths: list[str] = []
    improvements: list[str] = []
    errors: list[dict] = []
    word_count: int


_CACHE_TTL = timedelta(hours=24)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _build_response(task_data: dict, task_num: int, essay_text: str) -> WritingFeedbackResponse:
    """Build a WritingFeedbackResponse from raw Gemini task_data."""

    def _criterion(key: str) -> CriterionResult | None:
        val = task_data.get(key)
        if isinstance(val, dict):
            return CriterionResult(
                band=float(val.get("band", 0)),
                feedback=str(val.get("feedback", "")),
            )
        return None

    if task_num == 2:
        first_criterion = _criterion("task_response") or _criterion("task_achievement")
    else:
        first_criterion = _criterion("task_achievement")

    overall = _resolve_task_overall_band(task_data)
    if overall is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI returned invalid scores. Please try again.",
        )

    return WritingFeedbackResponse(
        overall_band=overall,
        task_achievement=first_criterion,
        coherence_cohesion=_criterion("coherence_cohesion"),
        lexical_resource=_criterion("lexical_resource"),
        grammatical_range=_criterion("grammatical_range"),
        strengths=list(task_data.get("strengths", [])),
        improvements=list(task_data.get("improvements", [])),
        errors=_sanitize_errors(task_data.get("errors", []), essay_text),
        word_count=int(task_data.get("word_count", 0)),
    )


@router.post(
    "/feedback/writing",
    response_model=WritingFeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def writing_feedback(
    payload: WritingFeedbackRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    # ── Rate limiting ──────────────────────────────────────────────────────
    now = time.monotonic()
    last = _user_last_request.get(actor.sub, 0.0)
    elapsed = now - last
    if elapsed < _FEEDBACK_COOLDOWN:
        remaining = int(_FEEDBACK_COOLDOWN - elapsed)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining}s before requesting feedback again.",
        )

    # ── Input validation ───────────────────────────────────────────────────
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text must not be empty",
        )

    word_count = len(payload.text.split())
    min_required = 30 if payload.task == 1 else 50
    if word_count < min_required:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Write at least {min_required} words before requesting feedback (current: {word_count}).",
        )

    full_prompt = payload.resolved_full_prompt()
    task_description = payload.resolved_description()
    task_statement = payload.resolved_statement()
    task_question = payload.resolved_question()
    task_instruction = payload.resolved_instruction()

    # ── Cache lookup ───────────────────────────────────────────────────────
    prompt_hash = _content_hash(full_prompt)
    text_hash = _content_hash(payload.text)
    cutoff = datetime.now(timezone.utc) - _CACHE_TTL

    try:
        cached_row = await db.execute(
            select(WritingFeedback)
            .where(
                WritingFeedback.prompt_hash == prompt_hash,
                WritingFeedback.text_hash == text_hash,
                WritingFeedback.task_number == payload.task,
                WritingFeedback.created_at >= cutoff,
            )
            .order_by(WritingFeedback.created_at.desc())
            .limit(1)
        )
        cached = cached_row.scalar_one_or_none()
    except Exception:
        logger.warning("Cache lookup failed (table may not exist), skipping", exc_info=True)
        cached = None
        await db.rollback()

    if cached is not None:
        logger.info("Returning cached writing feedback %s", cached.id)
        _user_last_request[actor.sub] = time.monotonic()
        return _build_response(cached.result, payload.task, payload.text)

    # ── Call Gemini ────────────────────────────────────────────────────────
    task_key = f"task_{payload.task}"
    images = {task_key: payload.image_url} if payload.image_url else {}
    essay_types = {task_key: payload.essay_type} if payload.essay_type else None

    try:
        result = await evaluate_writing(
            answers={task_key: payload.text},
            prompts={task_key: full_prompt},
            images=images or None,
            essay_types=essay_types,
            task_descriptions={task_key: task_description},
            task_instructions={task_key: task_instruction},
            task_statements={task_key: task_statement},
            task_questions={task_key: task_question},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI evaluation failed: {exc}",
        ) from exc

    tasks = result.get("tasks", {})
    task_data = tasks.get(task_key, {})

    response = _build_response(task_data, payload.task, payload.text)

    # ── Persist to DB ──────────────────────────────────────────────────────
    try:
        attempt_uuid = None
        if payload.attempt_id:
            try:
                attempt_uuid = uuid.UUID(payload.attempt_id)
            except ValueError:
                pass

        feedback_row = WritingFeedback(
            user_id=actor.user_id,
            attempt_id=attempt_uuid,
            task_number=payload.task,
            prompt_hash=prompt_hash,
            text_hash=text_hash,
            essay_text=payload.text,
            result=task_data,
            overall_band=response.overall_band,
        )
        db.add(feedback_row)
        await db.commit()
    except Exception:
        logger.warning("Failed to persist writing feedback", exc_info=True)
        await db.rollback()

    _user_last_request[actor.sub] = time.monotonic()

    return response


# ── History endpoint ───────────────────────────────────────────────────────────

class WritingFeedbackHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_number: int
    overall_band: float
    created_at: datetime


@router.get(
    "/feedback/writing/history",
    response_model=list[WritingFeedbackHistoryItem],
)
async def writing_feedback_history(
    attempt_id: str | None = Query(default=None),
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    query = select(WritingFeedback)

    if actor.role == "student" and actor.user_id:
        query = query.where(WritingFeedback.user_id == actor.user_id)

    if attempt_id:
        try:
            query = query.where(WritingFeedback.attempt_id == uuid.UUID(attempt_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid attempt_id")

    query = query.order_by(WritingFeedback.created_at.desc()).limit(50)
    rows = await db.execute(query)
    return list(rows.scalars().all())
