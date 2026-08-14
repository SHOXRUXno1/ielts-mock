#!/usr/bin/env python3
"""Load smoke for ~15 concurrent students (+ optional Speaking wave).

Usage (from backend/, API already running):
  python scripts/load_test_15.py --base-url http://localhost:8000 \\
      --students 15 --test-id <UUID> --token <student JWT>

Or create ephemeral students with an admin token:
  python scripts/load_test_15.py --admin-token <JWT> --test-id <UUID>

Reports p95 latency per endpoint and writing-band wait time.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
import uuid
from dataclasses import dataclass, field

import httpx


@dataclass
class Timings:
    samples: dict[str, list[float]] = field(default_factory=dict)

    def add(self, name: str, seconds: float) -> None:
        self.samples.setdefault(name, []).append(seconds)

    def report(self) -> None:
        print("\n=== Latency report (seconds) ===")
        for name, vals in sorted(self.samples.items()):
            if not vals:
                continue
            vals_sorted = sorted(vals)
            p95 = vals_sorted[max(0, int(len(vals_sorted) * 0.95) - 1)]
            print(
                f"{name:28s}  n={len(vals):3d}  "
                f"avg={statistics.mean(vals):.3f}  p95={p95:.3f}  "
                f"max={max(vals):.3f}"
            )


async def _timed(timings: Timings, name: str, coro):
    t0 = time.perf_counter()
    try:
        return await coro
    finally:
        timings.add(name, time.perf_counter() - t0)


async def _login_student(
    client: httpx.AsyncClient,
    login: str,
    password: str,
    timings: Timings,
) -> str:
    resp = await _timed(
        timings,
        "POST /auth/login",
        client.post("/auth/login", json={"login": login, "password": password}),
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def _ensure_student(
    client: httpx.AsyncClient,
    admin_token: str,
    phone: str,
    timings: Timings,
) -> str:
    """Create student (phone = login = password). Returns login."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post(
        "/admin/students/",
        headers=headers,
        json={
            "phone": phone,
            "full_name": f"Load {phone}",
            "group_name": "load15",
        },
    )
    # 201 created or 400 already exists — both fine for smoke.
    if resp.status_code not in (200, 201, 400, 409, 422):
        resp.raise_for_status()
    timings.add("POST /admin/students", 0.0)
    return phone


async def _run_student_flow(
    base_url: str,
    test_id: str,
    token: str,
    timings: Timings,
    *,
    autosave_rounds: int,
    poll_seconds: int,
) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0, headers=headers) as client:
        start = await _timed(
            timings,
            "POST /attempts",
            client.post(f"/tests/{test_id}/attempts"),
        )
        if start.status_code == 409:
            # Resume current
            cur = await client.get(f"/tests/{test_id}/attempts/current")
            cur.raise_for_status()
            attempt = cur.json()
        else:
            start.raise_for_status()
            attempt = start.json()
        attempt_id = attempt["id"]

        enter = await _timed(
            timings,
            "POST /sections/enter",
            client.post(f"/attempts/{attempt_id}/sections/listening/enter"),
        )
        # Listening may already be sealed in a resumed attempt — ignore 409.
        if enter.status_code not in (200, 409):
            enter.raise_for_status()

        # Minimal autosave loop (no real questions required — empty payload ok).
        for _ in range(autosave_rounds):
            save = await _timed(
                timings,
                "POST /answers",
                client.post(
                    f"/attempts/{attempt_id}/answers",
                    json={"answers": []},
                ),
            )
            if save.status_code not in (200, 400, 409):
                save.raise_for_status()
            await asyncio.sleep(0.2)

        finish = await _timed(
            timings,
            "POST /finish",
            client.post(f"/attempts/{attempt_id}/finish"),
        )
        if finish.status_code not in (200, 400):
            finish.raise_for_status()

        writing_band = None
        deadline = time.time() + poll_seconds
        while time.time() < deadline:
            detail = await _timed(
                timings,
                "GET /results/{id}",
                client.get(f"/results/{attempt_id}"),
            )
            if detail.status_code == 200:
                body = detail.json()
                writing_band = body.get("writing_band")
                jobs = body.get("evaluation_jobs") or []
                pending = any(
                    j.get("status") in ("pending", "processing") for j in jobs
                )
                if writing_band is not None or not pending:
                    break
            await asyncio.sleep(2.0)

        return {"attempt_id": attempt_id, "writing_band": writing_band}


async def _run_speaking_wave(
    base_url: str,
    token: str,
    timings: Timings,
    n: int,
) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}"}

    async def one(i: int) -> dict:
        async with httpx.AsyncClient(
            base_url=base_url, timeout=30.0, headers=headers
        ) as client:
            resp = await _timed(
                timings,
                "GET /simli-token",
                client.get("/admin/speaking-examiner/simli-token"),
            )
            data = resp.json() if resp.status_code == 200 else {"error": resp.text}
            return {"i": i, "status": resp.status_code, "body": data}

    return list(await asyncio.gather(*[one(i) for i in range(n)]))


async def main_async(args: argparse.Namespace) -> int:
    timings = Timings()
    tokens: list[str] = []

    if args.token:
        tokens = [args.token] * args.students
    elif args.admin_token:
        async with httpx.AsyncClient(base_url=args.base_url, timeout=30.0) as client:
            for i in range(args.students):
                # Phone doubles as login+password in this API.
                phone = f"+7999{i:02d}{uuid.uuid4().int % 10_000_000:07d}"
                login = await _ensure_student(
                    client, args.admin_token, phone, timings
                )
                tok = await _login_student(client, login, login, timings)
                tokens.append(tok)
    else:
        raise SystemExit("Provide --token or --admin-token")

    print(f"Running {len(tokens)} student flows against test {args.test_id}…")
    results = await asyncio.gather(
        *[
            _run_student_flow(
                args.base_url,
                args.test_id,
                tok,
                timings,
                autosave_rounds=args.autosave_rounds,
                poll_seconds=args.poll_seconds,
            )
            for tok in tokens
        ],
        return_exceptions=True,
    )

    ok = 0
    for r in results:
        if isinstance(r, Exception):
            print(f"FAIL: {r}")
        else:
            ok += 1
            print(
                f"OK attempt={r['attempt_id']} writing_band={r['writing_band']}"
            )
    print(f"Student flows ok: {ok}/{len(results)}")

    if args.speaking > 0:
        print(f"Speaking wave: {args.speaking} parallel simli-token calls…")
        wave = await _run_speaking_wave(
            args.base_url, tokens[0], timings, args.speaking
        )
        enabled = sum(
            1
            for w in wave
            if isinstance(w.get("body"), dict) and w["body"].get("enabled") is True
        )
        capacity = sum(
            1
            for w in wave
            if isinstance(w.get("body"), dict)
            and w["body"].get("reason") == "capacity"
        )
        print(f"Simli enabled={enabled} capacity_reject={capacity}")

    timings.report()
    return 0 if ok == len(results) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--test-id", required=True)
    p.add_argument("--students", type=int, default=15)
    p.add_argument("--token", default=None, help="Reuse one student JWT")
    p.add_argument("--admin-token", default=None, help="Create ephemeral students")
    p.add_argument("--autosave-rounds", type=int, default=3)
    p.add_argument("--poll-seconds", type=int, default=120)
    p.add_argument(
        "--speaking",
        type=int,
        default=8,
        help="Parallel GET /speaking-examiner/simli-token calls (0 to skip)",
    )
    return p


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(build_parser().parse_args())))
