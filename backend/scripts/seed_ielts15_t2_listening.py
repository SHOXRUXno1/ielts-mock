"""Seed Cambridge IELTS 14 Test 1 Listening (Q1–40).

Creates the test if needed. Idempotent on listening parts: wipes groups/
questions, keeps audio_url. Copies the Minster Park map into /media/images.

Usage:
    python /app/scripts/seed_ielts14_t1_listening.py
"""

from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.api.tests import DEFAULT_SECTIONS
from app.core.config import settings
from app.models.answer import Answer
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test
from app.services.scoring import scoring_slots_for_question
from app.services.section_settings import build_default_rows, ensure_settings
from app.services.seed_compound import gap_answer_key, next_group_order

BOOK_SLUG = "cambridge-ielts-14"
TEST_NUMBER = 1
TEST_TITLE = "Cambridge IELTS 14 – Test 1"
MAP_URL = "/media/images/minster-park.png"
MAP_ASSET = Path(__file__).resolve().parent / "assets" / "minster-park.png"


def _plain(text: str) -> dict:
    return {"variant": "plain", "segments": [{"type": "text", "value": text}]}


def _plain_gap(before: str, gap_id: str, after: str = "") -> dict:
    segments: list[dict] = []
    if before:
        segments.append({"type": "text", "value": before})
    segments.append({"type": "gap", "gap_id": gap_id})
    if after:
        segments.append({"type": "text", "value": after})
    return {"variant": "plain", "segments": segments}


# ── Part 1: table + notes ────────────────────────────────────────────────────

P1_TABLE_INSTRUCTION = (
    "Complete the table below.\nWrite ONE WORD ONLY for each answer."
)

P1_TABLE: dict = {
    "variant": "table",
    "title": "Festival information",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "headers": ["Date", "Type of event", "Details"],
    "rows": [
        [
            _plain("17th"),
            _plain("a concert"),
            _plain("performers from Canada"),
        ],
        [
            _plain("18th"),
            _plain("a ballet"),
            _plain_gap("company called ", "g1"),
        ],
        [
            _plain("19th–20th (afternoon)"),
            _plain("a play"),
            _plain_gap(
                "type of play: a comedy called Jemima has had a good ",
                "g2",
            ),
        ],
        [
            _plain("20th (evening)"),
            _plain_gap("a ", "g3", " show"),
            _plain_gap("show is called ", "g4"),
        ],
    ],
}

P1_TABLE_ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["Eustatis"]),
    ("g2", ["review"]),
    ("g3", ["dance"]),
    ("g4", ["Chat"]),
]

P1_NOTES_INSTRUCTION = (
    "Complete the notes below.\nWrite ONE WORD ONLY for each answer."
)

P1_NOTES: dict = {
    "variant": "notes",
    "title": "",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "Workshops",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Making "},
                        {"type": "gap", "gap_id": "g5"},
                        {"type": "text", "value": " food"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "(children only) Making "},
                        {"type": "gap", "gap_id": "g6"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "(adults only) Making toys from ",
                        },
                        {"type": "gap", "gap_id": "g7"},
                        {"type": "text", "value": " using various tools"},
                    ]
                },
            ],
        },
        {
            "heading": "Outdoor activities",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Swimming in the "},
                        {"type": "gap", "gap_id": "g8"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Walking in the woods, led by an expert on ",
                        },
                        {"type": "gap", "gap_id": "g9"},
                    ]
                },
            ],
        },
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "See the festival organiser's ",
                        },
                        {"type": "gap", "gap_id": "g10"},
                        {"type": "text", "value": " for more information."},
                    ]
                },
            ],
        },
    ],
}

P1_NOTES_ANSWERS: list[tuple[str, list[str]]] = [
    ("g5", ["healthy"]),
    ("g6", ["posters"]),
    ("g7", ["wood"]),
    ("g8", ["lake"]),
    ("g9", ["insects"]),
    ("g10", ["blog"]),
]

# ── Part 2: MCQ + map ────────────────────────────────────────────────────────

