"""Background evaluation worker.

Polls evaluation_jobs for pending tasks, processes them via LLM services,
and updates attempt band scores when all sections are scored.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.attempt import Attempt, AttemptStatus
from app.models.evaluation_job import EvaluationJob, JobStatus
from app.services.band_calc import compute_overall_band
from app.services.llm import NonEnglishError, evaluate_speaking, evaluate_writing, transcribe_audio

logger = logging.getLogger(__name__)

POLL_INTERVAL = 5  # seconds


async def _process_job(job: EvaluationJob, db: AsyncSession) -> None:
    job.status = JobStatus.PROCESSING
    await db.commit()

    try:
        if job.section_type == "writing":
            answers = job.input_data.get("answers", {})
            prompts = job.input_data.get("prompts", {})
            images = job.input_data.get("images", {})
            result = await evaluate_writing(answers, prompts, images=images)
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
            result = await evaluate_speaking(full_transcript.strip(), questions=questions)
        else:
            raise ValueError(f"Unknown section type: {job.section_type}")

        job.status = JobStatus.DONE
        job.result = result
        job.band_score = result.get("overall_band")
        job.processed_at = datetime.now(timezone.utc)

    except NonEnglishError as e:
        logger.warning("Job %s: non-English audio — %s", job.id, e)
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.processed_at = datetime.now(timezone.utc)

    except Exception as e:
        logger.exception("Evaluation job %s failed", job.id)
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.processed_at = datetime.now(timezone.utc)

    await db.commit()


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

    for job in jobs:
        if job.status != JobStatus.DONE:
            continue
        band = job.teacher_override_band if job.teacher_override_band is not None else job.band_score
        if band is None:
            continue
        if job.section_type == "writing":
            attempt.writing_band = band
        elif job.section_type == "speaking":
            attempt.speaking_band = band

    attempt.overall_band = compute_overall_band(attempt)

    if all_done:
        attempt.status = AttemptStatus.SCORED

    await db.commit()


_STALE_ATTEMPT_HOURS = 4
_CLEANUP_INTERVAL = 60 * 15  # run cleanup every 15 minutes
_cleanup_counter = 0


async def _cleanup_stale_attempts(db: AsyncSession) -> None:
    """Mark in_progress attempts older than 4 hours as abandoned."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_STALE_ATTEMPT_HOURS)
    stale_result = await db.execute(
        select(Attempt).where(
            Attempt.status == AttemptStatus.IN_PROGRESS,
            Attempt.started_at < cutoff,
        )
    )
    stale = stale_result.scalars().all()
    for a in stale:
        a.status = AttemptStatus.ABANDONED
    if stale:
        await db.commit()
        logger.info("Abandoned %d stale attempts (>%dh old)", len(stale), _STALE_ATTEMPT_HOURS)


async def run_worker() -> None:
    global _cleanup_counter
    logger.info("Evaluation worker started")
    while True:
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(EvaluationJob)
                    .where(EvaluationJob.status == JobStatus.PENDING)
                    .order_by(EvaluationJob.created_at)
                    .limit(1)
                )
                job = result.scalar_one_or_none()

                if job is not None:
                    logger.info("Processing job %s (%s)", job.id, job.section_type)
                    await _process_job(job, db)
                    await _update_attempt_bands(job.attempt_id, db)
                    continue

                # Periodic stale-attempt cleanup (every ~15 min)
                _cleanup_counter += POLL_INTERVAL
                if _cleanup_counter >= _CLEANUP_INTERVAL:
                    _cleanup_counter = 0
                    await _cleanup_stale_attempts(db)

        except Exception:
            logger.exception("Worker loop error")

        await asyncio.sleep(POLL_INTERVAL)
