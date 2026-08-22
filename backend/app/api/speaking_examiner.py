"""Speaking AI Examiner — live conversational IELTS Speaking test."""

import asyncio
import base64
import logging
import re
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_actor
from app.core.config import settings
from app.core.database import async_session, get_db
from app.models.attempt import Attempt
from app.models.section import SectionType
from app.models.section_progress import SectionProgress, SectionState
from app.models.speaking_session import SpeakingSession, SpeakingState
from app.services import section_progress as sp
from app.services import section_settings as settings_service
from app.schemas.speaking_examiner import (
    ConversationTurn,
    CriterionScore,
    ExaminerScore,
    ExaminerTurnResponse,
    NO_SPEECH_TRANSCRIPT,
    PerformanceTimings,
    PhraseResponse,
    RespondRequest,
    SaveSessionRequest,
    ScoreRequest,
    SessionIdResponse,
    SynthesizeTurnRequest,
    SynthesizeTurnResponse,
    TranscribeAndRespondResponse,
    TranscribeResponse,
)
from app.services.edge_tts_service import text_to_speech_edge
from app.services.elevenlabs_service import text_to_speech
from app.services.simli_slots import claim_slot, release_slot
from app.services.speaking_plan import (
    DEFAULT_PART1,
    SpeakingPlan,
    format_cue_card,
    load_speaking_plan,
)
from app.services.speaking_state import (
    InvalidStateTransition,
    assert_can_advance,
    http_detail_for_blocked_state,
    rounding_question,
    seconds_in_state,
    transition_state,
    PREP_MIN_SECONDS,
)
from pydantic import BaseModel
from app.services.llm import (
    evaluate_speaking_dialog,
    generate_cue_card,
    generate_examiner_turn,
    generate_part3_question,
    transcribe_audio_bytes,
)
from app.services.tts_cache import get_cached_tts, set_cached_tts

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/speaking-examiner",
    tags=["Speaking Examiner"],
)

_TAG_RE = re.compile(r"\s*\[PART:\d+\]\s*")
_END_RE = re.compile(r"\s*\[END_OF_TEST\]\s*")
_PART_RE = re.compile(r"\[PART:(\d+)\]")
_CUE_CARD_LEGACY_RE = re.compile(r"\[CUE_CARD\](.*?)\[/CUE_CARD\]", re.DOTALL)
_CUE_TOPIC_RE = re.compile(
    r"((?:Describe|Talk about)\b.+)",
    re.DOTALL | re.IGNORECASE,
)

PART2_CUE_INTRO = "Here is your topic card."
PART2_BEGIN_SPEAKING = "Your preparation time is over. Please begin speaking."

INTRO_GREETING = (
    "Good morning. My name is James. Can you tell me your full name, please?"
)
INTRO_NICKNAME_Q = "Thank you. And what should I call you?"
INTRO_FRAME = (
    "Alright, {nickname}. Now, in this first part, I'd like to ask you "
    "some questions about yourself."
)
INTRO_FRAME_NO_NAME = (
    "Alright. Now, in this first part, I'd like to ask you "
    "some questions about yourself."
)

# Legacy session-less Gemini path only (/respond without session_id).
# Live sessions use SpeakingPlan lengths + current_question_index instead.
_LEGACY_QUESTIONS_PER_PART: dict[int, int] = {1: 5, 2: 1, 3: 4}
# Backward-compatible alias for any external imports / tests.
QUESTIONS_PER_PART = _LEGACY_QUESTIONS_PER_PART
MAX_EXAMINER_TURNS = 15
FORCED_END_TEXT = "That is the end of the speaking test. Thank you very much."
PART3_TRANSITION = (
    "Now let's talk about some more general questions related to this."
)
MAX_TRANSCRIBE_BYTES = 10 * 1024 * 1024
ALLOWED_TRANSCRIBE_CONTENT_TYPES = frozenset({
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "application/octet-stream",
})

REACTIONS = (
    "Thank you.",
    "I see.",
    "Alright.",
    "OK.",
    "That's interesting.",
)

_NICK_FILLER_RE = re.compile(
    r"^(you can |please |just |my friends )?call me |^my name is |^i'?m ",
    re.IGNORECASE,
)


def _normalize_audio_content_type(content_type: str | None) -> str | None:
    """Strip codec params — browsers send e.g. audio/webm;codecs=opus."""
    if not content_type:
        return None
    return content_type.split(";", 1)[0].strip().lower()


def _is_allowed_transcribe_type(content_type: str | None) -> bool:
    if not content_type:
        return True
    if content_type in ALLOWED_TRANSCRIBE_CONTENT_TYPES:
        return True
    normalized = _normalize_audio_content_type(content_type)
    return normalized in ALLOWED_TRANSCRIBE_CONTENT_TYPES if normalized else False


def _parse_http_error_body(response: httpx.Response) -> str | None:
    """Extract a client-safe message from an API error response body."""
    try:
        data = response.json()
    except Exception:
        return None
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
        if data.get("detail"):
            detail = data["detail"]
            if isinstance(detail, str):
                return detail
            if isinstance(detail, list) and detail:
                first = detail[0]
                if isinstance(first, dict) and first.get("msg"):
                    return str(first["msg"])
        if data.get("message"):
            return str(data["message"])
    return None


def _gemini_error_detail(exc: Exception) -> str:
    """Return a client-safe error message without leaking API keys."""
    if isinstance(exc, httpx.HTTPStatusError):
        body_msg = _parse_http_error_body(exc.response)
        status = exc.response.status_code
        if status == 429:
            return body_msg or "Gemini rate limit exceeded — try again in a minute"
        if status == 503:
            return body_msg or "Gemini is temporarily overloaded — try again in a few seconds"
        if status == 400:
            return body_msg or "Invalid AI request — please try again"
        return body_msg or f"AI service unavailable (HTTP {status})"
    return f"AI service unavailable: {type(exc).__name__}"


def _groq_error_detail(exc: Exception) -> str:
    """Return a client-safe Groq/Whisper error message."""
    if isinstance(exc, httpx.HTTPStatusError):
        body_msg = _parse_http_error_body(exc.response)
        status = exc.response.status_code
        if status == 429:
            return body_msg or "Transcription rate limit exceeded — try again in a minute"
        if status == 400:
            return body_msg or "Could not transcribe audio — try recording again"
        if status in (401, 403):
            return (
                body_msg
                or "Speech recognition is unavailable — try Start again in a moment"
            )
        return body_msg or f"Transcription failed (HTTP {status})"
    return "Transcription failed — try speaking again"


def _upstream_error_detail(exc: Exception) -> str:
    """Pick Groq vs Gemini wording based on the failed request URL."""
    if isinstance(exc, httpx.HTTPStatusError):
        url = str(exc.request.url)
        if "groq.com" in url:
            return _groq_error_detail(exc)
    return _gemini_error_detail(exc)