P2_MCQ_INSTRUCTION = "Choose the correct letter, A, B or C."

P2_MCQ: list[dict] = [
    {
        "question": "The park was originally established",
        "options": [
            "as an amenity provided by the city council.",
            "as land belonging to a private house.",
            "as a shared area set up by the local community.",
        ],
        "correct": "C",
    },
    {
        "question": "Why is there a statue of Diane Gosforth in the park?",
        "options": [
            "She was a resident who helped to lead a campaign.",
            "She was a council member responsible for giving the public access.",
            "She was a senior worker at the park for many years.",
        ],
        "correct": "A",
    },
    {
        "question": "During the First World War, the park was mainly used for",
        "options": [
            "exercises by troops.",
            "growing vegetables.",
            "public meetings.",
        ],
        "correct": "B",
    },
    {
        "question": "When did the physical transformation of the park begin?",
        "options": ["2013", "2015", "2016"],
        "correct": "C",
    },
]

P2_MAP_INSTRUCTION = (
    "Label the map below.\n"
    "Choose the correct letter, A-I, next to Questions 15-20."
)

P2_MAP_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

P2_MAP_ITEMS: list[tuple[str, str]] = [
    ("statue of Diane Gosforth", "E"),
    ("wooden sculptures", "C"),
    ("playground", "B"),
    ("maze", "A"),
    ("tennis courts", "G"),
    ("fitness area", "D"),
]

# ── Part 3: multi_select + matching ──────────────────────────────────────────

P3_MULTI_INSTRUCTION = "Choose TWO letters, A-E."

P3_MULTI: list[dict] = [
    {
        "question": "Which TWO groups of people is the display primarily intended for?",
        "options": [
            "students from the English department",
            "residents of the local area",
            "the university's teaching staff",
            "potential new students",
            "students from other departments",
        ],
        "correct": ["B", "D"],
    },
    {
        "question": (
            "What are Cathy and Graham's TWO reasons for choosing "
            "the novelist Charles Dickens?"
        ),
        "options": [
            "His speeches inspired others to try to improve society.",
            "He used his publications to draw attention to social problems.",
            "His novels are well-known now.",
            "He was consulted on a number of social issues.",
            "His reputation has changed in recent times.",
        ],
        "correct": ["B", "C"],
    },
]

P3_MATCH_INSTRUCTION = (
    "What topic do Cathy and Graham choose to illustrate with each novel?\n"
    "Choose the correct letter, A-H, next to Questions 25-30."
)

P3_MATCH_OPTIONS = [
    "A. poverty",
    "B. education",
    "C. Dickens's travels",
    "D. entertainment",
    "E. crime and the law",
    "F. wealth",
    "G. medicine",
    "H. a woman's life",
]

P3_MATCH_ITEMS: list[tuple[str, str]] = [
    ("The Pickwick Papers", "G"),
    ("Oliver Twist", "B"),
    ("Nicholas Nickleby", "D"),
    ("Martin Chuzzlewit", "C"),
    ("Bleak House", "H"),
    ("Little Dorrit", "F"),
]

# ── Part 4: notes ────────────────────────────────────────────────────────────

P4_INSTRUCTION = (
    "Complete the notes below.\nWrite ONE WORD ONLY for each answer."
)

