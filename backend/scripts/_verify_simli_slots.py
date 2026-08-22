"""Prove the video-slot gate holds under a simultaneous start.

Three checks against real Postgres:

  1. A burst of candidates claiming at the very same moment: exactly as many
     are admitted as the plan allows, no more. This is the case that counting
     sessions could never catch, because the browser asks for a token before
     its exam session exists.
  2. Candidates mid-answer keep their slots, so video is genuinely rationed.
  3. Sessions that fell silent hand their slots back without waiting for the
     abandon sweep.

    python scripts/_verify_simli_slots.py --admin-login X --admin-password Y

Check 1 needs no Simli account and no network. Checks 2 and 3 talk to the
running server, so they need the login.
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
from app.models.simli_lease import SimliSlotLease  # noqa: E402
from app.models.speaking_session import SpeakingSession, SpeakingState  # noqa: E402
from app.services.simli_slots import claim_slot, occupied_slots  # noqa: E402

SEED_PREFIX = "slot-probe-"
BURST_PREFIX = "burst-"


async def purge() -> None:
    """Reset between checks. Every lease goes, including the operator's own from
    an earlier check — otherwise the gate rightly renews their existing claim
    and the next check measures nothing. Leases are short-lived claims, so
    clearing them on a test database costs nothing."""
    async with async_session() as db:
        await db.execute(
            delete(SpeakingSession).where(
                SpeakingSession.admin_email.like(f"{SEED_PREFIX}%")
            )
        )
        await db.execute(delete(SimliSlotLease))
        await db.commit()


async def seed_sessions(n: int, *, idle_minutes: float) -> None:
    """One session per candidate, each a different person — a slot is held by a
    candidate, so seeding many sessions for one email would rightly count once."""
    stamp = datetime.now(timezone.utc) - timedelta(minutes=idle_minutes)
    async with async_session() as db:
        await db.execute(
            insert(SpeakingSession),
            [
                {
                    "id": uuid.uuid4(),
                    "admin_email": f"{SEED_PREFIX}{i:02d}@load.test",
                    "status": "in_progress",
                    "current_state": SpeakingState.PART_1_ACTIVE.value,
                    "created_at": stamp,
                    "updated_at": stamp,
                    "state_entered_at": stamp,
                    "current_question_index": 1,
                }
                for i in range(n)
            ],
        )
        await db.commit()


async def age_seeded(idle_minutes: float) -> None:
    stamp = datetime.now(timezone.utc) - timedelta(minutes=idle_minutes)
    async with async_session() as db:
        await db.execute(
            update(SpeakingSession)
            .where(SpeakingSession.admin_email.like(f"{SEED_PREFIX}%"))
            .values(updated_at=stamp, state_entered_at=stamp)
        )
        await db.commit()


async def _claim_as(actor: str, gate: asyncio.Event) -> bool:
    """One candidate, on its own connection, released at the same instant as
    everyone else."""
    async with async_session() as db:
        await gate.wait()
        granted, _ = await claim_slot(db, actor)
        return granted


async def burst(n: int) -> tuple[int, int]:
    gate = asyncio.Event()
    tasks = [
        asyncio.create_task(_claim_as(f"{BURST_PREFIX}{i:02d}@load.test", gate))
        for i in range(n)
    ]
    await asyncio.sleep(0.3)  # let every task reach the gate first
    gate.set()
    results = await asyncio.gather(*tasks)
    async with async_session() as db:
        return sum(results), await occupied_slots(db)


async def ask_gate(client: httpx.AsyncClient) -> str:
    resp = await client.get("/admin/speaking-examiner/simli-token")
    resp.raise_for_status()
    body = resp.json()
    if body.get("enabled"):
        return "VIDEO granted"
    return f"refused: {body.get('reason')} — {body.get('detail', '')}".strip(" —")


async def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--admin-login")
    p.add_argument("--admin-password")
    p.add_argument("--students", type=int, default=25)
    p.add_argument(
        "--claim-only",
        type=int,
        help="Claim N slots and print how many were admitted, then exit. "
        "Run several of these at once to prove the gate holds across "
        "separate processes the way it must behind gunicorn.",
    )
    p.add_argument(
        "--prefix",
        default=BURST_PREFIX,
        help="Actor prefix, so parallel processes use distinct candidates.",
    )
    args = p.parse_args()

    if args.claim_only:
        gate = asyncio.Event()
        gate.set()
        admitted = sum(
            await asyncio.gather(
                *[
                    _claim_as(f"{args.prefix}{i:02d}@load.test", gate)
                    for i in range(args.claim_only)
                ]
            )
        )
        print(f"{args.prefix}: admitted {admitted} of {args.claim_only}")
        return

    if not args.admin_login or not args.admin_password:
        p.error("--admin-login and --admin-password are required")

    cap = settings.simli_max_concurrent
    print(f"plan allows {cap} concurrent video sessions")
    print(f"lease {settings.simli_lease_minutes} min, "
          f"idle cutoff {settings.simli_slot_idle_minutes} min\n")

    await purge()
    try:
        async with async_session() as db:
            before = await occupied_slots(db)
        expected = max(0, cap - before)

        print(f"--- {args.students} candidates claim at the same instant ---")
        print(f"  occupied beforehand: {before}")
        granted, occupied = await burst(args.students)
        verdict = "OK" if granted == expected else "OVERSHOOT"
        print(f"  admitted {granted}, refused {args.students - granted}")
        print(f"  slots now occupied: {occupied}")
        print(f"  {verdict}: expected exactly {expected} admitted\n")

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
            await seed_sessions(cap, idle_minutes=0)
            print(f"--- {cap} candidates mid-answer ---")
            print(f"  {await ask_gate(client)}   (expected: refused)")

            await purge()
            await seed_sessions(cap, idle_minutes=0)
            await age_seeded(settings.simli_slot_idle_minutes + 5)
            print(f"\n--- same {cap} sessions, silent for "
                  f"{settings.simli_slot_idle_minutes + 5} min ---")
            print(f"  {await ask_gate(client)}   (expected: granted)")
    finally:
        await purge()
        print("\nseeded rows removed")


if __name__ == "__main__":
    asyncio.run(main())
