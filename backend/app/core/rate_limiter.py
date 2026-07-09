"""Token-bucket rate limiter with round-robin key rotation for Gemini API."""

import asyncio
import time


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
