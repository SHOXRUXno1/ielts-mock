"""Seed Practice Set E Test 4 Listening, all four sections (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 4.
Every key is taken from the printed Explanatory Answer Key (pp.154-161).

Section 1  Q1-4   short_answer         Proof of name / address (THREE WORDS)
           Q5-7   note_completion      Savings Bank details (TWO WORDS OR NUMBERS)
           Q8-10  map_labeling         Banks on the map (A-H)
Section 2  Q11-14 table_completion     Preparing for the interview (THREE WORDS)
           Q15-20 note_completion      At the interview (THREE WORDS)
Section 3  Q21-24 summary_completion   Choosing modules (THREE WORDS)
           Q25-29 matching_features    Module features (A-C)
           Q30    mcq                  Spanish 1A private study chart (A-C)
Section 4  Q31-33 note_completion      Acraman Crater diagram (TWO WORDS AND/OR A NUMBER)
           Q34-36 mcq                  Acraman facts (A-C)
           Q37-40 short_answer         Impact sequence (THREE WORDS)

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t4_listening.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.services.compound import validate_compound_structure  # noqa: E402
from app.services.scoring import scoring_slots_for_question  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_e_common import (  # noqa: E402
    MAP_IMAGE_URL,
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 4
MAP_URL = MAP_IMAGE_URL.format(test=TEST_NUMBER)
CHARTS_URL = "/media/images/practice_e_t4_listening_charts.png"
CRATER_URL = "/media/images/practice_e_t4_listening_crater.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Section 1 — Opening a bank account ───────────────────────────────────────

SHORT1_ITEMS: list[tuple[str, list[str]]] = [
    (
        "Which other document could Sam use as proof of her name?",
        ["driving licence", "a driving licence", "(a) driving licence"],
    ),
    (
        "Which other document could she use as proof of her name?",
        ["benefit book", "a benefit book", "(a) benefit book"],
    ),
    (
        "Which other document could she use as proof of her address?",
        ["insurance certificate", "an insurance certificate",
         "(an) insurance certificate"],
    ),
    (
        "Which other document could she use as proof of her address?",
        ["electricity bill", "an electricity bill", "(an) electricity bill"],
    ),
]

NOTES1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Savings Bank",
    "instruction_words": "TWO WORDS OR NUMBERS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("Name of bank: Savings Bank")]},
                {"segments": [text("Open which days: Monday\u2013Friday")]},
                {
                    "segments": [
                        text("Opening hours: "),
                        gap("n5"),
                    ]
                },
                {
                    "segments": [
                        text("Where: "),
                        gap("n6"),
                    ]
                },
                {
                    "segments": [
                        text("Free gift: "),
                        gap("n7"),
                    ]
                },
            ],
        },
    ],
}

NOTES1_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n5",
        [
            "9.30-3.30", "9.30\u20133.30", "9.30 to 3.30",
            "9:30-3:30", "9.30-3.30",
            "nine thirty to half past three",
        ],
        2,
    ),
    (
        "n6",
        ["ground floor", "(the) ground floor", "the ground floor"],
        2,
    ),
    (
        "n7",
        ["no", "nothing", "no/nothing", "none"],
        2,
    ),
]

MAP1_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H"]

MAP1_ITEMS: list[tuple[str, str]] = [
    ("Royal Bank", "F"),
    ("Northern Bank", "A"),
    ("National Bank", "C"),
]


# ── Section 2 — Preparing for the interview ──────────────────────────────────

TABLE2_STRUCTURE: dict = {
    "variant": "table",
    "title": "Preparing for the interview",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "headers": ["What to do", "How to do it"],
    "rows": [
        [
            {
                "variant": "plain",
                "segments": [
                    text(
                        "Step 1: Gather all documents, e.g. copies of "
                        "r\u00e9sum\u00e9.\nAlso take some "
                    ),
                    gap("t11"),
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    text("e.g. designs, drawings, written work"),
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [
                    text(
                        "Step 2: Check you have pen and paper.\n"
                        "Get more information. Ask for "
                    ),
                    gap("t12"),
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    text(
                        "See profiles at Chamber of Commerce, library"
                    ),
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [
                    text("Step 3: Contact "),
                    gap("t13"),
                    text(" of this or related firms"),
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    text(
                        "Focus on you and the job.\n"
                        "Compare yourself with what is required.\n"
                        "Imagine likely questions and your answers.\n"
                        "Decide how to make up for any "
                    ),
                    gap("t14"),
                    text(" you lack."),
                ],
            },
        ],
    ],
}

TABLE2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t11", ["work samples", "(some) work samples"], 3),
    (
        "t12",
        [
            "job description", "a job description",
            "(a/the) job description", "the job description",
        ],
        3,
    ),
    (
        "t13",
        ["employees", "(the) employees", "people / employees"],
        3,
    ),
    (
        "t14",
        [
            "experience or skills", "experience / skills",
            "skills or experience",
        ],
        3,
    ),
]

NOTES2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "At the interview",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Arrive no more than "),
                        gap("n15"),
                        text(" before the time of the interview."),
                    ]
                },
                {
                    "segments": [
                        text("After you hear the question, you can "),
                        gap("n16"),
                        text(" before you reply."),
                    ]
                },
                {
                    "segments": [
                        text("You can "),
                        gap("n17"),
                        text(
                            " if you don\u2019t understand what "
                            "they\u2019re asking you."
                        ),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Wait for them to offer you the job before "
                            "you say what "
                        ),
                        gap("n18"),
                        text(" you want."),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Learning from the experience will make "
                            "you more "
                        ),
                        gap("n19"),
                        text(" in future interviews."),
                    ]
                },
                {
                    "segments": [
                        text("Pay attention to your "),
                        gap("n20"),
                        text(
                            " \u2014 it shows you have a positive "
                            "attitude."
                        ),
                    ]
                },
            ],
        },
    ],
}

NOTES2_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n15",
        ["ten minutes", "10 minutes", "10 mins", "ten mins"],
        3,
    ),
    ("n16", ["take your time"], 3),
    (
        "n17",
        [
            "ask for clarification", "ask for clarification",
            "ask clarification",
        ],
        3,
    ),
    ("n18", ["salary", "salaries"], 3),
    ("n19", ["confident"], 3),
    ("n20", ["appearance"], 3),
]


# ── Section 3 — Choosing modules ─────────────────────────────────────────────

SUMMARY3_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Choosing modules",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "paragraphs": [
        {
            "segments": [
                text(
                    "To many employers, academic success and personal "
                    "development as a result of being at "
                ),
                gap("s21"),
                text(
                    " can be as important as course content, so "
                    "choose "
                ),
                gap("s22"),
                text(
                    " modules that you may do well in. You should, "
                    "however, think more carefully about your choice "
                    "if your course is "
                ),
                gap("s23"),
                text(
                    ". In this case the course normally includes all "
                    "the modules necessary for professional training, "
                    "but if you are in any doubt check with your "
                    "academic department or the "
                ),
                gap("s24"),
                text(" at the university."),
            ]
        },
    ],
}

SUMMARY3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s21", ["university", "(a) university", "the university"], 3),
    ("s22", ["interesting"], 3),
    ("s23", ["vocational"], 3),
    (
        "s24",
        [
            "careers service", "(the) careers service",
            "Careers Service", "university's Careers Service",
        ],
        3,
    ),
]

MODULE_OPTIONS = [
    "A. Applied Chemical Engineering",
    "B. Fluid Mechanics",
    "C. Chemical Engineering: Science 1",
]

MODULE_ITEMS: list[tuple[str, str]] = [
    ("developing computer skills", "A"),
    ("exemption from part of a module", "C"),
    ("assessment by formal examination", "B"),
    ("developing speaking and writing skills", "A"),
    ("learning through problem solving", "C"),
]

MCQ3_30: list[dict] = [
    {
        "question": (
            "Which chart shows the percentage of private study "
            "time on the Spanish 1A module?"
        ),
        "options": ["A", "B", "C"],
        "correct": "C",
        "image_url": CHARTS_URL,
    },
]


# ── Section 4 — The Acraman Crater ───────────────────────────────────────────

DIAGRAM4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The Acraman Crater",
    "instruction_words": "TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "image_url": CRATER_URL,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Speed of meteorite: "),
                        gap("d31"),
                        text(" km per hour"),
                    ]
                },
                {
                    "segments": [
                        text("Depth of crater: "),
                        gap("d32"),
                    ]
                },
                {
                    "segments": [
                        text("Width of crater: "),
                        gap("d33"),
                    ]
                },
            ],
        },
    ],
}

DIAGRAM4_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "d31",
        [
            "90000", "90,000", "90 000", "ninety thousand",
            "90 thousand",
        ],
        2,
    ),
    (
        "d32",
        ["4 km", "4 kilometres", "4 kilometers", "four kilometres",
         "four km"],
        2,
    ),
    (
        "d33",
        [
            "40 km", "40 kilometres", "40 kilometers",
            "forty kilometres", "forty km",
        ],
        2,
    ),
]

MCQ4_ITEMS: list[dict] = [
    {
        "question": "The crater at Acraman is",
        "options": [
            "nowadays entirely covered by sea water.",
            "one of the most beautiful on Earth.",
            "less spectacular than others in Australia.",
        ],
        "correct": "C",
    },
    {
        "question": (
            "Williams realized what had happened at Acraman when he"
        ),
        "options": [
            "saw pictures of the area taken from above.",
            "visited Acraman for the first time in 1980.",
            "noticed a picture of the crater in a textbook.",
        ],
        "correct": "A",
    },
    {
        "question": "Where was rock from Acraman found?",
        "options": [
            "Only in the Flinders mountains.",
            "At several places over 300 km from Acraman.",
            "At a place 500 km from Acraman, but nowhere else.",
        ],
        "correct": "B",
    },
]

SHORT4_ITEMS: list[tuple[str, list[str]]] = [
    (
        "What made the sea water shake?",
        [
            "earthquake", "the earthquake", "(the) earthquake",
            "shock waves", "(the) shock waves",
            "earthquake/shock waves", "earthquake / shock waves",
        ],
    ),
    (
        "What threw the pebbles into the air?",
        ["explosion", "the explosion", "(the) explosion"],
    ),
    (
        "What was mixed with silt to form a layer of rock?",
        ["sand"],
    ),
    (
        "What shaped the ripples on top of the rock?",
        [
            "waves", "huge waves", "(huge) waves", "(the) (huge) waves",
            "the huge waves",
        ],
    ),
]


# ── writer helpers ───────────────────────────────────────────────────────────


class SectionWriter:
    def __init__(self, db: AsyncSession, section: Section) -> None:
        self.db = db
        self.section = section
        self.order = 1
        self.group_order = 1
        self.slots = 0

    async def _group(
        self,
        question_type: QuestionType,
        instruction: str,
        *,
        options_shared: dict | None = None,
        subtitle: str | None = None,
    ) -> QuestionGroup:
        if options_shared is not None and "variant" in options_shared:
            validate_compound_structure(question_type.value, options_shared)
        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=self.section.id,
            order=self.group_order,
            question_type=question_type.value,
            instruction=instruction,
            subtitle=subtitle,
            options_shared=options_shared,
        )
        self.db.add(group)
        await self.db.flush()
        self.group_order += 1
        return group

    def _add(
        self,
        group: QuestionGroup,
        question_type: QuestionType,
        content: dict,
        answer_key: dict | None,
        *,
        image_url: str | None = None,
    ) -> Question:
        question = Question(
            id=uuid.uuid4(),
            section_id=self.section.id,
            question_group_id=group.id,
            order=self.order,
            question_type=question_type,
            content=content,
            answer_key=answer_key,
            image_url=image_url,
        )
        self.db.add(question)
        self.order += 1
        self.slots += scoring_slots_for_question(question)
        return question

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str], int]],
    ) -> None:
        group = await self._group(
            question_type, instruction, options_shared=structure
        )
        for gap_id, variants, max_words in answers:
            self._add(
                group,
                question_type,
                {"gap_id": gap_id},
                gap_answer_key(variants, max_words=max_words),
            )

    async def short_answer(
        self,
        instruction: str,
        items: list[tuple[str, list[str]]],
        *,
        max_words: int = 3,
    ) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for prompt, variants in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                {"prompt": prompt, "max_words": max_words},
                gap_answer_key(variants, max_words=max_words),
            )

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            content = {
                "question": item["question"],
                "options": item["options"],
            }
            if item.get("image_url"):
                content["image_url"] = item["image_url"]
            self._add(
                group,
                QuestionType.MCQ,
                content,
                {"correct": item["correct"]},
                image_url=item.get("image_url"),
            )

    async def lettered(
        self,
        question_type: QuestionType,
        instruction: str,
        options: list[str],
        items: list[tuple[str, str]],
        *,
        options_heading: str | None = None,
    ) -> None:
        shared: dict = {"options": options}
        if options_heading:
            shared["options_heading"] = options_heading
        group = await self._group(
            question_type, instruction, options_shared=shared
        )
        for question, correct in items:
            self._add(
                group,
                question_type,
                {"question": question},
                {"correct": correct},
            )

    async def map_labeling(
        self,
        instruction: str,
        options: list[str],
        items: list[tuple[str, str]],
        *,
        image_url: str,
        subtitle: str | None = None,
    ) -> None:
        group = await self._group(
            QuestionType.MAP_LABELING,
            instruction,
            options_shared={"options": options, "image_url": image_url},
            subtitle=subtitle,
        )
        for location, letter in items:
            self._add(
                group,
                QuestionType.MAP_LABELING,
                {"location": location},
                {"correct": letter},
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    # -- Section 1: Opening a bank account --
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(
        f"\nSection 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.short_answer(
        "Answer the questions below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        SHORT1_ITEMS,
        max_words=3,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS OR NUMBERS for each answer.",
        NOTES1_STRUCTURE,
        NOTES1_ANSWERS,
    )
    await w.map_labeling(
        "Label the map below.\n"
        "Match the places in Questions 8\u201310 to the appropriate "
        "letters A\u2013H on the map.",
        MAP1_OPTIONS,
        MAP1_ITEMS,
        image_url=MAP_URL,
        subtitle="Which places are at the following locations?",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 2: Preparing for the interview --
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(
        f"\nSection 2 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        TABLE2_STRUCTURE,
        TABLE2_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        NOTES2_STRUCTURE,
        NOTES2_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 3: Choosing modules --
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(
        f"\nSection 3 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below by writing NO MORE THAN "
        "THREE WORDS in the spaces provided.",
        SUMMARY3_STRUCTURE,
        SUMMARY3_ANSWERS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Which modules have the following features?\n"
        "Write the appropriate letters A\u2013C against "
        "questions 25\u201329.\n"
        f"{SCREEN_LETTER_HINT}",
        MODULE_OPTIONS,
        MODULE_ITEMS,
        options_heading="Modules",
    )
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        MCQ3_30,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 4: The Acraman Crater --
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(
        f"\nSection 4 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Label the diagram.\n"
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
        DIAGRAM4_STRUCTURE,
        DIAGRAM4_ANSWERS,
    )
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        MCQ4_ITEMS,
    )
    await w.short_answer(
        "Answer the questions below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        SHORT4_ITEMS,
        max_words=3,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    total = sum(totals)
    if total != 40:
        raise SystemExit(
            f"expected 40 scoring slots across the four sections, got {total}"
        )

    await db.commit()
    print(f"\nDone. Listening seeded: {totals} = {total} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
