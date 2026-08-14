import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.admin import router as admin_router
from app.api.admin_panel import router as admin_panel_router
from app.api.auth import router as auth_router
from app.api.attempts import router as attempts_router
from app.api.devices import router as devices_router
from app.api.practice import router as practice_router
from app.api.question_groups import router as question_groups_router
from app.api.questions import router as questions_router
from app.api.results import router as results_router
from app.api.sections import router as sections_router
from app.api.student_panel import router as student_panel_router
from app.api.students import router as students_router
from app.api.take import router as take_router
from app.api.test_import import router as test_import_router
from app.api.tests import router as tests_router
from app.api.speaking_examiner import router as speaking_examiner_router
from app.api.upload import router as upload_router
from app.api.feedback import router as feedback_router
from app.core.config import settings
from app.core.database import engine
from app.services.admin_sessions import AdminSessionHeartbeatMiddleware
from app.services.background_lock import (
    release_background_lock,
    try_acquire_background_lock,
)
from app.services.elevenlabs_service import validate_voice_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = None
    cleanup_task = None
    admin_session_cleanup_task = None
    lock_conn = await try_acquire_background_lock(engine)
    run_background = lock_conn is not None

    if run_background:
        if settings.gemini_key_list:
            from app.services.worker import run_worker

            worker_task = asyncio.create_task(run_worker())
            logger.info("Evaluation worker launched")
        else:
            logger.warning("No Gemini API keys configured — evaluation worker disabled")

        from app.services.speaking_cleanup import run_session_cleanup
        from app.services.admin_sessions import run_admin_session_cleanup

        cleanup_task = asyncio.create_task(run_session_cleanup())
        logger.info("Speaking session cleanup task launched")

        admin_session_cleanup_task = asyncio.create_task(run_admin_session_cleanup())
        logger.info("Admin session cleanup task launched")
    else:
        logger.info("This worker will not run background tasks (advisory lock held elsewhere)")

    if settings.elevenlabs_api_key:
        ok, detail = await validate_voice_config()
        if ok:
            logger.info("ElevenLabs ready: %s", detail)
        else:
            logger.error(
                "ElevenLabs misconfigured — examiner TTS will fail: %s",
                detail,
            )
    else:
        logger.warning("ELEVENLABS_API_KEY not set — examiner TTS disabled")

    yield

    for task in (admin_session_cleanup_task, cleanup_task, worker_task):
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    await release_background_lock(lock_conn)
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AdminSessionHeartbeatMiddleware)

# Public auth (admin + students)
app.include_router(auth_router)

# Admin-only routes
app.include_router(admin_router)
app.include_router(admin_panel_router)
app.include_router(devices_router)
app.include_router(students_router)
app.include_router(test_import_router)   # must be before tests_router
app.include_router(tests_router)
app.include_router(sections_router)
app.include_router(questions_router)
app.include_router(question_groups_router)

# Shared auth (admin + student) — attempts, results, take-test reads
app.include_router(take_router)
app.include_router(attempts_router)
app.include_router(practice_router)
app.include_router(results_router)

# Upload & AI
app.include_router(upload_router)
app.include_router(speaking_examiner_router)
app.include_router(feedback_router)

# Student-only panel
app.include_router(student_panel_router)

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
# Prefer nginx alias for /media in production; StaticFiles remains for local/dev.
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


@app.get("/health")
async def health(response: Response):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception as exc:
        logger.exception("Health check DB failure")
        response.status_code = 503
        return {
            "status": "degraded",
            "database": "error",
            "detail": str(exc),
        }
