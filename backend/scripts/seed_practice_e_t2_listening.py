"""Seed Practice Set E Test 2 Listening, all four sections (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 2.
Every key is taken from the printed Explanatory Answer Key (pp.130-138).

Section 1  Q1-6   classification      Renting flat 3A (A/B/C)
           Q7-10  mcq                  Flat details (A-D)
Section 2  Q11-12 mcq                  Loneliness survey charts (A-C)
           Q13-20 sentence_completion  Loneliness counselling (TWO WORDS)
Section 3  Q21-23 multi_select         Language Centre (THREE from A-F)
           Q24    multi_select         Second floor TV (TWO from A-E)
           Q25-27 multi_select         Joining the Centre (THREE from A-F)
           Q28    multi_select         Tell librarian (TWO from A-E)
           Q29-30 multi_select         What you can do (TWO from A-E)
Section 4  Q31-34 table_completion     Zip fastener history (TWO WORDS OR A NUMBER)
           Q35-39 diagram_labeling     Separating zip diagram (THREE WORDS)
           Q40    mcq                  Speaker's overall aim (A-D)

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t2_listening.py
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
    AUDIO_URL,
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 2


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Section 1 — Renting flat 3A ──────────────────────────────────────────────

# Q1-6: Classification A=Yes definitely, B=Maybe, C=Definitely not
CLASSIFICATION1_OPTIONS = [
    "A. Yes, definitely",
    "B. Maybe",
    "C. Definitely not",
]

CLASSIFICATION1_ITEMS: list[tuple[str, str]] = [
    ("Current gas safety certificate?", "A"),
    ("Gas inspection within last twelve months?", "A"),
    ("Electricity checked in last five years?", "B"),
    ("Sufficient electric sockets?", "C"),
    ("Fire detection equipment that works?", "B"),
    ("Previous tenants all returned keys?", "A"),
]

# Q7-10: MCQ
MCQ1_ITEMS: list[dict] = [
    {
        "question": "On which floor is the storeroom?",
        "options": [
            "first",
            "second",
            "third",
        ],
        "correct": "C",
    },
    {
        "question": "What is the temperature of the hot water?",
        "options": [
            "55°",
            "60°",
            "70°",
        ],
        "correct": "B",
    },
    {
        "question": "How big is the garden?",
        "options": [
            "20 m²",
            "90 m²",
            "150 m²",
        ],
        "correct": "C",
    },
    {
        "question": "What size is the television?",
        "options": [
            "70 cm",
            "80 cm",
            "90 cm",
        ],
        "correct": "B",
    },
]


# ── Section 2 — Loneliness and counselling ───────────────────────────────────

MCQ2_ITEMS: list[dict] = [
    {
        "question": (
            "Which column of the chart shows the percentage of "
            "young people suffering loneliness?"
        ),
        "options": ["A", "B", "C"],
        "correct": "B",
    },
    {
        "question": (
            "Which chart shows the percentage of young people "
            "using the counselling service?"
        ),
        "options": ["A", "B", "C"],
        "correct": "A",
    },
]

# Q13-20: sentence/note completion — TWO WORDS
NOTES2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Loneliness and counselling",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Leaving home",
            "items": [
                {
                    "segments": [
                        text("In the "),
                        gap("n13"),
                        text(" a lot of young people suffer from loneliness."),
                    ]
                },
                {
                    "segments": [
                        text("Sense of isolation comes at a time when surrounded by "),
                        gap("n14"),
                        text("."),
                    ]
                },
                {
                    "segments": [
                        text("Those more used to being "),
                        gap("n15"),
                        text(" deal best with leaving home."),
                    ]
                },
                {
                    "segments": [
                        text("Making new friends since starting "),
                        gap("n16"),
                        text(" may be difficult."),
                    ]
                },
                {
                    "segments": [
                        text("A long-distance relationship with someone who lives "),
                        gap("n17"),
                        text("."),
                    ]
                },
            ],
        },
        {
            "heading": "Combating loneliness",
            "items": [
                {
                    "segments": [
                        text("Remember that "),
                        gap("n18"),
                        text(" has to deal with loneliness."),
                    ]
                },
                {
                    "segments": [
                        text("Get involved in "),
                        gap("n19"),
                        text(" which interest you."),
                    ]
                },
                {
                    "segments": [
                        text("For more information, contact the town hall's "),
                        gap("n20"),
                        text("."),
                    ]
                },
            ],
        },
    ],
}

NOTES2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n13", ["first year"], 2),
    ("n14", ["(other) people", "other people", "people"], 2),
    ("n15", ["on their own", "their own"], 2),
    ("n16", ["primary school"], 2),
    ("n17", ["far (away)", "far away", "far"], 2),
    ("n18", ["everyone", "everybody"], 2),
    ("n19", ["activities"], 2),
    ("n20", ["support services"], 2),
]


# ── Section 3 — The Language Centre ──────────────────────────────────────────

# Q21-23: Choose THREE letters A-F
MULTI3_21_23: dict = {
    "question": "What does Katy say about the Language Centre?",
    "options": [
        "It is near the College.",
        "The library's materials are for advanced learners only.",
        "All books have accompanying cassettes.",
        "It receives a Spanish newspaper every day.",
        "At present, at least fifteen languages are taught by computer.",
        "All the computers can be used for Internet learning.",
    ],
    "correct": ["A", "E", "F"],
}

# Q24: Choose TWO letters A-E — 1 mark (both needed), so use note_completion
# with letter-pair variants (same technique as seed_practice_d_t1).
NOTES3_Q24_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The Language Centre (continued)",
    "instruction_words": "TWO LETTERS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": (
                "Which TWO of the following can you watch on the "
                "second floor?\n"
                "A live TV in English  B live TV in Japanese  "
                "C live TV in Turkish  D recorded news in Arabic  "
                "E recorded news in Portuguese"
            ),
            "items": [{"segments": [gap("q24")]}],
        },
    ],
}

NOTES3_Q24_ANSWERS: list[tuple[str, list[str], int]] = [
    ("q24", ["C, D", "D, C", "CD", "DC", "C/D", "D/C",
             "C and D", "D and C"], 2),
]

# Q25-27: Choose THREE letters A-F
MULTI3_25_27: dict = {
    "question": "What must you do when you join the Language Centre?",
    "options": [
        "pay a small amount of money",
        "show some proof of identity",
        "be accompanied by someone from your Department",
        "take a test in the language you want to study",
        "register at Reception in the Language Centre",
        "learn how to use the Centre's equipment",
    ],
    "correct": ["B", "E", "F"],
}

# Q28: Choose TWO letters A-E — 1 mark (both needed), note_completion
NOTES3_Q28_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The Language Centre (continued)",
    "instruction_words": "TWO LETTERS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": (
                "Which TWO should you tell the librarian?\n"
                "A whether you have studied the language previously  "
                "B why you want to study this language  "
                "C how many hours per week you must study it  "
                "D which text books you will use  "
                "E which other languages you have learned"
            ),
            "items": [{"segments": [gap("q28")]}],
        },
    ],
}

NOTES3_Q28_ANSWERS: list[tuple[str, list[str], int]] = [
    ("q28", ["A, B", "B, A", "AB", "BA", "A/B", "B/A",
             "A and B", "B and A"], 2),
]

# Q29-30: Choose TWO letters A-E
MULTI3_29_30: dict = {
    "question": (
        "Which TWO of these can you do at the Language Centre?"
    ),
    "options": [
        "read and listen to materials on your own",
        "choose books to take away from the Centre",
        "copy tapes to listen to them outside the Centre",
        "photocopy materials yourself",
        "have a few pages of a book photocopied",
    ],
    "correct": ["A", "E"],
}


# ── Section 4 — The zip fastener ─────────────────────────────────────────────

# Q31-34: Table completion
TABLE4_STRUCTURE: dict = {
    "variant": "table",
    "title": "The Zip Fastener",
    "instruction_words": "TWO WORDS OR A NUMBER",
    "max_words_per_gap": 2,
    "headers": ["Year", "Inventor", "Product name", "Status", "Country"],
    "rows": [
        [
            {"variant": "plain", "segments": [text("1851")]},
            {"variant": "plain", "segments": [text("Howe")]},
            {"variant": "plain", "segments": [text("\u2018Automatic Continuous Clothing Closure\u2019")]},
            {"variant": "plain", "segments": [text("potential only")]},
            {"variant": "plain", "segments": [text("USA")]},
        ],
        [
            {"variant": "plain", "segments": [text("1893")]},
            {"variant": "plain", "segments": [text("Judson")]},
            {"variant": "plain", "segments": [text("\u2018Clasp Locker\u2019")]},
            {"variant": "plain", "segments": [text("commercial failure")]},
            {"variant": "plain", "segments": [gap("t31")]},
        ],
        [
            {"variant": "plain", "segments": [text("1908")]},
            {"variant": "plain", "segments": [text("Sundback")]},
            {"variant": "plain", "segments": [text("\u2018Hookless Fastener\u2019")]},
            {"variant": "plain", "segments": [text("commercial "), gap("t32")]},
            {"variant": "plain", "segments": [text("Sweden")]},
        ],
        [
            {"variant": "plain", "segments": [gap("t33")]},
            {"variant": "plain", "segments": [text("Kynoch")]},
            {"variant": "plain", "segments": [text("\u2018Ready Fastener\u2019")]},
            {"variant": "plain", "segments": [text("commercial success")]},
            {"variant": "plain", "segments": [text("UK")]},
        ],
        [
            {"variant": "plain", "segments": [text("1920s")]},
            {"variant": "plain", "segments": [gap("t34")]},
            {"variant": "plain", "segments": [text("\u2018Zipper\u2019")]},
            {"variant": "plain", "segments": [text("commercial success")]},
            {"variant": "plain", "segments": [text("USA")]},
        ],
    ],
}

TABLE4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t31", ["(the) US", "the US", "US", "USA", "America"], 2),
    ("t32", ["success"], 2),
    ("t33", ["1919"], 2),
    ("t34", ["Goodrich's", "Goodrich", "BF Goodrich"], 2),
]

# Q35-39: Diagram labeling — parts of a separating zip
DIAGRAM4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The Separating Zip Fastener",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("35: "),
                        gap("d35"),
                    ]
                },
                {
                    "segments": [
                        text("36: "),
                        gap("d36"),
                    ]
                },
                {
                    "segments": [
                        text("37: "),
                        gap("d37"),
                    ]
                },
                {
                    "segments": [
                        text("38: "),
                        gap("d38"),
                    ]
                },
                {
                    "segments": [
                        text("39: "),
                        gap("d39"),
                    ]
                },
            ],
        },
    ],
}

DIAGRAM4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("d35", ["pin"], 3),
    ("d36", ["box"], 3),
    ("d37", ["(metal) teeth", "metal teeth", "teeth"], 3),
    ("d38", ["pull tab"], 3),
    ("d39", ["top stop"], 3),
]

MCQ4_ITEM: dict = {
    "question": "The speaker's overall aim is to",
    "options": [
        "explain how different kinds of zip fastener work.",
        "outline the development of the zip fastener.",
        "advertise a particular kind of zip fastener.",
        "warn of the dangers of zip fasteners.",
    ],
    "correct": "B",
}


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

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": item["question"], "options": item["options"]},
                {"correct": item["correct"]},
            )

    async def multi_select(
        self, instruction: str, item: dict,
    ) -> None:
        group = await self._group(QuestionType.MULTI_SELECT, instruction)
        self._add(
            group,
            QuestionType.MULTI_SELECT,
            {
                "choose_n": len(item["correct"]),
                "question": item["question"],
                "options": item["options"],
            },
            {"correct": item["correct"]},
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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    # -- Section 1: Renting flat 3A --
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(
        f"\nSection 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "How does the owner answer? Write\n"
        "A if she says YES, DEFINITELY\n"
        "B if she says MAYBE\n"
        "C if she says DEFINITELY NOT\n"
        f"{SCREEN_LETTER_HINT}",
        CLASSIFICATION1_OPTIONS,
        CLASSIFICATION1_ITEMS,
        options_heading="Classification",
    )
    await w.mcq(
        "Circle the correct letters A\u2013D.",
        MCQ1_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 2: Loneliness and counselling --
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(
        f"\nSection 2 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.mcq(
        "Choose the correct letters A\u2013C.",
        MCQ2_ITEMS,
    )
    await w.compound(
        QuestionType.SENTENCE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        NOTES2_STRUCTURE,
        NOTES2_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 3: The Language Centre --
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(
        f"\nSection 3 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.multi_select(
        "Choose THREE letters A\u2013F.",
        MULTI3_21_23,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Choose TWO letters A\u2013E.",
        NOTES3_Q24_STRUCTURE,
        NOTES3_Q24_ANSWERS,
    )
    await w.multi_select(
        "Choose THREE letters A\u2013F.",
        MULTI3_25_27,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Choose TWO letters A\u2013E.",
        NOTES3_Q28_STRUCTURE,
        NOTES3_Q28_ANSWERS,
    )
    await w.multi_select(
        "Choose TWO letters A\u2013E.",
        MULTI3_29_30,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 4: The zip fastener --
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(
        f"\nSection 4 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Look at the table.\n"
        "Write NO MORE THAN TWO WORDS OR A NUMBER for each answer.",
        TABLE4_STRUCTURE,
        TABLE4_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Label the zip.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        DIAGRAM4_STRUCTURE,
        DIAGRAM4_ANSWERS,
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        [MCQ4_ITEM],
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