def _simli_credits_response(resp: httpx.Response) -> dict | None:
    """Simli returns 402 when free credits are exhausted."""
    if resp.status_code != 402:
        return None
    try:
        data = resp.json()
    except Exception:
        data = {}
    detail = (
        data.get("detail")
        or "Simli free credits are used up — upgrade at https://app.simli.com"
    )
    return {
        "enabled": False,
        "reason": "simli_credits_exhausted",
        "detail": detail,
    }


class _SimliCreditsError(Exception):
    def __init__(self, payload: dict):
        self.payload = payload


def _simli_error_response(exc: Exception) -> dict:
    """Return a structured, client-safe Simli failure payload."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        body_snippet = (exc.response.text or "")[:200]
        logger.error("Simli API HTTP %s: %s", status, body_snippet)
        credits_resp = _simli_credits_response(exc.response)
        if credits_resp:
            return credits_resp
        if status == 401:
            detail = "Invalid Simli API key"
        elif status == 403:
            detail = "Simli API access denied"
        else:
            detail = f"Simli API error (HTTP {status})"
        return {"enabled": False, "reason": "simli_api_error", "detail": detail}

    if isinstance(exc, httpx.TimeoutException):
        logger.error("Simli API timed out")
        return {
            "enabled": False,
            "reason": "simli_api_error",
            "detail": "Simli API timed out",
        }

    logger.exception("Simli token request failed")
    return {
        "enabled": False,
        "reason": "simli_api_error",
        "detail": f"Simli connection failed: {type(exc).__name__}",
    }


def _extract_cue_card(text: str) -> str | None:
    legacy = _CUE_CARD_LEGACY_RE.search(text)
    if legacy:
        return legacy.group(1).strip()

    match = _CUE_TOPIC_RE.search(text)
    if not match:
        return None

    topic = match.group(1).strip()
    topic = _TAG_RE.sub("", topic)
    topic = _END_RE.sub("", topic).strip()
    return topic or None


def _parse_tags(raw: str) -> tuple[str, int, bool, str | None]:
    """Strip hidden tags from examiner output.

    Returns (clean_text, part_number, is_end, cue_card).
    """
    is_end = bool(_END_RE.search(raw))

    part_match = _PART_RE.search(raw)
    part = int(part_match.group(1)) if part_match else 1

    without_legacy = _CUE_CARD_LEGACY_RE.sub("", raw)
    clean = _TAG_RE.sub("", without_legacy)
    clean = _END_RE.sub("", clean).strip()

    cue_card = _extract_cue_card(raw) if part == 2 else None

    return clean, part, is_end, cue_card


def _is_intro_turn(turn: dict) -> bool:
    return turn.get("phase") == "intro"


def _history_turn(role: str, text: str, phase: str | None = None) -> dict:
    turn: dict = {"role": role, "text": text}
    if phase:
        turn["phase"] = phase
    return turn


def _extract_nickname(text: str) -> str:
    """Pull a short preferred name from the candidate's nickname reply."""
    cleaned = _NICK_FILLER_RE.sub("", (text or "").strip()).strip(" .,!?'\"")
    if not cleaned:
        return ""
    first = cleaned.split()[0]
    return (first or cleaned)[:30].capitalize()


def _intro_frame(nickname: str) -> str:
    if nickname:
        return INTRO_FRAME.format(nickname=nickname)
    return INTRO_FRAME_NO_NAME


def _format_intro_to_part1(nickname: str, first_question: str = "") -> str:
    """Intro frame optionally followed by Part 1 Q1 (server-driven)."""
    frame = _intro_frame(nickname)
    q = (first_question or "").strip()
    return f"{frame} {q}".strip() if q else frame


def _reaction(index: int) -> str:
    return REACTIONS[index % len(REACTIONS)]


def _phase_count(history: list[dict], phase: str) -> int:
    return sum(
        1
        for t in history
        if t.get("role") == "examiner" and t.get("phase") == phase
    )


def _non_intro_examiner_count(history: list[dict]) -> int:
    return sum(
        1
        for t in history
        if t.get("role") == "examiner" and not _is_intro_turn(t)
    )


def strip_intro(history: list[dict]) -> list[dict]:
    """Remove INTRO turns from history for scoring / flow stats.

    Prefer explicit ``phase: intro`` markers; fall back to positional strip
    when the client history has no phase metadata but starts with GREETING.
    """
    if any(t.get("phase") == "intro" for t in history):
        return [t for t in history if t.get("phase") != "intro"]
    if history and (history[0].get("text") or "").strip() == INTRO_GREETING:
        return history[4:]
    return history


def count_questions_by_part(history: list[dict]) -> dict:
    """Count examiner turns per part and derive current flow position."""
    part1_count = 0
    part2_count = 0
    part3_count = 0
    current_part = 1

    for turn in history:
        if _is_intro_turn(turn):
            continue
        if turn["role"] == "examiner":
            if current_part == 1:
                part1_count += 1
            elif current_part == 2:
                part2_count += 1
            elif current_part == 3:
                part3_count += 1

        if part1_count >= _LEGACY_QUESTIONS_PER_PART[1] and current_part == 1:
            current_part = 2
        if part2_count >= 2 and current_part == 2:
            current_part = 3

    return {
        "part1": part1_count,
        "part2": part2_count,
        "part3": part3_count,
        "current_part": current_part,
        "should_end": (
            current_part == 3
            and part2_count >= 2
            and part3_count >= _LEGACY_QUESTIONS_PER_PART[3] - 1
        ),
    }


def _build_extra_instructions(counts: dict) -> str:
    if counts["should_end"]:
        return f"""
END THE TEST NOW. Say exactly:
'{FORCED_END_TEXT}'
Add [END_OF_TEST] tag. Do NOT ask any more questions.
"""

    if (
        counts["current_part"] == 3
        and counts["part3"] >= _LEGACY_QUESTIONS_PER_PART[3] - 2
    ):
        return """
IMPORTANT: This is the LAST question of the test. After the
candidate answers, say exactly:
'That is the end of the speaking test. Thank you very much.'
Add [END_OF_TEST] tag. Do NOT ask any more questions.
"""

    if counts["current_part"] == 2 and counts["part2"] >= 1:
        return """
IMPORTANT: The candidate has finished their Part 2 monologue.
Say 'Thank you.' and immediately move to Part 3.
Ask the first abstract discussion question related to the Part 2 topic.
Add [PART:3] tag.
"""

    if counts["current_part"] == 2 and counts["part2"] == 0:
        return """
IMPORTANT: Part 1 is complete. Move to Part 2 now.
Give a cue card topic in the format:
Describe [topic]. You should say:
- [point 1]
- [point 2]
- [point 3]
and explain [final point].
Add [PART:2] tag.
"""

    if counts["current_part"] == 1 and counts["part1"] >= QUESTIONS_PER_PART[1] - 1:
        return """
IMPORTANT: This is the LAST Part 1 question. Ask one more personal
introduction question. Add [PART:1] tag. Do NOT move to Part 2 yet.
"""

    return ""


