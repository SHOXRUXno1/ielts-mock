"""Correct the Dodo notes lead line in Practice set #24 without reseeding it.

The introductory sentence is context, not a note.  It must render as a plain
lead line, while the history and description entries below it remain bullets.
Run with ``--apply`` only after the script has first reported the expected
single target.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import uuid

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import async_session
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType


TEST_ID = uuid.UUID("d0538daf-1df0-4443-815d-b4cd5c03fe38")
INTRO = "The dodo was a large flightless bird which used to inhabit the island of Mauritius."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="persist the correction; without this flag, only inspect the target",
    )
    return parser.parse_args()


def item_text(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    segments = item.get("segments")
    if not isinstance(segments, list):
        return ""
    return "".join(
        segment.get("value", "")
        for segment in segments
        if isinstance(segment, dict) and segment.get("type") == "text"
    )


async def run(*, apply: bool) -> int:
    async with async_session() as session:
        groups = (
            await session.execute(
                select(QuestionGroup)
                .join(Section)
                .where(
                    Section.test_id == TEST_ID,
                    Section.type == SectionType.LISTENING,
                )
                .order_by(Section.order, QuestionGroup.order)
            )
        ).scalars().all()

        matches: list[tuple[QuestionGroup, int, int]] = []
        for group in groups:
            structure = group.options_shared
            if not isinstance(structure, dict) or structure.get("variant") != "notes":
                continue
            sections = structure.get("sections")
            if not isinstance(sections, list):
                continue
            for section_index, notes_section in enumerate(sections):
                if not isinstance(notes_section, dict):
                    continue
                items = notes_section.get("items")
                if not isinstance(items, list):
                    continue
                for item_index, item in enumerate(items):
                    if item_text(item) == INTRO:
                        matches.append((group, section_index, item_index))

        if len(matches) != 1:
            raise RuntimeError(
                f"Expected exactly one Dodo introductory line in Test {TEST_ID}; found {len(matches)}."
            )

        group, section_index, item_index = matches[0]
        structure = copy.deepcopy(group.options_shared)
        assert isinstance(structure, dict)
        item = structure["sections"][section_index]["items"][item_index]
        assert isinstance(item, dict)
        current_role = item.get("role")

        print(
            "Matched Dodo introduction in "
            f"group {group.id}; current role={current_role!r}, desired role='lead'."
        )
        if current_role == "lead":
            print("No update needed; the Dodo introduction is already a plain lead line.")
            return 0
        if current_role not in (None, ""):
            raise RuntimeError(
                f"Refusing to replace unexpected role {current_role!r} on the Dodo introduction."
            )

        if not apply:
            print("Dry run only. Re-run with --apply to persist this correction.")
            return 0

        item["role"] = "lead"
        group.options_shared = structure
        flag_modified(group, "options_shared")
        await session.commit()
        print("Updated Dodo introduction to role='lead'.")
        return 0


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(asyncio.run(run(apply=arguments.apply)))
