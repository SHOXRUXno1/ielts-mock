"""Seed Practice Set C Test 2 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 2. Every key is taken from the
printed Answer Key (p.175). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-10  form_completion       Pinder's Animal Park
Part 2  Q11-15 mcq                   Tamerton Centre
        Q16-20 matching_features     objects → rules A-C
Part 3  Q21-25 map_labeling          Biogas Plant (A-G)
        Q26-30 flow_chart_completion Year Three energy lesson (A-G)
Part 4  Q31-40 note_completion       Creating artificial gills

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t2_listening.py
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
from seed_practice_c_common import (  # noqa: E402
    MAP_IMAGE_URL,
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 2
MAP_URL = MAP_IMAGE_URL.format(test=TEST_NUMBER)


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 ───────────────────────────────────────────────────────────────────

FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "Pinder's Animal Park",
    "instruction_words": "NO MORE THAN TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "fields": [
        {
            "label": "Example Enquiries about",
            "type": "static",
            "value": "temporary work",
        },
        {
            "label": "Name",
            "type": "gap_line",
            "segments": [text("Jane "), gap("g1")],
        },
        {
            "label": "Address",
            "type": "gap_line",
            "segments": [gap("g2"), text(" Exeter")],
        },
        {
            "label": "Telephone number",
            "type": "static",
            "value": "07792430921",
        },
        {
            "label": "Availability",
            "type": "gap_line",
            "segments": [text("Can start work on "), gap("g3")],
        },
        {
            "label": "Preferred type of work",
            "type": "gap_line",
            "segments": [text("Assistant "), gap("g4")],
        },
        {
            "label": "Relevant skills",
            "type": "gap_line",
            "segments": [text("Familiar with kitchen "), gap("g5")],
        },
        {
            "label": "Relevant qualifications",
            "type": "gap_line",
            "segments": [text("A "), gap("g6"), text(" certificate")],
        },
        {
            "label": "Training required",
            "type": "gap_line",
            "segments": [text("A "), gap("g7"), text(" course")],
        },
        {
            "label": "Referee Name",
            "type": "static",
            "value": "Dr Ruth Price",
        },
        {
            "label": "Position",
            "type": "gap_line",
            "segments": [gap("g8")],
        },
        {
            "label": "Phone number",
            "type": "gap_line",
            "segments": [gap("g9")],
        },
        {
            "label": "Other",
            "type": "gap_line",
            "segments": [text("Applicant has a form of "), gap("g10")],
        },
    ],
}

FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["Lamerton"], 1),
    ("g2", ["42 West Lane"], 3),
    ("g3", ["11th June", "11.06", "06.11"], 2),
    ("g4", ["cook"], 1),
    ("g5", ["equipment"], 1),
    ("g6", ["food-handling", "food handling"], 2),
    ("g7", ["First Aid", "first aid"], 2),
    ("g8", ["college tutor", "tutor"], 2),
    ("g9", ["0208 685114"], 2),
    (
        "g10",
        ["colour blindness", "color blindness"],
        2,
    ),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_MCQ: list[dict] = [
    {
        "question": (
            "The Tamerton Centre was set up in order to encourage people"
        ),
        "options": [
            "to enjoy being in the countryside.",
            "to help conserve the countryside.",
            "to learn more about the countryside.",
        ],
        "correct": "A",
    },
    {
        "question": "Last year's group said that the course",
        "options": [
            "built their self esteem.",
            "taught them lots of new skills.",
            "made them fitter and stronger.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "For the speaker, what's the most special feature of the course?"
        ),
        "options": [
            "You can choose which activities you do.",
            "There's such a wide variety of activities.",
            "You can become an expert in new activities.",
        ],
        "correct": "B",
    },
    {
        "question": "The speaker advises people to bring",
        "options": [
            "their own board games.",
            "extra table tennis equipment.",
            "a selection of films on DVD.",
        ],
        "correct": "A",
    },
    {
        "question": "Bed-time is strictly enforced because",
        "options": [
            "it's a way to reduce bad behaviour.",
            "tiredness can lead to accidents.",
            "it makes it easy to check everyone's in.",
        ],
        "correct": "C",
    },
]

RULE_OPTIONS = [
    "A. You MUST take this",
    "B. You CAN take this, if you wish",
    "C. You must NOT take this",
]

RULE_ITEMS: list[tuple[str, str]] = [
    ("Electrical equipment", "C"),
    ("Mobile phone", "A"),
    ("Sun cream", "B"),
    ("Aerosol deodorant", "C"),
    ("Towel", "B"),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

DIAGRAM_OPTIONS = ["A", "B", "C", "D", "E", "F", "G"]

DIAGRAM_ITEMS: list[tuple[str, str]] = [
    ("Waste container", "C"),
    ("Slurry", "G"),
    ("Water inlet", "A"),
    ("Gas", "E"),
    ("Overflow tank", "F"),
]

LESSON_OPTIONS = [
    "A. Identify sequence.",
    "B. Ask questions.",
    "C. Copy.",
    "D. Demonstrate meaning.",
    "E. Distribute worksheet.",
    "F. Draw pictures.",
    "G. Present sentences.",
]

FLOW3_STRUCTURE: dict = {
    "variant": "flow",
    "title": "LESSON OUTLINE YEAR THREE — TOPIC: ENERGY",
    "instruction_words": "letter A–G",
    "max_words_per_gap": 1,
    "options": LESSON_OPTIONS,
    "steps": [
        {
            "segments": [
                text("Teacher: Introduce word"),
                text("\nPupils: look and listen"),
            ]
        },
        {
            "segments": [
                text("Teacher: "),
                gap("f26"),
                text("\nPupils: look and listen"),
            ]
        },
        {
            "segments": [
                text("Teacher: Present question"),
                text("\nPupils: respond"),
            ]
        },
        {
            "segments": [
                text("Teacher: "),
                gap("f27"),
                text("\nPupils: "),
                gap("f28"),
                text(" and expand"),
            ]
        },
        {
            "segments": [
                text("Teacher: Display pictures"),
                text("\nPupils: "),
                gap("f29"),
            ]
        },
        {
            "segments": [
                text("Teacher: "),
                gap("f30"),
                text("\nPupils: write"),
            ]
        },
        {"segments": [text("Teacher: Monitor pupils")]},
    ],
}

FLOW3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("f26", ["D", "Demonstrate meaning.", "Demonstrate meaning"], 1),
    ("f27", ["G", "Present sentences.", "Present sentences"], 1),
    ("f28", ["C", "Copy.", "Copy"], 1),
    ("f29", ["A", "Identify sequence.", "Identify sequence"], 1),
    ("f30", ["E", "Distribute worksheet.", "Distribute worksheet"], 1),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Creating artificial gills",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Background",
            "items": [
                {
                    "segments": [
                        text(
                            "Taking in oxygen: mammals — lungs; fish — gills"
                        )
                    ]
                },
                {
                    "segments": [
                        text(
                            "Long-held dreams — humans swimming underwater "
                            "without oxygen tanks"
                        )
                    ]
                },
                {
                    "segments": [
                        text("Oxygen tanks considered too "),
                        gap("n31"),
                        text(" and large"),
                    ]
                },
                {
                    "segments": [
                        text("Attempts to extract oxygen directly from water")
                    ]
                },
                {
                    "segments": [
                        text(
                            "1960s — prediction that humans would have gills "
                            "added by "
                        ),
                        gap("n32"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Ideas for artificial gills were inspired by "
                            "research on fish gills, fish swim bladders, "
                            "animals without gills — especially bubbles "
                            "used by "
                        ),
                        gap("n33"),
                    ]
                },
            ],
        },
        {
            "heading": "Building a simple artificial gill",
            "items": [
                {
                    "segments": [
                        text(
                            "Make a watertight box of a material which lets "
                        ),
                        gap("n34"),
                        text(" pass through"),
                    ]
                },
                {"segments": [text("Fill with air and submerge in water")]},
                {
                    "segments": [
                        text(
                            "Important that the diver and the water keep "
                        ),
                        gap("n35"),
                    ]
                },
                {
                    "segments": [
                        text("The gill has to have a large "),
                        gap("n36"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Designers often use a network of small "
                        ),
                        gap("n37"),
                        text(" on their gill"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Main limitation — problems caused by increased "
                        ),
                        gap("n38"),
                        text(" in deeper water"),
                    ]
                },
            ],
        },
        {
            "heading": "Other applications",
            "items": [
                {
                    "segments": [
                        text("Supplying oxygen for use on "),
                        gap("n39"),
                    ]
                },
                {
                    "segments": [
                        text("Powering "),
                        gap("n40"),
                        text(
                            " cells for driving machinery underwater"
                        ),
                    ]
                },
            ],
        },
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["heavy"], 1),
    ("n32", ["surgery"], 1),
    ("n33", ["beetles"], 1),
    ("n34", ["gas"], 1),
    ("n35", ["moving"], 1),
    ("n36", ["surface area"], 2),
    ("n37", ["tubes"], 1),
    ("n38", ["pressure"], 1),
    ("n39", ["submarines", "a submarine"], 2),
    ("n40", ["fuel"], 1),
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
        group = await self._group(question_type, instruction, options_shared=shared)
        for question, correct in items:
            self._add(
                group, question_type, {"question": question}, {"correct": correct}
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

    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.FORM_COMPLETION,
        "Complete the form below.\n"
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
        FORM_STRUCTURE,
        FORM_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the correct answer, A, B or C.", PART2_MCQ)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What rules apply to taking different objects to the Centre?\n"
        "Match each object with the correct rule, A–C.\n"
        "Write the correct letter, A–C.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        RULE_OPTIONS,
        RULE_ITEMS,
        options_heading="Rules",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.map_labeling(
        "Label the diagram below.\n"
        "Write the correct letter, A–G, next to questions 21–25.",
        DIAGRAM_OPTIONS,
        DIAGRAM_ITEMS,
        image_url=MAP_URL,
        subtitle="(Year 6 Lesson) Biogas Plant",
    )
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Choose FIVE answers from the box and write the correct letter, A–G, "
        f"next to questions 26–30.\n{SCREEN_LETTER_HINT}",
        FLOW3_STRUCTURE,
        FLOW3_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
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
