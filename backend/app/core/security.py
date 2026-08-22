from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

# bcrypt only consumes the first 72 bytes; truncate explicitly so long inputs
# verify instead of raising.
_BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(plain), hashed.encode("utf-8"))
    except ValueError:
        # Malformed or unsupported hash in the row — treat as a failed login.
        return False


async def hash_password_async(password: str) -> str:
    """Hashing costs ~100ms of CPU; keep it off the event loop."""
    return await run_in_threadpool(hash_password, password)


async def verify_password_async(plain: str, hashed: str) -> bool:
    return await run_in_threadpool(verify_password, plain, hashed)


def create_access_token(subject: int | str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
