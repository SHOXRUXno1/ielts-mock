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
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_rpm_limit: int = 15  # requests per minute per key

    @property
    def gemini_key_list(self) -> list[str]:
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]

    # ── Groq Whisper (Speech-to-Text) ────────────────────
    groq_api_key: str = ""
    groq_examiner_model: str = "llama-3.3-70b-versatile"

    # ── ElevenLabs (Text-to-Speech) ─────────────────────
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "onwK4e9ZLuTAKqWW03F9"  # Daniel, British
    elevenlabs_model_id: str = "eleven_turbo_v2"  # or eleven_flash_v2_5 for lower latency

    # ── Simli (Video Avatar) ─────────────────────────────
    simli_api_key: str = ""
    simli_face_id: str = ""

    # ── S3 (Timeweb) ────────────────────────────────────
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "ielts-mock"
    s3_region: str = "ru-1"

    # ── CORS ─────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
