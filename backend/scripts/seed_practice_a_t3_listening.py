"""Seed Practice Set A Test 3 Listening, all four parts (Q1-40).

Part 1  Q1-5   form_completion   library membership application
        Q6-8   multi_select      the books Peter likes (choose three)
        Q9-10  short_answer
Part 2  Q11-14 note_completion   four reasons for a blood transfusion
        Q15-17 table_completion  what each blood component is used for
        Q18-20 note_completion   giving blood
Part 3  Q21-27 note_completion   the university computer labs
        Q28-30 mcq
Part 4  Q31-35 note_completion   the Shinkansen
        Q36-40 sentence_completion

Every answer here was checked against the recording's own transcript, not just
copied off the answer sheet.

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t3_listening.py
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
from seed_practice_a_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 3


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "WESTLEY PUBLIC LIBRARY — Membership application form",
    "instruction_words": "THREE WORDS OR A NUMBER",
    "max_words_per_gap": 3,
    "fields": [
        {"label": "Name", "type": "static", "value": "Camden (example)"},
        {"label": "First name", "type": "static", "value": "Peter"},
        {
            "label": "Address",
            "type": "gap_line",
            "segments": [text("Flat 5, 53 "), gap("g1"), text(", Finsbury")],
        },
        {"label": "Postcode", "type": "gap_line", "segments": [gap("g2")]},
        {
            "label": "Date of birth",
            "type": "gap_line",
            "segments": [text("8th July "), gap("g3")],
        },
        {"label": "Home tel.", "type": "static", "value": "None"},
        {"label": "Mobile tel.", "type": "gap_line", "segments": [gap("g4")]},
        {
            "label": "Proof of residence provided",
            "type": "gap_line",
            "segments": [gap("g5")],
        },
    ],
}

# (gap_id, accepted answers, max words)
FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["Green Street", "Green St", "Green St."], 2),
    ("g2", ["7434"], 1),
    ("g3", ["1976"], 1),
    ("g4", ["06634 982 746", "06634982746"], 3),
    # The key prints the qualifier in brackets, so the bare noun is enough.
    ("g5", ["An addressed letter", "Addressed letter", "A letter", "Letter"], 3),
]

MULTI_SELECT_ITEM = {
    "question": "What type of books does Peter like?",
    "options": [
        "Wildlife books",
        "Romance books",
        "Travel books",
        "Historical novels",
        "Science Fiction novels",
        "Mystery books",
    ],
    "correct": ["A", "D", "F"],
}

PART1_SHORT_ANSWER: list[dict] = [
    {
        "prompt": "How much does it cost to join the library?",
        "correct": ["Free", "Nothing", "No charge", "No cost", "Nothing at all"],
        "max_words": 3,
    },
    {
        "prompt": "How much does it cost to rent a DVD?",
        # The $60 deposit is the bracketed half of the key: optional, not required.
        "correct": [
            "$6",
            "6",
            "6 dollars",
            "Six dollars",
            "$6 ($60 deposit)",
            "$6 and a $60 deposit",
        ],
        "max_words": 3,
    },
]

# ── Part 2 ───────────────────────────────────────────────────────────────────

# The paper asks for any four reasons in any order, and the key lists seven
# acceptable ones spread over its four boxes. Nothing here marks one pooled set
# across four gaps, so every gap accepts the whole pool. That credits a candidate
# who lists the same reason twice, which is too generous, but the alternative —
# pinning each reason to one gap — would fail candidates who wrote four correct
# reasons in a different order.
TRANSFUSION_REASONS = [
    "Accidents",
    "Accident victims",
    "Victims of accidents",
    "Burns",
    "Heart surgery",
    "Organ transplants",
    "Organ transplant",
    "Patients with leukaemia",
    "Patients with leukemia",
    "Leukaemia",
    "Leukemia",
    "Cancer",
    "Cancer patients",
    "Patients with cancer",
    "Premature babies",
]

REASONS_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Reasons for needing a blood transfusion",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "The four reasons may be given in any order.",
            "items": [{"segments": [gap(f"r{n}")]} for n in (11, 12, 13, 14)],
        }
    ],
}

REASONS_ANSWERS: list[tuple[str, list[str], int]] = [
    (f"r{n}", TRANSFUSION_REASONS, 3) for n in (11, 12, 13, 14)
]

BLOOD_TABLE_STRUCTURE: dict = {
    "variant": "table",
    "title": "Blood — component parts (types of blood: O, A, B + AB)",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["Part", "Used for"],
    "rows": [
        [cell(text("red blood cells")), cell(gap("t15"), text(" to cells"))],
        [cell(text("white blood cells")), cell(text("help patients’ "), gap("t16"))],
        [cell(text("platelets")), cell(text("blood clotting"))],
        [cell(text("plasma")), cell(gap("t17"), text(" the other blood parts"))],
    ],
}

BLOOD_TABLE_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t15", ["Carrying oxygen", "Carry oxygen", "Carries oxygen", "To carry oxygen"], 3),
    (
        "t16",
        [
            "Immune system",
            "Defence system",
            "Defense system",
            "Immune systems",
            "Defence systems",
        ],
        3,
    ),
    ("t17", ["Carrying", "Carries", "Carry"], 1),
]

DONATION_STRUCTURE: dict = {
    "variant": "notes",
    "title": "GIVING BLOOD",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "Days",
            "items": [{"segments": [text("Wednesday + next 2 days")]}],
        },
        {
            "heading": "Where",
            "items": [
                {
                    "segments": [
                        text("Westley General Hospital, "),
                        gap("n18"),
                        text(" Department"),
                    ]
                }
            ],
        },
        {
            "heading": "When",
            "items": [{"segments": [text("Between 9.00am and "), gap("n19")]}],
        },
        {
            "heading": "Must",
            "items": [
                {"segments": [text("be healthy")]},
                {"segments": [text("be "), gap("n20"), text(" or over")]},
                {"segments": [text("weigh more than 110 pounds")]},
                {"segments": [text("have had no tattoos this year")]},
                {"segments": [text("not have donated blood within past 56 days")]},
            ],
        },
    ],
}

DONATION_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n18", ["Outpatients", "Outpatient", "Out-patients", "Out patients"], 2),
    # The key prints one clock format; the same time written the usual other ways
    # is the same answer.
    ("n19", ["4.30pm", "4.30 pm", "4:30pm", "4:30 pm", "16.30", "16:30"], 2),
    ("n20", ["17", "Seventeen", "17 years old", "17 years of age"], 3),
]

# ── Part 3 ───────────────────────────────────────────────────────────────────

LABS_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Computer Labs",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "The 4 labs below can be used by undergraduates.",
            "items": [
                {
                    "segments": [
                        text("Other computer labs can only be used by postgraduates and "),
                        gap("n21"),
                    ]
                }
            ],
        },
        {
            "heading": "Lab Locations",
            "items": [
                {"segments": [text("Wimborne — Johnson Building")]},
                {"segments": [text("Franklin — Computer Sciences Building")]},
                {"segments": [text("Salisbury — "), gap("n22")]},
                {"segments": [text("Court — Johnson Building")]},
            ],
        },
        {
            "heading": "Reservations",
            "items": [
                {"segments": [gap("n23"), text(" a day unless computers are free")]},
                {"segments": [text("Write reservation in book "), gap("n24")]},
                {
                    "segments": [
                        text("(Penalty for erasing someone else’s reservation — 1 year ban)")
                    ]
                },
            ],
        },
        {"heading": "User Name", "items": [{"segments": [text("jamessmith2")]}]},
        {"heading": "Password", "items": [{"segments": [gap("n25")]}]},
        {
            "heading": "Printing",
            "items": [
                {
                    "segments": [
                        text("Pick up print outs from "),
                        gap("n26"),
                        text(" in Franklin"),
                    ]
                },
                {"segments": [text("Costs "), gap("n27")]},
            ],
        },
    ],
}

LABS_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n21", ["Staff", "The staff", "Staff members"], 2),
    ("n22", ["Library", "The library", "In the library"], 3),
    ("n23", ["2 hours", "Two hours", "2 hrs"], 2),
    ("n24", ["In pen", "Pen", "In a pen", "With a pen", "Using a pen"], 3),
    ("n25", ["Biology"], 1),
    ("n26", ["Tray", "A tray", "The tray"], 2),
    ("n27", ["Nothing", "Free", "No cost", "Nothing at all"], 3),
]

PART3_MCQ: list[dict] = [
    {
        "question": "The introductory computer course that James decides to take is...",
        "options": ["beginner.", "intermediate.", "advanced."],
        "correct": "A",
    },
    {
        "question": (
            "The computer laboratory for James’ introductory computer course is in..."
        ),
        "options": ["Wimborne", "Franklin", "Court"],
        "correct": "B",
    },
    {
        "question": "James will take his introductory computer course...",
        "options": [
            "on Thursday at 2.00pm.",
            "on Tuesday at 4.30pm.",
            "on Tuesday at 5.00pm.",
        ],
        "correct": "C",
    },
]

# ── Part 4 ───────────────────────────────────────────────────────────────────

SHINKANSEN_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The Shinkansen or Bullet Train",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "Safety",
            "items": [
                {
                    "segments": [
                        text(
                            "No deaths (bar 1 from passenger misadventure) "
                            "since its launch in "
                        ),
                        gap("n31"),
                        text("."),
                    ]
                }
            ],
        },
        {
            "heading": "Speed",
            "items": [
                {
                    "segments": [
                        text("Holds world train record for "),
                        gap("n32"),
                        text(" of 261.8 kph."),
                    ]
                },
                {"segments": [text("500 series Nozumi’s fastest speed is 300kph.")]},
            ],
        },
        {
            "heading": "Punctuality",
            "items": [
                {"segments": [text("Punctual to within the second.")]},
                {
                    "segments": [
                        text("All bullet trains for 1 year were a total of "),
                        gap("n33"),
                        text(" late."),
                    ]
                },
            ],
        },
        {
            "heading": "History",
            "items": [
                {"segments": [text("First used on Tokyo to Osaka route.")]},
                {"segments": [text("Old models have now been retired.")]},
                {"segments": [text("300, 500 and 700 are recent models.")]},
            ],
        },
        {
            "heading": "Services",
            "items": [
                {
                    "segments": [
                        text("Nozomi trains stop at the "),
                        gap("n34"),
                        text("."),
                    ]
                },
                {"segments": [text("Hikari stop more frequently.")]},
                {"segments": [text("Kodama trains stop at "), gap("n35"), text(".")]},
            ],
        },
    ],
}

SHINKANSEN_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["1964"], 1),
    ("n32", ["Fastest average speed", "The fastest average speed"], 3),
    ("n33", ["12 seconds", "Twelve seconds", "12 secs"], 2),
    ("n34", ["Most important stations", "The most important stations"], 3),
    ("n35", ["All stations", "All the stations", "Every station"], 3),
]

PART4_SENTENCES: list[dict] = [
    {
        "prompt": (
            "French TGV locomotives pull the TGV trains from both ends using a "
            "__________."
        ),
        "correct": [
            "Centralised power system",
            "Centralized power system",
            "Centralised power",
            "Centralized power",
        ],
        "max_words": 3,
    },
    {
        "prompt": (
            "Japanese ground is unsuitable for the TGV type of train because it is "
            "__________ and the tracks frequently curve horizontally and vertically."
        ),
        "correct": ["Flimsy"],
        "max_words": 3,
    },
    {
        "prompt": (
            "An extra advantage of the Japanese electric car system is that it can "
            "act as a __________."
        ),
        "correct": ["Brake"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Even after the power supply is cut off in the electric car system, "
            "electricity is still produced by __________."
        ),
        "correct": ["Magnetic induction"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Huge improvements in power, operability and safety administration have "
            "been made possible by advances in __________."
        ),
        "correct": ["Semiconductor technologies", "Semiconductor technology"],
        "max_words": 3,
    },
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
    ) -> QuestionGroup:
        if options_shared is not None:
            validate_compound_structure(question_type.value, options_shared)
        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=self.section.id,
            order=self.group_order,
            question_type=question_type.value,
            instruction=instruction,
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

    async def free_text(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[dict],
    ) -> None:
        group = await self._group(question_type, instruction)
        for item in items:
            self._add(
                group,
                question_type,
                {"prompt": item["prompt"], "max_words": item["max_words"]},
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
        "Write NO MORE THAN THREE WORDS OR A NUMBER for each answer.",
        FORM_STRUCTURE,
        FORM_ANSWERS,
    )
    await w.multi_select("Choose THREE letters, A-F.", MULTI_SELECT_ITEM)
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        PART1_SHORT_ANSWER,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 2
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "List FOUR reasons given for people needing blood transfusions.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        REASONS_STRUCTURE,
        REASONS_ANSWERS,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        BLOOD_TABLE_STRUCTURE,
        BLOOD_TABLE_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        DONATION_STRUCTURE,
        DONATION_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 3
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        LABS_STRUCTURE,
        LABS_ANSWERS,
    )
    await w.mcq("Choose the correct letter, A, B or C.", PART3_MCQ)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 4
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        SHINKANSEN_STRUCTURE,
        SHINKANSEN_ANSWERS,
    )
    await w.free_text(
        QuestionType.SENTENCE_COMPLETION,
        "Complete the sentences below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        PART4_SENTENCES,
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
