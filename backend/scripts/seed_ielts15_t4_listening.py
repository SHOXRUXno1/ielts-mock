"""Seed Cambridge IELTS 15 Test 4 Listening (Q1–40).

Reuses the existing Test 4 record. Idempotent wipe of listening
groups/questions only. Keeps audio_url. Does not create a new test.

Usage:
    python /app/scripts/seed_ielts15_t4_listening.py
"""

from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

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
TEST_NUMBER = 4
TEST_TITLE = "Cambridge IELTS 15 – Test 4"
BOOK_NAME = "Cambridge IELTS 15"
# Existing unpublished draft on production (audio already uploaded).
TEST_ID = uuid.UUID("8e84227c-abde-41f9-ab36-7ea51527b7e6")
LEGACY_SLUG = "cambridge-ielts-15-test-4"

PROTECTED_TEST_IDS = {
    uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590"),  # Test 1
    uuid.UUID("6074d5f2-70b8-4f31-9b59-10f861a3eadf"),  # Test 2
    uuid.UUID("3b766b14-d188-4c81-814f-77fadff4e3fa"),  # Test 3
}

MAP_URL = "/media/images/croft-valley-park.png"
MAP_ASSET = Path(__file__).resolve().parent / "assets" / "croft-valley-park.png"


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
    "title": "Customer Satisfaction Survey",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "bullets": False,
    "sections": [
        {
            "heading": "1. Customer details",
            "items": [
                _item("Name: Sophie Bird"),
                _item("Occupation: ", _gap("g1")),
                _item("Reason for travel today: ", _gap("g2")),
            ],
        },
        {
            "heading": "2. Journey information",
            "items": [
                _item("Name of station returning to: ", _gap("g3")),
                _item("Type of ticket purchased: standard ", _gap("g4"), " ticket"),
                _item("Cost of ticket: £", _gap("g5")),
                _item("When ticket was purchased: yesterday"),
                _item("Where ticket was bought: ", _gap("g6")),
            ],
        },
        {
            "heading": "3. Satisfaction with journey",
            "items": [
                _item("Most satisfied with: the wifi"),
                _item("Least satisfied with: the ", _gap("g7"), " this morning"),
            ],
        },
        {
            "heading": "4. Satisfaction with station facilities",
            "items": [
                _item("Most satisfied with: how much ", _gap("g8"), " was provided"),
                _item(
                    "Least satisfied with: lack of seats, particularly on the ",
                    _gap("g9"),
                ),
                _item(
                    "Neither satisfied nor dissatisfied with: the ",
                    _gap("g10"),
                    " available",
                ),
            ],
        },
    ],
}

P1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["journalist"], 1),
    ("g2", ["shopping"], 1),
    ("g3", ["Staunfirth"], 1),
    ("g4", ["return"], 1),
    ("g5", ["23.70"], 2),
    ("g6", ["online"], 1),
    ("g7", ["delay"], 1),
    ("g8", ["information"], 1),
    ("g9", ["platform", "platforms"], 1),
    ("g10", ["parking"], 1),
]

# ── Part 2: map + multi_select ───────────────────────────────────────────────

P2_MAP_INSTRUCTION = (
    "Label the map below.\n"
    "Choose the correct letter, A-H, next to Questions 11-16."
)

P2_MAP_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H"]

P2_MAP_ITEMS: list[tuple[str, str]] = [
    ("café", "D"),
    ("toilets", "C"),
    ("formal gardens", "G"),
    ("outdoor gym", "H"),
    ("skateboard ramp", "A"),
    ("wild flowers", "E"),
]

P2_MULTI_INSTRUCTION = "Choose TWO letters, A-E."

P2_MULTI: list[dict] = [
    {
        "question": "What does the speaker say about the adventure playground?",
        "options": [
            "Children must be supervised.",
            "It costs more in winter.",
            "Some activities are only for younger children.",
            "No payment is required.",
            "It was recently expanded.",
        ],
        "correct": ["A", "D"],
    },
    {
        "question": "What does the speaker say about the glass houses?",
        "options": [
            "They are closed at weekends.",
            "Volunteers are needed to work there.",
            "They were badly damaged by fire.",
            "More money is needed to repair some of the glass.",
            "Visitors can see palm trees from tropical regions.",
        ],
        "correct": ["A", "C"],
    },
]

