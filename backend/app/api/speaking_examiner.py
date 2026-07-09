"""Speaking AI Examiner — live conversational IELTS Speaking test."""

import asyncio
import base64
import logging
import re
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_actor
from app.core.config import settings
from app.core.database import async_session, get_db
from app.models.speaking_session import SpeakingSession
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
from app.services.llm import (
    evaluate_speaking_dialog,
    generate_examiner_turn,
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

QUESTIONS_PER_PART: dict[int, int] = {1: 5, 2: 1, 3: 4}
MAX_EXAMINER_TURNS = 15
FORCED_END_TEXT = "That is the end of the speaking test. Thank you very much."
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


def count_questions_by_part(history: list[dict]) -> dict:
    """Count examiner turns per part and derive current flow position."""
    part1_count = 0
    part2_count = 0
    part3_count = 0
    current_part = 1

    for turn in history:
        if turn["role"] == "examiner":
            if current_part == 1:
                part1_count += 1
            elif current_part == 2:
                part2_count += 1
            elif current_part == 3:
                part3_count += 1

        if part1_count >= QUESTIONS_PER_PART[1] and current_part == 1:
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
            and part3_count >= QUESTIONS_PER_PART[3] - 1
        ),
    }


def _build_extra_instructions(counts: dict) -> str:
    if counts["should_end"]:
        return f"""
END THE TEST NOW. Say exactly:
'{FORCED_END_TEXT}'
Add [END_OF_TEST] tag. Do NOT ask any more questions.
"""

    if counts["current_part"] == 3 and counts["part3"] >= QUESTIONS_PER_PART[3] - 2:
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
) -> dict:
    payload = {
        "text": clean_text,
        "audio_base64": audio_b64,
        "part": part,
        "is_end": is_end,
        "cue_card": cue_card,
        "question_number": question_number,
    }
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
    """
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
) -> SpeakingSession | None:
    result = await db.execute(
        select(SpeakingSession).where(
            SpeakingSession.id == session_id,
            SpeakingSession.admin_email == actor_sub,
        )
    )
    return result.scalar_one_or_none()


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
async def part2_begin_phrase():
    """Cached TTS for the Part 2 preparation end cue."""
    audio_b64, tts_error, _cache_hit = await _tts_base64(PART2_BEGIN_SPEAKING)
    return PhraseResponse(
        text=PART2_BEGIN_SPEAKING,
        audio_base64=audio_b64,
        tts_error=tts_error,
    )


async def _create_start_session(admin_email: str, clean_text: str) -> SpeakingSession:
    async with async_session() as db:
        started_at = datetime.now(timezone.utc)
        session = SpeakingSession(
            admin_email=admin_email,
            started_at=started_at,
            status="in_progress",
            history_json=[{"role": "examiner", "text": clean_text}],
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session


@router.post("/start", response_model=ExaminerTurnResponse)
async def start_session(
    _actor: Actor = Depends(get_current_actor),
):
    """Start a new speaking examiner session — returns greeting + first question."""
    t0 = time.perf_counter()
    try:
        raw = await generate_examiner_turn([], None)
    except Exception as e:
        logger.exception("Failed to start examiner session")
        return JSONResponse(
            status_code=502,
            content={"detail": _gemini_error_detail(e)},
        )

    gemini_ms = int((time.perf_counter() - t0) * 1000)
    clean_text, _, _, _ = _parse_tags(raw)
    part = 1
    is_end = False
    cue_card = None

    t1 = time.perf_counter()
    tts_task = asyncio.create_task(_tts_for_turn(clean_text, part, cue_card))
    session_task = asyncio.create_task(_create_start_session(_actor.sub, clean_text))
    audio_b64, tts_error, cache_hit = await tts_task
    session = await session_task
    tts_ms = int((time.perf_counter() - t1) * 1000)

    logger.info(
        "Examiner /start gemini_ms=%d tts_ms=%d text_len=%d part=1 session_id=%s cache_hit=%s",
        gemini_ms,
        tts_ms,
        len(clean_text),
        session.id,
        cache_hit,
    )

    return _examiner_turn_payload(
        clean_text,
        part,
        is_end,
        cue_card,
        audio_b64,
        _question_number_for_start(),
        session_id=str(session.id),
        tts_error=tts_error,
        timings=PerformanceTimings(
            gemini_ms=gemini_ms,
            tts_ms=tts_ms,
            tts_cache_hit=cache_hit,
        ),
    )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_recording(file: UploadFile):
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
) -> tuple[dict, PerformanceTimings, list[dict]]:
    """Core respond logic shared by /respond and /transcribe-and-respond."""
    counts = count_questions_by_part(history)
    total_examiner_turns = sum(1 for t in history if t["role"] == "examiner")

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

    extra_instructions = _build_extra_instructions(counts)
    logger.info(
        "Speaking flow: part=%s p1=%s p2=%s p3=%s total=%s directive=%s",
        counts["current_part"],
        counts["part1"],
        counts["part2"],
        counts["part3"],
        total_examiner_turns,
        "YES" if extra_instructions else "NO",
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
    background_tasks: BackgroundTasks,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Generate next examiner turn given candidate's response + history."""
    t0 = time.perf_counter()
    live_session: SpeakingSession | None = None
    if req.session_id:
        live_session = await _get_live_session(req.session_id, _actor.sub, db)
        if not live_session:
            raise HTTPException(status_code=404, detail="Session not found")
        history = list(live_session.history_json or [])
    else:
        history = [t.model_dump() for t in req.conversation_history]

    try:
        payload, timings, updated_history = await _generate_examiner_response(
            req.candidate_text,
            history,
            include_tts=True,
        )
    except Exception as e:
        logger.exception("Failed to generate examiner response")
        return JSONResponse(
            status_code=502,
            content={"detail": _gemini_error_detail(e)},
        )

    db_ms = 0
    if live_session is not None:
        db_start = time.perf_counter()
        background_tasks.add_task(
            _persist_live_history_background,
            live_session.id,
            updated_history,
            _actor.sub,
        )
        db_ms = int((time.perf_counter() - db_start) * 1000)
        payload["session_id"] = str(live_session.id)
        timings.db_ms = db_ms
        payload["timings"] = timings.model_dump(exclude_none=True)

    total_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(
        "Examiner /respond total_ms=%d gemini_ms=%s tts_ms=%s db_ms=%s turns=%s",
        total_ms,
        timings.gemini_ms,
        timings.tts_ms,
        timings.db_ms,
        timings.history_turns,
    )
    return payload


