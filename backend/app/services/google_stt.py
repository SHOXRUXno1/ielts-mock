"""Google Cloud Speech-to-Text v2 (Chirp) for live Speaking turns.

Chirp 3 is what products like ielts.gg use for the same job: short
candidate answers, British-English exam speech. The call is a plain
Recognize against the regional v2 endpoint. Service-account JSON is
minted into an access token here so the rest of the app can keep using
httpx instead of pulling in the full Google client libraries.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from app.core.config import settings
from app.services.shared_http import get_http_client

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_TOKEN_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
_TOKEN_TTL_S = 3600
_TOKEN_REFRESH_S = 60

_UNSET = object()
_credentials: dict[str, Any] | None | object = _UNSET
_access_token: str | None = None
_access_token_expires_at = 0.0
_blocked = False

# Sync Recognize rejects anything over 60s. Chunks stay under that with
# room for ffmpeg seek slop so a 120s Part 2 still fits on Chirp.
_SYNC_LIMIT_S = 55.0
_EMPTY_WAV_BYTES = 16_000  # ~0.5s of 16 kHz 16-bit mono; shorter is noise


def reset() -> None:
    """Clear cached credentials, token, and the circuit. Tests call this."""
    global _credentials, _access_token, _access_token_expires_at, _blocked
    _credentials = _UNSET
    _access_token = None
    _access_token_expires_at = 0.0
    _blocked = False


def is_blocked() -> bool:
    return _blocked


def block(reason: str) -> None:
    global _blocked
    if not _blocked:
        logger.error("Disabling Google STT for this process (%s)", reason)
    _blocked = True


def is_configured() -> bool:
    return load_credentials() is not None


def load_credentials() -> dict[str, Any] | None:
    """Parse the service-account JSON once and keep it for the process."""
    global _credentials
    if _credentials is not _UNSET:
        return _credentials if isinstance(_credentials, dict) else None

    raw = settings.google_stt_credentials_json.strip()
    if not raw:
        path = settings.google_application_credentials.strip()
        if path:
            try:
                raw = Path(path).read_text(encoding="utf-8")
            except OSError as exc:
                logger.error("Google STT credentials file is unreadable: %s", exc)
                _credentials = None
                return None
    if not raw:
        _credentials = None
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Google STT credentials JSON is not valid")
        _credentials = None
        return None

    if not isinstance(parsed, dict) or not parsed.get("private_key") or not parsed.get(
        "client_email"
    ):
        logger.error("Google STT credentials JSON is missing private_key or client_email")
        _credentials = None
        return None

    _credentials = parsed
    return parsed


def project_id() -> str:
    if settings.google_cloud_project.strip():
        return settings.google_cloud_project.strip()
    creds = load_credentials() or {}
    return str(creds.get("project_id") or "")


def transcript_from_response(payload: dict[str, Any]) -> str:
    """Join every result's top alternative. Empty payload is silence."""
    parts: list[str] = []
    for result in payload.get("results") or []:
        if not isinstance(result, dict):
            continue
        alternatives = result.get("alternatives") or []
        if not alternatives or not isinstance(alternatives[0], dict):
            continue
        text = alternatives[0].get("transcript")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return " ".join(parts)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _service_account_jwt(creds: dict[str, Any], now: int) -> str:
    header = _b64url(
        json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    payload = _b64url(
        json.dumps(
            {
                "iss": creds["client_email"],
                "sub": creds["client_email"],
                "aud": _TOKEN_URL,
                "iat": now,
                "exp": now + _TOKEN_TTL_S,
                "scope": _TOKEN_SCOPE,
            },
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode()
    key = load_pem_private_key(creds["private_key"].encode(), password=None)
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{payload}.{_b64url(signature)}"


async def _access_token_value() -> str:
    global _access_token, _access_token_expires_at
    now = time.time()
    if _access_token and now < _access_token_expires_at - _TOKEN_REFRESH_S:
        return _access_token

    creds = load_credentials()
    if creds is None:
        raise RuntimeError("Google STT credentials are not configured")

    assertion = _service_account_jwt(creds, int(now))
    client = get_http_client()
    resp = await client.post(
        _TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=30.0,
    )
    if resp.status_code >= 400:
        logger.error("Google STT token exchange failed (%s)", resp.status_code)
    resp.raise_for_status()
    body = resp.json()
    token = body.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Google STT token exchange returned no access_token")
    expires_in = body.get("expires_in")
    ttl = int(expires_in) if isinstance(expires_in, (int, float)) else _TOKEN_TTL_S
    _access_token = token
    _access_token_expires_at = now + ttl
    return token


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def is_duration_limit_error(exc: BaseException) -> bool:
    """Google's wording for 'this clip is longer than sync Recognize allows'."""
    if not isinstance(exc, httpx.HTTPStatusError):
        return False
    body = (exc.response.text or "").lower()
    return (
        "60 seconds" in body
        or "1 minute" in body
        or "1 min" in body
        or "sync input too long" in body
        or "exceeds duration limit" in body
    )


def _join_chunk_transcripts(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


async def recognize(audio_bytes: bytes) -> str:
    """Transcribe with Chirp. Clips over ~60s are split, then recognized in parallel.

    Google will not raise the sync Recognize ceiling — 60 seconds is a hard
    product limit. Batch needs a GCS bucket; streaming is gRPC and wants
    near-realtime send. For a 2-minute Part 2 the honest path on this stack
    is cut-and-stitch.
    """
    if ffmpeg_available():
        chunks = await split_for_sync_recognize(audio_bytes)
        if len(chunks) > 1:
            return await _recognize_chunks(chunks)

    try:
        return await recognize_once(audio_bytes)
    except httpx.HTTPStatusError as exc:
        if is_duration_limit_error(exc) and ffmpeg_available():
            chunks = await split_for_sync_recognize(audio_bytes, force=True)
            if len(chunks) > 1:
                return await _recognize_chunks(chunks)
        raise


async def _recognize_chunks(chunks: list[bytes]) -> str:
    logger.info("Google STT recognizing %d chunks in parallel", len(chunks))
    parts = await asyncio.gather(*[recognize_once(chunk) for chunk in chunks])
    text = _join_chunk_transcripts(list(parts))
    logger.info("Google STT joined %d chunks → %d chars", len(chunks), len(text))
    return text


async def recognize_once(audio_bytes: bytes) -> str:
    """One synchronous Chirp Recognize. Audio longer than ~60s is rejected."""
    project = project_id()
    if not project:
        raise RuntimeError("Google STT project_id is missing")

    location = settings.google_stt_location.strip() or "us"
    model = settings.google_stt_model.strip() or "chirp_3"
    token = await _access_token_value()
    url = (
        f"https://{location}-speech.googleapis.com/v2/projects/{project}"
        f"/locations/{location}/recognizers/_:recognize"
    )
    payload = {
        "config": {
            "autoDecodingConfig": {},
            "languageCodes": ["en-GB"],
            "model": model,
            "features": {"enableAutomaticPunctuation": True},
        },
        "configMask": "*",
        "content": base64.b64encode(audio_bytes).decode("ascii"),
    }
    client = get_http_client()
    resp = await client.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        # Wall-clock wait is longer than the 60s *audio* limit so a 55s
        # clip that Chirp is still chewing is not cut by our client first.
        timeout=120.0,
    )
    if resp.status_code >= 400:
        logger.error(
            "Google STT recognize failed (%s): %s",
            resp.status_code,
            resp.text[:500],
        )
    resp.raise_for_status()
    transcript = transcript_from_response(resp.json())
    logger.info("Google STT (%s) transcript length: %d chars", model, len(transcript))
    return transcript


async def split_for_sync_recognize(
    audio_bytes: bytes,
    *,
    force: bool = False,
) -> list[bytes]:
    """Cut a long take into ≤55s WAV pieces Chirp will accept."""
    with tempfile.TemporaryDirectory(prefix="chirp-") as tmp:
        src = Path(tmp) / "in.webm"
        src.write_bytes(audio_bytes)
        duration = await _probe_duration_s(src)
        if duration is not None and duration <= _SYNC_LIMIT_S and not force:
            return [audio_bytes]
        if duration is None and not force:
            return [audio_bytes]
        chunks = await _extract_chunks(src, duration)
        return chunks or [audio_bytes]


async def _probe_duration_s(path: Path) -> float | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return None
    out, _err = await proc.communicate()
    if proc.returncode != 0:
        return None
    raw = out.decode("utf-8", errors="replace").strip()
    try:
        value = float(raw)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


async def _extract_chunks(src: Path, duration: float | None) -> list[bytes]:
    chunks: list[bytes] = []
    start = 0.0
    limit = duration if duration is not None else 180.0
    idx = 0
    while start < limit - 0.05:
        dest = src.with_name(f"chunk-{idx}.wav")
        ok = await _cut_wav(src, dest, start, _SYNC_LIMIT_S)
        if not ok or dest.stat().st_size < _EMPTY_WAV_BYTES:
            break
        chunks.append(dest.read_bytes())
        start += _SYNC_LIMIT_S
        idx += 1
        if duration is None and idx >= 4:
            break
    return chunks


async def _cut_wav(src: Path, dest: Path, start: float, length: float) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(src),
            "-ss",
            f"{start:.2f}",
            "-t",
            f"{length:.2f}",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(dest),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return False
    _out, err = await proc.communicate()
    if proc.returncode != 0:
        logger.warning("ffmpeg cut failed: %s", err.decode("utf-8", errors="replace")[:300])
        return False
    return dest.exists()
