"""Seed Cambridge IELTS 15 Test 3 Listening (Q1–40).

Reuses the existing Test 3 record. Idempotent wipe of listening
groups/questions only. Keeps audio_url. Does not create a new test.

Usage:
    python /app/scripts/seed_ielts15_t3_listening.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.answer import Answer
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test
from app.services.scoring import scoring_slots_for_question
from app.services.section_settings import ensure_settings
from app.services.seed_compound import gap_answer_key, next_group_order

BOOK_SLUG = "cambridge-ielts-15"
TEST_NUMBER = 3
TEST_TITLE = "Cambridge IELTS 15 – Test 3"
BOOK_NAME = "Cambridge IELTS 15"
# Existing unpublished draft on production (audio already uploaded).
TEST_ID = uuid.UUID("3b766b14-d188-4c81-814f-77fadff4e3fa")
LEGACY_SLUG = "cambridge-ielts-15-test-3"

PROTECTED_TEST_IDS = {
    uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590"),  # Test 1
    uuid.UUID("6074d5f2-70b8-4f31-9b59-10f861a3eadf"),  # Test 2
}


def _text(value: str) -> dict:
    return {"type": "text", "value": value}


def _gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def _item(*parts: str | dict, nested: bool = False) -> dict:
    segments: list[dict] = []
    for part in parts:
        segments.append(_text(part) if isinstance(part, str) else part)
    if nested:
        if segments and segments[0]["type"] == "text":
            segments[0] = {**segments[0], "value": "  " + segments[0]["value"]}
        else:
            segments.insert(0, _text("  "))
    return {"segments": segments}


# ── Part 1: notes ────────────────────────────────────────────────────────────

P1_INSTRUCTION = (
    "Complete the notes below.\n"
    "Write ONE WORD AND/OR A NUMBER for each answer."
)

P1_NOTES: dict = {
    "variant": "notes",
    "title": "Employment Agency: Possible Jobs",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "First Job",
            "items": [
                _item(
                    "Administrative assistant in a company that produces ",
                    _gap("g1"),
                    " (North London)",
                ),
                _item("Responsibilities:"),
                _item("data entry", nested=True),
                _item("go to ", _gap("g2"), " and take notes", nested=True),
                _item("general admin", nested=True),
                _item("management of ", _gap("g3"), nested=True),
                _item("Requirements:"),
                _item("good computer skills including spreadsheets", nested=True),
                _item("good interpersonal skills", nested=True),
                _item("attention to ", _gap("g4"), nested=True),
                _item("Experience:"),
                _item(
                    "need a minimum of ",
                    _gap("g5"),
                    " of experience of teleconferencing",
                    nested=True,
                ),
            ],
        },
        {
            "heading": "Second Job",
            "items": [
                _item("Warehouse assistant in South London"),
                _item("Responsibilities:"),
                _item("stock management", nested=True),
                _item("managing ", _gap("g6"), nested=True),
                _item("Requirements:"),
                _item("ability to work with numbers", nested=True),
                _item("good computer skills", nested=True),
                _item("very organised and ", _gap("g7"), nested=True),
                _item("good communication skills", nested=True),
                _item("used to working in a ", _gap("g8"), nested=True),
                _item("able to cope with items that are ", _gap("g9"), nested=True),
                _item("Need experience of:"),
                _item("driving in London", nested=True),
                _item("warehouse work", nested=True),
                _item(_gap("g10"), " service", nested=True),
            ],
        },
    ],
}

P1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["furniture"], 1),
    ("g2", ["meetings"], 1),
    ("g3", ["diary"], 1),
    ("g4", ["detail", "details"], 1),
    ("g5", ["1", "1 year", "one year"], 2),
    ("g6", ["deliveries"], 1),
    ("g7", ["tidy"], 1),
    ("g8", ["team"], 1),
    ("g9", ["heavy"], 1),
    ("g10", ["customer"], 1),
]

# ── Part 2: MCQ + multi_select ───────────────────────────────────────────────

P2_MCQ_INSTRUCTION = "Choose the correct letter, A, B or C."

P2_MCQ: list[dict] = [
    {
        "question": "When did the Street Play Scheme first take place?",
        "options": ["two years ago", "three years ago", "six years ago"],
        "correct": "B",
    },
    {
        "question": "How often is Beechwood Road closed to traffic now?",
        "options": ["once a week", "on Saturdays and Sundays", "once a month"],
        "correct": "A",
    },
    {
        "question": "Who is responsible for closing the road?",
        "options": ["a council official", "the police", "local wardens"],
        "correct": "C",
    },
    {
        "question": "Residents who want to use their cars",
        "options": [
            "have to park in another street.",
            "must drive very slowly.",
            "need permission from a warden.",
        ],
        "correct": "B",
    },
    {
        "question": "Alice says that Street Play Schemes are most needed in",
        "options": [
            "wealthy areas.",
            "quiet suburban areas.",
            "areas with heavy traffic.",
        ],
        "correct": "C",
    },
    {
        "question": "What has been the reaction of residents who are not parents?",
        "options": [
            "Many of them were unhappy at first.",
            "They like seeing children play in the street.",
            "They are surprised by the lack of noise.",
        ],
        "correct": "B",
    },
]

P2_MULTI_INSTRUCTION = "Choose TWO letters, A-E."

P2_MULTI: list[dict] = [
    {
        "question": "Which TWO benefits for children does Alice think are the most important?",
        "options": [
            "increased physical activity",
            "increased sense of independence",
            "opportunity to learn new games",
            "opportunity to be part of a community",
            "opportunity to make new friends",
        ],
        "correct": ["B", "D"],
    },
    {
        "question": "Which TWO results of the King Street experiment surprised Alice?",
        "options": [
            "more shoppers",
            "improved safety",
            "less air pollution",
            "more relaxed atmosphere",
            "less noise pollution",
        ],
        "correct": ["A", "E"],
    },
]

# ── Part 3: notes + matching ─────────────────────────────────────────────────

P3_NOTES_INSTRUCTION = (
    "Complete the notes below.\nWrite ONE WORD ONLY for each answer."
)

P3_NOTES: dict = {
    "variant": "notes",
    "title": "What Hazel should analyse about items in newspapers:",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "",
            "items": [
                _item("What ", _gap("g21"), " the item is on"),
                _item("the ", _gap("g22"), " of the item, including the headline"),
                _item("any ", _gap("g23"), " accompanying the item"),
                _item(
                    "the ",
                    _gap("g24"),
                    " of the item, e.g. what's made prominent",
                ),
                _item("the writer's main ", _gap("g25")),
                _item(
                    "the ",
                    _gap("g26"),
                    " the writer may make about the reader",
                ),
            ],
        }
    ],
}

P3_NOTES_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g21", ["page"], 1),
    ("g22", ["size"], 1),
    ("g23", ["graphic", "graphics"], 1),
    ("g24", ["structure"], 1),
    ("g25", ["purpose"], 1),
    ("g26", ["assumption", "assumptions"], 1),
]

P3_MATCH_INSTRUCTION = (
    "What does Hazel decide to do about each of the following types of articles?\n"
    "Choose the correct letter, A-C, next to Questions 27-30."
)

P3_MATCH_OPTIONS = [
    "A. She will definitely look for a suitable article.",
    "B. She may look for a suitable article.",
    "C. She definitely won't look for an article.",
]

P3_MATCH_ITEMS: list[tuple[str, str]] = [
    ("national news item", "A"),
    ("editorial", "C"),
    ("human interest", "C"),
    ("arts", "B"),
]

# ── Part 4: notes ────────────────────────────────────────────────────────────

P4_INSTRUCTION = (
    "Complete the notes below.\nWrite ONE WORD ONLY for each answer."
)

P4_NOTES: dict = {
    "variant": "notes",
    "title": "Early history of keeping clean",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "Prehistoric times:",
            "items": [_item("water was used to wash off ", _gap("g31"))],
        },
        {
            "heading": "Ancient Babylon:",
            "items": [
                _item("soap-like material found in ", _gap("g32"), " cylinders")
            ],
        },
        {
            "heading": "Ancient Greece:",
            "items": [
                _item("people cleaned themselves with sand and other substances"),
                _item("used a strigil – scraper made of ", _gap("g33")),
                _item("washed clothes in streams"),
            ],
        },
        {
            "heading": "Ancient Germany and Gaul:",
            "items": [_item("used soap to colour their ", _gap("g34"))],
        },
        {
            "heading": "Ancient Rome:",
            "items": [
                _item(
                    "animal fat, ashes and clay mixed through action of rain, "
                    "used for washing clothes"
                ),
                _item(
                    "from about 312 BC, water carried to Roman ",
                    _gap("g35"),
                    " by aqueducts",
                ),
            ],
        },
        {
            "heading": "Europe in Middle Ages:",
            "items": [
                _item(
                    "decline in bathing contributed to occurrence of ",
                    _gap("g36"),
                ),
                _item(_gap("g37"), " began to be added to soap"),
            ],
        },
        {
            "heading": "Europe from 17th century:",
            "items": [
                _item("1600s: cleanliness and bathing started becoming usual"),
                _item(
                    "1791: Leblanc invented a way of making soda ash from ",
                    _gap("g38"),
                ),
                _item(
                    "early 1800s: Chevreul turned soapmaking into a ",
                    _gap("g39"),
                ),
                _item("from 1800s, there was no longer a ", _gap("g40"), " on soap"),
            ],
        },
    ],
}

P4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g31", ["mud"], 1),
    ("g32", ["clay"], 1),
    ("g33", ["metal"], 1),
    ("g34", ["hair"], 1),
    ("g35", ["bath", "baths"], 1),
    ("g36", ["disease", "diseases"], 1),
    ("g37", ["perfume"], 1),
    ("g38", ["salt"], 1),
    ("g39", ["science"], 1),
    ("g40", ["tax"], 1),
]


def validate_payload() -> None:
    if len(P1_ANSWERS) != 10:
        raise SystemExit("Part 1 must have 10 gaps")
    if [row[0] for row in P1_ANSWERS] != [f"g{i}" for i in range(1, 11)]:
        raise SystemExit("Part 1 gap ids must be g1–g10")
    if P1_ANSWERS[1][1] != ["meetings"] or P1_ANSWERS[2][1] != ["diary"]:
        raise SystemExit("Part 1 Q2/Q3 keys must be meetings / diary")
    if len(P2_MCQ) != 6:
        raise SystemExit("Part 2 must have 6 MCQ")
    if [item["correct"] for item in P2_MCQ] != ["B", "A", "C", "B", "C", "B"]:
        raise SystemExit("Part 2 MCQ keys must be B A C B C B")
    if len(P2_MULTI) != 2:
        raise SystemExit("Part 2 must have 2 multi_select pairs")
    if P2_MULTI[0]["correct"] != ["B", "D"] or P2_MULTI[1]["correct"] != ["A", "E"]:
        raise SystemExit("Part 2 multi_select keys must be B/D and A/E")
    if len(P3_NOTES_ANSWERS) != 6 or len(P3_MATCH_ITEMS) != 4:
        raise SystemExit("Part 3 must be 6 notes + 4 matching")
    if [letter for _, letter in P3_MATCH_ITEMS] != ["A", "C", "C", "B"]:
        raise SystemExit("Part 3 matching keys must be A C C B")
    if len(P4_ANSWERS) != 10:
        raise SystemExit("Part 4 must have 10 gaps")
    if [row[0] for row in P4_ANSWERS] != [f"g{i}" for i in range(31, 41)]:
        raise SystemExit("Part 4 gap ids must be g31–g40")


async def _wipe_section(db: AsyncSession, section_id: uuid.UUID) -> int:
    qids = (
        await db.execute(select(Question.id).where(Question.section_id == section_id))
    ).scalars().all()
    if qids:
        await db.execute(sa_delete(Answer).where(Answer.question_id.in_(qids)))
        await db.flush()

    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == section_id)
        )
    ).scalars().all()
    n = 0
    for g in groups:
        qs = (
            await db.execute(
                select(Question).where(Question.question_group_id == g.id)
            )
        ).scalars().all()
        for q in qs:
            await db.delete(q)
        await db.flush()
        await db.delete(g)
        n += 1
    leftovers = (
        await db.execute(select(Question).where(Question.section_id == section_id))
    ).scalars().all()
    for q in leftovers:
        await db.delete(q)
        n += 1
    if n:
        await db.flush()
    return n


async def _add_gaps(
    db: AsyncSession,
    *,
    section: Section,
    group: QuestionGroup,
    answers: list[tuple[str, list[str], int]],
    qtype: QuestionType,
    order_start: int,
) -> int:
    order = order_start
    for gap_id, variants, max_words in answers:
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=order,
                question_type=qtype,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=max_words),
            )
        )
        print(f"    {gap_id} -> {variants}")
        order += 1
    return order


async def _first_test(db: AsyncSession, stmt) -> Test | None:
    return (await db.execute(stmt)).scalar_one_or_none()


async def _load_existing_test(db: AsyncSession) -> Test:
    test = await _first_test(db, select(Test).where(Test.id == TEST_ID))
    if test is None:
        test = await _first_test(
            db,
            select(Test).where(
                Test.book_slug == BOOK_SLUG,
                Test.test_number == TEST_NUMBER,
            ),
        )
    if test is None:
        test = await _first_test(
            db,
            select(Test).where(Test.book_slug == LEGACY_SLUG),
        )
    if test is None:
        test = await _first_test(db, select(Test).where(Test.title == TEST_TITLE))
    if test is None:
        raise SystemExit(
            f"Test 3 not found ({TEST_ID}). Refusing to create a new test."
        )
    if test.id in PROTECTED_TEST_IDS:
        raise SystemExit(f"Refusing to seed into protected test {test.id}")

    test.title = TEST_TITLE
    test.book_name = BOOK_NAME
    test.book_slug = BOOK_SLUG
    test.test_number = TEST_NUMBER
    test.description = "Cambridge IELTS 15 Academic, Test 3"
    test.is_published = False
    print(f"Found existing test: {test.title} ({test.id})")
    return test


async def _listening_parts(db: AsyncSession, test: Test) -> dict[int, Section]:
    rows = (
        await db.execute(
            select(Section)
            .where(Section.test_id == test.id, Section.type == SectionType.LISTENING)
            .order_by(Section.order)
        )
    ).scalars().all()
    if len(rows) < 4:
        raise SystemExit(f"Expected 4 listening sections, found {len(rows)}")
    return {i: rows[i - 1] for i in range(1, 5)}


async def main() -> None:
    validate_payload()
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await _load_existing_test(db)
        await ensure_settings(db, test.id)
        parts = await _listening_parts(db, test)

        for part, section in parts.items():
            if section.id is None:
                raise SystemExit(f"Part {part} has no section id")
            removed = await _wipe_section(db, section.id)
            if removed:
                print(f"  Part {part}: removed {removed} old group/question row(s)")
            if section.audio_url:
                print(f"  Part {part}: keep audio {section.audio_url}")
            else:
                print(f"  Part {part}: no audio_url yet")

        # Part 1
        p1 = parts[1]
        p1.title = "Part 1 — Employment Agency: Possible Jobs"
        notes1 = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p1.id,
            order=await next_group_order(db, p1.id),
            question_type=QuestionType.NOTE_COMPLETION.value,
            instruction=P1_INSTRUCTION,
            options_shared=P1_NOTES,
        )
        db.add(notes1)
        await db.flush()
        print("\nPart 1 — notes")
        await _add_gaps(
            db,
            section=p1,
            group=notes1,
            answers=P1_ANSWERS,
            qtype=QuestionType.NOTE_COMPLETION,
            order_start=1,
        )

        # Part 2
        p2 = parts[2]
        p2.title = "Part 2 — Street Play Scheme"
        g_order = await next_group_order(db, p2.id)
        order = 1
        mcq_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p2.id,
            order=g_order,
            question_type=QuestionType.MCQ.value,
            instruction=P2_MCQ_INSTRUCTION,
            subtitle="Street Play Scheme",
        )
        db.add(mcq_group)
        await db.flush()
        print("\nPart 2 — MCQ")
        for item in P2_MCQ:
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p2.id,
                    question_group_id=mcq_group.id,
                    order=order,
                    question_type=QuestionType.MCQ,
                    content={
                        "question": item["question"],
                        "options": item["options"],
                    },
                    answer_key={"correct": item["correct"]},
                )
            )
            print(f"    MCQ order={order} -> {item['correct']}")
            order += 1
        g_order += 1

        print("Part 2 — multi_select")
        for item in P2_MULTI:
            g = QuestionGroup(
                id=uuid.uuid4(),
                section_id=p2.id,
                order=g_order,
                question_type=QuestionType.MULTI_SELECT.value,
                instruction=P2_MULTI_INSTRUCTION,
            )
            db.add(g)
            await db.flush()
            g_order += 1
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p2.id,
                    question_group_id=g.id,
                    order=order,
                    question_type=QuestionType.MULTI_SELECT,
                    content={
                        "choose_n": 2,
                        "question": item["question"],
                        "options": item["options"],
                    },
                    answer_key={"correct": item["correct"]},
                )
            )
            print(f"    multi order={order} -> {item['correct']}")
            order += 1

        # Part 3
        p3 = parts[3]
        p3.title = "Part 3 — Newspaper articles"
        g_order = await next_group_order(db, p3.id)
        notes3 = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p3.id,
            order=g_order,
            question_type=QuestionType.NOTE_COMPLETION.value,
            instruction=P3_NOTES_INSTRUCTION,
            options_shared=P3_NOTES,
        )
        db.add(notes3)
        await db.flush()
        print("\nPart 3 — notes")
        order = await _add_gaps(
            db,
            section=p3,
            group=notes3,
            answers=P3_NOTES_ANSWERS,
            qtype=QuestionType.NOTE_COMPLETION,
            order_start=1,
        )

        match_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p3.id,
            order=g_order + 1,
            question_type=QuestionType.MATCHING_FEATURES.value,
            instruction=P3_MATCH_INSTRUCTION,
            subtitle="\u00a0",
            options_shared={"options": P3_MATCH_OPTIONS},
        )
        db.add(match_group)
        await db.flush()
        print("Part 3 — matching")
        for stem, letter in P3_MATCH_ITEMS:
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p3.id,
                    question_group_id=match_group.id,
                    order=order,
                    question_type=QuestionType.MATCHING_FEATURES,
                    content={"question": stem},
                    answer_key={"correct": letter},
                )
            )
            print(f"    {stem!r} -> {letter}")
            order += 1

        # Part 4
        p4 = parts[4]
        p4.title = "Part 4 — Early history of keeping clean"
        notes4 = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p4.id,
            order=await next_group_order(db, p4.id),
            question_type=QuestionType.NOTE_COMPLETION.value,
            instruction=P4_INSTRUCTION,
            options_shared=P4_NOTES,
        )
        db.add(notes4)
        await db.flush()
        print("\nPart 4 — notes")
        await _add_gaps(
            db,
            section=p4,
            group=notes4,
            answers=P4_ANSWERS,
            qtype=QuestionType.NOTE_COMPLETION,
            order_start=1,
        )

        await db.flush()
        for part, section in parts.items():
            qs = (
                await db.execute(
                    select(Question).where(Question.section_id == section.id)
                )
            ).scalars().all()
            slots = sum(scoring_slots_for_question(q) for q in qs)
            print(f"  Part {part} scoring slots: {slots}")
            if slots != 10:
                raise SystemExit(f"Part {part} must have 10 slots, got {slots}")

        await db.commit()
        print(f"\nDone. {TEST_TITLE} listening Q1–40 seeded. Unpublished.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