def _question_number_for_part3(counts: dict) -> int:
    """Part 3 Q1 is on the thank-you turn; counter tracks Q2–Q4."""
    part3 = counts["part3"]
    if part3 >= QUESTIONS_PER_PART[3] - 2:
        return QUESTIONS_PER_PART[3]
    return part3 + 2


def _next_turn_metadata(counts: dict) -> tuple[int, bool, int]:
    """Server-authoritative part, is_end, and question_number for the next turn."""
    if counts["should_end"]:
        return 3, True, QUESTIONS_PER_PART[3]

    current_part = counts["current_part"]
    part1 = counts["part1"]
    part2 = counts["part2"]

    if current_part == 2 and part2 >= 1:
        return 3, False, 1

    if current_part == 2 and part2 == 0:
        return 2, False, 1

    if current_part == 1:
        return 1, False, min(part1 + 1, QUESTIONS_PER_PART[1])

    if current_part == 3:
        return 3, False, _question_number_for_part3(counts)

    return current_part, False, 1


def _resolve_server_metadata(
    counts: dict,
    parsed_is_end: bool,
    cue_card: str | None,
) -> tuple[int, bool, int, str | None]:
    part, is_end, question_number = _next_turn_metadata(counts)

    if parsed_is_end or counts["should_end"]:
        is_end = True

    if part != 2 or counts["part2"] != 0:
        cue_card = None

    return part, is_end, question_number, cue_card


async def _forced_end_payload(counts: dict) -> dict:
    audio_b64, tts_error, cache_hit = await _tts_base64(FORCED_END_TEXT)
    return _examiner_turn_payload(
        FORCED_END_TEXT,
        3,
        True,
        None,
        audio_b64,
        min(counts["part3"], QUESTIONS_PER_PART[3]),
        tts_error=tts_error,
        timings=PerformanceTimings(tts_cache_hit=cache_hit),
    )


def _question_number_for_start() -> int:
    return 1


def _examiner_turn_payload(
    clean_text: str,
    part: int,
    is_end: bool,
    cue_card: str | None,
    audio_b64: str,
    question_number: int,
    session_id: str | None = None,
    tts_error: str | None = None,
    timings: PerformanceTimings | None = None,
    questions_total: int | None = None,
) -> dict:
    payload = {
        "text": clean_text,
        "audio_base64": audio_b64,
        "part": part,
        "is_end": is_end,
        "cue_card": cue_card,
        "question_number": question_number,
    }
    if questions_total is not None:
        payload["questions_total"] = questions_total
    if session_id:
        payload["session_id"] = session_id
    if tts_error:
        payload["tts_error"] = tts_error
    if timings is not None:
        payload["timings"] = timings.model_dump(exclude_none=True)
    return payload


async def _tts_base64(text: str) -> tuple[str, str | None, bool]:
    """Generate TTS audio and return (base64, error, cache_hit).

    Tries ElevenLabs first; falls back to Edge TTS if ElevenLabs fails.
    Never raises — /start must still return a turn if TTS dies.
    """
    try:
        return await _tts_base64_inner(text)
    except Exception:
        logger.exception("TTS pipeline crashed — returning empty audio")
        return "", "TTS failed", False


async def _tts_base64_inner(text: str) -> tuple[str, str | None, bool]:
    cached = get_cached_tts(text)
    if cached is not None:
        return cached, None, True

    t0 = time.perf_counter()
    result = await text_to_speech(text)
    tts_ms = int((time.perf_counter() - t0) * 1000)
    voice_prefix = settings.elevenlabs_voice_id[:8]

    if result.ok:
        logger.info(
            "ElevenLabs OK voice=%s bytes=%d tts_ms=%d",
            voice_prefix,
            len(result.audio),
            tts_ms,
        )
        encoded = base64.b64encode(result.audio).decode()
        set_cached_tts(text, encoded)
        return encoded, None, False

    # ElevenLabs failed — try Edge TTS fallback
    logger.warning(
        "TTS: ElevenLabs failed voice=%s error=%s tts_ms=%d — trying Edge TTS fallback",
        voice_prefix,
        result.error,
        tts_ms,
    )
    t1 = time.perf_counter()
    edge_audio = await text_to_speech_edge(text)
    edge_ms = int((time.perf_counter() - t1) * 1000)

    if edge_audio:
        logger.info("TTS: Edge TTS fallback OK bytes=%d edge_ms=%d", len(edge_audio), edge_ms)
        encoded = base64.b64encode(edge_audio).decode()
        set_cached_tts(text, encoded)
        return encoded, None, False

    logger.error("TTS: both ElevenLabs and Edge TTS failed — returning empty audio")
    return "", result.error, False


async def _tts_for_turn(
    clean_text: str,
    part: int,
    cue_card: str | None,
) -> tuple[str, str | None, bool]:
    if part == 2 and cue_card:
        return await _tts_base64(PART2_CUE_INTRO)
    return await _tts_base64(clean_text)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _get_live_session(
    session_id: uuid.UUID,
    actor_sub: str,
    db: AsyncSession,
    *,
    for_update: bool = False,
) -> SpeakingSession | None:
    stmt = select(SpeakingSession).where(
        SpeakingSession.id == session_id,
        SpeakingSession.admin_email == actor_sub,
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _raise_if_session_not_advanceable(session: SpeakingSession) -> None:
    """HTTP guard before advancing a live session turn."""
    state = session.current_state
    if state in (
        SpeakingState.ENDED.value,
        SpeakingState.ABANDONED.value,
        SpeakingState.SCORING.value,
    ):
        status, detail = http_detail_for_blocked_state(state)
        raise HTTPException(status_code=status, detail=detail)


async def _persist_live_history(
    session: SpeakingSession,
    history: list[dict],
    db: AsyncSession,
) -> None:
    session.history_json = history
    await db.commit()


async def _persist_live_history_background(
    session_id: uuid.UUID,
    history: list[dict],
    admin_email: str,
) -> None:
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(SpeakingSession).where(
                        SpeakingSession.id == session_id,
                        SpeakingSession.admin_email == admin_email,
                    )
                )
                session = result.scalar_one_or_none()
                if session is None:
                    return
                session.history_json = history
                await db.commit()
            return
        except Exception:
            if attempt >= max_attempts - 1:
                logger.exception(
                    "Background history persist failed session_id=%s after %d attempts",
                    session_id,
                    max_attempts,
                )
            else:
                await asyncio.sleep(0.5 * (attempt + 1))


async def _read_transcribe_blob(file: UploadFile) -> tuple[bytes | None, JSONResponse | None]:
    if not _is_allowed_transcribe_type(file.content_type):
        return None, JSONResponse(
            status_code=400,
            content={"detail": "Unsupported audio format"},
        )
    contents = await file.read()
    if len(contents) < 1024:
        return None, JSONResponse(
            status_code=400,
            content={"detail": "Recording too short"},
        )
    if len(contents) > MAX_TRANSCRIBE_BYTES:
        return None, JSONResponse(
            status_code=400,
            content={"detail": "Recording too large"},
        )
    return contents, None


