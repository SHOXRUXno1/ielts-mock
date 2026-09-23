"""Provision or deactivate an isolated student for browser acceptance testing.

The account is deliberately separate from real students.  Its password is the
same as its login, matching the existing admin-created-student convention; the
workflow that invokes this script never prints that value.

Usage inside the backend container:
    python scripts/qa_browser_student.py provision qa-browser-20260923
    python scripts/qa_browser_student.py deactivate qa-browser-20260923
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password_async
from app.models.user import User


LOGIN_PATTERN = re.compile(r"^qa-[a-z0-9-]{3,80}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("provision", "deactivate"))
    parser.add_argument("login")
    args = parser.parse_args()
    if not LOGIN_PATTERN.fullmatch(args.login):
        parser.error("login must begin with 'qa-' and use only lowercase letters, digits and hyphens")
    return args


async def run(action: str, login: str) -> int:
    async with async_session() as session:
        user = (
            await session.execute(select(User).where(User.login == login))
        ).scalar_one_or_none()

        if action == "deactivate":
            if user is None:
                print(f"QA student {login!r} does not exist; nothing to deactivate.")
                return 0
            user.is_active = False
            await session.commit()
            print(f"QA student {login!r} is inactive.")
            return 0

        if user is None:
            user = User(
                login=login,
                hashed_password=await hash_password_async(login),
                full_name="QA Browser Student",
                phone=login,
                group_name="QA",
                role="student",
                is_active=True,
            )
            session.add(user)
            outcome = "created"
        else:
            # Re-enabling a previously used QA login also rotates the known
            # test password, so no stale browser session can keep using it.
            user.hashed_password = await hash_password_async(login)
            user.full_name = "QA Browser Student"
            user.group_name = "QA"
            user.role = "student"
            user.is_active = True
            outcome = "re-enabled"

        await session.commit()
        print(f"QA student {login!r} {outcome} and ready for browser testing.")
        return 0


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(asyncio.run(run(arguments.action, arguments.login)))