# ── Part 3: MCQ + matching ───────────────────────────────────────────────────

P3_MCQ_INSTRUCTION = "Choose the correct letter, A, B or C."

P3_MCQ: list[dict] = [
    {
        "question": "What did Annie discover from reading about icehouses?",
        "options": [
            "why they were first created",
            "how the ice was kept frozen",
            "where they were located",
        ],
        "correct": "B",
    },
    {
        "question": "What point does Annie make about refrigeration in ancient Rome?",
        "options": [
            "It became a commercial business.",
            "It used snow from nearby.",
            "It took a long time to become popular.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "In connection with modern refrigerators, both Annie and Jack "
            "are worried about"
        ),
        "options": [
            "the complexity of the technology.",
            "the fact that some are disposed of irresponsibly.",
            "the large number that quickly break down.",
        ],
        "correct": "B",
    },
    {
        "question": "What do Jack and Annie agree regarding domestic fridges?",
        "options": [
            "They are generally good value for money.",
            "There are plenty of useful variations.",
            "They are more useful than other domestic appliances.",
        ],
        "correct": "A",
    },
]

P3_MATCH_INSTRUCTION = (
    "Who is going to do research into each topic?\n"
    "Choose the correct letter, A-C, next to Questions 25-30."
)

P3_MATCH_OPTIONS = [
    "A. Annie",
    "B. Jack",
    "C. both Annie and Jack",
]

P3_MATCH_ITEMS: list[tuple[str, str]] = [
    ("the goods that are refrigerated", "A"),
    ("the effects on health", "A"),
    ("the impact on food producers", "B"),
    ("the impact on cities", "B"),
    ("refrigerated transport", "A"),
    ("domestic fridges", "C"),
]

# ── Part 4: notes ────────────────────────────────────────────────────────────

P4_INSTRUCTION = (
    "Complete the notes below.\nWrite ONE WORD ONLY for each answer."
)

P4_NOTES: dict = {
    "variant": "notes",
    "title": "How the Industrial Revolution affected life in Britain",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "19th century",
            "items": [
                _item(
                    "For the first time, people's possessions were used to measure Britain's ",
                    _gap("g31"),
                ),
                _item(
                    "Developments in production of goods and in ",
                    _gap("g32"),
                    " greatly changed lives.",
                ),
            ],
        },
        {
            "heading": "MAIN AREAS OF CHANGE",
            "items": [],
        },
        {
            "heading": "Manufacturing",
            "items": [
                _item(
                    "The Industrial Revolution would not have happened without the new types of ",
                    _gap("g33"),
                    " that were used then.",
                ),
                _item(
                    "The leading industry was ",
                    _gap("g34"),
                    " (its products became widely available).",
                ),
                _item(
                    "New ",
                    _gap("g35"),
                    " made factories necessary and so more people moved into towns.",
                ),
            ],
        },
        {
            "heading": "Transport",
            "items": [
                _item("The railways took the place of canals."),
                _item("Because of the new transport:"),
                _item(
                    "greater access to ",
                    _gap("g36"),
                    " made people more aware of what they could buy in shops.",
                    nested=True,
                ),
                _item(
                    "when shopping, people were not limited to buying ",
                    _gap("g37"),
                    " goods.",
                    nested=True,
                ),
            ],
        },
        {
            "heading": "Retailing",
            "items": [
                _item("The first department stores were opened."),
                _item("The displays of goods were more visible:"),
                _item(
                    "inside stores because of better ",
                    _gap("g38"),
                    ".",
                    nested=True,
                ),
                _item(
                    "outside stores, because ",
                    _gap("g39"),
                    " were bigger.",
                    nested=True,
                ),
                _item(_gap("g40"), " that was persuasive became much more common."),
            ],
        },
    ],
}

P4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g31", ["wealth"], 1),
    ("g32", ["technology"], 1),
    ("g33", ["power"], 1),
    ("g34", ["textile", "textiles"], 1),
    ("g35", ["machines"], 1),
    ("g36", ["newspapers"], 1),
    ("g37", ["local"], 1),
    ("g38", ["lighting"], 1),
    ("g39", ["windows"], 1),
    ("g40", ["Advertising", "advertising"], 1),
]


