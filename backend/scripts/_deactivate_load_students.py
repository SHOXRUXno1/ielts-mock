#!/usr/bin/env python3
"""Deactivate load-test students via the admin API (soft delete, reversible).

  python scripts/_deactivate_load_students.py \\
      --base-url https://mock.shox-software.uz \\
      --admin-login Adminbek --admin-password '...'
"""

from __future__ import annotations

import argparse
import asyncio

import httpx

TEST_GROUPS = ("load-writing", "load-speaking")


async def main_async(args: argparse.Namespace) -> int:
    async with httpx.AsyncClient(base_url=args.base_url, timeout=60.0) as client:
        login = await client.post(
            "/auth/login",
            json={"login": args.admin_login, "password": args.admin_password},
        )
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        targets: list[dict] = []
        for group in TEST_GROUPS:
            resp = await client.get(
                "/admin/students/",
                headers=headers,
                params={"group": group, "is_active": True, "limit": 500},
            )
            resp.raise_for_status()
            targets.extend(resp.json())

        if not targets:
            print("No active load-test students found.")
            return 0

        print(f"Deactivating {len(targets)} load-test students…")
        done = 0
        for student in targets:
            resp = await client.delete(
                f"/admin/students/{student['id']}", headers=headers
            )
            if resp.status_code in (200, 204):
                done += 1
            else:
                print(f"  FAILED {student['login']}: HTTP {resp.status_code}")
        print(f"Deactivated {done}/{len(targets)}.")
        return 0 if done == len(targets) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", required=True)
    p.add_argument("--admin-login", default="admin")
    p.add_argument("--admin-password", required=True)
    return p


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(build_parser().parse_args())))
