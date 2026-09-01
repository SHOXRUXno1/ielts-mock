"""Seed Practice Set D Test 1 Listening, all four parts (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 1.
Every key is taken from the printed Answer Key.

Part 1  Q1-4   note_completion       Easylet Accommodation Agency
        Q5-7   multi_select          free items (THREE of A-G)
        Q8-10  map_labeling          blocks of flats (A-H)
Part 2  Q11    multi_select          activities needing advance booking (TWO of A-E)
        Q12    multi_select          facilities closed in winter (TWO of A-E)
        Q13-17 table_completion      Hollylands exhibitions
        Q18-20 map_labeling          museum plan (A-F)
Part 3  Q21-25 mcq                   Kate and Martin
        Q26-30 matching_features     tasks — who does them A/B/C
Part 4  Q31-34 note_completion       Waste (one word)
        Q35-37 short_answer          factors for waste increase (two words)
        Q38-40 matching_features     waste disposal methods — countries A-F

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t1_listening.py
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
from seed_practice_d_common import (  # noqa: E402
    MAP_IMAGE_URL,
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 1
MAP_URL = MAP_IMAGE_URL.format(test=TEST_NUMBER)


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

NOTES1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Easylet Accommodation Agency",
    "instruction_words": "TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Cheapest properties: \u00a3 "),
                        gap("n1"),
                        text(" per week"),
                    ]
                },
                {
                    "segments": [
                        text("Minimum period of contract: "),
                        gap("n2"),
                    ]
                },
                {
                    "segments": [
                        text("Office open Saturdays until "),
                        gap("n3"),
                    ]
                },
                {
                    "segments": [
                        text("List of properties available on "),
                        gap("n4"),
                    ]
                },
            ],
        },
    ],
}

NOTES1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n1", ["90", "\u00a390"], 2),
    ("n2", ["6 months", "six months"], 2),
    ("n3", ["4 pm", "4pm", "4.00", "16:00", "4.00 pm"], 2),
    ("n4", ["internet", "the internet"], 2),
]

PART1_MULTI_5 = {
    "question": (
        "Which THREE things are included for free with every property?"
    ),
    "options": [
        "heating bills",
        "kitchen equipment",
        "plates and glasses",
        "sheets and towels",
        "telephone",
        "television",
        "water bill",
    ],
    "correct": ["B", "F", "G"],
}

MAP1_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H"]

MAP1_ITEMS: list[tuple[str, str]] = [
    ("Eastern Towers", "B"),
    ("Granby Mansions", "H"),
    ("Busby Garden", "E"),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────
# Q11 and Q12 each ask for TWO correct letters but count as 1 mark each in the
# Thomson paper (both letters must be correct for 1 mark). The platform's
# multi_select counts choose_n as separate slots, so we use note_completion
# with letter-pair variants instead (1 slot per gap).

NOTES2_CHOOSE: dict = {
    "variant": "notes",
    "title": "Hollylands Museum & Arts Centre",
    "instruction_words": "TWO LETTERS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": (
                "Which TWO activities for school groups need to be "
                "booked one week in advance?\n"
                "A drama workshops  B garden sculpture exhibition  "
                "C painting demonstrations  D tours for the blind  "
                "E video making"
            ),
            "items": [{"segments": [gap("b11")]}],
        },
        {
            "heading": (
                "Which TWO facilities are closed in winter?\n"
                "A adventure playground  B artists\u2019 studio  "
                "C caf\u00e9  D mini cinema  E shop"
            ),
            "items": [{"segments": [gap("b12")]}],
        },
    ],
}

NOTES2_CHOOSE_ANSWERS: list[tuple[str, list[str], int]] = [
    ("b11", ["A, C", "C, A", "AC", "CA", "A/C", "C/A",
             "A and C", "C and A"], 2),
    ("b12", ["B, D", "D, B", "BD", "DB", "B/D", "D/B",
             "B and D", "D and B"], 2),
]

TABLE2_STRUCTURE: dict = {
    "variant": "table",
    "title": "Hollylands Museum & Education Centre",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["Exhibition", "Starting date", "Points to remember"],
    "rows": [
        [
            cell(text("History in Pictures")),
            cell(gap("t13")),
            cell(text("opportunity to go on an old bus")),
        ],
        [
            cell(gap("t14")),
            cell(text("19th September")),
            cell(text("visitors can use "), gap("t15"), text(" service")),
        ],
        [
            cell(gap("t16")),
            cell(text("1st November")),
            cell(text("competition \u2014 prize: "), gap("t17"), text(" for 2 people")),
        ],
    ],
}

TABLE2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t13", ["28 August", "28th August", "28 August"], 3),
    ("t14", ["People at Work"], 3),
    ("t15", ["careers advice"], 2),
    ("t16", ["Land from Air"], 3),
    ("t17", ["balloon trip", "a balloon trip"], 2),
]

MAP2_OPTIONS_LIST = [
    "A. parking",
    "B. drinks machine",
    "C. first aid room",
    "D. manager\u2019s office",
    "E. telephones",
    "F. ticket office",
]

MAP2_ITEMS: list[tuple[str, str]] = [
    ("18", "B"),
    ("19", "E"),
    ("20", "C"),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_MCQ: list[dict] = [
    {
        "question": "Before giving her presentation, Kate was worried about",
        "options": [
            "being asked difficult questions.",
            "using the projection equipment.",
            "explaining statistical results.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "During many presentations by students, Martin feels that"
        ),
        "options": [
            "the discussion of research methods is not detailed enough.",
            "lecturers do not show enough interest in their students\u2019 work.",
            "the student does not make enough eye contact with the audience.",
        ],
        "correct": "C",
    },
    {
        "question": "What is Kate\u2019s opinion of the tutorials she attends?",
        "options": [
            "They involve too much preparation.",
            "They should be held more frequently.",
            "They do not have a clear focus.",
        ],
        "correct": "C",
    },
    {
        "question": "What does Martin intend to do next semester?",
        "options": [
            "make better use of the internet",
            "improve his note-taking",
            "prioritise reading lists",
        ],
        "correct": "A",
    },
    {
        "question": (
            "What problem do Kate and Martin both have when using "
            "the library?"
        ),
        "options": [
            "The opening hours are too short.",
            "There are too few desks to work at.",
            "The catalogue is difficult to use.",
        ],
        "correct": "A",
    },
]

TASK_OPTIONS = [
    "A. Martin",
    "B. Kate",
    "C. both Martin and Kate",
]

TASK_ITEMS: list[tuple[str, str]] = [
    ("compose questionnaire", "C"),
    ("select people to interview", "C"),
    ("conduct interviews", "B"),
    ("analyse statistics", "C"),
    ("prepare visuals for presentation", "A"),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Waste",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "History of waste",
            "items": [
                {
                    "segments": [
                        text("Stone Age rubbish dump found in "),
                        gap("n31"),
                    ]
                },
                {
                    "segments": [
                        text("In Medieval times, most common waste was "),
                        gap("n32"),
                    ]
                },
                {
                    "segments": [
                        text("Science linked "),
                        gap("n33"),
                        text(" with waste"),
                    ]
                },
                {
                    "segments": [
                        text("Biggest problem for the environment: "),
                        gap("n34"),
                    ]
                },
            ],
        },
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["Norway"], 1),
    ("n32", ["organic"], 1),
    ("n33", ["disease"], 1),
    ("n34", ["plastic", "plastics"], 1),
]

NOTES4B_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Increase in waste",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Three factors which led to the increase in waste",
            "items": [
                {"segments": [gap("n35")]},
                {"segments": [gap("n36")]},
                {"segments": [gap("n37")]},
            ],
        },
    ],
}

NOTES4B_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n35", ["mass manufacturing"], 2),
    ("n36", ["packaging"], 1),
    ("n37", ["disposable goods"], 2),
]

COUNTRY_OPTIONS = [
    "A. Denmark",
    "B. Germany",
    "C. Japan",
    "D. Switzerland",
    "E. UK",
    "F. USA",
]

COUNTRY_ITEMS: list[tuple[str, str]] = [
    ("incineration", "C"),
    ("landfill", "E"),
    ("recycling", "D"),
]


# ── writing helpers ──────────────────────────────────────────────────────────


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

    async def multi_select(self, instruction: str, item: dict) -> None:
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

    # -- Part 1 --
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(
        f"\nPart 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
        NOTES1_STRUCTURE,
        NOTES1_ANSWERS,
    )
    await w.multi_select(
        "Choose THREE letters, A\u2013G.",
        PART1_MULTI_5,
    )
    await w.map_labeling(
        "Label the map below.\n"
        "Write the correct letter, A\u2013H, next to questions 8\u201310.",
        MAP1_OPTIONS,
        MAP1_ITEMS,
        image_url=MAP_URL,
        subtitle="Where are the following blocks of flats situated?",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 2 --
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(
        f"\nPart 2 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "For each question, choose TWO letters, A\u2013E.",
        NOTES2_CHOOSE,
        NOTES2_CHOOSE_ANSWERS,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        TABLE2_STRUCTURE,
        TABLE2_ANSWERS,
    )
    await w.lettered(
        QuestionType.MAP_LABELING,
        "Label the plan below.\n"
        "Choose THREE answers from the box and write the correct letter, "
        "A\u2013F, next to questions 18\u201320.\n"
        f"{SCREEN_LETTER_HINT}",
        MAP2_OPTIONS_LIST,
        MAP2_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 3 --
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(
        f"\nPart 3 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        PART3_MCQ,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Who will do the following tasks?\n"
        "Write the correct letter, A, B or C, next to questions 26\u201330.\n"
        f"{SCREEN_LETTER_HINT}",
        TASK_OPTIONS,
        TASK_ITEMS,
        options_heading="Person",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 4 --
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(
        f"\nPart 4 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Answer the questions below.\n"
        "Write NO MORE THAN ONE WORD AND/OR A NUMBER for each answer.",
        NOTES4_STRUCTURE,
        NOTES4_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "List THREE factors which led to the increase in waste.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        NOTES4B_STRUCTURE,
        NOTES4B_ANSWERS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Which country uses the highest proportion of each method "
        "of waste disposal?\n"
        "Choose your answers from the box and write the correct letter, "
        "A\u2013F, next to questions 38\u201340.\n"
        f"{SCREEN_LETTER_HINT}",
        COUNTRY_OPTIONS,
        COUNTRY_ITEMS,
        options_heading="Country",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    total = sum(totals)
    if total != 40:
        raise SystemExit(
            f"expected 40 scoring slots across the four parts, got {total}"
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
