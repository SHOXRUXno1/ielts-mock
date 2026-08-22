"""Prove the video-slot gate both ways against a live server.

Seeds fake speaking sessions, asks /simli-token, and reports what the gate
decided. A slot must be held while a candidate is taking turns and released
once the session stops moving — the old gate only ever did the former.

    python scripts/_verify_simli_slots.py --admin-login X --admin-password Y
"""

import argparse
import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, insert, update  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import async_session  # noqa: E402
from app.models.speaking_session import SpeakingSession, SpeakingState  # noqa: E402

SEED_EMAIL = "slot-probe@load.test"


async def seed(n: int, *, idle_minutes: float) -> None:
    stamp = datetime.now(timezone.utc) - timedelta(minutes=idle_minutes)
    async with async_session() as db:
        await db.execute(
            insert(SpeakingSession),
            [
                {
                    "id": uuid.uuid4(),
                    "admin_email": SEED_EMAIL,
                    "status": "in_progress",
                    "current_state": SpeakingState.PART_1_ACTIVE.value,
                    "created_at": stamp,
                    "updated_at": stamp,
                    "state_entered_at": stamp,
                    "current_question_index": 1,
                }
                for _ in range(n)
            ],
        )
        await db.commit()


async def age_seeded(idle_minutes: float) -> None:
    stamp = datetime.now(timezone.utc) - timedelta(minutes=idle_minutes)
    async with async_session() as db:
        await db.execute(
            update(SpeakingSession)
            .where(SpeakingSession.admin_email == SEED_EMAIL)
            .values(updated_at=stamp, state_entered_at=stamp)
        )
        await db.commit()


async def purge() -> None:
    async with async_session() as db:
        await db.execute(
            delete(SpeakingSession).where(SpeakingSession.admin_email == SEED_EMAIL)
        )
        await db.commit()


async def ask_gate(client: httpx.AsyncClient) -> str:
    resp = await client.get("/admin/speaking-examiner/simli-token")
    resp.raise_for_status()
    body = resp.json()
    if body.get("enabled"):
        return "VIDEO granted"
    return f"fallback: {body.get('reason')} — {body.get('detail', '')}".strip(" —")


async def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--admin-login", required=True)
    p.add_argument("--admin-password", required=True)
    args = p.parse_args()

    cap = settings.simli_max_concurrent
    idle = settings.simli_slot_idle_minutes
    print(f"capacity={cap} slots, idle cutoff={idle} min\n")

    await purge()
    async with httpx.AsyncClient(base_url=args.base_url, timeout=60.0) as anon:
        login = await anon.post(
            "/auth/login",
            json={"login": args.admin_login, "password": args.admin_password},
        )
        login.raise_for_status()
        jwt = login.json()["access_token"]

    async with httpx.AsyncClient(
        base_url=args.base_url,
        timeout=60.0,
        headers={"Authorization": f"Bearer {jwt}"},
    ) as client:
        try:
            await seed(cap, idle_minutes=0)
            print(f"{cap} candidates mid-answer (just took a turn)")
            print(f"  -> {await ask_gate(client)}")

            await age_seeded(idle + 5)
            print(f"\nsame {cap} sessions, silent for {idle + 5} min (browsers gone)")
            print(f"  -> {await ask_gate(client)}")
        finally:
            await purge()
            print("\nseeded rows removed")


if __name__ == "__main__":
    asyncio.run(main())
