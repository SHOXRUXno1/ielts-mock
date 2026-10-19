"""Restore audited Reading content IN PLACE; never run destructive seeds on prod.

Default is dry run. --apply requires an exclusive backup path. Existing question
IDs/answers/attempts/scores are retained. Refuses unreviewed data drift and any
unfinished Full Mock or Reading practice on an affected test. No force flag.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path[:0] = [str(Path(__file__).resolve().parent.parent), str(Path(__file__).resolve().parent)]

from app.core.config import settings  # noqa: E402
from app.models.attempt import Attempt  # noqa: E402
from app.models.question import Question  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section  # noqa: E402
from app.models.test import Test  # noqa: E402
from app.services.scoring import scoring_slots_for_question  # noqa: E402
from seed_practice_f_common import BOOK_SLUG, data_dir  # noqa: E402
from seed_practice_f_reading import _read_json, build_passage  # noqa: E402

AUDITED_BEFORE = {
    1: "9b2aeb813ec4ba8de2bb0e2d86212481a3b8ba4d0327667c8ee1e657e3e378eb",
    2: "bef2f8c1128eda67e46d417f8d964cc2b3002bbb6607971846e4e55413959770",
    3: "8843b640cc5ad7d079fc2ae6164aea20e50840f8d324a2d1cb5f69cf212a5f35",
    4: "d2795c7384560a1ea7bb465325888f18c4c6355bb482ce9cf4e7423079b6654b",
    5: "affabc0e70bade002e3bf3e454d1955f9a2afc1a7b893c1eae6d3ca28d8637d0",
    6: "2d033dec6bc62edbaa8d57f8fdac0d573f41b1dd758facc97d7c5a750c53d21c",
}

# Exact verified state after the content repair, before the browser-discovered
# duplicate MCQ/multi-select prefixes were removed. No arbitrary drift accepted.
AUDITED_CONTENT_REPAIRED = {
    1: "ed3e2fea4179c6d8313bcdbd50edbdb8eff8bd1078b9e36b786e20edbfd15254",
    2: "347efb67c655cfe15e5e0d8e0832d5e4f5cdc9e0111e249061e26663f78c9ffa",
    5: "7e41d456ed6dca98d7a1488f781759fb4b1971705372977ed3cedc02beeb59d6",
    6: "d10c35d8e1085a7cb5645423e65c172b8d4e592e2cf2ef80b63539217054f94b",
}


def value(v: Any) -> Any:
    return getattr(v, "value", v)


@dataclass
class GroupRows:
    record: QuestionGroup
    questions: list[Question]


@dataclass
class SectionRows:
    record: Section
    groups: list[GroupRows]


def payload(sections: list[SectionRows], *, include_ids: bool = False) -> list[dict[str, Any]]:
    result = []
    for section in sections:
        s: dict[str, Any] = {"order": section.record.order, "groups": []}
        if include_ids:
            s["id"] = str(section.record.id)
        for group in section.groups:
            g: dict[str, Any] = {
                "order": group.record.order,
                "type": value(group.record.question_type),
                "instruction": group.record.instruction,
                "options_shared": group.record.options_shared,
                "questions": [],
            }
            if include_ids:
                g.update(id=str(group.record.id), subtitle=group.record.subtitle)
            for question in group.questions:
                q = {"order": question.order, "type": value(question.question_type),
                     "content": question.content, "answer_key": question.answer_key}
                if include_ids:
                    q.update(id=str(question.id), section_id=str(question.section_id),
                             question_group_id=str(question.question_group_id))
                g["questions"].append(q)
            s["groups"].append(g)
        result.append(s)
    return result


def fingerprint(sections: list[SectionRows]) -> str:
    encoded = json.dumps(payload(sections), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def numbered(sections: list[SectionRows]) -> dict[int, tuple[Question, GroupRows, SectionRows]]:
    cursor = 1
    result = {}
    for section in sections:
        for group in section.groups:
            for q in group.questions:
                if q.section_id != section.record.id or q.question_group_id != group.record.id:
                    raise ValueError("Question/group/section ownership mismatch")
                result[cursor] = (q, group, section)
                cursor += scoring_slots_for_question(q)
    if cursor != 41:
        raise ValueError(f"Expected 40 Reading slots, found {cursor - 1}")
    return result


@dataclass
class Update:
    record: Any
    fields: dict[str, Any]


@dataclass
class RepairPlan:
    test_number: int
    before: str
    after: str
    updates: list[Update] = field(default_factory=list)
    empty_groups: list[QuestionGroup] = field(default_factory=list)


def plan_repair(test_number: int, current: list[SectionRows], desired: list[SectionRows]) -> RepairPlan:
    before, after = fingerprint(current), fingerprint(desired)
    plan = RepairPlan(test_number, before, after)
    if before == after:
        return plan
    if before not in {AUDITED_BEFORE[test_number], AUDITED_CONTENT_REPAIRED.get(test_number)}:
        raise ValueError(f"T{test_number}: published content differs from audited baseline; refusing overwrite")
    old, new = numbered(current), numbered(desired)
    if set(old) != set(new):
        raise ValueError("Question slot boundaries changed")
    used_groups = set()
    target_groups = {}
    for number, (q, group, section) in new.items():
        if group.record.id not in target_groups:
            original = old[number][1].record
            if original.id in used_groups:
                raise ValueError("Cannot split an existing group without explicit review")
            used_groups.add(original.id)
            target_groups[group.record.id] = original
            fields = {
                "section_id": section.record.id, "order": group.record.order,
                "question_type": value(group.record.question_type),
                "instruction": group.record.instruction, "options_shared": group.record.options_shared,
            }
            if any(getattr(original, k) != v for k, v in fields.items()):
                plan.updates.append(Update(original, fields))
        original_q = old[number][0]
        if scoring_slots_for_question(original_q) != scoring_slots_for_question(q):
            raise ValueError("Cannot change scoring slot allocation")
        target = target_groups[group.record.id]
        fields = {"section_id": section.record.id, "question_group_id": target.id,
                  "order": q.order, "question_type": value(q.question_type),
                  "content": q.content, "answer_key": q.answer_key}
        if any(getattr(original_q, k) != v for k, v in fields.items()):
            plan.updates.append(Update(original_q, fields))
    plan.empty_groups = [g.record for s in current for g in s.groups if g.record.id not in used_groups]
    return plan


async def load_graph(db: AsyncSession, test_id: Any, *, for_update: bool = False) -> list[SectionRows]:
    section_query = select(Section).where(
        Section.test_id == test_id, Section.type == "reading"
    ).order_by(Section.order)
    sections = (await db.execute(section_query.with_for_update() if for_update else section_query)).scalars().all()
    if [s.order for s in sections] != [10, 11, 12]:
        raise ValueError("Unexpected Practice Set F Reading sections")
    result = []
    for section in sections:
        group_query = select(QuestionGroup).where(
            QuestionGroup.section_id == section.id
        ).order_by(QuestionGroup.order)
        groups = (await db.execute(group_query.with_for_update() if for_update else group_query)).scalars().all()
        rows = []
        for group in groups:
            question_query = select(Question).where(
                Question.question_group_id == group.id
            ).order_by(Question.order)
            questions = (await db.execute(question_query.with_for_update() if for_update else question_query)).scalars().all()
            rows.append(GroupRows(group, list(questions)))
        result.append(SectionRows(section, rows))
    return result


async def desired_graph(test_number: int, current: list[SectionRows]) -> list[SectionRows]:
    folder = data_dir(test_number)
    questions = _read_json(folder / "reading_questions.json")
    answers = _read_json(folder / "reading_answers.json")
    result = []
    for index, section in enumerate(current, 1):
        built = build_passage(test_number, index, section.record.id, questions, answers)
        result.append(SectionRows(section.record, [GroupRows(g, list(g.questions)) for g in built.groups]))
    return result


async def unfinished_count(db: AsyncSession, test_id: Any) -> int:
    return (await db.execute(select(func.count()).select_from(Attempt).where(
        Attempt.test_id == test_id,
        Attempt.status.in_(["in_progress", "speaking_in_progress"]),
        or_(
            Attempt.mode == "full_mock",
            Attempt.practice_section_type == "reading",
            # Fail closed for older/ambiguous practice records, too.
            Attempt.practice_section_type.is_(None),
            Attempt.practice_section_id.in_(select(Section.id).where(
                Section.test_id == test_id, Section.type == "reading"
            )),
        ),
    ))).scalar_one()


def write_backup(path: Path, data: dict[str, Any]) -> None:
    # Refuse accidental overwrite, even when the operator supplies an existing path.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())


async def repair(db: AsyncSession, *, apply: bool, backup: Path | None = None) -> int:
    if apply and backup is None:
        raise ValueError("--apply requires --backup /absolute/new-file.json")
    if backup is not None and not backup.is_absolute():
        raise ValueError("Backup path must be absolute")
    if apply:
        await db.execute(text("SET LOCAL lock_timeout = '2s'"))
        await db.execute(text("SET LOCAL statement_timeout = '30s'"))
    plans = []
    snapshots = []
    for n in AUDITED_BEFORE:
        query = select(Test).where(Test.book_slug == BOOK_SLUG, Test.test_number == n)
        # A Test row FOR UPDATE conflicts with FK key-share checks on new attempts.
        # New attempts wait briefly; existing unfinished attempts cause an abort.
        if apply:
            query = query.with_for_update()
        test = (await db.execute(query)).scalar_one()
        current = await load_graph(db, test.id, for_update=apply)
        desired = await desired_graph(n, current)
        plan = plan_repair(n, current, desired)
        active = await unfinished_count(db, test.id) if plan.updates else 0
        print(f"T{n}: updates={len(plan.updates)}, empty_group_shells={len(plan.empty_groups)}, unfinished={active}")
        if apply and active:
            raise ValueError(f"T{n}: {active} unfinished attempts; no changes applied")
        plans.append((test, plan, {q.id for q, _, _ in numbered(current).values()}))
        snapshots.append({"test_number": n, "test_id": str(test.id), "reading": payload(current, include_ids=True),
                          "before_sha256": plan.before, "after_sha256": plan.after})
    changes = sum(len(p.updates) for _, p, _ in plans)
    if not apply or not changes:
        await db.rollback()
        print(f"{'Dry run' if not apply else 'Already repaired'}: {changes} updates; no database writes")
        return changes
    # The migrated database (unlike Base.metadata) has a non-deferrable unique
    # constraint on (question_group_id, order). Park only moving/reordered rows
    # in a disjoint positive SMALLINT range before assigning their final slots.
    moving = [u for _, plan, _ in plans for u in plan.updates if isinstance(u.record, Question)
              and (u.record.order != u.fields["order"] or u.record.question_group_id != u.fields["question_group_id"])]
    highest = max(q["order"] for snapshot in snapshots for s in snapshot["reading"] for g in s["groups"] for q in g["questions"])
    highest = max([highest, *(u.fields["order"] for u in moving)])
    if highest + len(moving) > 32767:
        raise ValueError("No collision-free SMALLINT order range; refusing update")
    write_backup(backup, {"created_at": datetime.now(timezone.utc).isoformat(), "tests": snapshots})
    for temporary_order, update in enumerate(moving, highest + 1):
        update.record.order = temporary_order
    if moving:
        await db.flush()
    for _, plan, _ in plans:
        for update in plan.updates:
            for name, field_value in update.fields.items():
                setattr(update.record, name, field_value)
    await db.flush()
    for _, plan, _ in plans:
        for group in plan.empty_groups:
            remaining = (await db.execute(select(func.count()).select_from(Question).where(
                Question.question_group_id == group.id
            ))).scalar_one()
            if remaining:
                raise ValueError("Refusing to remove nonempty group")
            # Only the now-empty obsolete Q14 group shell is removed, never questions.
            await db.delete(group)
    await db.flush()
    for test, plan, old_ids in plans:
        actual = await load_graph(db, test.id)
        if fingerprint(actual) != plan.after or {q.id for q, _, _ in numbered(actual).values()} != old_ids:
            raise ValueError("Post-update structure or question identity verification failed")
    await db.commit()
    print(f"Applied {changes} updates; question IDs retained; answers/attempts/scores untouched")
    return changes


async def main(apply: bool, backup: Path | None) -> None:
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            try:
                await repair(db, apply=apply, backup=backup)
            except Exception:
                await db.rollback()
                raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    asyncio.run(main(args.apply, args.backup))
