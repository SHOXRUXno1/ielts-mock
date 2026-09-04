"""Seed Practice Set E Test 3 Listening, all four sections (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 3.
Every key is taken from the printed Explanatory Answer Key (pp.141-149).

Section 1  Q1-6   classification      What to bring (A-G)
           Q7-10  sentence_completion  Packing advice (THREE WORDS)
Section 2  Q11-13 multi_select         Sally on universities (THREE from A-F)
           Q14-19 table_completion     Disability facilities (THREE WORDS)
           Q20    mcq                  Speaker's main purpose (A-D)
Section 3  Q21-26 matching_features    Orientation Course activities (A-F)
           Q27-30 mcq                  Orientation details (A-D)
Section 4  Q31-33 sentence_completion  Fireworks history (TWO WORDS)
           Q34-37 note_completion      Firework mortar diagram (THREE WORDS)
           Q38-40 mcq                  Firework shells (A-C)

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t3_listening.py
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

TEST_NUMBER = 3


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Section 1 — What to bring (Lisa + Dan) ───────────────────────────────────

# Q1-6: Classification — What does Lisa say about each object?
# Paper only prints A/B/C (Essential / Recommended / Not Recommended).
CLASSIFICATION1_OPTIONS = [
    "A. Essential",
    "B. Recommended",
    "C. Not Recommended",
]

CLASSIFICATION1_ITEMS: list[tuple[str, str]] = [
    ("At least \u00a350 in cash", "B"),
    ("Warm clothing", "A"),
    ("Personal computer", "C"),
    ("Food from home", "C"),
    ("Favourite tapes or CDs", "B"),
    ("Photos from home", "B"),
]

# Q7-10: Sentence completion — THREE WORDS
SENTENCES1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Packing advice",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("The labels on Dan\u2019s luggage must state \u2018Mr & Mrs "),
                        gap("s7"),
                        text("\u2019 and their address."),
                    ]
                },
                {
                    "segments": [
                        text("Lisa says he should carry some spare clothes in "),
                        gap("s8"),
                        text("."),
                    ]
                },
                {
                    "segments": [
                        text("For health reasons, Dan intends to wear "),
                        gap("s9"),
                        text(" during the flight."),
                    ]
                },
                {
                    "segments": [
                        text("Dan should practise carrying his luggage for a minimum distance of "),
                        gap("s10"),
                        text("."),
                    ]
                },
            ],
        },
    ],
}

SENTENCES1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s7", ["Wark"], 3),
    ("s8", ["his hand luggage", "hand luggage"], 3),
    ("s9", ["tights", "(wear) tights"], 3),
    ("s10", ["500 metres", "500 meters", "five hundred metres"], 3),
]


# ── Section 2 — Disabled students at university ──────────────────────────────

# Q11-13: Choose THREE letters A-F
MULTI2_11_13: dict = {
    "question": "What does Sally say about universities?",
    "options": [
        "Compared to the general population, few students are disabled.",
        "Most universities don\u2019t want students aged over 25.",
        "Old universities can present particular difficulties for the disabled.",
        "All university buildings have to provide facilities for the disabled.",
        "There are very few university disability advisors.",
        "Some disability advisors can do little to help disabled students.",
    ],
    "correct": ["A", "C", "F"],
}

# Q14-19: Table completion — Disability Facilities (THREE WORDS)
TABLE2_STRUCTURE: dict = {
    "variant": "table",
    "title": "Disability Facilities",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "headers": ["Disability", "Facilities"],
    "rows": [
        [
            {"variant": "plain", "segments": [text("General")]},
            {"variant": "plain", "segments": [text("personal care and assistance")]},
        ],
        [
            {"variant": "plain", "segments": [text("Mobility impairment")]},
            {"variant": "plain", "segments": [
                text("ramps and easy access\nfire and emergency procedures\n"),
                gap("t14"),
                text("\nlavatory facilities"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [gap("t15")]},
            {"variant": "plain", "segments": [
                text("induction loops, flashing sirens, "),
                gap("t16"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [text("Sight impairment")]},
            {"variant": "plain", "segments": [
                gap("t17"),
                text(" on stairs, floors, etc\nfire and emergency procedures"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [text("Dyslexia")]},
            {"variant": "plain", "segments": [
                text("use of computer\n"),
                gap("t18"),
                text(" to finish work"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [text("Other difficulties")]},
            {"variant": "plain", "segments": [
                text("access to treatment: medication/therapy\n"),
                gap("t19"),
                text(" procedures"),
            ]},
        ],
    ],
}

TABLE2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t14", ["lifts that work"], 3),
    ("t15", ["hearing impairment"], 3),
    ("t16", ["visual doorbells"], 3),
    ("t17", ["clear markings"], 3),
    ("t18", ["extra time"], 3),
    ("t19", ["emergency"], 3),
]

# Q20: MCQ — speaker's main purpose
MCQ2_ITEM: list[dict] = [
    {
        "question": "What is the speaker\u2019s main purpose?",
        "options": [
            "to explain why comparatively few students are disabled",
            "to advise disabled students what to look for in a university",
            "to describe the facilities for the disabled in a particular university",
            "to criticize the facilities for the disabled in most universities",
        ],
        "correct": "B",
    },
]


# ── Section 3 — Orientation Course ───────────────────────────────────────────

# Q21-26: Matching activities A-F to what Liz liked / Mark would improve
ORIENTATION_OPTIONS = [
    "A. tour of the university campus",
    "B. formal dinner party",
    "C. meeting with \u2018senior\u2019 students",
    "D. driving in this country",
    "E. visit to a night club",
    "F. tour of the city",
]

ORIENTATION_ITEMS: list[tuple[str, str]] = [
    ("What Liz liked about the course (21)", "C"),
    ("What Liz liked about the course (22)", "B"),
    ("What Liz liked about the course (23)", "F"),
    ("What Mark thinks could be improved (24)", "E"),
    ("What Mark thinks could be improved (25)", "A"),
    ("What Mark thinks could be improved (26)", "D"),
]

# Q27-30: MCQ
MCQ3_ITEMS: list[dict] = [
    {
        "question": "Your room during the Orientation Course is",
        "options": [
            "usually shared with another student.",
            "the same room you will have for the rest of the year.",
            "some distance from the university.",
            "furnished, and with bedclothes provided.",
        ],
        "correct": "D",
    },
    {
        "question": "The daytime temperature will probably be",
        "options": [
            "less than 10\u00b0C.",
            "between 10\u00b0C and 20\u00b0C.",
            "20\u00b0C.",
            "more than 20\u00b0C.",
        ],
        "correct": "B",
    },
    {
        "question": "How much free email time do you get?",
        "options": [
            "30 minutes",
            "20 minutes",
            "15 minutes",
            "10 minutes",
        ],
        "correct": "B",
    },
    {
        "question": "There are Orientation Course activities from",
        "options": [
            "Sunday to Saturday.",
            "Sunday to Friday.",
            "Monday to Friday.",
            "Monday to Saturday.",
        ],
        "correct": "C",
    },
]


# ── Section 4 — Fireworks ────────────────────────────────────────────────────

# Q31-33: Sentence completion (TWO WORDS)
SENTENCES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Fireworks",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Fireworks were first used in China, probably in the "),
                        gap("s31"),
                        text(" century."),
                    ]
                },
                {
                    "segments": [
                        text("By the following century, they were known in Arabia as "),
                        gap("s32"),
                        text("."),
                    ]
                },
                {
                    "segments": [
                        text("Fireworks first appeared in "),
                        gap("s33"),
                        text(" in the thirteenth century."),
                    ]
                },
            ],
        },
    ],
}

SENTENCES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s31", ["sixth", "6th"], 2),
    ("s32", ["Chinese Arrows"], 2),
    ("s33", ["Europe"], 2),
]

# Q34-37: Diagram labeling — Firework Mortar (THREE WORDS)
DIAGRAM4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Firework Mortar",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("34 (sphere at top of mortar): "),
                        gap("d34"),
                    ]
                },
                {
                    "segments": [
                        text("35 width of mortar: "),
                        gap("d35"),
                    ]
                },
                {
                    "segments": [
                        text("36 length of mortar: "),
                        gap("d36"),
                    ]
                },
                {
                    "segments": [
                        text("37 (charge at bottom): "),
                        gap("d37"),
                        text(" charge"),
                    ]
                },
            ],
        },
    ],
}

DIAGRAM4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("d34", ["shell", "(the) shell"], 3),
    ("d35", ["75 mm", "75 millimetres", "75 millimeters",
             "seventy-five mm", "seventy-five millimetres"], 3),
    ("d36", ["500 mm", "500 millimetres", "500 millimeters",
             "five hundred mm", "five hundred millimetres"], 3),
    ("d37", ["lifting"], 3),
]

# Q38-40: MCQ
MCQ4_ITEMS: list[dict] = [
    {
        "question": "A multibreak shell",
        "options": [
            "is more dangerous than a simple shell.",
            "may make a noise when it bursts.",
            "has a single fuse for all its sections.",
        ],
        "correct": "B",
    },
    {
        "question": "An aerial heart shape is made by the explosion of",
        "options": [
            "stars placed inside a shell in the form of a circle.",
            "heart-shaped stars placed inside a shell.",
            "stars arranged in the form of a heart inside a shell.",
        ],
        "correct": "C",
    },
    {
        "question": (
            "What does a Serpentine shell look like in the sky?"
        ),
        "options": [
            "Symmetrical ring of coloured lights.",
            "Small tubes scattering outwards in random paths, "
            "possibly culminating in exploding stars.",
            "Charges travelling outwards, exploding and curving "
            "downwards like the limbs of a palm tree.",
        ],
        "correct": "B",
    },
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

    # -- Section 1: What to bring --
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(
        f"\nSection 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What does Lisa say about each object? Write\n"
        "A if she says it is ESSENTIAL\n"
        "B if she says it is RECOMMENDED\n"
        "C if she says it is NOT RECOMMENDED\n"
        f"{SCREEN_LETTER_HINT}",
        CLASSIFICATION1_OPTIONS,
        CLASSIFICATION1_ITEMS,
        options_heading="Recommendation",
    )
    await w.compound(
        QuestionType.SENTENCE_COMPLETION,
        "Complete the sentences below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        SENTENCES1_STRUCTURE,
        SENTENCES1_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 2: Disabled students at university --
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(
        f"\nSection 2 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.multi_select(
        "Choose THREE letters A\u2013F.",
        MULTI2_11_13,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        TABLE2_STRUCTURE,
        TABLE2_ANSWERS,
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        MCQ2_ITEM,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 3: Orientation Course --
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(
        f"\nSection 3 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete the notes below using letters A\u2013F from the box.\n"
        "NB You may use any letter more than once.\n"
        f"{SCREEN_LETTER_HINT}",
        ORIENTATION_OPTIONS,
        ORIENTATION_ITEMS,
        options_heading="Activities",
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        MCQ3_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Section 4: Fireworks --
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(
        f"\nSection 4 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.SENTENCE_COMPLETION,
        "Complete the sentences below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        SENTENCES4_STRUCTURE,
        SENTENCES4_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Label the diagram.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        DIAGRAM4_STRUCTURE,
        DIAGRAM4_ANSWERS,
    )
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        MCQ4_ITEMS,
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