P4_NOTES: dict = {
    "variant": "notes",
    "title": "Agricultural programme in Mozambique",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "How the programme was organised",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "It focused on a dry and arid region in "
                                "Chicualacuala district, near the Limpopo River."
                            ),
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "People depended on the forest to provide "
                                "charcoal as a source of income."
                            ),
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g31"},
                        {
                            "type": "text",
                            "value": (
                                " was seen as the main priority to ensure "
                                "the supply of water."
                            ),
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Most of the work organised by farmers' "
                                "associations was done by "
                            ),
                        },
                        {"type": "gap", "gap_id": "g32"},
                        {"type": "text", "value": "."},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Fenced areas were created to keep animals "
                                "away from crops."
                            ),
                        }
                    ]
                },
            ],
        },
        {
            "heading": "The programme provided",
            "items": [
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g33"},
                        {"type": "text", "value": " for the fences"},
                    ]
                },
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g34"},
                        {"type": "text", "value": " for suitable crops"},
                    ]
                },
                {"segments": [{"type": "text", "value": "water pumps."}]},
            ],
        },
        {
            "heading": "The farmers provided",
            "items": [
                {"segments": [{"type": "text", "value": "labour"}]},
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g35"},
                        {
                            "type": "text",
                            "value": " for the fences on their land.",
                        },
                    ]
                },
            ],
        },
        {
            "heading": "Further developments",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "The marketing of produce was sometimes "
                                "difficult due to lack of "
                            ),
                        },
                        {"type": "gap", "gap_id": "g36"},
                        {"type": "text", "value": "."},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Training was therefore provided in "
                                "methods of food "
                            ),
                        },
                        {"type": "gap", "gap_id": "g37"},
                        {"type": "text", "value": "."},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Farmers made special places where ",
                        },
                        {"type": "gap", "gap_id": "g38"},
                        {"type": "text", "value": " could be kept."},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Local people later suggested keeping ",
                        },
                        {"type": "gap", "gap_id": "g39"},
                        {"type": "text", "value": "."},
                    ]
                },
            ],
        },
        {
            "heading": "Evaluation and lessons learned",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Agricultural production increased, "
                                "improving incomes and food security."
                            ),
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Enough time must be allowed, particularly "
                                "for the "
                            ),
                        },
                        {"type": "gap", "gap_id": "g40"},
                        {
                            "type": "text",
                            "value": " phase of the programme.",
                        },
                    ]
                },
            ],
        },
    ],
}

P4_ANSWERS: list[tuple[str, list[str]]] = [
    ("g31", ["Irrigation", "irrigation"]),
    ("g32", ["women"]),
    ("g33", ["wire", "wires"]),
    ("g34", ["seed", "seeds"]),
    ("g35", ["posts"]),
    ("g36", ["transport"]),
    ("g37", ["preservation"]),
    ("g38", ["fish", "fishes"]),
    ("g39", ["bees"]),
    ("g40", ["design"]),
]


def validate_payload() -> None:
    if len(P1_TABLE_ANSWERS) != 4 or len(P1_NOTES_ANSWERS) != 6:
        raise SystemExit("Part 1 must be 4 table + 6 notes")
    if len(P2_MCQ) != 4 or len(P2_MAP_ITEMS) != 6:
        raise SystemExit("Part 2 must be 4 MCQ + 6 map labels")
    if len(P3_MULTI) != 2 or len(P3_MATCH_ITEMS) != 6:
        raise SystemExit("Part 3 must be 2 multi_select + 6 matching")
    if P3_MULTI[0]["correct"] != ["B", "D"] or P3_MULTI[1]["correct"] != ["B", "C"]:
        raise SystemExit("Part 3 multi_select keys must be B/D and B/C")
    if len(P4_ANSWERS) != 10:
        raise SystemExit("Part 4 must have 10 gaps")
    if not MAP_ASSET.is_file():
        raise SystemExit(f"Missing map asset: {MAP_ASSET}")


def install_map_image() -> str:
    dest_dir = Path(__file__).resolve().parent.parent / "media" / "images"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "minster-park.png"
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
    answers: list[tuple[str, list[str]]],
    qtype: QuestionType,
    order_start: int,
) -> int:
    order = order_start
    for gap_id, variants in answers:
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=order,
                question_type=qtype,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
        )
        print(f"    {gap_id} -> {variants}")
        order += 1
    return order