@router.get("/part2-begin-phrase", response_model=PhraseResponse)
async def part2_begin_phrase(_actor: Actor = Depends(get_current_actor)):
    """Cached TTS for the Part 2 preparation end cue."""
    audio_b64, tts_error, _cache_hit = await _tts_base64(PART2_BEGIN_SPEAKING)
    return PhraseResponse(
        text=PART2_BEGIN_SPEAKING,
        audio_base64=audio_b64,
        tts_error=tts_error,
    )


@router.get("/intro-greeting-phrase", response_model=PhraseResponse)
async def intro_greeting_phrase(_actor: Actor = Depends(get_current_actor)):
    """Cached TTS for the examiner intro greeting.

    Called from the pre-Speaking readiness gate to warm the TTS cache so the
    first turn of /start hits a cache entry and plays without a synth delay.
    Never creates or advances any session; safe to call any number of times.
    """
    audio_b64, tts_error, _cache_hit = await _tts_base64(INTRO_GREETING)
    return PhraseResponse(
        text=INTRO_GREETING,
        audio_base64=audio_b64,
        tts_error=tts_error,
    )


async def _create_start_session(
    admin_email: str,
    *,
    attempt_id: uuid.UUID | None = None,
    test_id: uuid.UUID | None = None,
) -> SpeakingSession:
    async with async_session() as db:
        started_at = datetime.now(timezone.utc)
        session = SpeakingSession(
            admin_email=admin_email,
            started_at=started_at,
            status="in_progress",
            current_state=SpeakingState.INTRO_GREETING.value,
            state_entered_at=started_at,
            current_question_index=0,
            history_json=[_history_turn("examiner", INTRO_GREETING, "intro")],
            attempt_id=attempt_id,
            test_id=test_id,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session


def _cue_topic_hint(plan: SpeakingPlan, history: list[dict]) -> str:
    if plan.cue_card is not None:
        return plan.cue_card.topic
    for turn in reversed(history):
        if turn.get("role") == "examiner" and turn.get("phase") == "part2":
            text = turn.get("text") or ""
            match = _CUE_TOPIC_RE.search(text)
            if match:
                return match.group(1).strip()[:120]
    return ""


async def _issue_cue_card(plan: SpeakingPlan) -> tuple[str, str]:
    """Return (spoken_or_display_text, cue_card_field). Authored = no Gemini."""
    if plan.cue_card is not None:
        text = format_cue_card(plan.cue_card)
        return text, text
    raw = await generate_cue_card()
    clean, _, _, _ = _parse_tags(raw)
    cue = _extract_cue_card(raw) or clean
    return clean or cue, cue


async def _part3_question(
    plan: SpeakingPlan,
    history: list[dict],
    idx: int,
) -> str:
    if plan.part3_authored and idx < len(plan.part3):
        return plan.part3[idx]
    topic = _cue_topic_hint(plan, history)
    raw = await generate_part3_question(
        history,
        cue_topic=topic,
        question_index=idx,
    )
    clean, _, _, _ = _parse_tags(raw)
    return clean.strip() or "What are the advantages and disadvantages of this?"


async def _advance_turn(
    session: SpeakingSession,
    candidate_text: str,
    plan: SpeakingPlan,
    db: AsyncSession,
    *,
    include_tts: bool,
) -> dict:
    """Server-driven next examiner turn using current_state + question index."""
    history = list(session.history_json or [])
    state = session.current_state
    idx = int(getattr(session, "current_question_index", 0) or 0)
    part1_questions = plan.part1 or list(DEFAULT_PART1)

    text = FORCED_END_TEXT
    exam_phase = "end"
    cand_phase: str | None = None
    part = 3
    is_end = False
    cue_card: str | None = None
    question_number = 1
    questions_total: int | None = None

    if _non_intro_examiner_count(history) >= MAX_EXAMINER_TURNS:
        text = FORCED_END_TEXT
        transition_state(session, SpeakingState.ENDED)
        exam_phase = "end"
        part = 3
        is_end = True
        cand_phase = None
    elif state == SpeakingState.INTRO_GREETING.value:
        text = INTRO_NICKNAME_Q
        transition_state(session, SpeakingState.INTRO_NICKNAME)
        exam_phase = "intro"
        cand_phase = "intro"
        part = 1
        question_number = 1
        questions_total = len(part1_questions)
    elif state == SpeakingState.INTRO_NICKNAME.value:
        nickname = _extract_nickname(candidate_text)
        session.candidate_nickname = nickname or None
        first_q = part1_questions[0]
        text = _format_intro_to_part1(nickname, first_q)
        transition_state(session, SpeakingState.PART_1_ACTIVE)
        session.current_question_index = 1  # Q1 already asked
        exam_phase = "part1"
        cand_phase = "intro"
        part = 1
        question_number = 1
        questions_total = len(part1_questions)
    elif state == SpeakingState.PART_1_ACTIVE.value:
        cand_phase = "part1"
        if idx < len(part1_questions):
            text = f"{_reaction(idx)} {part1_questions[idx]}"
            session.current_question_index = idx + 1
            exam_phase = "part1"
            part = 1
            question_number = idx + 1
            questions_total = len(part1_questions)
        else:
            text, cue_card = await _issue_cue_card(plan)
            transition_state(session, SpeakingState.PART_2_PREP)
            exam_phase = "part2"
            part = 2
            question_number = 1
            questions_total = 1
    elif state in (
        SpeakingState.PART_2_PREP.value,
        SpeakingState.PART_2_CUE.value,
        SpeakingState.PART_2_TALK.value,
    ):
        elapsed = seconds_in_state(session)
        if elapsed < PREP_MIN_SECONDS:
            logger.warning(
                "Session %s: monologue submitted after %.1fs of prep (min=%s)",
                session.id,
                elapsed,
                PREP_MIN_SECONDS,
            )
        rq = rounding_question(session)
        text = f"Thank you. {rq}"
        transition_state(session, SpeakingState.PART_2_ROUNDING)
        exam_phase = "part2"
        cand_phase = "part2"
        part = 2
        cue_card = None
        question_number = 1
        questions_total = 1
    elif state == SpeakingState.PART_2_ROUNDING.value:
        q = await _part3_question(plan, history, 0)
        text = f"{PART3_TRANSITION} {q}"
        transition_state(session, SpeakingState.PART_3_ACTIVE)
        session.current_question_index = 1
        exam_phase = "part3"
        cand_phase = "part2"
        part = 3
        question_number = 1
        questions_total = plan.part3_target
    elif state == SpeakingState.PART_3_ACTIVE.value:
        cand_phase = "part3"
        target = plan.part3_target
        if idx < target:
            q = await _part3_question(plan, history, idx)
            text = f"{_reaction(idx)} {q}"
            session.current_question_index = idx + 1
            exam_phase = "part3"
            part = 3
            question_number = idx + 1
            questions_total = target
        else:
            text = FORCED_END_TEXT
            transition_state(session, SpeakingState.ENDED)
            exam_phase = "end"
            part = 3
            is_end = True
            question_number = target
            questions_total = target
    else:
        assert_can_advance(session)
        raise InvalidStateTransition(f"Cannot advance from {state}")

    history.append(_history_turn("candidate", candidate_text, cand_phase))
    history.append(_history_turn("examiner", text, exam_phase))
    session.history_json = history
    if is_end:
        session.status = "completed"
        if session.finished_at is None:
            session.finished_at = datetime.now(timezone.utc)
        await _seal_speaking_progress(db, session.attempt_id)
    # Commit before TTS so row lock is not held during synthesis.
    await db.commit()

    audio_b64 = ""
    tts_error: str | None = None
    cache_hit: bool | None = None
    tts_ms = 0
    if include_tts:
        t1 = time.perf_counter()
        audio_b64, tts_error, cache_hit = await _tts_for_turn(text, part, cue_card)
        tts_ms = int((time.perf_counter() - t1) * 1000)

    logger.info(
        "Examiner turn state=%s -> %s part=%s q=%s/%s end=%s tts_ms=%s",
        state,
        session.current_state,
        part,
        question_number,
        questions_total,
        is_end,
        tts_ms if include_tts else None,
    )

    return _examiner_turn_payload(
        text,
        part,
        is_end,
        cue_card,
        audio_b64,
        question_number,
        session_id=str(session.id),
        tts_error=tts_error,
        timings=PerformanceTimings(
            tts_ms=tts_ms if include_tts else None,
            tts_cache_hit=cache_hit,
            history_turns=len(history),
        ),
        questions_total=questions_total,
    )


async def _handle_intro_turn(
    session: SpeakingSession,
    candidate_text: str,
    db: AsyncSession,
    *,
    include_tts: bool,
    plan: SpeakingPlan | None = None,
) -> dict | None:
    """Backward-compatible INTRO-only helper for unit tests."""
    if session.current_state not in (
        SpeakingState.INTRO_GREETING.value,
        SpeakingState.INTRO_NICKNAME.value,
    ):
        return None
    return await _advance_turn(
        session,
        candidate_text,
        plan or SpeakingPlan(
            part1=["Do you work or are you a student?"],
            cue_card=None,
            part3=[],
            part1_authored=False,
            part3_authored=False,
            cue_card_authored=False,
        ),
        db,
        include_tts=include_tts,
    )


class StartRequest(BaseModel):
    attempt_id: uuid.UUID | None = None


async def _enter_speaking_progress(
    db: AsyncSession,
    attempt: Attempt,
) -> None:
    """Mark speaking SectionProgress ACTIVE when a speaking session starts."""
    now = datetime.now(timezone.utc)
    rows_result = await db.execute(
        select(SectionProgress).where(SectionProgress.attempt_id == attempt.id)
    )
    rows = list(rows_result.scalars().all())
    if not any(r.section_type == SectionType.SPEAKING.value for r in rows):
        rows.append(
            SectionProgress(
                attempt_id=attempt.id,
                section_type=SectionType.SPEAKING.value,
                state=SectionState.NOT_STARTED.value,
            )
        )
        db.add(rows[-1])
        await db.flush()

    settings = await settings_service.ensure_settings(db, attempt.test_id)
    # Speaking may start after prior skills; pass present from progress rows
    # so orphan types not in the attempt still don't block incorrectly.
    try:
        sp.apply_enter(
            rows,
            settings,
            SectionType.SPEAKING.value,
            now,
            present_types=sp.TYPE_ORDER,
        )
    except sp.SectionConflictError:
        # Already sealed or prior sections incomplete — leave as-is.
        return
    except sp.SectionProgressError:
        return


async def _seal_speaking_progress(
    db: AsyncSession,
    attempt_id: uuid.UUID | None,
) -> None:
    """Seal speaking SectionProgress when the AI session ends."""
    if attempt_id is None:
        return
    now = datetime.now(timezone.utc)
    rows_result = await db.execute(
        select(SectionProgress).where(
            SectionProgress.attempt_id == attempt_id,
            SectionProgress.section_type == SectionType.SPEAKING.value,
        )
    )
    row = rows_result.scalar_one_or_none()
    if row is None:
        return
    state = row.state if isinstance(row.state, str) else row.state.value
    if state == SectionState.SEALED.value:
        return
    sp.apply_seal(row, sp.SEAL_REASON_MANUAL, now)


@router.post("/start", response_model=ExaminerTurnResponse)
async def start_session(
    req: StartRequest | None = None,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Start a new speaking examiner session — returns hardcoded INTRO greeting."""
    t0 = time.perf_counter()
    body = req or StartRequest()
    attempt_id = body.attempt_id
    test_id: uuid.UUID | None = None

    if attempt_id is not None:
        attempt = await db.get(Attempt, attempt_id)
        if attempt is None:
            raise HTTPException(status_code=404, detail="Attempt not found")
        if _actor.role == "student" and attempt.user_id != _actor.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        test_id = attempt.test_id
        # Transition attempt to speaking_in_progress when starting from auto_scored
        from app.models.attempt import AttemptStatus as _AS
        if attempt.status == _AS.AUTO_SCORED:
            attempt.status = _AS.SPEAKING_IN_PROGRESS
        await _enter_speaking_progress(db, attempt)
        await db.flush()

    t1 = time.perf_counter()
    tts_task = asyncio.create_task(_tts_base64(INTRO_GREETING))
    session_task = asyncio.create_task(
        _create_start_session(
            _actor.sub,
            attempt_id=attempt_id,
            test_id=test_id,
        )
    )
    audio_b64, tts_error, cache_hit = await tts_task
    session = await session_task
    tts_ms = int((time.perf_counter() - t1) * 1000)
    total_ms = int((time.perf_counter() - t0) * 1000)

    logger.info(
        "Examiner /start tts_ms=%d total_ms=%d text_len=%d part=1 session_id=%s "
        "cache_hit=%s attempt_id=%s test_id=%s state=%s",
        tts_ms,
        total_ms,
        len(INTRO_GREETING),
        session.id,
        cache_hit,
        attempt_id,
        test_id,
        session.current_state,
    )

    return _examiner_turn_payload(
        INTRO_GREETING,
        1,
        False,
        None,
        audio_b64,
        _question_number_for_start(),
        session_id=str(session.id),
        tts_error=tts_error,
        timings=PerformanceTimings(
            tts_ms=tts_ms,
            tts_cache_hit=cache_hit,
        ),
    )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_recording(file: UploadFile, _actor: Actor = Depends(get_current_actor)):
    """Transcribe candidate's audio recording via Groq Whisper (lenient mode)."""
    try:
        contents, error_resp = await _read_transcribe_blob(file)
        if error_resp is not None:
            return error_resp
        assert contents is not None
        transcript = await transcribe_audio_bytes(
            contents,
            content_type=file.content_type,
        )
        if not transcript.strip():
            transcript = NO_SPEECH_TRANSCRIPT
        return TranscribeResponse(transcript=transcript)
    except Exception as e:
        logger.exception("Failed to transcribe audio")
        return JSONResponse(
            status_code=502,
            content={"detail": _upstream_error_detail(e)},
        )


async def _generate_examiner_response(
    candidate_text: str,
    history: list[dict],
    *,
    include_tts: bool = True,
    test_context: str | None = None,
) -> tuple[dict, PerformanceTimings, list[dict]]:
    """Core respond logic shared by /respond and /transcribe-and-respond."""
    counts = count_questions_by_part(history)
    total_examiner_turns = sum(
        1 for t in history if t["role"] == "examiner" and not _is_intro_turn(t)
    )

    if total_examiner_turns >= MAX_EXAMINER_TURNS:
        logger.info(
            "Speaking flow: forced end at max turns total=%d",
            total_examiner_turns,
        )
        payload = await _forced_end_payload(counts)
        candidate_turn = {"role": "candidate", "text": candidate_text}
        examiner_turn = {"role": "examiner", "text": payload["text"]}
        updated_history = history + [candidate_turn, examiner_turn]
        timings = PerformanceTimings(history_turns=len(history))
        if payload.get("timings"):
            timings = PerformanceTimings(**payload["timings"])
        return payload, timings, updated_history

    flow_instructions = _build_extra_instructions(counts)
    # When Part 2 cue card is about to be issued and we have authored content,
    # reinforce using the test cue card rather than inventing one.
    if (
        test_context
        and counts["current_part"] == 2
        and counts["part2"] == 0
        and "PART 2 CUE CARD" in test_context
    ):
        flow_instructions = (
            f"{flow_instructions}\n\n"
            "Use the PART 2 CUE CARD from the test-specific questions exactly."
        ).strip()

    extra_parts = [p for p in (test_context, flow_instructions) if p]
    extra_instructions = "\n\n".join(extra_parts) if extra_parts else ""

    logger.info(
        "Speaking flow: part=%s p1=%s p2=%s p3=%s total=%s directive=%s has_context=%s",
        counts["current_part"],
        counts["part1"],
        counts["part2"],
        counts["part3"],
        total_examiner_turns,
        "YES" if flow_instructions else "NO",
        bool(test_context),
    )

    t0 = time.perf_counter()
    raw = await generate_examiner_turn(history, candidate_text, extra_instructions)
    gemini_ms = int((time.perf_counter() - t0) * 1000)

    clean_text, _, parsed_is_end, _ = _parse_tags(raw)
    cue_card = (
        _extract_cue_card(raw)
        if counts["current_part"] == 2 and counts["part2"] == 0
        else None
    )
    part, is_end, question_number, cue_card = _resolve_server_metadata(
        counts,
        parsed_is_end,
        cue_card,
    )

    audio_b64 = ""
    tts_error: str | None = None
    tts_ms = 0
    cache_hit: bool | None = None
    if include_tts:
        t1 = time.perf_counter()
        audio_b64, tts_error, cache_hit = await _tts_for_turn(clean_text, part, cue_card)
        tts_ms = int((time.perf_counter() - t1) * 1000)

    candidate_turn = {"role": "candidate", "text": candidate_text}
    examiner_turn = {"role": "examiner", "text": clean_text}
    updated_history = history + [candidate_turn, examiner_turn]

    timings = PerformanceTimings(
        gemini_ms=gemini_ms,
        tts_ms=tts_ms if include_tts else None,
        history_turns=len(history),
        tts_cache_hit=cache_hit,
    )

    payload = _examiner_turn_payload(
        clean_text,
        part,
        is_end,
        cue_card,
        audio_b64,
        question_number,
        tts_error=tts_error,
        timings=timings,
    )
    return payload, timings, updated_history


@router.post("/respond", response_model=ExaminerTurnResponse)
async def respond_to_candidate(
    req: RespondRequest,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Generate next examiner turn given candidate's response + history."""
    t0 = time.perf_counter()
    live_session: SpeakingSession | None = None
    if req.session_id:
        live_session = await _get_live_session(
            req.session_id, _actor.sub, db, for_update=True
        )
        if not live_session:
            raise HTTPException(status_code=404, detail="Session not found")
        _raise_if_session_not_advanceable(live_session)
        history = list(live_session.history_json or [])
    else:
        history = [t.model_dump() for t in req.conversation_history]

    # Live sessions use the server-driven question engine.
    if live_session is not None:
        try:
            plan = await load_speaking_plan(live_session.test_id, db)
            return await _advance_turn(
                live_session,
                req.candidate_text,
                plan,
                db,
                include_tts=True,
            )
        except InvalidStateTransition as e:
            status, detail = http_detail_for_blocked_state(
                live_session.current_state
            )
            raise HTTPException(status_code=status, detail=detail) from e
        except Exception as e:
            logger.exception("Failed to advance server-driven examiner turn")
            return JSONResponse(
                status_code=502,
                content={"detail": _gemini_error_detail(e)},
            )

    # Legacy session-less path (admin debug / unit tests without session_id)
    try:
        payload, timings, _updated_history = await _generate_examiner_response(
            req.candidate_text,
            history,
            include_tts=True,
            test_context=None,
        )
    except Exception as e:
        logger.exception("Failed to generate examiner response")
        return JSONResponse(
            status_code=502,
            content={"detail": _gemini_error_detail(e)},
        )

    total_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(
        "Examiner /respond (session-less) total_ms=%d gemini_ms=%s tts_ms=%s turns=%s",
        total_ms,
        timings.gemini_ms,
        timings.tts_ms,
        timings.history_turns,
    )
    return payload


@router.post("/transcribe-and-respond", response_model=TranscribeAndRespondResponse)
async def transcribe_and_respond(
    file: UploadFile,
    session_id: uuid.UUID | None = Query(None),
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe audio and generate examiner turn in one request (TTS deferred)."""
    try:
        contents, error_resp = await _read_transcribe_blob(file)
        if error_resp is not None:
            return error_resp
        assert contents is not None

        t0 = time.perf_counter()
        transcript = await transcribe_audio_bytes(
            contents,
            content_type=file.content_type,
        )
        whisper_ms = int((time.perf_counter() - t0) * 1000)

        if not transcript.strip():
            return JSONResponse(
                status_code=400,
                content={"detail": "Could not detect speech — try again"},
            )

        live_session: SpeakingSession | None = None
        if session_id:
            live_session = await _get_live_session(
                session_id, _actor.sub, db, for_update=True
            )
            if not live_session:
                raise HTTPException(status_code=404, detail="Session not found")
            _raise_if_session_not_advanceable(live_session)
            history = list(live_session.history_json or [])
        else:
            history = []

        if live_session is not None:
            plan = await load_speaking_plan(live_session.test_id, db)
            try:
                payload = await _advance_turn(
                    live_session,
                    transcript,
                    plan,
                    db,
                    include_tts=False,
                )
            except InvalidStateTransition as e:
                status, detail = http_detail_for_blocked_state(
                    live_session.current_state
                )
                raise HTTPException(status_code=status, detail=detail) from e
            payload["transcript"] = transcript
            timings = payload.get("timings") or {}
            if isinstance(timings, dict):
                timings["whisper_ms"] = whisper_ms
                payload["timings"] = timings
            else:
                payload["timings"] = {"whisper_ms": whisper_ms}
            logger.info(
                "Examiner /transcribe-and-respond whisper_ms=%d state=%s part=%s",
                whisper_ms,
                live_session.current_state,
                payload.get("part"),
            )
            return payload

        # Legacy session-less path
        payload, timings, _updated_history = await _generate_examiner_response(
            transcript,
            history,
            include_tts=False,
            test_context=None,
        )
        timings.whisper_ms = whisper_ms
        payload["transcript"] = transcript
        payload["timings"] = timings.model_dump(exclude_none=True)

        logger.info(
            "Examiner /transcribe-and-respond (session-less) whisper_ms=%d gemini_ms=%s",
            whisper_ms,
            timings.gemini_ms,
        )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("transcribe-and-respond failed")
        return JSONResponse(
            status_code=502,
            content={"detail": _upstream_error_detail(e)},
        )


@router.post("/synthesize-turn", response_model=SynthesizeTurnResponse)
async def synthesize_turn(req: SynthesizeTurnRequest, _actor: Actor = Depends(get_current_actor)):
    """Synthesize TTS audio for an examiner turn (used after text-first respond)."""
    t0 = time.perf_counter()
    audio_b64, tts_error, cache_hit = await _tts_for_turn(
        req.text,
        req.part,
        req.cue_card,
    )
    tts_ms = int((time.perf_counter() - t0) * 1000)
    return SynthesizeTurnResponse(
        audio_base64=audio_b64,
        tts_error=tts_error,
        timings=PerformanceTimings(tts_ms=tts_ms, tts_cache_hit=cache_hit),
    )


_SCORE_CRITERION_KEYS = (
    "fluency_coherence",
    "lexical_resource",
    "grammatical_range",
    "pronunciation",
)


def _round_band(band: float) -> float:
    return round(band * 2) / 2


def _candidate_speech_stats(history: list[dict]) -> tuple[list[str], int, int]:
    candidate_lines = [t["text"] for t in history if t.get("role") == "candidate"]
    total_words = sum(len(line.split()) for line in candidate_lines)
    total_turns = len(candidate_lines)
    return candidate_lines, total_words, total_turns


def _to_conversation_turns(history: list[dict]) -> list[ConversationTurn]:
    turns: list[ConversationTurn] = []
    for turn in history:
        role = turn.get("role")
        text = turn.get("text")
        if role in ("examiner", "candidate") and text:
            turns.append(ConversationTurn(role=role, text=text))
    return turns


def _examiner_score_from_dict(result: dict, history: list[dict]) -> ExaminerScore:
    payload = dict(result)
    payload["conversation_history"] = _to_conversation_turns(history)
    return ExaminerScore(**payload)


def _guard_score_tier0(history: list[dict]) -> ExaminerScore:
    return ExaminerScore(
        fluency_coherence=CriterionScore(
            band=0.0,
            feedback=(
                "No speech was produced during the test. "
                "The candidate did not attempt to answer any questions."
            ),
        ),
        lexical_resource=CriterionScore(
            band=0.0,
            feedback="No language was produced to assess.",
        ),
        grammatical_range=CriterionScore(
            band=0.0,
            feedback="No language was produced to assess.",
        ),
        pronunciation=CriterionScore(
            band=0.0,
            feedback="No speech was produced to evaluate pronunciation.",
        ),
        overall_band=0.0,
        strengths=[],
        improvements=[
            "Attempt to answer every question from the examiner.",
            "Practice speaking English out loud daily, even for 5 minutes.",
        ],
        transcript="(No speech detected)",
        corrections=[],
        example_phrases=[],
        conversation_history=_to_conversation_turns(history),
    )


def _guard_score_tier1(candidate_lines: list[str], history: list[dict]) -> ExaminerScore:
    return ExaminerScore(
        fluency_coherence=CriterionScore(
            band=1.0,
            feedback=(
                "Only isolated words were produced. "
                "No connected speech or coherent responses."
            ),
        ),
        lexical_resource=CriterionScore(
            band=1.0,
            feedback="Extremely limited vocabulary. Only basic words used without context.",
        ),
        grammatical_range=CriterionScore(
            band=1.0,
            feedback="No sentence structures were produced. Only single words or short fragments.",
        ),
        pronunciation=CriterionScore(
            band=1.0,
            feedback="Insufficient connected speech to assess pronunciation meaningfully.",
        ),
        overall_band=1.0,
        strengths=["The candidate attempted to respond to at least one question."],
        improvements=[
            "Answer each question with at least 2-3 complete sentences.",
            "Practice forming full sentences before taking the test again.",
            "Focus on speaking continuously, even if you make mistakes.",
        ],
        transcript=" ".join(candidate_lines),
        corrections=[],
        example_phrases=[],
        conversation_history=_to_conversation_turns(history),
    )


def _cap_score_bands(result: dict, max_band: float) -> dict:
    for key in _SCORE_CRITERION_KEYS:
        if result[key]["band"] > max_band:
            result[key]["band"] = max_band
    avg = sum(result[key]["band"] for key in _SCORE_CRITERION_KEYS) / 4
    result["overall_band"] = min(_round_band(avg), max_band)
    return result


async def _score_with_guard(history: list[dict]) -> ExaminerScore:
    # Score only the rated portion of the test; keep full history for the response.
    scored_history = strip_intro(history)
    candidate_lines, total_words, total_turns = _candidate_speech_stats(scored_history)
    logger.info(
        "SCORING INPUT: words=%d turns=%d history_len=%d scored_len=%d",
        total_words,
        total_turns,
        len(history),
        len(scored_history),
    )

    if total_words == 0:
        logger.warning("SCORING GUARD: zero words, returning band 0")
        return _guard_score_tier0(history)

    if total_words < 10:
        logger.warning("SCORING GUARD: %d words, returning band 1", total_words)
        return _guard_score_tier1(candidate_lines, history)

    if total_words < 30:
        logger.warning("SCORING GUARD: %d words, capping at band 3", total_words)
        result = await evaluate_speaking_dialog(scored_history)
        result = _cap_score_bands(result, 3.0)
        improvements = list(result.get("improvements") or [])
        improvements.insert(
            0,
            "Your responses were extremely short. Aim for at least 3-4 sentences per answer.",
        )
        result["improvements"] = improvements
        return _examiner_score_from_dict(result, history)

    if total_turns < 3 and total_words < 50:
        logger.warning(
            "SCORING GUARD: only %d turns, %d words, capping at band 2",
            total_turns,
            total_words,
        )
        result = await evaluate_speaking_dialog(scored_history)
        result = _cap_score_bands(result, 2.0)
        return _examiner_score_from_dict(result, history)

    logger.info(
        "SCORING: %d words, %d turns — full Gemini evaluation",
        total_words,
        total_turns,
    )
    result = await evaluate_speaking_dialog(scored_history)
    return _examiner_score_from_dict(result, history)


@router.post("/score", response_model=ExaminerScore)
async def score_session(
    req: ScoreRequest,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Score the full conversation using Gemini.

    When session_id is provided, the computed band is persisted on the
    SpeakingSession so subsequent attempt updates can trust a server-side
    score instead of a client-supplied band.
    """
    live_session: SpeakingSession | None = None
    client_history = [t.model_dump() for t in req.conversation_history]
    if client_history:
        history = client_history
    elif req.session_id:
        live_session = await _get_live_session(
            req.session_id, _actor.sub, db, for_update=True
        )
        if not live_session:
            raise HTTPException(status_code=404, detail="Session not found")
        history = list(live_session.history_json or [])
    else:
        history = []

    if live_session is None and req.session_id:
        live_session = await _get_live_session(
            req.session_id, _actor.sub, db, for_update=True
        )
        if not live_session:
            raise HTTPException(status_code=404, detail="Session not found")

    if live_session is not None:
        if live_session.current_state == SpeakingState.ABANDONED.value:
            raise HTTPException(status_code=400, detail="Test already ended")
        transition_state(session=live_session, new_state=SpeakingState.SCORING)
        await db.commit()

    try:
        score = await _score_with_guard(history)
    except Exception as e:
        logger.exception("Failed to score speaking session")
        if live_session is not None:
            transition_state(session=live_session, new_state=SpeakingState.ENDED)
            live_session.status = "completed"
            if live_session.finished_at is None:
                live_session.finished_at = datetime.now(timezone.utc)
            await db.commit()
        return JSONResponse(
            status_code=502,
            content={"detail": _gemini_error_detail(e)},
        )

    if live_session is not None:
        live_session.overall_band = score.overall_band
        live_session.score_json = score.model_dump(mode="json")
        live_session.status = "completed"
        transition_state(session=live_session, new_state=SpeakingState.ENDED)
        if live_session.finished_at is None:
            live_session.finished_at = datetime.now(timezone.utc)
        await _seal_speaking_progress(db, live_session.attempt_id)
        await db.commit()

    return score


@router.get("/simli-token")
async def get_simli_token(
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Generate a Simli session token for the video avatar.

    Returns empty config if Simli is not configured or at capacity.
    """
    if not settings.simli_api_key or not settings.simli_face_id:
        return {"enabled": False, "reason": "not_configured"}

    # Claim a slot before calling out to Simli, so candidates starting together
    # are admitted one at a time rather than all seeing an empty house.
    granted, taken = await claim_slot(db, _actor.sub)
    if not granted:
        logger.info(
            "Simli at capacity taken=%s max=%s — audio-only fallback",
            taken,
            settings.simli_max_concurrent,
        )
        return {
            "enabled": False,
            "reason": "capacity",
            "detail": (
                f"Video avatar slots are full ({taken}/"
                f"{settings.simli_max_concurrent}). Audio-only mode is active."
            ),
        }

    headers = {
        "Content-Type": "application/json",
        "x-simli-api-key": settings.simli_api_key,
    }
    compose_config = {
        "faceId": settings.simli_face_id,
        "handleSilence": True,
        "maxSessionLength": 1800,
        "maxIdleTime": 1800,
    }

    async def fetch_token() -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.simli.ai/compose/token",
                json=compose_config,
                headers=headers,
            )
            credits_resp = _simli_credits_response(resp)
            if credits_resp:
                raise _SimliCreditsError(credits_resp)
            resp.raise_for_status()
            return resp.json()

    async def fetch_ice() -> list | None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            ice_resp = await client.get(
                "https://api.simli.ai/compose/ice",
                headers=headers,
            )
            return ice_resp.json() if ice_resp.status_code == 200 else None

    try:
        token_data, ice_servers = await asyncio.gather(fetch_token(), fetch_ice())
        logger.info("Simli token OK face_id=%s", settings.simli_face_id[:8])
        return {
            "enabled": True,
            "session_token": token_data["session_token"],
            "face_id": settings.simli_face_id,
            "ice_servers": ice_servers,
        }
    except _SimliCreditsError as e:
        logger.warning("Simli credits exhausted: %s", e.payload.get("detail"))
        await release_slot(db, _actor.sub)
        return e.payload
    except Exception as e:
        # No stream was established, so the claim would only deny somebody else.
        await release_slot(db, _actor.sub)
        return _simli_error_response(e)


@router.post("/sessions", response_model=SessionIdResponse)
async def save_speaking_session(
    req: SaveSessionRequest,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Persist a completed speaking session.

    Non-admins cannot self-report band scores: overall_band / score_json are
    only written when an admin saves, or when already set by server scoring.
    """
    try:
        trust_client_band = _actor.role == "admin"

        if req.session_id:
            result = await db.execute(
                select(SpeakingSession).where(
                    SpeakingSession.id == req.session_id,
                    SpeakingSession.admin_email == _actor.sub,
                )
            )
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            session.finished_at = _parse_dt(req.finished_at) or datetime.now(timezone.utc)
            session.history_json = [t.model_dump() for t in req.history_json]
            session.status = "completed"
            if trust_client_band:
                session.overall_band = req.overall_band
                session.score_json = req.score_json
            await db.commit()
            await db.refresh(session)
            return SessionIdResponse(id=str(session.id))

        session = SpeakingSession(
            admin_email=_actor.sub,
            started_at=_parse_dt(req.started_at),
            finished_at=_parse_dt(req.finished_at) or datetime.now(timezone.utc),
            overall_band=req.overall_band if trust_client_band else None,
            score_json=req.score_json if trust_client_band else None,
            history_json=[t.model_dump() for t in req.history_json],
            status="completed",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return SessionIdResponse(id=str(session.id))
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to save speaking session")
        raise HTTPException(status_code=500, detail="Could not save session") from None


@router.get("/sessions")
async def list_speaking_sessions(
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpeakingSession)
        .where(SpeakingSession.admin_email == _actor.sub)
        .order_by(SpeakingSession.created_at.desc())
        .limit(50)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "finished_at": s.finished_at.isoformat() if s.finished_at else None,
            "overall_band": s.overall_band,
            "created_at": s.created_at.isoformat(),
        }
        for s in rows
    ]


@router.get("/sessions/{session_id}")
async def get_speaking_session(
    session_id: uuid.UUID,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpeakingSession).where(
            SpeakingSession.id == session_id,
            SpeakingSession.admin_email == _actor.sub,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": str(session.id),
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "finished_at": session.finished_at.isoformat() if session.finished_at else None,
        "overall_band": session.overall_band,
        "score_json": session.score_json,
        "history_json": session.history_json,
        "created_at": session.created_at.isoformat(),
    }
