"""Background evaluation worker.

Polls evaluation_jobs for pending tasks, processes them via LLM services,
and updates attempt band scores when all sections are scored.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session
from app.models.attempt import Attempt, AttemptMode, AttemptStatus, PRACTICE_MODES
from app.models.evaluation_job import EvaluationJob, JobStatus
from app.services.band_calc import compute_overall_band, derive_scored_status
from app.services.llm import (
    NonEnglishError,
    WritingEvaluationError,
    evaluate_speaking,
    evaluate_writing,
    redact_api_keys,
    transcribe_audio,
)
from app.services.scoring import compute_writing_band

logger = logging.getLogger(__name__)

POLL_INTERVAL = 5  # seconds
_STALE_ATTEMPT_HOURS = 24
_CLEANUP_INTERVAL = 60 * 15  # run cleanup every 15 minutes
_cleanup_counter = 0


async def _process_job(job_id: uuid.UUID) -> uuid.UUID | None:
    """Process a single claimed job in its own DB session. Returns attempt_id."""
    async with async_session() as db:
        job = await db.get(EvaluationJob, job_id)
        if job is None or job.status != JobStatus.PROCESSING:
            return None

        attempt_id = job.attempt_id
        try:
            if job.section_type == "writing":
                answers = job.input_data.get("answers", {})
                prompts = job.input_data.get("prompts", {})
                images = job.input_data.get("images", {})
                result = await evaluate_writing(
                    answers,
                    prompts,
                    images=images,
                    essay_types=job.input_data.get("essay_types") or {},
                    task_descriptions=job.input_data.get("task_descriptions"),
                    task_instructions=job.input_data.get("task_instructions"),
                    task_statements=job.input_data.get("task_statements"),
                    task_questions=job.input_data.get("task_questions"),
                )
            elif job.section_type == "speaking":
                audio_urls = job.input_data.get("audio_urls", [])
                if not audio_urls:
                    raise ValueError("No audio URLs provided for speaking evaluation")

                full_transcript = ""
                for url in audio_urls:
                    logger.info("Transcribing audio: %s", url)
                    transcript = await transcribe_audio(url)
                    logger.info("Transcript length: %d chars", len(transcript))
                    full_transcript += transcript + "\n\n"

                questions = job.input_data.get("prompts", [])
                logger.info("Evaluating speaking with %d question prompts", len(questions))
                result = await evaluate_speaking(
                    full_transcript.strip(), questions=questions
                )
            else:
                raise ValueError(f"Unknown section type: {job.section_type}")

            job.status = JobStatus.DONE
            job.result = result
            job.band_score = result.get("overall_band")
            job.processed_at = datetime.now(timezone.utc)
            job.error_message = None

        except NonEnglishError as e:
            logger.warning("Job %s: non-English audio — %s", job.id, e)
            job.status = JobStatus.FAILED
            job.error_message = redact_api_keys(str(e))
            job.processed_at = datetime.now(timezone.utc)

        except Exception as e:
            # A rejected evaluation is an expected, retryable outcome — keep the
            # log readable and reserve tracebacks for genuine faults.
            if isinstance(e, WritingEvaluationError):
                logger.warning("Evaluation job %s rejected: %s", job.id, e)
            else:
                logger.exception("Evaluation job %s failed", job.id)
            retries = int(job.retry_count or 0) + 1
            job.retry_count = retries
            # This text is stored and shown in the admin panel, so it must not
            # carry a provider credential.
            job.error_message = redact_api_keys(str(e))
            job.processed_at = datetime.now(timezone.utc)
            if retries < settings.worker_job_max_retries:
                # Re-queue with backoff recorded in error_message for operators.
                job.status = JobStatus.PENDING
                logger.info(
                    "Job %s requeued (retry %d/%d)",
                    job.id,
                    retries,
                    settings.worker_job_max_retries,
                )
            else:
                job.status = JobStatus.FAILED

        await db.commit()
        return attempt_id


async def _update_attempt_bands(attempt_id, db: AsyncSession) -> None:
    """Recompute attempt bands after an evaluation job finishes."""
    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        return

    jobs_result = await db.execute(
        select(EvaluationJob).where(EvaluationJob.attempt_id == attempt_id)
    )
    jobs = jobs_result.scalars().all()

    all_done = all(j.status in (JobStatus.DONE, JobStatus.FAILED) for j in jobs)
    if not all_done:
        return

    mode = attempt.mode or AttemptMode.FULL_MOCK.value
    is_practice = mode in PRACTICE_MODES
    is_single_part = mode == AttemptMode.SINGLE_PART.value
    # Whole-section practice writes skill bands onto the attempt (dashboard
    # still filters mode == full_mock, so mock averages stay clean).
    # Single-part practice keeps the band on the job only.
    write_skill_band = not is_single_part

    for job in jobs:
        if job.status != JobStatus.DONE:
            continue
        if job.section_type == "writing":
            if job.teacher_override_band is not None:
                weighted = job.teacher_override_band
            else:
                tasks = (job.result or {}).get("tasks") or {}
                t1 = (tasks.get("task_1") or {}).get("overall_band")
                t2 = (tasks.get("task_2") or {}).get("overall_band")
                if is_single_part:
                    # Single-task practice — band is whichever task has a value.
                    weighted = (
                        float(t1) if t1 is not None
                        else float(t2) if t2 is not None
                        else None
                    )
                else:
                    weighted = compute_writing_band(
                        float(t1) if t1 is not None else None,
                        float(t2) if t2 is not None else None,
                    )
            job.band_score = weighted
            if write_skill_band:
                # Incomplete (missing T1 or T2) → None, never fall back to 0.0
                attempt.writing_band = weighted
        elif job.section_type == "speaking":
            band = (
                job.teacher_override_band
                if job.teacher_override_band is not None
                else job.band_score
            )
            if band is not None and write_skill_band:
                attempt.speaking_band = band

    if not is_practice:
        attempt.overall_band = compute_overall_band(attempt)
        if all_done:
            attempt.status = derive_scored_status(attempt)
    else:
        # Practice flips to AUTO_SCORED once the job settles. overall_band
        # stays None — a single-skill paper is not a 4-skill IELTS overall.
        attempt.status = AttemptStatus.AUTO_SCORED

    await db.commit()


async def _cleanup_stale_attempts(db: AsyncSession) -> None:
    """Mark in_progress attempts inactive for >24h as abandoned."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_STALE_ATTEMPT_HOURS)
    stale_result = await db.execute(
        select(Attempt).where(
            Attempt.status == AttemptStatus.IN_PROGRESS,
            Attempt.updated_at < cutoff,
        )
    )
    stale = stale_result.scalars().all()
    for a in stale:
        a.status = AttemptStatus.ABANDONED
    if stale:
        await db.commit()
        logger.info(
            "Abandoned %d stale attempts (>%dh inactive)",
            len(stale),
            _STALE_ATTEMPT_HOURS,
        )