def validate_payload() -> None:
    if len(P1_ANSWERS) != 10:
        raise SystemExit("Part 1 must have 10 gaps")
    if [row[0] for row in P1_ANSWERS] != [f"g{i}" for i in range(1, 11)]:
        raise SystemExit("Part 1 gap ids must be g1–g10")
    if P1_ANSWERS[0][1] != ["journalist"] or P1_ANSWERS[4][1] != ["23.70"]:
        raise SystemExit("Part 1 Q1/Q5 keys must be journalist / 23.70")
    if len(P2_MAP_ITEMS) != 6:
        raise SystemExit("Part 2 must have 6 map labels")
    if [letter for _, letter in P2_MAP_ITEMS] != ["D", "C", "G", "H", "A", "E"]:
        raise SystemExit("Part 2 map keys must be D C G H A E")
    if len(P2_MULTI) != 2:
        raise SystemExit("Part 2 must have 2 multi_select pairs")
    if P2_MULTI[0]["correct"] != ["A", "D"] or P2_MULTI[1]["correct"] != ["A", "C"]:
        raise SystemExit("Part 2 multi_select keys must be A/D and A/C")
    if len(P3_MCQ) != 4:
        raise SystemExit("Part 3 must have 4 MCQ")
    if [item["correct"] for item in P3_MCQ] != ["B", "A", "B", "A"]:
        raise SystemExit("Part 3 MCQ keys must be B A B A")
    if [letter for _, letter in P3_MATCH_ITEMS] != ["A", "A", "B", "B", "A", "C"]:
        raise SystemExit("Part 3 matching keys must be A A B B A C")
    if len(P4_ANSWERS) != 10:
        raise SystemExit("Part 4 must have 10 gaps")
    if [row[0] for row in P4_ANSWERS] != [f"g{i}" for i in range(31, 41)]:
        raise SystemExit("Part 4 gap ids must be g31–g40")
    if not MAP_ASSET.is_file():
        raise SystemExit(f"Missing map asset: {MAP_ASSET}")


def install_map_image() -> str:
    dest_dir = Path(__file__).resolve().parent.parent / "media" / "images"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "croft-valley-park.png"
    shutil.copyfile(MAP_ASSET, dest)
    return MAP_URL


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
            f"Test 4 not found ({TEST_ID}). Refusing to create a new test."
        )
    if test.id in PROTECTED_TEST_IDS:
        raise SystemExit(f"Refusing to seed into protected test {test.id}")

    test.title = TEST_TITLE
    test.book_name = BOOK_NAME
    test.book_slug = BOOK_SLUG
    test.test_number = TEST_NUMBER
    test.description = "Cambridge IELTS 15 Academic, Test 4"
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
    map_url = install_map_image()
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
        p1.title = "Part 1 — Customer Satisfaction Survey"
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
        p2.title = "Part 2 — Croft Valley Park"
        g_order = await next_group_order(db, p2.id)
        order = 1
        map_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p2.id,
            order=g_order,
            question_type=QuestionType.MAP_LABELING.value,
            instruction=P2_MAP_INSTRUCTION,
            subtitle="Croft Valley Park",
            options_shared={"options": P2_MAP_OPTIONS, "image_url": map_url},
        )
        db.add(map_group)
        await db.flush()
        print("\nPart 2 — map")
        for location, letter in P2_MAP_ITEMS:
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p2.id,
                    question_group_id=map_group.id,
                    order=order,
                    question_type=QuestionType.MAP_LABELING,
                    content={"location": location},
                    answer_key={"correct": letter},
                )
            )
            print(f"    {location!r} -> {letter}")
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
        p3.title = "Part 3 — Presentation about refrigeration"
        g_order = await next_group_order(db, p3.id)
        order = 1
        mcq_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p3.id,
            order=g_order,
            question_type=QuestionType.MCQ.value,
            instruction=P3_MCQ_INSTRUCTION,
            subtitle="Presentation about refrigeration",
        )
        db.add(mcq_group)
        await db.flush()
        print("\nPart 3 — MCQ")
        for item in P3_MCQ:
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p3.id,
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
        p4.title = "Part 4 — How the Industrial Revolution affected life in Britain"
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
        print(f"\nDone. {TEST_TITLE} listening Q1–40 seeded. Map: {map_url}. Unpublished.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
