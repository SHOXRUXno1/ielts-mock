"""Delete the load-writing test students and everything they created."""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import delete, select

sys.path.insert(0, ".")

from app.core.database import async_session  # noqa: E402
from app.models.attempt import Attempt  # noqa: E402
from app.models.user import User  # noqa: E402


async def main() -> None:
    async with async_session() as db:
        user_ids = (
            await db.execute(
                select(User.id).where(User.group_name == "load-writing")
            )
        ).scalars().all()
        if not user_ids:
            print("Nothing to clean.")
            return

        attempt_ids = (
            await db.execute(
                select(Attempt.id).where(Attempt.user_id.in_(user_ids))
            )
        ).scalars().all()

        # answers / evaluation_jobs / section_progress cascade from attempts.
        await db.execute(delete(Attempt).where(Attempt.id.in_(attempt_ids)))
        await db.execute(delete(User).where(User.id.in_(user_ids)))
        await db.commit()
        print(f"Deleted {len(user_ids)} students and {len(attempt_ids)} attempts.")


asyncio.run(main())
