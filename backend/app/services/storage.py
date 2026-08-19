"""Media storage abstraction: local filesystem (default) or S3 when configured."""

import uuid
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings

MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent / "media"
AUDIO_DIR = MEDIA_ROOT / "audio"
IMAGES_DIR = MEDIA_ROOT / "images"


def _s3_configured() -> bool:
    return bool(settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key)


_FILENAME_AUDIO_EXT = {
    ".mp3": "mp3",
    ".mpeg": "mp3",
    ".ogg": "ogg",
    ".mp4": "mp4",
    ".m4a": "m4a",
    ".wav": "wav",
    ".webm": "webm",
    ".aac": "aac",
}


def _audio_ext(content_type: str, filename: str = "") -> str:
    name = (filename or "").lower()
    for suffix, ext in _FILENAME_AUDIO_EXT.items():
        if name.endswith(suffix):
            return ext
    ct = content_type.lower()
    if "mpeg" in ct or "mp3" in ct:
        return "mp3"
    if "ogg" in ct:
        return "ogg"
    if "mp4" in ct or "m4a" in ct:
        return "mp4"
    if "wav" in ct:
        return "wav"
    if "aac" in ct:
        return "aac"
    return "webm"


def save_audio(
    file_bytes: bytes,
    content_type: str = "audio/webm",
    filename: str = "",
) -> tuple[str, str]:
    """Save audio and return (relative_url_path, local_path)."""
    ext = _audio_ext(content_type, filename)
    filename = f"{uuid.uuid4()}.{ext}"

    if _s3_configured():
        from app.services.s3 import upload_audio
        url = upload_audio(file_bytes, content_type=content_type)
        return url, ""

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    local_path = AUDIO_DIR / filename
    local_path.write_bytes(file_bytes)
    return f"/media/audio/{filename}", str(local_path)


def save_image(file_bytes: bytes, content_type: str = "image/png") -> tuple[str, str]:
    """Save image and return (relative_url_path, local_path)."""
    ext = "png"
    if "jpeg" in content_type or "jpg" in content_type:
        ext = "jpg"
    elif "webp" in content_type:
        ext = "webp"
    filename = f"{uuid.uuid4()}.{ext}"

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    local_path = IMAGES_DIR / filename
    local_path.write_bytes(file_bytes)
    return f"/media/images/{filename}", str(local_path)


def _extract_media_path(url: str) -> str | None:
    """Extract the /media/... relative path from either a relative or absolute URL."""
    if url.startswith("/media/"):
        return url
    parsed = urlparse(url)
    if parsed.path.startswith("/media/"):
        return parsed.path
    return None


def resolve_local_path(url: str) -> Path | None:
    """If url points to a local /media/... file, return the absolute Path on disk."""
    media_path = _extract_media_path(url)
    if media_path is None:
        return None
    rel = media_path.lstrip("/")
    candidate = MEDIA_ROOT.parent / rel
    return candidate if candidate.exists() else None


# Keep backward-compatible alias
resolve_audio_local_path = resolve_local_path
