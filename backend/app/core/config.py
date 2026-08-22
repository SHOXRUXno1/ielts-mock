from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────
    app_name: str = "IELTS Mock API"
    debug: bool = False

    # ── Database ─────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ielts_mock"

    # ── Admin ────────────────────────────────────────────
    admin_login: str = "admin"
    admin_password: str = "admin"
    admin_name: str = "Admin"

    # ── JWT ──────────────────────────────────────────────
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # ── Gemini (LLM evaluation) ──────────────────────────
    gemini_api_keys: str = ""  # comma-separated list of API keys for rotation
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_rpm_limit: int = 15  # requests per minute per key

    @property
    def gemini_key_list(self) -> list[str]:
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]

    # ── Groq Whisper (Speech-to-Text) ────────────────────
    groq_api_key: str = ""
    groq_examiner_model: str = "llama-3.3-70b-versatile"
    whisper_max_concurrent: int = 8
    # Groq's on-demand tier allows only 20 Whisper requests per minute for the
    # whole account, which 20+ live Speaking sessions blow through instantly.
    # Transcriptions that find no token left spill over to Gemini STT rather
    # than waiting for the window or failing the candidate's turn. This budget
    # is per process, so divide the account limit by the number of app workers.
    groq_stt_rpm_limit: int = 5

    # ── ElevenLabs (Text-to-Speech) ─────────────────────
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "onwK4e9ZLuTAKqWW03F9"  # Daniel, British
    elevenlabs_model_id: str = "eleven_turbo_v2"  # or eleven_flash_v2_5 for lower latency
    elevenlabs_max_concurrent: int = 6

    # ── Simli (Video Avatar) ─────────────────────────────
    simli_api_key: str = ""
    simli_face_id: str = ""
    # Simli Pro allows 10 concurrent sessions. Extra students fall back to
    # audio-only. Admission is claimed up front (see services/simli_slots), so
    # the plan ceiling can be used in full instead of held back as slack.
    simli_max_concurrent: int = 10
    # A live candidate answers every minute or so, so a session untouched for
    # longer has lost its browser and is no longer holding a WebRTC stream.
    # Without this, sessions that died mid-exam kept reserving a video slot
    # until the abandon sweep caught them, and everyone else got audio-only.
    simli_slot_idle_minutes: int = 5
    # How long a granted video token holds its slot before the exam session
    # takes over the claim. Long enough to cover the loading screen and a
    # candidate hesitating before they begin, short enough that someone who
    # closes the tab frees the slot quickly.
    simli_lease_minutes: int = 3

    # ── Evaluation worker ───────────────────────────────
    worker_max_concurrent_jobs: int = 4
    worker_job_max_retries: int = 3
    worker_stuck_processing_minutes: int = 15

    # ── S3 (Timeweb) ────────────────────────────────────
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "ielts-mock"
    s3_region: str = "ru-1"

    # ── CORS ─────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()

if not settings.debug:
    _insecure: list[str] = []
    if settings.secret_key == "change-me-in-production":
        _insecure.append("SECRET_KEY is still the default value")
    if settings.admin_password in ("changeme", "admin"):
        _insecure.append("ADMIN_PASSWORD is still the default value")
    if _insecure:
        raise RuntimeError(
            "Insecure configuration detected (DEBUG=false):\n  - "
            + "\n  - ".join(_insecure)
            + "\nSet proper values in .env before running in production."
        )
