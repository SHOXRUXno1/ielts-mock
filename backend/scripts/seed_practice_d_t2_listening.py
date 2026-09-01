"""Seed Practice Set D Test 2 Listening, all four parts (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 2.
Every key is taken from the printed Answer Key (pp.212-214).

Part 1  Q1-10  form_completion       Complaint Record Form (TWO WORDS AND/OR A NUMBER)
Part 2  Q11-15 matching_features     Temporary Hotel Jobs (A-H)
        Q16-20 flow_chart_completion Recruitment Process (TWO WORDS)
Part 3  Q21-26 note_completion       David, Jane and Dr Wilson sentences (THREE WORDS)
        Q27-30 matching_features     Cambridge field-trip timetable (A-H)
Part 4  Q31-35 summary_completion    The London Eye (TWO WORDS)
        Q36-40 diagram_labeling      London Eye construction diagram (TWO WORDS)

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t2_listening.py
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

TEST_NUMBER = 2
DIAGRAM_URL = f"/media/images/practice_d_t{TEST_NUMBER}_listening_diagram.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 — Complaint Record Form ──────────────────────────────────────────

FORM1_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "Complaint Record Form",
    "instruction_words": "TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "fields": [
        {"label": "Holiday booked in name of", "type": "gap_line",
         "segments": [gap("n1")]},
        {"label": "Address", "type": "gap_line",
         "segments": [text("Flat 4, "), gap("n2"), text(", Winchester SO2 4ER")]},
        {"label": "Daytime telephone number", "type": "gap_line",
         "segments": [gap("n3")]},
        {"label": "Booking reference", "type": "gap_line",
         "segments": [gap("n4")]},
        {"label": "Booked through", "type": "gap_line",
         "segments": [gap("n5"), text(" company")]},
        {"label": "Insurance", "type": "gap_line",
         "segments": [gap("n6"), text(" Policy")]},
        {"label": "Type of holiday booked", "type": "gap_line",
         "segments": [gap("n7"), text(" Break")]},
        {"label": "Date holiday commenced", "type": "gap_line",
         "segments": [gap("n8")]},
        {"label": "Details of complaint (1)", "type": "gap_line",
         "segments": [text("no "), gap("n9"), text(" at station")]},
        {"label": "Details of complaint (2)", "type": "gap_line",
         "segments": [gap("n10"), text(" was missing")]},
    ],
}

FORM1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n1", ["Andrew Sharpe"], 2),
    ("n2", ["Beaconsfield House"], 2),
    ("n3", ["0374 55793"], 2),
    ("n4", ["MH66G4"], 2),
    ("n5", ["credit card"], 2),
    ("n6", ["Gold Star"], 2),
    ("n7", ["Mid-winter", "mid-winter", "Midwinter", "midwinter"], 2),
    ("n8", ["16 January", "16th January", "January 16"], 2),
    ("n9", ["taxi"], 2),
    ("n10", ["bicycle"], 2),
]


# ── Part 2 — Temporary Hotel Jobs (Q11-15) ──────────────────────────────────

JOB_OPTIONS = [
    "A. driving licence",
    "B. flexible working week",
    "C. free meals",
    "D. heavy lifting",
    "E. late shifts",
    "F. training certificate",
    "G. travel allowance",
    "H. website maintenance",
]

JOB_ITEMS: list[tuple[str, str]] = [
    ("Reception Assistant, Park Hotel — note 1", "D"),
    ("Reception Assistant, Park Hotel — note 2", "A"),
    ("General Assistant, Avenue Hotel — note 1", "C"),
    ("General Assistant, Avenue Hotel — note 2", "F"),
    ("Catering Assistant, Hotel 56", "E"),
]


# ── Part 2 — Recruitment Process (Q16-20) ───────────────────────────────────

FLOW2_STRUCTURE: dict = {
    "variant": "flow",
    "title": "Recruitment Process",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "steps": [
        {"segments": [text("Step 1: Complete a "), gap("f16"), text(" form")]},
        {"segments": [text("Step 2: Do a "), gap("f17"), text(" questionnaire")]},
        {"segments": [
            text("Step 3: If accepted, go on a "),
            gap("f18"),
            text(" course — includes "),
            gap("f19"),
            text(" activities"),
        ]},
        {"segments": [
            text("Step 4: Will be sent a "),
            gap("f20"),
            text(" about the hotel"),
        ]},
    ],
}

FLOW2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("f16", ["personal information"], 2),
    ("f17", ["skills"], 2),
    ("f18", ["general"], 2),
    ("f19", ["role-play", "role play", "roleplay"], 2),
    ("f20", ["video"], 2),
]


# ── Part 3 — Sentences (Q21-26) ─────────────────────────────────────────────

SENTENCES3_STRUCTURE: dict = {
    "variant": "notes",
    "title": "",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [
                    text("David feels that progress on the project has been "
                         "slow because other members of the group are not "),
                    gap("s21"),
                ]},
                {"segments": [
                    text("Jane thinks that "),
                    gap("s22"),
                    text(" were not clearly established."),
                ]},
                {"segments": [
                    text("Dr Wilson suggests that the group use the "),
                    gap("s23"),
                    text(" available from the Resource Centre."),
                ]},
                {"segments": [
                    text("David doubts that the research will include "
                         "an adequate "),
                    gap("s24"),
                ]},
                {"segments": [
                    text("According to Dr Wilson, the "),
                    gap("s25"),
                    text(" is now the most important thing to focus on."),
                ]},
                {"segments": [
                    text("Jane believes the group could make more use "
                         "of some "),
                    gap("s26"),
                ]},
            ],
        },
    ],
}

SENTENCES3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s21", ["following the plan"], 3),
    ("s22", ["individual responsibilities"], 3),
    ("s23", ["advice service"], 3),
    ("s24", ["reference section"], 3),
    ("s25", ["methodology"], 3),
    ("s26", ["websites"], 3),
]


# ── Part 3 — Cambridge timetable (Q27-30) ───────────────────────────────────

TIMETABLE_OPTIONS = [
    "A. Compare photographs at newspaper offices",
    "B. Interview a local historian",
    "C. Listen to tapes in the City Library",
    "D. Study records of shop ownership",
    "E. Take photographs of the castle area",
    "F. Talk to the archivist at the City Library",
    "G. Tour city centre using copies of old maps",
    "H. Visit an exhibition at the University Library",
]

TIMETABLE_ITEMS: list[tuple[str, str]] = [
    ("Monday afternoon", "H"),
    ("Tuesday morning", "B"),
    ("Wednesday morning", "G"),
    ("Wednesday afternoon", "E"),
]


# ── Part 4 — London Eye summary (Q31-35) ────────────────────────────────────

SUMMARY4_STRUCTURE: dict = {
    "variant": "summary",
    "title": "The London Eye",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "paragraphs": [
        {"segments": [
            text("The architects who designed the London Eye originally "
                 "drew it for a "),
            gap("n31"),
            text(" in 1993. Subsequently, they formed a partnership "
                 "with "),
            gap("n32"),
            text(" to develop the project. As the biggest observation "
                 "wheel ever built, its construction involved 1,700 "
                 "people in five countries. Most of its components had "
                 "to be "),
            gap("n33"),
            text(", and delivering them had to be coordinated with "
                 "the "),
            gap("n34"),
            text(" in the River Thames. On average, 350 hours a week "
                 "are spent on maintenance of the Eye, and only "),
            gap("n35"),
            text(" is used to clean the glass."),
        ]},
    ],
}

SUMMARY4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["competition", "a competition"], 2),
    ("n32", ["British Airways"], 2),
    ("n33", ["invented"], 2),
    ("n34", ["tides"], 2),
    ("n35", ["distilled water"], 2),
]


# ── Part 4 — London Eye diagram (Q36-40) ────────────────────────────────────

DIAGRAM4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The London Eye — Construction Diagram",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "image_url": DIAGRAM_URL,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [
                    gap("d36"),
                    text(" piles — driven into the ground"),
                ]},
                {"segments": [
                    gap("d37"),
                    text(" — installed over the piles"),
                ]},
                {"segments": [
                    gap("d38"),
                    text(" — attached to the plinths"),
                ]},
                {"segments": [
                    text("mounting "),
                    gap("d39"),
                ]},
                {"segments": [
                    gap("d40"),
                    text(" — underneath the wheel"),
                ]},
            ],
        },
    ],
}

DIAGRAM4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("d36", ["tension"], 2),
    ("d37", ["base cap"], 2),
    ("d38", ["A-frame", "a-frame", "A frame"], 2),
    ("d39", ["rings"], 2),
    ("d40", ["boarding platform"], 2),
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
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
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
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete the table below.\n"
        "Choose your answers from the box and write the correct letter, "
        "A\u2013H, next to questions 11\u201315.\n"
        f"{SCREEN_LETTER_HINT}",
        JOB_OPTIONS,
        JOB_ITEMS,
        options_heading="Notes",
    )
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        FLOW2_STRUCTURE,
        FLOW2_ANSWERS,
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
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the sentences below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        SENTENCES3_STRUCTURE,
        SENTENCES3_ANSWERS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete the timetable below.\n"
        "Choose your answers from the box and write the correct letter, "
        "A\u2013H, next to questions 27\u201330.\n"
        f"{SCREEN_LETTER_HINT}",
        TIMETABLE_OPTIONS,
        TIMETABLE_ITEMS,
        options_heading="Activity",
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
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        SUMMARY4_STRUCTURE,
        SUMMARY4_ANSWERS,
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the diagram below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        DIAGRAM4_STRUCTURE,
        DIAGRAM4_ANSWERS,
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
