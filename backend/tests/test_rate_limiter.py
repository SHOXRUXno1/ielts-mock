import asyncio

import pytest

from app.core.rate_limiter import AsyncSemaphorePool


@pytest.mark.asyncio
async def test_try_acquire_nowait_does_not_use_asyncio_semaphore():
    pool = AsyncSemaphorePool(1)
    assert pool.try_acquire_nowait() is True
    assert pool.try_acquire_nowait() is False
    pool.release()
    assert pool.try_acquire_nowait() is True
    pool.release()


@pytest.mark.asyncio
async def test_async_acquire_waits_until_release():
    pool = AsyncSemaphorePool(1)
    assert pool.try_acquire_nowait() is True

    got = asyncio.Event()

    async def waiter() -> None:
        async with pool.acquire():
            got.set()

    task = asyncio.create_task(waiter())
    await asyncio.sleep(0)
    assert got.is_set() is False
    pool.release()
    await asyncio.wait_for(task, timeout=1)
    assert got.is_set() is True
