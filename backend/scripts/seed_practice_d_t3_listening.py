"""Seed Practice Set D Test 3 Listening, all four parts (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 3.
Keys from the printed Answer Key (pp.218-220). Tip strips omitted.

Part 1  Q1-10  short_answer          Cycling club (THREE WORDS AND/OR A NUMBER)
Part 2  Q11-20 table_completion      Park Arts Centre timetable
Part 3  Q21-25 matching_features     dissertation opinions A-I
        Q26-30 flow_chart_completion Ben's programme
Part 4  Q31-40 note_completion       Cinématographe sentences (TWO WORDS)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t3_listening.py
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


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 — Cycling club ────────────────────────────────────────────────────

PART1_ITEMS: list[dict] = [
    {
        "question": "How many members does the cycling club have currently?",
        "correct": ["76"],
        "max_words": 3,
    },
    {
        "question": "How much does Youth Membership cost?",
        "correct": [
            "£30 per year",
            "30 per year",
            "£30 a year",
            "30 a year",
            "£30/year",
        ],
        "max_words": 3,
    },
    {
        "question": (
            "From whom must you get a signature when applying to join?"
        ),
        "correct": ["teacher or parent", "parent or teacher"],
        "max_words": 3,
    },
    {
        "question": "How long does it take to process a membership application?",
        "correct": ["3 weeks", "three weeks"],
        "max_words": 3,
    },
    {
        "question": "How often do family rides take place?",
        "correct": ["every month"],
        "max_words": 3,
    },
    {
        "question": "How long are the Saturday rides usually?",
        "correct": ["60 km", "60km"],
        "max_words": 3,
    },
    {
        "question": "What must you get for your bike?",
        "correct": [
            "a safety certificate",
            "safety certificate",
            "(a) safety certificate",
        ],
        "max_words": 3,
    },
    {
        "question": "When is the next camping tour?",
        "correct": [
            "July 14",
            "14 July",
            "July 14th",
            "14th July",
            "on July 14",
            "(on) July 14",
        ],
        "max_words": 3,
    },
    {
        "question": "What is happening on May 5th?",
        "correct": ["a picnic", "picnic", "(a) picnic"],
        "max_words": 3,
    },
    {
        "question": (
            "How much discount do members get at Wheels Bike Shop?"
        ),
        "correct": ["15%", "15 per cent", "15 percent"],
        "max_words": 3,
    },
]


# ── Part 2 — Park Arts Centre timetable ──────────────────────────────────────

TABLE2_STRUCTURE: dict = {
    "variant": "table",
    "title": "PARK ARTS CENTRE",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["DATES", "Times", "Event", "NOTES"],
    "rows": [
        [
            cell(text("18\u201324 Feb")),
            cell(gap("t11"), text(" and "), gap("t11b")),
            cell(text("Folk music concert")),
            cell(text("Can get a "), gap("t12"), text(" in shop")),
        ],
        [
            cell(text("1\u20138 March")),
            cell(text("See the "), gap("t13")),
            cell(text("Annual "), gap("t14")),
            cell(text("Groups from "), gap("t15")),
        ],
        [
            cell(gap("t16")),
            cell(text("8 pm")),
            cell(text("Film: "), gap("t17")),
            cell(text("Talk by the "), gap("t18")),
        ],
        [
            cell(text("2 April")),
            cell(text("To be confirmed")),
            cell(gap("t19")),
            cell(text("It will be "), gap("t20")),
        ],
    ],
}

# Q11 is one mark needing both times — store both gaps with same acceptable
# pair scoring via note_completion-style: use ONE gap for both times instead.
TABLE2_STRUCTURE_FLAT: dict = {
    "variant": "table",
    "title": "PARK ARTS CENTRE",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["DATES", "Times", "Event", "NOTES"],
    "rows": [
        [
            cell(text("18\u201324 Feb")),
            cell(gap("t11")),
            cell(text("Folk music concert")),
            cell(text("Can get a "), gap("t12"), text(" in shop")),
        ],
        [
            cell(text("1\u20138 March")),
            cell(text("See the "), gap("t13")),
            cell(text("Annual "), gap("t14")),
            cell(text("Groups from "), gap("t15")),
        ],
        [
            cell(gap("t16")),
            cell(text("8 pm")),
            cell(text("Film: "), gap("t17")),
            cell(text("Talk by the "), gap("t18")),
        ],
        [
            cell(text("2 April")),
            cell(text("To be confirmed")),
            cell(gap("t19")),
            cell(text("It will be "), gap("t20")),
        ],
    ],
}

TABLE2_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "t11",
        [
            "2.30/7.30 pm",
            "2.30 and 7.30 pm",
            "2.30 & 7.30 pm",
            "7.30/2.30 pm",
            "7.30 and 2.30 pm",
            "2.30pm/7.30pm",
            "2.30 pm and 7.30 pm",
        ],
        3,
    ),
    ("t12", ["CD"], 3),
    ("t13", ["separate programme"], 3),
    ("t14", ["dance festival"], 3),
    ("t15", ["continents", "4 continents"], 3),
    (
        "t16",
        [
            "14-20 March",
            "14\u201320 March",
            "14 to 20 March",
            "14–20 March",
        ],
        3,
    ),
    ("t17", ["Love and Hope"], 3),
    ("t18", ["producer"], 3),
    (
        "t19",
        ["singing competition", "a singing competition"],
        3,
    ),
    ("t20", ["shown on TV", "shown on television"], 3),
]


# ── Part 3 — Dissertations + Ben's programme ─────────────────────────────────

DISSERTATION_OPTIONS = [
    "A. It has an inadequate index",
    "B. It contains unusual illustrations",
    "C. It is too detailed in places",
    "D. It presents clear arguments",
    "E. It contains diagrams which are not clear",
    "F. It omits important historical facts",
    "G. It is poorly translated",
    "H. It contains useful background information",
    "I. It is not suitable for new students",
]

DISSERTATION_ITEMS: list[tuple[str, str]] = [
    ("Twentieth Century Architecture", "B"),
    ("Modern Construction", "I"),
    ("Steel, Glass and Concrete", "D"),
    ("The Space We Make", "F"),
    ("Change and Tradition", "A"),
]

FLOW3_STRUCTURE: dict = {
    "variant": "flow",
    "title": "BEN\u2019S PROGRAMME",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "steps": [
        {
            "segments": [
                text("Look at drawings of "),
                gap("f26"),
            ]
        },
        {
            "segments": [
                text("Get images of "),
                gap("f27"),
                text(" from internet"),
            ]
        },
        {
            "segments": [
                text("Find books that include "),
                gap("f28"),
                text(" of the period"),
            ]
        },
        {
            "segments": [
                text("Show "),
                gap("f29"),
                text(" to Dr Forbes"),
            ]
        },
        {
            "segments": [
                text("Ask Dr Gray for more "),
                gap("f30"),
            ]
        },
    ],
}

FLOW3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("f26", ["large private houses"], 3),
    ("f27", ["window designs"], 3),
    ("f28", ["typical furniture"], 3),
    ("f29", ["outline plan", "an outline plan"], 3),
    ("f30", ["references"], 3),
]


# ── Part 4 — Cinématographe ──────────────────────────────────────────────────

SENTENCES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text(
                            "Rival cameras were claimed to "
                        ),
                        gap("s31"),
                        text(" less than the Cinématographe."),
                    ]
                },
                {
                    "segments": [
                        text(
                            "In Russia, on one occasion, the "
                            "Cinématographe was suspected of being a "
                        ),
                        gap("s32"),
                        text("."),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Early filming in Russia led to the "
                            "creation of a new approach to "
                        ),
                        gap("s33"),
                        text("."),
                    ]
                },
                {
                    "segments": [
                        text(
                            "One problem for historians is not knowing "
                            "whether early equipment "
                        ),
                        gap("s34"),
                        text(" as it was claimed."),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Marey encountered difficulties achieving "
                            "the "
                        ),
                        gap("s35"),
                        text(
                            " of strips of photographic paper."
                        ),
                    ]
                },
                {
                    "segments": [
                        text("The "),
                        gap("s36"),
                        text(
                            " of the comic strip influenced the way "
                            "films were planned."
                        ),
                    ]
                },
                {
                    "segments": [
                        text("Documentaries used "),
                        gap("s37"),
                        text(
                            " shots before fiction films did."
                        ),
                    ]
                },
                {
                    "segments": [
                        text("The popularity of "),
                        gap("s38"),
                        text(
                            " films led to increased numbers of shots."
                        ),
                    ]
                },
                {
                    "segments": [
                        text("When filming "),
                        gap("s39"),
                        text(
                            ", the screen might be divided."
                        ),
                    ]
                },
                {
                    "segments": [
                        text(
                            "As films became more complex, "
                        ),
                        gap("s40"),
                        text(
                            " became an important part of "
                            "film-making."
                        ),
                    ]
                },
            ],
        },
    ],
}

SENTENCES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s31", ["shake"], 2),
    ("s32", ["bomb"], 2),
    ("s33", ["journalism"], 2),
    ("s34", ["functioned"], 2),
    ("s35", ["regular movement"], 2),
    ("s36", ["structure"], 2),
    ("s37", ["travelling", "traveling"], 2),
    ("s38", ["chase"], 2),
    ("s39", ["telephone conversations"], 2),
    ("s40", ["editing"], 2),
]


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
    ) -> Question:
        question = Question(
            id=uuid.uuid4(),
            section_id=self.section.id,
            question_group_id=group.id,
            order=self.order,
            question_type=question_type,
            content=content,
            answer_key=answer_key,
        )
        self.db.add(question)
        self.order += 1
        self.slots += scoring_slots_for_question(question)
        return question

    async def short_answer(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                {"prompt": item["question"], "max_words": item["max_words"]},
                {
                    "correct": item["correct"],
                    "max_words": item["max_words"],
                    "case_sensitive": False,
                },
            )

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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    totals: list[int] = []

    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(
        f"\nPart 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.short_answer(
        "Answer the questions below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        PART1_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(
        f"\nPart 2 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the timetable below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        TABLE2_STRUCTURE_FLAT,
        TABLE2_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(
        f"\nPart 3 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What opinion is expressed about each dissertation?\n"
        "Choose your answers from the box and write the letters A\u2013I "
        "next to questions 21\u201325.\n"
        f"{SCREEN_LETTER_HINT}",
        DISSERTATION_OPTIONS,
        DISSERTATION_ITEMS,
        options_heading="Opinions",
    )
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        FLOW3_STRUCTURE,
        FLOW3_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 4)
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
