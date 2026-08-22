"""Seed Practice Set A Test 1 Listening, all four parts (Q1-40).

Part 1  Q1-5   form_completion   lost property report
        Q6-8   multi_select      what the bag contained (choose three)
        Q9-10  mcq
Part 2  Q11-14 diagram_labeling  campus map, typed labels
        Q15-20 note_completion   student facilities
Part 3  Q21-25 table_completion  John and Jane
        Q26-29 short_answer
        Q30    mcq
Part 4  Q31-34 mcq               oil tankers and slicks
        Q35-39 table_completion  clean-up techniques
        Q40    note_completion

Every answer here was checked against the recording's own transcript, not just
copied off the answer sheet.

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t1_listening.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.services.compound import validate_compound_structure  # noqa: E402
from app.services.scoring import scoring_slots_for_question  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_a_common import (  # noqa: E402
    MAP_IMAGE_URL,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 1


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "PAN ASIAN AIRWAYS — Lost property report form",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    # Postcodes and phone numbers are single items that read as several words,
    # so the ceiling has to clear the longest of them.
    "max_words_per_gap": 3,
    "fields": [
        {"label": "First name", "type": "static", "value": "Kirsty (example)"},
        {"label": "Surname", "type": "static", "value": "Allen"},
        {
            "label": "Address",
            "type": "gap_line",
            "segments": [gap("g1"), text(" Windham Road, Richmond")],
        },
        {"label": "Postcode", "type": "gap_line", "segments": [gap("g2")]},
        {"label": "Home tel.", "type": "static", "value": "020 8927 7651"},
        {"label": "Mobile tel.", "type": "gap_line", "segments": [gap("g3")]},
        {"label": "Flight number", "type": "gap_line", "segments": [gap("g4")]},
        {"label": "Seat number", "type": "gap_line", "segments": [gap("g5")]},
        {"label": "From", "type": "static", "value": "New York"},
        {"label": "To", "type": "static", "value": "London Heathrow"},
    ],
}

# (gap_id, accepted answers, max words)
FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["48"], 1),
    # The recording spells this out; the printed key and the spoken letter make
    # the digit one and the letter I indistinguishable, so both are accepted.
    ("g2", ["R16 GH7", "RI6 GH7", "R16GH7", "RI6GH7"], 2),
    ("g3", ["07754 897 432", "07754897432"], 3),
    ("g4", ["PA 365", "PA365"], 2),
    ("g5", ["E6", "E 6"], 2),
]

MULTI_SELECT_ITEM = {
    "question": "What items did Kirsty's bag contain?",
    "options": [
        "17 pounds",
        "pens",
        "her passport",
        "a book",
        "200 dollars",
        "her house keys",
    ],
    "correct": ["B", "D", "E"],
}

PART1_MCQ: list[dict] = [
    {
        "question": "What has Kirsty done regarding the loss of her credit card?",
        "options": [
            "Informed the police but not the credit card company.",
            "Informed the credit card company but not the police.",
            "Informed both the police and the credit card company.",
            "Informed neither the police nor the credit card company.",
        ],
        "correct": "C",
    },
    {
        "question": "What must Kirsty do after the call regarding her lost handbag?",
        "options": [
            "Call back after 1½ hours.",
            "Just wait for a call back.",
            "Call back after 1½ hours if she has heard nothing.",
            "Call back the next day if she has heard nothing.",
        ],
        "correct": "C",
    },
]

# ── Part 2 ───────────────────────────────────────────────────────────────────

# The paper has candidates write into boxes drawn on the map. Inputs cannot be
# placed on an image here, so the map is shown with its printed numbers and the
# four answers are typed below it — still recall, not multiple choice.
MAP_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Campus map",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "image_url": MAP_IMAGE_URL.format(test=TEST_NUMBER),
    "sections": [
        {
            "heading": "Write the name of each numbered building on the map above.",
            "items": [{"segments": [gap(f"m{n}")]} for n in (11, 12, 13, 14)],
        }
    ],
}

MAP_ANSWERS: list[tuple[str, list[str], int]] = [
    ("m11", ["Students' Union", "Student Union", "Students Union", "Union"], 3),
    ("m12", ["University Library", "Library"], 3),
    ("m13", ["Hall of Residence", "Halls of Residence", "Hall of residence"], 3),
    ("m14", ["Sports Hall", "Sports hall"], 3),
]

NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Notes on Student Facilities",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "Students' Union",
            "items": [
                {"segments": [text("Very cheap")]},
                {"segments": [text("Bookshop")]},
                {"segments": [text("Food and drink available")]},
                {"segments": [text("Parties!")]},
                {"segments": [text("Offices — travel, welfare etc.")]},
                {"segments": [text("Open 8am – 12 midnight")]},
            ],
        },
        {
            "heading": "Library",
            "items": [
                {"segments": [text("Must register")]},
                {"segments": [text("Tours every "), gap("n15"), text(" for 2 weeks.")]},
                {
                    "segments": [
                        text("Open 9am – 9pm (later during "),
                        gap("n16"),
                        text(")"),
                    ]
                },
            ],
        },
        {
            "heading": "Refectory",
            "items": [
                {"segments": [text("Cheap meals")]},
                {"segments": [text("Lunch 12 noon – 3pm")]},
                {"segments": [text("Dinner "), gap("n17"), text(" – 8.30pm")]},
                {"segments": [text("Types of food — favourites, healthy, ethnic,")]},
                {"segments": [gap("n18"), text(", vegan")]},
            ],
        },
        {
            "heading": "Sports Hall",
            "items": [
                {"segments": [text("Must join Athletic Union, which:")]},
                {"segments": [text("lets me use facilities")]},
                {"segments": [text("lets me play for teams")]},
                {"segments": [gap("n19"), text(" me all year")]},
            ],
        },
        {
            "heading": "Discount Card",
            "items": [
                {"segments": [text("Costs £"), gap("n20")]},
                {"segments": [text("Gives me discounts on all uni. services")]},
            ],
        },
    ],
}

NOTES_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n15", ["2 hours", "two hours"], 2),
    ("n16", ["final exams", "finals"], 2),
    ("n17", ["6pm", "6 pm", "6.00pm", "18.00"], 2),
    ("n18", ["vegetarian", "vegetarians"], 1),
    ("n19", ["fully insures", "insures"], 2),
    ("n20", ["50", "£50"], 1),
]

# ── Part 3 ───────────────────────────────────────────────────────────────────

TABLE3_STRUCTURE: dict = {
    "variant": "table",
    "title": "",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "headers": ["", "John", "Jane"],
    "rows": [
        [cell(text("Day of Arrival")), cell(text("Thursday")), cell(gap("t21"))],
        [
            cell(text("Subjects Studying")),
            cell(text("Economics, Maths, French")),
            {
                "variant": "plain",
                "segments": [gap("t22"), text(", History, Music")],
            },
        ],
        [cell(text("Monday's 9am lecture")), cell(text("French")), cell(text("History"))],
        [cell(text("Monday's 2pm lecture")), cell(text("Maths")), cell(gap("t23"))],
        [
            cell(text("Wednesday afternoon sport selected")),
            cell(gap("t24")),
            cell(text("Volleyball")),
        ],
        [cell(text("Location of Sport")), cell(text("Sports hall")), cell(gap("t25"))],
    ],
}

TABLE3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t21", ["Tuesday"], 1),
    ("t22", ["Economics"], 1),
    ("t23", ["free", "nothing", "a free", "free period"], 2),
    ("t24", ["Squash"], 1),
    ("t25", ["Main sports hall", "main sports hall", "sports hall"], 3),
]

SHORT_ANSWER_ITEMS: list[dict] = [
    {
        "question": (
            "Students can choose from how many essay titles for their "
            "first assignment?"
        ),
        "correct": ["10", "about 10", "around 10", "ten"],
        "max_words": 2,
    },
    {
        "question": "Where did John travel during the summer?",
        "correct": ["Africa and Asia", "Asia and Africa"],
        "max_words": 3,
    },
    {
        "question": "What is the word limit for the essays?",
        "correct": ["4000 words", "4000", "4,000 words", "4,000"],
        "max_words": 2,
    },
    {
        "question": "When must the first essay be handed in by?",
        "correct": ["30th October", "October 30th", "30 October", "30th of October"],
        "max_words": 3,
    },
]

PART3_MCQ: list[dict] = [
    {
        "question": "Where will John and Jane meet up later that day?",
        "options": [
            "the economics course office",
            "the economics common room",
            "the campus cafeteria",
        ],
        "correct": "B",
    },
]

# ── Part 4 ───────────────────────────────────────────────────────────────────

PART4_MCQ: list[dict] = [
    {
        "question": "Japan relies on oil tankers because...",
        "options": [
            "the country consists of islands.",
            "the country has no pipeline network.",
            "the country has no natural oil resources.",
        ],
        "correct": "C",
    },
    {
        "question": "Professor Wilson says that oil tankers are...",
        "options": ["very safe.", "quite safe.", "quite unsafe."],
        "correct": "B",
    },
    {
        "question": (
            "According to Professor Wilson, the main cause of oil slicks is..."
        ),
        "options": [
            "accidents while loading and unloading oil.",
            "collisions.",
            "deliberate releases of oil.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "According to Professor Wilson, slicks are rarely burned off "
            "nowadays because..."
        ),
        "options": [
            "the oil is refined.",
            "it usually doesn't work.",
            "it creates too much air pollution.",
        ],
        "correct": "B",
    },
]

TABLE4_STRUCTURE: dict = {
    "variant": "table",
    "title": "Oil exploration clean-up techniques",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "headers": ["Techniques", "Advantages", "Disadvantages"],
    "rows": [
        [
            cell(text("The Containment Boom")),
            cell(text("Cheap and easy")),
            cell(text("Only good when there are "), gap("t35")),
        ],
        [
            cell(text("Chemical Detergents")),
            cell(text("Good for treating "), gap("t36")),
            cell(text("Chemicals remain in the water + kill marine life.")),
        ],
        [
            cell(text("The Sponge")),
            cell(text("Oil remains permanently in the sponge.")),
            cell(text("The sponge mats turn into "), gap("t37")),
        ],
        [
            cell(text("Bacteria")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("Cheap")]},
                    {"segments": [text("Easy to administer")]},
                    {"segments": [text("Totally "), gap("t38")]},
                ],
            },
            cell(gap("t39")),
        ],
    ],
}

TABLE4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t35", ["very calm seas", "calm seas"], 3),
    ("t36", ["larger slicks", "large slicks", "the larger slicks"], 3),
    ("t37", ["toxic waste"], 2),
    ("t38", ["eco-friendly", "eco friendly", "ecofriendly"], 2),
    (
        "t39",
        [
            "no discernable drawbacks",
            "no discernible drawbacks",
            "no drawbacks",
            "none",
        ],
        3,
    ),
]

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Optional essay question",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": (
                "Remember to check out the faculty's notice boards. "
                "You will find:"
            ),
            "items": [
                {"segments": [text("reading lists")]},
                {"segments": [text("essay questions")]},
                {"segments": [gap("n40")]},
            ],
        }
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n40",
        ["deadline for submission", "the deadline for submission", "submission deadline"],
        3,
    ),
]


# ── writing helpers ──────────────────────────────────────────────────────────


class SectionWriter:
    """Accumulates groups and questions for one listening part."""

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
        if options_shared is not None:
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

    async def short_answer(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                # The take screen reads a short answer's wording from
                # content.prompt; under any other key the line renders blank.
                {"prompt": item["question"], "max_words": item["max_words"]},
                {
                    "correct": item["correct"],
                    "max_words": item["max_words"],
                    "case_sensitive": False,
                },
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    # Part 1
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.FORM_COMPLETION,
        "Complete the form below.\n"
        "Write NO MORE THAN ONE WORD AND/OR A NUMBER for each answer.",
        FORM_STRUCTURE,
        FORM_ANSWERS,
    )
    await w.multi_select(
        "Choose THREE letters, A-F.", MULTI_SELECT_ITEM
    )
    await w.mcq("Choose the correct letter, A, B, C or D.", PART1_MCQ)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 2
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the locations on the map below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        MAP_STRUCTURE,
        MAP_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        NOTES_STRUCTURE,
        NOTES_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 3
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        TABLE3_STRUCTURE,
        TABLE3_ANSWERS,
    )
    await w.short_answer(
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        SHORT_ANSWER_ITEMS,
    )
    await w.mcq("Choose the correct letter, A, B or C.", PART3_MCQ)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 4
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the correct letter, A, B or C.", PART4_MCQ)
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        TABLE4_STRUCTURE,
        TABLE4_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS for the answer.",
        NOTES4_STRUCTURE,
        NOTES4_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    total = sum(totals)
    if total != 40:
        raise SystemExit(f"expected 40 scoring slots across the four parts, got {total}")

    await db.commit()
    print(f"\nDone. Listening seeded: {totals} = {total} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
