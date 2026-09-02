"""Seed Practice Set D Test 6 Listening, all four parts (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 6.
Keys from the printed Answer Key (pp.231-235). Tip strips omitted.

Part 1  Q1-7   form_completion       Go-Travel Booking Form (TWO WORDS AND/OR A NUMBER)
        Q8-10  multi_select          options woman wants to book (THREE of A-H)
Part 2  Q11-17 note_completion       Run-Well Charity (THREE WORDS AND/OR A NUMBER)
        Q18-20 multi_select          fundraising methods (THREE of A-I)
Part 3  Q21-26 matching_features     Joe's presentation topics A/B/C
        Q27-30 summary_completion    Brand names study (TWO WORDS)
Part 4  Q31-40 note_completion       Gas balloons / airships (TWO WORDS)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t6_listening.py
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

TEST_NUMBER = 6


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 — Travel Booking Form ─────────────────────────────────────────────

FORM1_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "GO-TRAVEL BOOKING FORM",
    "instruction_words": "TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "fields": [
        {"label": "Name", "type": "gap_line",
         "segments": [gap("n1")]},
        {"label": "Source of enquiry", "type": "gap_line",
         "segments": [text("saw ad in "), gap("n2"), text(" Magazine")]},
        {"label": "Holiday reference", "type": "gap_line",
         "segments": [gap("n3")]},
        {"label": "Number of people", "type": "gap_line",
         "segments": [gap("n4")]},
        {"label": "Preferred departure date", "type": "gap_line",
         "segments": [gap("n5")]},
        {"label": "Number of nights", "type": "gap_line",
         "segments": [gap("n6")]},
        {"label": "Type of insurance", "type": "gap_line",
         "segments": [gap("n7")]},
    ],
}

FORM1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n1", [
        "Grieves Anna", "Anna Grieves",
        "Grieves, Anna", "Grieves / Anna", "Grieves/Anna",
    ], 2),
    ("n2", ["Holiday World"], 2),
    ("n3", ["FT4551"], 2),
    ("n4", ["3", "three"], 2),
    ("n5", [
        "August 16", "16 August",
        "August 16th", "16th August", "16th of August",
    ], 2),
    ("n6", ["11", "eleven"], 2),
    ("n7", ["Super"], 2),
]

PART1_MULTI_8: dict = {
    "question": "Which THREE options does the woman want to book?",
    "options": [
        "arts demonstration",
        "dance show",
        "museums trip",
        "bus tour at night",
        "picnic lunches",
        "river trip",
        "room with balcony",
        "trip to mountains",
    ],
    "correct": ["G", "A", "F"],
}


# ── Part 2 — Run-Well Charity ────────────────────────────────────────────────

NOTES2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Run-Well Charity",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "Background",
            "items": [
                {"segments": [text("Set up in "), gap("n11")]},
                {"segments": [
                    text("Aim: raise money for the "), gap("n12"),
                ]},
            ],
        },
        {
            "heading": "Race details",
            "items": [
                {"segments": [
                    text("Teams to supply own "), gap("n13"),
                ]},
                {"segments": [
                    text("Teams should "), gap("n14"),
                    text(" together"),
                ]},
                {"segments": [
                    text("Important to bring enough "), gap("n15"),
                ]},
                {"segments": [
                    text("Race will finish in the "), gap("n16"),
                ]},
                {"segments": [
                    text("Prizes given by the "), gap("n17"),
                ]},
            ],
        },
    ],
}

NOTES2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n11", ["1992"], 3),
    ("n12", ["hospital"], 3),
    ("n13", ["numbers"], 3),
    ("n14", ["train"], 3),
    ("n15", ["food and drink"], 3),
    ("n16", ["main square"], 3),
    ("n17", ["minister for health", "Minister for Health"], 3),
]

PART2_MULTI_18: dict = {
    "question": (
        "Which THREE ways of raising money for the charity "
        "are recommended?"
    ),
    "options": [
        "badges",
        "bread and cake stall",
        "swimming event",
        "concert",
        "door-to-door collecting",
        "picnic",
        "postcards",
        "quiz",
        "second-hand sale",
    ],
    "correct": ["C", "A", "H"],
}


# ── Part 3 — Joe's Presentation ──────────────────────────────────────────────

PRESENTATION_OPTIONS = [
    "A. Joe will definitely include this topic",
    "B. Joe might include this topic",
    "C. Joe will not include this topic",
]

PRESENTATION_ITEMS: list[tuple[str, str]] = [
    ("cultural aspects of naming people", "A"),
    ("similarities across languages in naming practices", "B"),
    ("meanings of first names", "A"),
    ("place names describing geographic features", "C"),
    ("influence of immigration on place names", "B"),
    ("origins of names of countries", "A"),
]

SUMMARY3_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Brand Names Study",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "paragraphs": [
        {"segments": [
            text(
                "Researchers showed a group of students many "
                "common nouns, brand names and "
            ),
            gap("s27"),
            text(
                ". Students found it easier to identify brand "
                "names when they were shown in "
            ),
            gap("s28"),
            text(". Researchers think that "),
            gap("s29"),
            text(
                " is important in making brand names special "
                "within the brain. Brand names create a number "
                "of "
            ),
            gap("s30"),
            text(" within the brain."),
        ]},
    ],
}

SUMMARY3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s27", ["meaningless words"], 2),
    ("s28", ["capital letters"], 2),
    ("s29", ["colour", "color"], 2),
    ("s30", ["associations"], 2),
]


# ── Part 4 — Gas Balloons and Airships ───────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Gas Balloons and Airships",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Gas balloons \u2014 Uses",
            "items": [
                {"segments": [
                    text("instead of "), gap("s31"),
                    text(" in the US civil war"),
                ]},
                {"segments": [text("to make "), gap("s32")]},
                {"segments": [
                    text("to "), gap("s33"),
                    text(" for research"),
                ]},
                {"segments": [
                    text("as part of studies of "), gap("s34"),
                ]},
            ],
        },
        {
            "heading": "Hot air balloons",
            "items": [
                {"segments": [
                    text("Create less "), gap("s35"),
                    text(" than gas balloons"),
                ]},
            ],
        },
        {
            "heading": "Airships",
            "items": [
                {"segments": [
                    text("Early examples had no "), gap("s36"),
                    text(" for crew"),
                ]},
                {"segments": [
                    text("To be efficient, needed a safe "),
                    gap("s37"),
                ]},
                {"segments": [
                    text("Development stopped: success of "),
                    gap("s38"),
                ]},
                {"segments": [
                    text("Development stopped: series of "),
                    gap("s39"),
                ]},
                {"segments": [
                    text("Recent interest in use for carrying "),
                    gap("s40"),
                ]},
            ],
        },
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s31", ["spies"], 2),
    ("s32", ["maps"], 2),
    ("s33", ["collect data"], 2),
    ("s34", ["climate"], 2),
    ("s35", ["lift"], 2),
    ("s36", ["weather protection"], 2),
    ("s37", ["framework"], 2),
    ("s38", ["airliners"], 2),
    ("s39", ["crashes"], 2),
    ("s40", ["cargo"], 2),
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
    await w.compound(
        QuestionType.FORM_COMPLETION,
        "Complete the form below.\n"
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each "
        "answer.",
        FORM1_STRUCTURE,
        FORM1_ANSWERS,
    )
    await w.multi_select(
        "Choose THREE letters, A\u2013H.",
        PART1_MULTI_8,
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
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each "
        "answer.",
        NOTES2_STRUCTURE,
        NOTES2_ANSWERS,
    )
    await w.multi_select(
        "Choose THREE letters, A\u2013I.",
        PART2_MULTI_18,
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
        "What do the students decide about each topic for "
        "Joe\u2019s presentation?\n"
        "Write the correct letter, A, B or C next to questions "
        "21\u201326.\n"
        f"{SCREEN_LETTER_HINT}",
        PRESENTATION_OPTIONS,
        PRESENTATION_ITEMS,
        options_heading="Decision",
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
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        NOTES4_STRUCTURE,
        NOTES4_ANSWERS,
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
