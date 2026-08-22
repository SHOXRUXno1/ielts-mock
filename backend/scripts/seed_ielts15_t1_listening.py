"""Seed Cambridge IELTS 15 Test 1 Listening (Q1–40).

Idempotent: wipes listening groups/questions, keeps audio_url.
Official keys from Cambridge IELTS 15 Academic, Test 1.

Usage (prod container):
    python /app/scripts/seed_ielts15_t1_listening.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test
from app.services.scoring import scoring_slots_for_question
from app.services.seed_compound import gap_answer_key, next_group_order

TEST_ID = uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590")
PART_IDS = {
    1: uuid.UUID("1c0ceaef-47f0-49c4-828d-d04fe6c25053"),
    2: uuid.UUID("60ef0f0c-c254-4301-a4c2-0fa5c0bd117c"),
    3: uuid.UUID("955aaaa9-3a6f-48f4-8d71-d49bc86a7f4b"),
    4: uuid.UUID("0c1cc2fc-7d8d-4ce0-83a8-5c6e427ee29c"),
}

# ── Part 1: notes ────────────────────────────────────────────────────────────

P1_INSTRUCTION = (
    "Complete the notes below.\n"
    "Write ONE WORD AND/OR A NUMBER for each answer."
)

P1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Bankside Recruitment Agency",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Address of agency: 497 Eastside, Docklands"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Name of agent: Becky "},
                        {"type": "gap", "gap_id": "g1"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Phone number: 07866 510333"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Best to call her in the "},
                        {"type": "gap", "gap_id": "g2"},
                    ]
                },
            ],
        },
        {
            "heading": "Typical jobs",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Clerical and admin roles, mainly in the finance industry",
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Must have good "},
                        {"type": "gap", "gap_id": "g3"},
                        {"type": "text", "value": " skills"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Jobs are usually for at least one "},
                        {"type": "gap", "gap_id": "g4"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Pay is usually £"},
                        {"type": "gap", "gap_id": "g5"},
                        {"type": "text", "value": " per hour"},
                    ]
                },
            ],
        },
        {
            "heading": "Registration process",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Wear a "},
                        {"type": "gap", "gap_id": "g6"},
                        {"type": "text", "value": " to the interview"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Must bring your "},
                        {"type": "gap", "gap_id": "g7"},
                        {"type": "text", "value": " to the interview"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "They will ask questions about each applicant's ",
                        },
                        {"type": "gap", "gap_id": "g8"},
                    ]
                },
            ],
        },
        {
            "heading": "Advantages of using an agency",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "The "},
                        {"type": "gap", "gap_id": "g9"},
                        {
                            "type": "text",
                            "value": " you receive at interview will benefit you",
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Will get access to vacancies which are not advertised",
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Less "},
                        {"type": "gap", "gap_id": "g10"},
                        {
                            "type": "text",
                            "value": " is involved in applying for jobs",
                        },
                    ]
                },
            ],
        },
    ],
}

P1_ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["Jamieson"]),
    ("g2", ["afternoon"]),
    ("g3", ["communication"]),
    ("g4", ["week"]),
    ("g5", ["10", "ten"]),
    ("g6", ["suit"]),
    ("g7", ["passport"]),
    ("g8", ["personality"]),
    ("g9", ["feedback"]),
    ("g10", ["time"]),
]

# ── Part 2: MCQ + table ──────────────────────────────────────────────────────

P2_MCQ_INSTRUCTION = "Choose the correct letter, A, B or C."

P2_MCQ: list[dict] = [
    {
        "question": "According to the speaker, the company",
        "options": [
            "has been in business for longer than most of its competitors.",
            "arranges holidays to more destinations than its competitors.",
            "has more customers than its competitors.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "Where can customers meet the tour manager before travelling "
            "to the Isle of Man?"
        ),
        "options": ["Liverpool", "Heysham", "Luton"],
        "correct": "B",
    },
    {
        "question": "How many lunches are included in the price of the holiday?",
        "options": ["three", "four", "five"],
        "correct": "A",
    },
    {
        "question": "Customers have to pay extra for",
        "options": [
            "guaranteeing themselves a larger room.",
            "booking at short notice.",
            "transferring to another date.",
        ],
        "correct": "C",
    },
]


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


P2_TABLE: dict = {
    "variant": "table",
    "title": "Timetable for Isle of Man holiday",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 1,
    "headers": ["Day", "Activity", "Notes"],
    "rows": [
        [
            _plain("Day 1"),
            _plain("Arrive"),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [{"type": "text", "value": "Introduction by manager"}]},
                    {
                        "segments": [
                            {"type": "text", "value": "Hotel dining room has view of the "},
                            {"type": "gap", "gap_id": "g15"},
                        ]
                    },
                ],
            },
        ],
        [
            _plain("Day 2"),
            _plain("Tynwald Exhibition and Peel"),
            _plain_gap("Tynwald may have been founded in ", "g16", " not 979."),
        ],
        [
            _plain("Day 3"),
            _plain("Trip to Snaefell"),
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": "Travel along promenade in a tram",
                            }
                        ]
                    },
                    {
                        "segments": [
                            {"type": "text", "value": "train to Laxey"}
                        ]
                    },
                    {
                        "segments": [
                            {"type": "text", "value": "train to the "},
                            {"type": "gap", "gap_id": "g17"},
                            {"type": "text", "value": " of Snaefell"},
                        ]
                    },
                ],
            },
        ],
        [
            _plain("Day 4"),
            _plain("Free day"),
            _plain_gap(
                "Company provides a ",
                "g18",
                " for local transport and heritage sites.",
            ),
        ],
        [
            _plain("Day 5"),
            _plain_gap("Take the ", "g19", " railway train from Douglas to Port Erin"),
            _plain_gap(
                "Free time, then coach to Castletown – former ",
                "g20",
                " has old castle.",
            ),
        ],
        [
            _plain("Day 6"),
            _plain("Leave"),
            _plain("Leave the island by ferry or plane"),
        ],
    ],
}

P2_TABLE_ANSWERS: list[tuple[str, list[str]]] = [
    ("g15", ["river"]),
    ("g16", ["1422"]),
    ("g17", ["top"]),
    ("g18", ["pass"]),
    ("g19", ["steam"]),
    ("g20", ["capital"]),
]

P2_TABLE_INSTRUCTION = (
    "Complete the table below.\n"
    "Write ONE WORD AND/OR A NUMBER for each answer."
)

# ── Part 3: matching + MCQ + multi_select ────────────────────────────────────

P3_MATCH_INSTRUCTION = (
    "What did findings of previous research claim about the personality "
    "traits a child is likely to have because of their position in the family?\n"
    "Choose SIX answers from the box and write the correct letter, A-H, "
    "next to Questions 21-26."
)

P3_MATCH_OPTIONS = [
    "A. outgoing",
    "B. selfish",
    "C. independent",
    "D. attention-seeking",
    "E. introverted",
    "F. co-operative",
    "G. caring",
    "H. competitive",
]

P3_MATCH_ITEMS: list[tuple[str, str]] = [
    ("the eldest child", "G"),
    ("a middle child", "F"),
    ("the youngest child", "A"),
    ("a twin", "E"),
    ("an only child", "B"),
    ("a child with much older siblings", "C"),
]

P3_MCQ: list[dict] = [
    {
        "question": (
            "What do the speakers say about the evidence relating to "
            "birth order and academic success?"
        ),
        "options": [
            "There is conflicting evidence about whether oldest children perform best in intelligence tests.",
            "There is little doubt that birth order has less influence on academic achievement than socio-economic status.",
            "Some studies have neglected to include important factors such as family size.",
        ],
        "correct": "C",
    },
    {
        "question": (
            "What does Ruth think is surprising about the difference in "
            "oldest children's academic performance?"
        ),
        "options": [
            "It is mainly thanks to their roles as teachers for their younger siblings.",
            "The advantages they have only lead to a slightly higher level of achievement.",
            "The extra parental attention they receive at a young age makes little difference.",
        ],
        "correct": "A",
    },
]

P3_MULTI = {
    "question": (
        "Which TWO experiences of sibling rivalry do the speakers agree "
        "has been valuable for them?"
    ),
    "options": [
        "learning to share",
        "learning to stand up for oneself",
        "learning to be a good loser",
        "learning to be tolerant",
        "learning to say sorry",
    ],
    "correct": ["B", "D"],
}

# ── Part 4: notes ────────────────────────────────────────────────────────────

P4_INSTRUCTION = (
    "Complete the notes below.\nWrite ONE WORD ONLY for each answer."
)

P4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The Eucalyptus Tree in Australia",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "Importance",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "it provides "},
                        {"type": "gap", "gap_id": "g31"},
                        {
                            "type": "text",
                            "value": " and food for a wide range of species",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "its leaves provide "},
                        {"type": "gap", "gap_id": "g32"},
                        {
                            "type": "text",
                            "value": " which is used to make a disinfectant",
                        },
                    ]
                },
            ],
        },
        {
            "heading": "Reasons for present decline in number",
            "items": [],
        },
        {
            "heading": "A) Diseases",
            "items": [],
        },
        {
            "heading": "(i) 'Mundulla Yellows'",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Cause – lime used for making "},
                        {"type": "gap", "gap_id": "g33"},
                        {"type": "text", "value": " was absorbed"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "  trees were unable to take in necessary "
                                "iron through their roots"
                            ),
                        }
                    ]
                },
            ],
        },
        {
            "heading": "(ii) 'Bell-miner Associated Die-back'",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Cause – "},
                        {"type": "gap", "gap_id": "g34"},
                        {"type": "text", "value": " feed on eucalyptus leaves"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "  they secrete a substance containing sugar",
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "  bell-miner birds are attracted by this "
                                "and keep away other species"
                            ),
                        }
                    ]
                },
            ],
        },
        {
            "heading": "B) Bushfires",
            "items": [],
        },
        {
            "heading": "William Jackson's theory:",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "high-frequency bushfires have impact on "
                                "vegetation, resulting in the growth of "
                            ),
                        },
                        {"type": "gap", "gap_id": "g35"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "mid-frequency bushfires result in the "
                                "growth of eucalyptus forests, because they:"
                            ),
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "  make more "},
                        {"type": "gap", "gap_id": "g36"},
                        {"type": "text", "value": " available to the trees"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "  maintain the quality of the "},
                        {"type": "gap", "gap_id": "g37"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "low-frequency bushfires result in the "
                                "growth of '"
                            ),
                        },
                        {"type": "gap", "gap_id": "g38"},
                        {"type": "text", "value": " rainforest', which is:"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "  a "},
                        {"type": "gap", "gap_id": "g39"},
                        {"type": "text", "value": " ecosystem"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "  an ideal environment for the ",
                        },
                        {"type": "gap", "gap_id": "g40"},
                        {"type": "text", "value": " of the bell-miner"},
                    ]
                },
            ],
        },
    ],
}

P4_ANSWERS: list[tuple[str, list[str]]] = [
    ("g31", ["shelter"]),
    ("g32", ["oil"]),
    ("g33", ["roads"]),
    ("g34", ["insects"]),
    ("g35", ["grass", "grasses"]),
    ("g36", ["water"]),
    ("g37", ["soil"]),
    ("g38", ["dry"]),
    ("g39", ["simple"]),
    ("g40", ["nest", "nests"]),
]


async def _wipe_section(db: AsyncSession, section_id: uuid.UUID) -> int:
    from sqlalchemy import delete as sa_delete

    from app.models.answer import Answer

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


def _validate_payload() -> None:
    p1 = [v for _, v in P1_ANSWERS]
    p2_table = [v for _, v in P2_TABLE_ANSWERS]
    if len(P1_ANSWERS) != 10:
        raise SystemExit(f"Part 1 must have 10 gaps, got {len(P1_ANSWERS)}")
    if len(P2_MCQ) != 4 or len(P2_TABLE_ANSWERS) != 6:
        raise SystemExit("Part 2 must be 4 MCQ + 6 table gaps")
    if len(P3_MATCH_ITEMS) != 6 or len(P3_MCQ) != 2:
        raise SystemExit("Part 3 must be 6 matching + 2 MCQ + 1 multi")
    if len(P4_ANSWERS) != 10:
        raise SystemExit(f"Part 4 must have 10 gaps, got {len(P4_ANSWERS)}")
    if P3_MULTI["correct"] != ["B", "D"]:
        raise SystemExit("Q29-30 must be B and D")
    for block in (p1, p2_table, [v for _, v in P4_ANSWERS]):
        for variants in block:
            if not variants or any(not str(x).strip() for x in variants):
                raise SystemExit(f"Empty answer variant: {variants}")


async def _seed_notes(
    db: AsyncSession,
    *,
    section: Section,
    title: str,
    instruction: str,
    structure: dict,
    answers: list[tuple[str, list[str]]],
    qtype: QuestionType,
) -> None:
    section.title = title
    group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=qtype.value,
        instruction=instruction,
        subtitle=None,
        options_shared=structure,
    )
    db.add(group)
    await db.flush()
    for i, (gap_id, variants) in enumerate(answers, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=i,
                question_type=qtype,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
        )
        print(f"    Q{i} {gap_id} -> {variants}")


async def main() -> None:
    _validate_payload()
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")
        if not (test.book_name or "").strip():
            test.book_name = "Cambridge IELTS 15"
        print(f"Test: {test.title} ({test.id})")

        sections: dict[int, Section] = {}
        for part, sid in PART_IDS.items():
            section = await db.get(Section, sid)
            if section is None or section.test_id != TEST_ID:
                raise SystemExit(f"Listening Part {part} {sid} not found")
            sections[part] = section
            if section.audio_url:
                print(f"  Part {part}: keep audio {section.audio_url}")
            removed = await _wipe_section(db, sid)
            if removed:
                print(f"  Part {part}: removed {removed} old group/question row(s)")

        print("\nPart 1 — notes")
        await _seed_notes(
            db,
            section=sections[1],
            title="Part 1 — Bankside Recruitment Agency",
            instruction=P1_INSTRUCTION,
            structure=P1_STRUCTURE,
            answers=P1_ANSWERS,
            qtype=QuestionType.NOTE_COMPLETION,
        )

        print("\nPart 2 — MCQ + table")
        p2 = sections[2]
        p2.title = "Part 2 — Matthews Island Holidays"
        order = 1
        group_order = await next_group_order(db, p2.id)
        mcq_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p2.id,
            order=group_order,
            question_type=QuestionType.MCQ.value,
            instruction=P2_MCQ_INSTRUCTION,
            subtitle="Matthews Island Holidays",
            options_shared=None,
        )
        db.add(mcq_group)
        await db.flush()
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

        table_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p2.id,
            order=group_order + 1,
            question_type=QuestionType.TABLE_COMPLETION.value,
            instruction=P2_TABLE_INSTRUCTION,
            subtitle=None,
            options_shared=P2_TABLE,
        )
        db.add(table_group)
        await db.flush()
        for gap_id, variants in P2_TABLE_ANSWERS:
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p2.id,
                    question_group_id=table_group.id,
                    order=order,
                    question_type=QuestionType.TABLE_COMPLETION,
                    content={"gap_id": gap_id},
                    answer_key=gap_answer_key(variants, max_words=1),
                )
            )
            print(f"    {gap_id} -> {variants}")
            order += 1

        print("\nPart 3 — matching + MCQ + multi_select")
        p3 = sections[3]
        p3.title = "Part 3 — Birth order"
        group_order = await next_group_order(db, p3.id)
        order = 1
        match_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p3.id,
            order=group_order,
            question_type=QuestionType.MATCHING_FEATURES.value,
            instruction=P3_MATCH_INSTRUCTION,
            subtitle="Personality Traits",
            options_shared={
                "options": P3_MATCH_OPTIONS,
                "questions_heading": "Position in family",
            },
        )
        db.add(match_group)
        await db.flush()
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
            print(f"    match {stem!r} -> {letter}")
            order += 1

        mcq3 = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p3.id,
            order=group_order + 1,
            question_type=QuestionType.MCQ.value,
            instruction=P2_MCQ_INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(mcq3)
        await db.flush()
        for item in P3_MCQ:
            db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=p3.id,
                    question_group_id=mcq3.id,
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

        multi_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=p3.id,
            order=group_order + 2,
            question_type=QuestionType.MULTI_SELECT.value,
            instruction="Choose TWO letters, A-E.",
            subtitle=None,
            options_shared=None,
        )
        db.add(multi_group)
        await db.flush()
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=p3.id,
                question_group_id=multi_group.id,
                order=order,
                question_type=QuestionType.MULTI_SELECT,
                content={
                    "choose_n": 2,
                    "question": P3_MULTI["question"],
                    "options": P3_MULTI["options"],
                },
                answer_key={"correct": P3_MULTI["correct"]},
            )
        )
        print(f"    multi_select order={order} -> {P3_MULTI['correct']}")

        print("\nPart 4 — notes")
        await _seed_notes(
            db,
            section=sections[4],
            title="Part 4 — The Eucalyptus Tree in Australia",
            instruction=P4_INSTRUCTION,
            structure=P4_STRUCTURE,
            answers=P4_ANSWERS,
            qtype=QuestionType.NOTE_COMPLETION,
        )

        print("\nVerify scoring slots")
        total_slots = 0
        for part, sid in PART_IDS.items():
            qs = (
                await db.execute(
                    select(Question)
                    .where(Question.section_id == sid)
                    .order_by(Question.order)
                )
            ).scalars().all()
            slots = sum(scoring_slots_for_question(q) for q in qs)
            total_slots += slots
            audio = sections[part].audio_url
            print(f"  Part {part}: {len(qs)} rows, {slots} slots, audio={bool(audio)}")
        if total_slots != 40:
            raise SystemExit(f"Expected 40 listening slots, got {total_slots}")

        await db.commit()
        print("\nDone. IELTS 15 Test 1 Listening Q1–40 seeded. Audio unchanged.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
