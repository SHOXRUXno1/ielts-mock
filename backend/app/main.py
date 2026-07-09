import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.attempts import router as attempts_router
from app.api.question_groups import router as question_groups_router
from app.api.questions import router as questions_router
from app.api.results import router as results_router
from app.api.sections import router as sections_router
from app.api.student_panel import router as student_panel_router
from app.api.students import router as students_router
from app.api.test_import import router as test_import_router
from app.api.tests import router as tests_router
from app.api.speaking_examiner import router as speaking_examiner_router
from app.api.upload import router as upload_router
from app.api.feedback import router as feedback_router
from app.core.config import settings
from app.core.database import engine
from app.services.elevenlabs_service import validate_voice_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = None
    if settings.gemini_key_list:
        from app.services.worker import run_worker

        worker_task = asyncio.create_task(run_worker())
        logger.info("Evaluation worker launched")
    else:
        logger.warning("No Gemini API keys configured — evaluation worker disabled")

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

    if worker_task is not None:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
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

# Public auth (admin + students)
app.include_router(auth_router)

# Admin-only routes
app.include_router(admin_router)
app.include_router(students_router)
app.include_router(test_import_router)   # must be before tests_router
app.include_router(tests_router)
app.include_router(sections_router)
app.include_router(questions_router)
app.include_router(question_groups_router)

# Shared auth (admin + student) — attempts and results
app.include_router(attempts_router)
app.include_router(results_router)

# Upload & AI
app.include_router(upload_router)
app.include_router(speaking_examiner_router)
app.include_router(feedback_router)

# Student-only panel
app.include_router(student_panel_router)

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


@app.get("/health")
async def health():
    return {"status": "ok"}