@router.post("/transcribe-and-respond", response_model=TranscribeAndRespondResponse)
async def transcribe_and_respond(
    file: UploadFile,
    background_tasks: BackgroundTasks,
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
            live_session = await _get_live_session(session_id, _actor.sub, db)
            if not live_session:
                raise HTTPException(status_code=404, detail="Session not found")
            history = list(live_session.history_json or [])
        else:
            history = []

        payload, timings, updated_history = await _generate_examiner_response(
            transcript,
            history,
            include_tts=False,
        )
        timings.whisper_ms = whisper_ms

        if live_session is not None:
            background_tasks.add_task(
                _persist_live_history_background,
                live_session.id,
                updated_history,
                _actor.sub,
            )
            payload["session_id"] = str(live_session.id)

        payload["transcript"] = transcript
        payload["timings"] = timings.model_dump(exclude_none=True)

        logger.info(
            "Examiner /transcribe-and-respond whisper_ms=%d gemini_ms=%s turns=%s",
            whisper_ms,
            timings.gemini_ms,
            timings.history_turns,
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
async def synthesize_turn(req: SynthesizeTurnRequest):
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
    candidate_lines, total_words, total_turns = _candidate_speech_stats(history)
    logger.info(
        "SCORING INPUT: words=%d turns=%d history_len=%d",
        total_words,
        total_turns,
        len(history),
    )

    if total_words == 0:
        logger.warning("SCORING GUARD: zero words, returning band 0")
        return _guard_score_tier0(history)

    if total_words < 10:
        logger.warning("SCORING GUARD: %d words, returning band 1", total_words)
        return _guard_score_tier1(candidate_lines, history)

    if total_words < 30:
        logger.warning("SCORING GUARD: %d words, capping at band 3", total_words)
        result = await evaluate_speaking_dialog(history)
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
        result = await evaluate_speaking_dialog(history)
        result = _cap_score_bands(result, 2.0)
        return _examiner_score_from_dict(result, history)

    logger.info(
        "SCORING: %d words, %d turns — full Gemini evaluation",
        total_words,
        total_turns,
    )
    result = await evaluate_speaking_dialog(history)
    return _examiner_score_from_dict(result, history)


@router.post("/score", response_model=ExaminerScore)
async def score_session(
    req: ScoreRequest,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Score the full conversation using Gemini."""
    client_history = [t.model_dump() for t in req.conversation_history]
    if client_history:
        history = client_history
    elif req.session_id:
        live_session = await _get_live_session(req.session_id, _actor.sub, db)
        if not live_session:
            raise HTTPException(status_code=404, detail="Session not found")
        history = list(live_session.history_json or [])
    else:
        history = []

    try:
        return await _score_with_guard(history)
    except Exception as e:
        logger.exception("Failed to score speaking session")
        return JSONResponse(
            status_code=502,
            content={"detail": _gemini_error_detail(e)},
        )


@router.get("/simli-token")
async def get_simli_token():
    """Generate a Simli session token for the video avatar.

    Returns empty config if Simli is not configured.
    """
    if not settings.simli_api_key or not settings.simli_face_id:
        return {"enabled": False, "reason": "not_configured"}

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
        return e.payload
    except Exception as e:
        return _simli_error_response(e)


@router.post("/sessions", response_model=SessionIdResponse)
async def save_speaking_session(
    req: SaveSessionRequest,
    _actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    try:
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
            session.overall_band = req.overall_band
            session.score_json = req.score_json
            session.history_json = [t.model_dump() for t in req.history_json]
            session.status = "completed"
            await db.commit()
            await db.refresh(session)
            return SessionIdResponse(id=str(session.id))

        session = SpeakingSession(
            admin_email=_actor.sub,
            started_at=_parse_dt(req.started_at),
            finished_at=_parse_dt(req.finished_at) or datetime.now(timezone.utc),
            overall_band=req.overall_band,
            score_json=req.score_json,
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
