"""Seed Practice Set A Test 4 Listening, all four parts (Q1-40).

Part 1  Q1-5   form_completion       new patient form at Oakham Surgery
        Q6-10  mcq
Part 2  Q11-16 note_completion       joining and using the library
        Q17-20 diagram_labeling      library floor plan, typed labels
Part 3  Q21-24 short_answer          tutorial on essay progress
        Q25-27 sentence_completion
        Q28-30 note_completion       the tutor's notes on Melanie
Part 4  Q31-33 mcq                   tsunami
        Q34-35 short_answer          the two NOAA detection methods
        Q36-40 table_completion      tsunami examples

Every answer here was checked against the recording's own transcript, not just
copied off the answer sheet.

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t4_listening.py
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

TEST_NUMBER = 4


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

# The printed form leaves three further blank rows (2nd, 3rd, 4th child) that
# carry no question; they are dropped so the form does not render empty labels.
FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "OAKHAM SURGERY — New patient form",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "fields": [
        {"label": "New patient's road", "type": "static", "value": "Dawson Road (example)"},
        {
            "label": "Full name",
            "type": "gap_line",
            "segments": [text("Mike "), gap("g1")],
        },
        {"label": "Wife's first name", "type": "static", "value": "Janet"},
        {
            "label": "Childrens' first names",
            "type": "gap_line",
            "segments": [text("1st "), gap("g2")],
        },
        {
            "label": "Address",
            "type": "gap_line",
            "segments": [text("52 Dawson Road, "), gap("g3"), text(", Melbourne")],
        },
        {"label": "Health card number", "type": "gap_line", "segments": [gap("g4")]},
        {
            "label": "Wife's health card number",
            "type": "static",
            "value": "will give later",
        },
        {
            "label": "Preferred doctor selected",
            "type": "gap_line",
            "segments": [gap("g5")],
        },
    ],
}

# (gap_id, accepted answers, max words)
FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["Jacobs"], 1),
    ("g2", ["Rod"], 1),
    ("g3", ["Highfield"], 1),
    # A health card number is one item read out as six tokens, so the ceiling
    # has to clear it even though the rubric says three words.
    ("g4", ["NH 87 18 12 C", "NH871812C", "NH 871812 C"], 6),
    (
        "g5",
        [
            "Dr. White",
            "Dr White",
            "Doctor White",
            "White",
            "Dr. Kevin White",
            "Dr Kevin White",
            "Kevin White",
        ],
        3,
    ),
]

PART1_MCQ: list[dict] = [
    {
        "question": "When is Mike's wife's first appointment?",
        "options": [
            "Friday 21st at 2.00pm.",
            "Friday 21st at 2.30pm.",
            "Friday 21st at 3.30pm.",
        ],
        "correct": "A",
    },
    {
        "question": "What is the surgery's phone number?",
        "options": ["7253 9819", "7253 9829", "7523 9829"],
        "correct": "B",
    },
    {
        "question": (
            "What is the name of the girl with whom Mike is speaking at the surgery?"
        ),
        "options": ["Rachel", "Elizabeth", "Angela"],
        "correct": "C",
    },
    {
        "question": "What's the night doctor's mobile number?",
        "options": ["0506 759 3856", "0506 759 3857", "0506 758 3856"],
        "correct": "A",
    },
    {
        "question": "Which of the following does the surgery NOT make a charge for?",
        "options": ["Travel vaccinations", "Consultations", "Insurance reports"],
        "correct": "B",
    },
]

# ── Part 2 ───────────────────────────────────────────────────────────────────

NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Notes on Library",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "Joining Library — you will need:",
            "items": [
                {"segments": [text("A completed application form.")]},
                {"segments": [gap("n11")]},
                {"segments": [gap("n12")]},
                {"segments": [text("Two passport photos.")]},
            ],
        },
        {
            "heading": "Opening Hours",
            "items": [
                {"segments": [text("Library 8am – 10pm "), gap("n13")]},
                {
                    "segments": [
                        text("Reception 9am – 5pm (– 6.30 on "),
                        gap("n14"),
                        text(")"),
                    ]
                },
                {"segments": [text("(Mon – Sat; closed on Sundays)")]},
            ],
        },
        {
            "heading": "Borrowing",
            "items": [
                {"segments": [text("Undergraduates 4 books")]},
                {"segments": [text("Postgraduates "), gap("n15"), text(" books")]},
                {
                    "segments": [
                        text("Borrowing for 2 weeks + "),
                        gap("n16"),
                        text(" renewals (in person)"),
                    ]
                },
                {"segments": [text("No renewals over phone")]},
                {"segments": [text("Late return penalty: £2 per week")]},
            ],
        },
    ],
}

NOTES_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n11", ["5 pound fee", "£5 fee", "5 pounds", "£5", "a 5 pound fee"], 3),
    ("n12", ["University card"], 2),
    ("n13", ["Daily"], 1),
    ("n14", ["Fridays", "Friday"], 1),
    ("n15", ["6", "six", "6 books"], 2),
    ("n16", ["1 week", "one week"], 2),
]

# The paper has candidates write into boxes drawn on the plan. Inputs cannot be
# placed on an image here, so the plan is shown with its printed numbers and the
# four answers are typed below it — still recall, not multiple choice.
PLAN_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Library plan",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "image_url": MAP_IMAGE_URL.format(test=TEST_NUMBER),
    "sections": [
        {
            "heading": "Write the label for each numbered space on the plan above.",
            "items": [{"segments": [gap(f"p{n}")]} for n in (17, 18, 19, 20)],
        }
    ],
}

PLAN_ANSWERS: list[tuple[str, list[str], int]] = [
    ("p17", ["Computers", "the computers", "Computer"], 2),
    (
        "p18",
        ["Non-lending section", "non lending section", "the non-lending section"],
        3,
    ),
    ("p19", ["Arts", "Arts section", "the Arts"], 2),
    ("p20", ["Basement", "the basement"], 2),
]

# ── Part 3 ───────────────────────────────────────────────────────────────────

SHORT_ANSWER_ITEMS: list[dict] = [
    {
        "prompt": "When will Simon begin writing his essay?",
        "correct": ["Tomorrow"],
        "max_words": 3,
    },
    {
        "prompt": (
            "According to Simon, what kind of problems did Jaguar have in the "
            "1970s and 80s?"
        ),
        "correct": ["Reliability", "reliability problems"],
        "max_words": 3,
    },
    {
        "prompt": "What is the word limit for the essay?",
        "correct": ["4000 words", "4000", "4,000 words", "4,000"],
        "max_words": 3,
    },
    {
        "prompt": "What is the preferable method for handing in the essay?",
        "correct": [
            "E-mail attachment",
            "email attachment",
            "as an e-mail attachment",
            "as an email attachment",
        ],
        "max_words": 3,
    },
]

SENTENCE_ITEMS: list[dict] = [
    {
        "prompt": "Jennifer wants to write about how ____ are used by supermarkets.",
        "correct": ["Market surveys", "market survey"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Jennifer found some publications in the library ____ to help her "
            "analysis."
        ),
        "correct": ["Stack system", "the stack system"],
        "max_words": 3,
    },
    {
        "prompt": "The tutor warned Jennifer about ____ in her work.",
        # The key offers both halves of the tutor's warning as alternatives.
        "correct": ["Plagiarism", "using their conclusions"],
        "max_words": 3,
    },
]

NOTES3_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Notes on Student Essays",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    # Printed as a paragraph rather than a bulleted list.
    "bullets": False,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Student Melanie needs an "),
                        gap("n28"),
                        text(" as she has been unwell with the flu. She will get a "),
                        gap("n29"),
                        text(" from the doctor. She's going to write about "),
                        gap("n30"),
                        text(
                            " in the UK and their effect on housing trends. She "
                            "should be on track with the essay by the end of the "
                            "weekend."
                        ),
                    ]
                }
            ],
        }
    ],
}

NOTES3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n28", ["Extension", "an extension"], 2),
    # The sentence already supplies "from the doctor", so the bare noun is
    # enough; the key prints the note and the certificate as alternatives.
    ("n29", ["Doctor's note", "certificate", "note", "doctor's certificate"], 3),
    ("n30", ["Mortgage interest rates"], 3),
]

# ── Part 4 ───────────────────────────────────────────────────────────────────

PART4_MCQ: list[dict] = [
    {
        "question": "The Pacific is more prone to tsunami because...",
        "options": [
            "it has many faults.",
            "its faults undergo subduction.",
            "its tectonic plates are bigger than elsewhere.",
        ],
        "correct": "B",
    },
    {
        "question": "The biggest tsunami are usually created by...",
        "options": [
            "undersea volcanic eruptions.",
            "undersea earthquakes.",
            "undersea landslides.",
        ],
        "correct": "B",
    },
    {
        "question": "Tsunami are difficult to detect in deep water because of...",
        "options": ["their wavelength.", "their high speed.", "their wave rate."],
        "correct": "A",
    },
]

# The paper asks for a list of two, so a candidate who writes them the other way
# round has still answered correctly; both are accepted in either box.
DETECTION_ITEMS: list[dict] = [
    {
        "prompt": "First way the NOAA has set up to detect tsunami.",
        "correct": [
            "Seismic detection system",
            "a seismic detection system",
            "Buoys at sea",
            "Buoys",
        ],
        "max_words": 3,
    },
    {
        "prompt": "Second way the NOAA has set up to detect tsunami.",
        "correct": [
            "Buoys at sea",
            "Buoys",
            "Seismic detection system",
            "a seismic detection system",
        ],
        "max_words": 3,
    },
]

TABLE4_STRUCTURE: dict = {
    "variant": "table",
    "title": "TSUNAMI EXAMPLES",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["When Happened", "Cause", "Deaths Caused", "Wave Height"],
    "rows": [
        [
            cell(text("1992")),
            cell(gap("t36")),
            cell(text("none")),
            cell(text("3 feet")),
        ],
        [
            cell(text("1992")),
            cell(text("Underwater earthquake")),
            cell(text("none")),
            cell(gap("t37")),
        ],
        [
            cell(text("1998")),
            cell(gap("t38")),
            cell(text("1200")),
            cell(text("23 feet")),
        ],
        [
            cell(text("1998")),
            cell(text("Underwater volcanic eruption")),
            cell(text("3000")),
            cell(text("40 feet")),
        ],
        [
            cell(text("1896")),
            cell(text("Underwater earthquake")),
            cell(gap("t39")),
            cell(text("35 feet")),
        ],
        [
            cell(text("8000 years ago")),
            cell(text("Underwater landslide")),
            cell(gap("t40")),
            cell(text("30 feet")),
        ],
    ],
}

TABLE4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t36", ["Offshore landslide", "an offshore landslide"], 3),
    ("t37", ["No wave", "zero feet", "0 feet", "none"], 3),
    # The lecture says "submarine earthquake"; the table's other rows print the
    # same thing as "underwater earthquake", so both wordings are credited.
    ("t38", ["Submarine earthquake", "underwater earthquake"], 3),
    ("t39", ["26,000 people", "26,000", "26000", "26000 people"], 2),
    ("t40", ["None", "no deaths", "0", "zero"], 2),
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

    async def free_text(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[dict],
    ) -> None:
        """Short-answer and sentence-completion rows, which share a shape."""
        group = await self._group(question_type, instruction)
        for item in items:
            self._add(
                group,
                question_type,
                # The take UI reads content.prompt; content.question keeps the
                # admin previews in step with the rest of the book.
                {
                    "prompt": item["prompt"],
                    "question": item["prompt"],
                    "max_words": item["max_words"],
                },
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
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        FORM_STRUCTURE,
        FORM_ANSWERS,
    )
    await w.mcq("Choose the correct letter, A, B or C.", PART1_MCQ)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 2
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        NOTES_STRUCTURE,
        NOTES_ANSWERS,
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the library plan below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        PLAN_STRUCTURE,
        PLAN_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 3
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        SHORT_ANSWER_ITEMS,
    )
    await w.free_text(
        QuestionType.SENTENCE_COMPLETION,
        "Complete the sentences below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        SENTENCE_ITEMS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the tutor's summary notes on Melanie below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        NOTES3_STRUCTURE,
        NOTES3_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 4
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the correct letter, A, B or C.", PART4_MCQ)
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "List the two ways which the National Oceanic and Atmospheric "
        "Administration has set up to detect tsunami.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        DETECTION_ITEMS,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        TABLE4_STRUCTURE,
        TABLE4_ANSWERS,
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