async def _get_or_create_test(db: AsyncSession) -> Test:
    test = (
        await db.execute(
            select(Test).where(
                Test.book_slug == BOOK_SLUG,
                Test.test_number == TEST_NUMBER,
            )
        )
    ).scalar_one_or_none()
    if test is not None:
        test.title = TEST_TITLE
        test.book_name = "Cambridge IELTS 14"
        print(f"Found existing test: {test.title} ({test.id})")
        return test

    test = Test(
        id=uuid.uuid4(),
        title=TEST_TITLE,
        description="Cambridge IELTS 14 Academic, Test 1",
        is_published=False,
        type="academic",
        book_slug=BOOK_SLUG,
        book_name="Cambridge IELTS 14",
        test_number=TEST_NUMBER,
    )
    db.add(test)
    await db.flush()
    for section_type, order in DEFAULT_SECTIONS:
        db.add(Section(test_id=test.id, type=section_type, order=order))
    db.add_all(build_default_rows(test.id))
    await db.flush()
    print(f"Created test: {test.title} ({test.id})")
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
        test = await _get_or_create_test(db)
        await ensure_settings(db, test.id)
        parts = await _listening_parts(db, test)

        for part, section in parts.items():
            removed = await _wipe_section(db, section.id)
            if removed:
                print(f"  Part {part}: removed {removed} old group/question row(s)")
            if section.audio_url:
                print(f"  Part {part}: keep audio {section.audio_url}")

        # Part 1
        p1 = parts[1]
        p1.title = "Part 1 — Festival information"
        g_order = await next_group_order(db, p1.id)
        table_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p1.id,
            order=g_order,
            question_type=QuestionType.TABLE_COMPLETION.value,
            instruction=P1_TABLE_INSTRUCTION,
            options_shared=P1_TABLE,
        )
        db.add(table_group)
        await db.flush()
        print("\nPart 1 — table")
        order = await _add_gaps(
            db,
            section=p1,
            group=table_group,
            answers=P1_TABLE_ANSWERS,
            qtype=QuestionType.TABLE_COMPLETION,
            order_start=1,
        )
        notes1 = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p1.id,
            order=g_order + 1,
            question_type=QuestionType.NOTE_COMPLETION.value,
            instruction=P1_NOTES_INSTRUCTION,
            options_shared=P1_NOTES,
        )
        db.add(notes1)
        await db.flush()
        print("Part 1 — notes")
        await _add_gaps(
            db,
            section=p1,
            group=notes1,
            answers=P1_NOTES_ANSWERS,
            qtype=QuestionType.NOTE_COMPLETION,
            order_start=order,
        )

        # Part 2
        p2 = parts[2]
        p2.title = "Part 2 — Minster Park"
        g_order = await next_group_order(db, p2.id)
        order = 1
        mcq_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p2.id,
            order=g_order,
            question_type=QuestionType.MCQ.value,
            instruction=P2_MCQ_INSTRUCTION,
            subtitle="Minster Park",
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

        map_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p2.id,
            order=g_order + 1,
            question_type=QuestionType.MAP_LABELING.value,
            instruction=P2_MAP_INSTRUCTION,
            subtitle="Minster Park",
            options_shared={"options": P2_MAP_OPTIONS, "image_url": map_url},
        )
        db.add(map_group)
        await db.flush()
        print("Part 2 — map")
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

        # Part 3
        p3 = parts[3]
        p3.title = "Part 3 — Dickens display"
        g_order = await next_group_order(db, p3.id)
        order = 1
        print("\nPart 3 — multi_select")
        for item in P3_MULTI:
            g = QuestionGroup(
                id=uuid.uuid4(),
                section_id=p3.id,
                order=g_order,
                question_type=QuestionType.MULTI_SELECT.value,
                instruction=P3_MULTI_INSTRUCTION,
            )
            db.add(g)
            await db.flush()
            g_order += 1
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p3.id,
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

        match_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p3.id,
            order=g_order,
            question_type=QuestionType.MATCHING_FEATURES.value,
            instruction=P3_MATCH_INSTRUCTION,
            subtitle="Topics",
            options_shared={
                "options": P3_MATCH_OPTIONS,
                "questions_heading": "Novels",
            },
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
        p4.title = "Part 4 — Agricultural programme in Mozambique"
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
        print(f"\nDone. {TEST_TITLE} listening Q1–40 seeded. Map: {map_url}")
        print("Test is unpublished until Reading/Writing/Speaking are added.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
