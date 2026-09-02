"""Seed Practice Set D Test 5 Listening, all four parts (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 5.
Keys from the printed Answer Key (pp.226-230). Tip strips omitted.

Part 1  Q1-6   short_answer          Group trip to Tidborough (TWO WORDS AND/OR A NUMBER)
        Q7-10  mcq                   Train ride MCQ A/B/C
Part 2  Q11-13 mcq                   Company sales/dept charts A/B/C
        Q14-19 note_completion       Company induction notes (TWO WORDS)
        Q20    note_completion        Choose TWO letters (single gap, B+E)
Part 3  Q21-24 matching_features     Penguin actions A-G
        Q25-27 short_answer          Penguin facts (TWO WORDS)
        Q28-30 summary_completion    Penguin summary (TWO WORDS)
Part 4  Q31-40 note_completion       Cities/housing sentences (TWO WORDS)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t5_listening.py
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
    AUDIO_URL,
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 5


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 — Group Trip to Tidborough ────────────────────────────────────────

P1_SHORT: list[tuple[str, list[str]]] = [
    (
        "How far is it from the youth hostel to the city centre?",
        ["2 km", "2km", "2 kilometres", "2 kilometers"],
    ),
    (
        "What is the website address of the hostel?",
        ["www.cheapstay.com"],
    ),
    (
        "What event is taking place on March 22nd?",
        ["street festival", "a street festival"],
    ),
    (
        "Who does the concert feature?",
        ["local musicians"],
    ),
    (
        "What exhibition starts on March 24th?",
        ["natural history"],
    ),
    (
        "What will be closed in March?",
        ["sports centre", "sports center", "the sports centre", "the sports center"],
    ),
]

MCQ1_ITEMS: list[dict] = [
    {
        "question": "When does the train ride depart?",
        "options": ["A. 9.00", "B. 9.15", "C. 9.30"],
        "correct": "C",
    },
    {
        "question": "Where is it recommended to buy tickets?",
        "options": [
            "A. at the tourist office",
            "B. at the station",
            "C. at the youth hostel",
        ],
        "correct": "A",
    },
    {
        "question": "How much is the group discount?",
        "options": ["A. 10%", "B. 15%", "C. 20%"],
        "correct": "B",
    },
    {
        "question": "How long does the excursion last?",
        "options": [
            "A. 3 hours",
            "B. 3\u00bd hours",
            "C. 4 hours",
        ],
        "correct": "C",
    },
]


# ── Part 2 — Company Induction ───────────────────────────────────────────────

MCQ2_ITEMS: list[dict] = [
    {
        "question": (
            "Which chart shows the company\u2019s sales figures for "
            "the last five years?"
        ),
        "options": [
            "A. Sales rise, level off for three years, then rise again",
            "B. Sales rise steadily throughout the five-year period",
            "C. Sales rise, level off for three years, then fall",
        ],
        "correct": "A",
    },
    {
        "question": (
            "Which chart shows how the three departments compare "
            "this year?"
        ),
        "options": [
            "A. Food sales are much higher than Clothing and Electrical",
            "B. Food, Clothing and Electrical are roughly equal",
            "C. Electrical sales are much higher than Food and Clothing",
        ],
        "correct": "B",
    },
    {
        "question": (
            "Which chart shows numbers of temporary staff in the "
            "company?"
        ),
        "options": [
            "A. Numbers decrease from last year to next year",
            "B. Numbers increase from last year to next year",
            "C. Numbers stay approximately the same each year",
        ],
        "correct": "B",
    },
]

NOTES2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Company Induction",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [
                    text("Company\u2019s mission statement: \u2018"),
                    gap("n14"),
                    text(" for customers\u2019"),
                ]},
                {"segments": [
                    text("In case of problems, always ask your "),
                    gap("n15"),
                    text(" for help"),
                ]},
                {"segments": [
                    text("Important for customers to have a "),
                    gap("n16"),
                    text(" experience"),
                ]},
                {"segments": [
                    text("Tell customers about "),
                    gap("n17"),
                    text(" goods"),
                ]},
                {"segments": [
                    text("Read the "),
                    gap("n18"),
                    text(" every month"),
                ]},
                {"segments": [
                    text("Must attend "),
                    gap("n19"),
                    text(" on Thursdays"),
                ]},
            ],
        },
    ],
}

NOTES2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n14", ["creating value"], 2),
    ("n15", ["line manager"], 2),
    ("n16", ["positive"], 2),
    ("n17", ["special offer"], 2),
    ("n18", ["newsletter"], 2),
    ("n19", ["progress meetings"], 2),
]

Q20_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Which TWO things must be done today?",
    "instruction_words": "TWO LETTERS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [gap("q20")]},
            ],
        },
    ],
}

Q20_ANSWERS: list[tuple[str, list[str], int]] = [
    ("q20", [
        "B, E", "E, B", "BE", "EB",
        "B/E", "E/B", "B and E", "E and B",
    ], 3),
]


# ── Part 3 — Penguins ────────────────────────────────────────────────────────

PENGUIN_OPTIONS = [
    "A. always hesitate before jumping",
    "B. avoid climbing if possible",
    "C. lean backwards when calling",
    "D. move around at night",
    "E. use its bill when climbing",
    "F. usually look twice at things",
    "G. walk with its flippers pointing downwards",
]

PENGUIN_ITEMS: list[tuple[str, str]] = [
    ("Gentoo", "A"),
    ("Rockhopper", "E"),
    ("Magellanic", "F"),
    ("King", "G"),
]

P3_SHORT: list[tuple[str, list[str]]] = [
    (
        "How do penguins usually sleep?",
        ["standing"],
    ),
    (
        "What do the yellow feathers of a Rockhopper penguin do?",
        ["stick out"],
    ),
    (
        "What feature helps to recognise Magellanic penguins?",
        ["white patches"],
    ),
]

SUMMARY3_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Penguins",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "paragraphs": [
        {"segments": [
            text(
                "Penguins prefer to swim in groups because it makes "
                "it easier to "
            ),
            gap("s28"),
            text(
                ". When they are on land, they appear to be "
            ),
            gap("s29"),
            text(
                ". The majority of species are characterised by "
                "their "
            ),
            gap("s30"),
            text(
                " which makes them particularly interesting for "
                "humans to study."
            ),
        ]},
    ],
}

SUMMARY3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s28", ["find food"], 2),
    ("s29", ["calm"], 2),
    ("s30", ["social nature"], 2),
]


# ── Part 4 — Cities and Housing ──────────────────────────────────────────────

SENTENCES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Cities and Housing",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [
                    text("Governments have been mistaken to "),
                    gap("s31"),
                    text(" slums."),
                ]},
                {"segments": [
                    text("There is often a lack of "),
                    gap("s32"),
                    text(" concerning housing projects."),
                ]},
                {"segments": [
                    text("Housing policies which are based on principles "
                         "of "),
                    gap("s33"),
                    text(" are particularly effective."),
                ]},
                {"segments": [
                    text("Some "),
                    gap("s34"),
                    text(" should always be provided by governments."),
                ]},
                {"segments": [
                    text("Migrants will only "),
                    gap("s35"),
                    text(" in housing if they feel secure."),
                ]},
                {"segments": [
                    text("Governments often underestimate the "
                         "importance of "),
                    gap("s36"),
                    text(" to housing projects."),
                ]},
                {"segments": [
                    text("The availability of "),
                    gap("s37"),
                    text(" is the starting point for successful "
                         "housing development."),
                ]},
                {"segments": [
                    text("Urbanisation can have a positive effect on "
                         "the "),
                    gap("s38"),
                    text(" of individuals."),
                ]},
                {"segments": [
                    text("The population size of cities enables a "
                         "range of "),
                    gap("s39"),
                    text(" to occur."),
                ]},
                {"segments": [
                    text("City living tends to raise the level of "),
                    gap("s40"),
                    text("."),
                ]},
            ],
        },
    ],
}

SENTENCES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s31", ["demolish"], 2),
    ("s32", ["real consultation"], 2),
    ("s33", ["self-help", "self help"], 2),
    ("s34", ["services"], 2),
    ("s35", ["invest money"], 2),
    ("s36", ["community values"], 2),
    ("s37", ["employment"], 2),
    ("s38", ["freedom"], 2),
    ("s39", ["specialist activities"], 2),
    ("s40", ["understanding"], 2),
]


# ── writer helper ─────────────────────────────────────────────────────────────

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

    async def mcq(
        self,
        instruction: str,
        items: list[dict],
    ) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {
                    "question": item["question"],
                    "options": item["options"],
                },
                {"correct": item["correct"]},
            )

    async def short_answer(
        self,
        instruction: str,
        items: list[tuple[str, list[str]]],
        *,
        max_words: int = 2,
    ) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for prompt, variants in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                {"prompt": prompt, "max_words": max_words},
                gap_answer_key(variants, max_words=max_words),
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    totals: list[int] = []

    # -- Part 1 --
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    part.audio_url = AUDIO_URL.format(test=TEST_NUMBER, part=1)
    print(
        f"\nPart 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.short_answer(
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each "
        "answer.",
        P1_SHORT,
        max_words=2,
    )
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        MCQ1_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 2 --
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    part.audio_url = AUDIO_URL.format(test=TEST_NUMBER, part=2)
    print(
        f"\nPart 2 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        MCQ2_ITEMS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        NOTES2_STRUCTURE,
        NOTES2_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Choose TWO letters A\u2013E.\n"
        "Which TWO things must be done today?\n"
        "A  complete form\n"
        "B  get security pass\n"
        "C  register for discount\n"
        "D  show certificates\n"
        "E  watch information video",
        Q20_STRUCTURE,
        Q20_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 3 --
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    part.audio_url = AUDIO_URL.format(test=TEST_NUMBER, part=3)
    print(
        f"\nPart 3 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Which action does each type of penguin do?\n"
        "Choose your answers A\u2013G from the box and write them "
        "next to questions 21\u201324.\n"
        f"{SCREEN_LETTER_HINT}",
        PENGUIN_OPTIONS,
        PENGUIN_ITEMS,
        options_heading="Action",
    )
    await w.short_answer(
        "Write NO MORE THAN TWO WORDS for each answer.",
        P3_SHORT,
        max_words=2,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        SUMMARY3_STRUCTURE,
        SUMMARY3_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 4 --
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    part.audio_url = AUDIO_URL.format(test=TEST_NUMBER, part=4)
    print(
        f"\nPart 4 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the sentences below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        SENTENCES4_STRUCTURE,
        SENTENCES4_ANSWERS,
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
