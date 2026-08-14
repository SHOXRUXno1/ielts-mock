"""Postgres advisory lock so only one gunicorn worker runs background tasks."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

logger = logging.getLogger(__name__)

# Stable app-wide lock id (int4). Must not collide with other apps on the same DB.
BACKGROUND_LOCK_KEY = 874_512_03


async def try_acquire_background_lock(engine: AsyncEngine) -> AsyncConnection | None:
    """
    Try to acquire a session-level advisory lock.

    Returns an open connection that holds the lock for the process lifetime,
    or None if another worker already owns it. Caller must keep the connection
    open and release via ``release_background_lock``.
    """
    conn = await engine.connect()
    try:
        got = (
            await conn.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": BACKGROUND_LOCK_KEY},
            )
        ).scalar()
        if not got:
            await conn.close()
            logger.info("Background advisory lock not acquired — skipping worker tasks")
            return None
        logger.info("Background advisory lock acquired")
        return conn
    except Exception:
        await conn.close()
        raise


async def release_background_lock(conn: AsyncConnection | None) -> None:
    if conn is None:
        return
    try:
        await conn.execute(
            text("SELECT pg_advisory_unlock(:key)"),
            {"key": BACKGROUND_LOCK_KEY},
        )
    except Exception:
        logger.exception("Failed to release background advisory lock")
    finally:
        await conn.close()
