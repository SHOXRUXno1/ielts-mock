"""Seed Practice Set D Test 4 Listening, all four parts (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 4.
Keys from the printed Answer Key (pp.225-227). Tip strips omitted.

Part 1  Q1-10  form_completion       Able Employment Agency (THREE WORDS AND/OR A NUMBER)
Part 2  Q11-16 sentence/note_comp    Hotel & activities (TWO WORDS)
        Q17-20 map_labeling          Town map A-I
Part 3  Q21-26 matching_features     Forth/Haines colleges A/B/C
        Q27-30 mcq                   David & Dr Smith
Part 4  Q31-37 table_completion      Types of writing (TWO WORDS)
        Q38-40 mcq                   Novel-writing advice

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t4_listening.py
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

TEST_NUMBER = 4


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 — Able Employment Agency ──────────────────────────────────────────

FORM1_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "ABLE EMPLOYMENT AGENCY — APPLICATION FORM",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "fields": [
        {"label": "Full name", "type": "gap_line",
         "segments": [gap("n1")]},
        {"label": "Address", "type": "gap_line",
         "segments": [gap("n2"), text(", Melford MF4 5UB")]},
        {"label": "Contact number", "type": "gap_line",
         "segments": [gap("n3")]},
        {"label": "Qualifications", "type": "gap_line",
         "segments": [
             text("(a) A levels  (b) "),
             gap("n4"),
             text("  (c) "),
             gap("n5"),
         ]},
        {"label": "Previous experience", "type": "gap_line",
         "segments": [
             text("(a) general work in a "),
             gap("n6"),
             text(" (3 months)  (b) part-time job as a "),
             gap("n7"),
         ]},
        {"label": "Interests", "type": "gap_line",
         "segments": [
             text("(a) member of a "),
             gap("n8"),
             text("  (b) enjoys "),
             gap("n9"),
         ]},
        {"label": "Date available", "type": "gap_line",
         "segments": [gap("n10")]},
    ],
}

FORM1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n1", ["James Bowen"], 3),
    ("n2", ["4 Lion Road", "4 Lion Rd"], 3),
    ("n3", [
        "09954 721 822",
        "09954721822",
        "09954 721822",
    ], 3),
    ("n4", ["history diploma"], 3),
    ("n5", ["computer skills certificate"], 3),
    ("n6", ["hospital"], 3),
    ("n7", ["tour guide", "a tour guide"], 3),
    ("n8", ["swimming club", "a swimming club"], 3),
    ("n9", ["playing piano", "playing the piano"], 3),
    ("n10", [
        "June 28",
        "28 June",
        "June 28th",
        "28th June",
        "28th of June",
    ], 3),
]


# ── Part 2 — Hotel & activities + map ────────────────────────────────────────

NOTES2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "The hotel",
            "items": [
                {"segments": [
                    text("You must book "),
                    gap("s11"),
                    text(" in advance."),
                ]},
                {"segments": [
                    text("There are some interesting "),
                    gap("s12"),
                    text(" in the lounge."),
                ]},
            ],
        },
        {
            "heading": "Activities",
            "items": [
                {"segments": [
                    text("The visit to the "),
                    gap("s13"),
                    text(" has been cancelled."),
                ]},
                {"segments": [
                    text("There will be a talk about "),
                    gap("s14"),
                    text(" from the area on Saturday."),
                ]},
                {"segments": [
                    text("The visit to the "),
                    gap("s15"),
                    text(" will take place on Sunday."),
                ]},
                {"segments": [
                    text("There is a collection of "),
                    gap("s16"),
                    text(" in the art gallery."),
                ]},
            ],
        },
    ],
}

NOTES2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s11", ["breakfast"], 2),
    ("s12", ["paintings"], 2),
    ("s13", ["castle"], 2),
    ("s14", ["famous people"], 2),
    ("s15", ["antiques show"], 2),
    ("s16", ["old postcards"], 2),
]

MAP2_LABELS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

MAP2_ITEMS: list[tuple[str, str]] = [
    ("Park Hotel", "E"),
    ("Internet Cafe", "F"),
    ("Tourist Information Office", "A"),
    ("Royal House Restaurant", "D"),
]


# ── Part 3 — College choice (Forth / Haines) ─────────────────────────────────

COLLEGE_OPTIONS = [
    "A. Forth College",
    "B. Haines College",
    "C. Both Forth and Haines Colleges",
]

COLLEGE_ITEMS: list[tuple[str, str]] = [
    ("student support services", "A"),
    ("residential accommodation", "C"),
    ("on-line resources", "A"),
    ("libraries", "B"),
    ("teaching staff", "B"),
    ("research record", "B"),
]

MCQ3_ITEMS: list[dict] = [
    {
        "question": "David is concerned that he may feel",
        "options": ["A. unmotivated", "B. isolated", "C. competitive"],
        "correct": "B",
    },
    {
        "question": "In the future, Dr Smith thinks David should aim to",
        "options": [
            "A. do further research",
            "B. publish articles",
            "C. get teaching work",
        ],
        "correct": "B",
    },
    {
        "question": (
            "What does Dr Smith think has improved masters\u2019 study "
            "in recent years?"
        ),
        "options": [
            "A. the development of the internet",
            "B. the growth of flexible courses",
            "C. the introduction of changes in assessment",
        ],
        "correct": "B",
    },
    {
        "question": "David would like to improve the way he",
        "options": [
            "A. takes notes in lectures",
            "B. writes up assignments",
            "C. manages his time",
        ],
        "correct": "C",
    },
]


# ── Part 4 — Types of writing ────────────────────────────────────────────────

TABLE4_STRUCTURE: dict = {
    "variant": "table",
    "title": "Types of Writing",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "headers": ["Type of writing", "Notes / Tips"],
    "rows": [
        [
            cell(text("Short stories")),
            cell(text("start with a "), gap("t31")),
        ],
        [
            cell(text("Non-fiction biographies")),
            cell(
                text("tell publishers about your "),
                gap("t32"),
            ),
        ],
        [
            cell(text("Articles")),
            cell(text("write for a "), gap("t33")),
        ],
        [
            cell(text("Poetry")),
            cell(
                text("meaning shouldn\u2019t be too "),
                gap("t34"),
            ),
        ],
        [
            cell(text("Plays")),
            cell(
                text("movements usually decided by the "),
                gap("t35"),
            ),
        ],
        [
            cell(text("Radio")),
            cell(gap("t36"), text(" first")),
        ],
        [
            cell(text("Children\u2019s literature")),
            cell(text("decide on an "), gap("t37")),
        ],
    ],
}

TABLE4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t31", ["crisis"], 2),
    ("t32", ["specialist knowledge"], 2),
    ("t33", ["definite market"], 2),
    ("t34", ["obvious"], 2),
    ("t35", ["director"], 2),
    ("t36", ["regional stations"], 2),
    ("t37", ["age group"], 2),
]

MCQ4_ITEMS: list[dict] = [
    {
        "question": (
            "What is a disadvantage of first person narration in novels?"
        ),
        "options": [
            "A. It makes it harder for the main character to be interesting.",
            "B. It is difficult for beginners to do well.",
            "C. It limits what can be described.",
        ],
        "correct": "C",
    },
    {
        "question": "What is a mistake when writing novels?",
        "options": [
            "A. failing to include enough detail",
            "B. trying to explain ironic effects",
            "C. including too many characters",
        ],
        "correct": "B",
    },
    {
        "question": (
            "In order to make dialogue seem natural, writers should"
        ),
        "options": [
            "A. make recordings of real conversations",
            "B. include unfinished sentences",
            "C. break up long speeches",
        ],
        "correct": "C",
    },
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
        QuestionType.FORM_COMPLETION,
        "Complete the form below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        FORM1_STRUCTURE,
        FORM1_ANSWERS,
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
        "Complete the sentences below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        NOTES2_STRUCTURE,
        NOTES2_ANSWERS,
    )
    map_structure: dict = {
        "options": MAP2_LABELS,
        "image_url": MAP_IMAGE_URL.format(test=TEST_NUMBER),
    }
    await w.lettered(
        QuestionType.MAP_LABELING,
        "Label the map below.\n"
        "Write the correct letter A\u2013I next to questions 17\u201320.\n"
        f"{SCREEN_LETTER_HINT}",
        MAP2_LABELS,
        MAP2_ITEMS,
        options_heading="Location",
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
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "At which college are the following features recommended?\n"
        "Write the correct letter, A, B or C next to questions "
        "21\u201326.\n"
        f"{SCREEN_LETTER_HINT}",
        COLLEGE_OPTIONS,
        COLLEGE_ITEMS,
        options_heading="College",
    )
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        MCQ3_ITEMS,
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
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        TABLE4_STRUCTURE,
        TABLE4_ANSWERS,
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