async def _requeue_stuck_jobs(db: AsyncSession) -> int:
    """Return jobs stuck in processing (crashed worker) back to pending."""
    cutoff = datetime.now(timezone.utc) - timedelta(
        minutes=settings.worker_stuck_processing_minutes
    )
    result = await db.execute(
        update(EvaluationJob)
        .where(
            EvaluationJob.status == JobStatus.PROCESSING,
            EvaluationJob.updated_at < cutoff,
        )
        .values(status=JobStatus.PENDING)
        .returning(EvaluationJob.id)
    )
    ids = list(result.scalars().all())
    if ids:
        await db.commit()
        logger.warning("Requeued %d stuck processing jobs", len(ids))
    return len(ids)


async def _claim_jobs(limit: int) -> list[uuid.UUID]:
    """Atomically claim up to `limit` pending jobs via SKIP LOCKED."""
    if limit <= 0:
        return []
    async with async_session() as db:
        result = await db.execute(
            select(EvaluationJob)
            .where(EvaluationJob.status == JobStatus.PENDING)
            .order_by(EvaluationJob.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        jobs = list(result.scalars().all())
        if not jobs:
            return []
        now = datetime.now(timezone.utc)
        ids: list[uuid.UUID] = []
        for job in jobs:
            job.status = JobStatus.PROCESSING
            job.updated_at = now
            ids.append(job.id)
        await db.commit()
        return ids


async def run_worker() -> None:
    global _cleanup_counter
    max_jobs = max(1, settings.worker_max_concurrent_jobs)
    logger.info("Evaluation worker started (max_concurrent=%d)", max_jobs)
    while True:
        try:
            async with async_session() as db:
                await _requeue_stuck_jobs(db)

            claimed = await _claim_jobs(max_jobs)
            if claimed:
                logger.info("Claimed %d evaluation job(s)", len(claimed))
                results = await asyncio.gather(
                    *[_process_job(job_id) for job_id in claimed],
                    return_exceptions=True,
                )
                attempt_ids: set[uuid.UUID] = set()
                for r in results:
                    if isinstance(r, Exception):
                        logger.exception("Worker job task failed: %s", r)
                    elif r is not None:
                        attempt_ids.add(r)
                async with async_session() as db:
                    for aid in attempt_ids:
                        await _update_attempt_bands(aid, db)
                continue

            # Periodic stale-attempt cleanup (every ~15 min)
            _cleanup_counter += POLL_INTERVAL
            if _cleanup_counter >= _CLEANUP_INTERVAL:
                _cleanup_counter = 0
                async with async_session() as db:
                    await _cleanup_stale_attempts(db)

        except Exception:
            logger.exception("Worker loop error")

        await asyncio.sleep(POLL_INTERVAL)
