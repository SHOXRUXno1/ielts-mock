"""Token-bucket rate limiter with round-robin key rotation for Gemini API."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator


class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    async def acquire(self) -> None:
        while True:
            self._refill()
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            wait = (1.0 - self.tokens) / self.rate
            await asyncio.sleep(wait)


class KeyRotator:
    """Round-robin API key rotation with per-key rate limiting."""

    def __init__(self, keys: list[str], rpm_per_key: int = 15):
        self._keys = keys
        self._buckets = {key: TokenBucket(rate=rpm_per_key / 60.0, capacity=rpm_per_key) for key in keys}
        self._index = 0

    async def get_key(self) -> str:
        if not self._keys:
            raise RuntimeError("No Gemini API keys configured")

        key = self._keys[self._index % len(self._keys)]
        self._index += 1
        await self._buckets[key].acquire()
        return key

    async def acquire_for(self, key: str) -> None:
        """Wait for rate-limit bucket of a specific key."""
        if key not in self._buckets:
            raise RuntimeError("Unknown Gemini API key")
        await self._buckets[key].acquire()


class AsyncSemaphorePool:
    """Concurrency cap that works on Python 3.12+ (no Semaphore.acquire_nowait)."""

    def __init__(self, limit: int):
        self._limit = max(1, limit)
        self._available = self._limit
        self._cond: asyncio.Condition | None = None

    def _get_cond(self) -> asyncio.Condition:
        if self._cond is None:
            self._cond = asyncio.Condition()
        return self._cond

    def try_acquire_nowait(self) -> bool:
        """Non-blocking acquire. Caller must release() if True."""
        if self._available <= 0:
            return False
        self._available -= 1
        return True

    def release(self) -> None:
        self._available = min(self._limit, self._available + 1)
        cond = self._cond
        if cond is None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        async def _notify() -> None:
            async with cond:
                cond.notify()

        loop.create_task(_notify())

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        cond = self._get_cond()
        async with cond:
            while self._available <= 0:
                await cond.wait()
            self._available -= 1
        try:
            yield
        finally:
            self.release()


_whisper_pool: AsyncSemaphorePool | None = None
_elevenlabs_pool: AsyncSemaphorePool | None = None


def get_whisper_pool() -> AsyncSemaphorePool:
    global _whisper_pool
    if _whisper_pool is None:
        from app.core.config import settings

        _whisper_pool = AsyncSemaphorePool(settings.whisper_max_concurrent)
    return _whisper_pool


def get_elevenlabs_pool() -> AsyncSemaphorePool:
    global _elevenlabs_pool
    if _elevenlabs_pool is None:
        from app.core.config import settings

        _elevenlabs_pool = AsyncSemaphorePool(settings.elevenlabs_max_concurrent)
    return _elevenlabs_pool
