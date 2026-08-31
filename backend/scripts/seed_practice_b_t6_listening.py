"""Seed Practice Set B Test 6 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 6. Every key is taken from the
printed Answer Key (pp.183-184). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-10  form_completion      abandoned vehicle report
Part 2  Q11-17 sentence_completion  John Manjiro
        Q18-20 map_labeling         Fairhaven walk (A-I)
Part 3  Q21-23 mcq                  Julia / fashion postgraduate course
        Q24-27 matching_features    university facilities → features A-G
        Q28-30 summary_completion   MA assessment
Part 4  Q31-40 note_completion      Laughter

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t6_listening.py
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
from seed_practice_b_common import (  # noqa: E402
    MAP_IMAGE_URL,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 6
MAP_URL = MAP_IMAGE_URL.format(test=TEST_NUMBER)


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 ───────────────────────────────────────────────────────────────────

FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "Report on abandoned vehicle",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "fields": [
        {"label": "Example Name of caller", "type": "static", "value": "Mrs Shefford"},
        {
            "label": "Address",
            "type": "gap_line",
            "segments": [
                text("41, "),
                gap("g1"),
                text(" / Barrowdale / WH4 5JP"),
            ],
        },
        {
            "label": "Telephone",
            "type": "gap_line",
            "segments": [gap("g2")],
        },
        {
            "label": "Vehicle location",
            "type": "gap_line",
            "segments": [
                text("in "),
                gap("g3"),
                text(" near main road (A69)"),
            ],
        },
        {
            "label": "Type of vehicle",
            "type": "gap_line",
            "segments": [gap("g4")],
        },
        {"label": "Make", "type": "static", "value": "Catala"},
        {
            "label": "Model",
            "type": "gap_line",
            "segments": [gap("g5")],
        },
        {
            "label": "Present colour of vehicle",
            "type": "gap_line",
            "segments": [gap("g6")],
        },
        {"label": "Vehicle number", "type": "static", "value": "S 322 GEC"},
        {
            "label": "General condition",
            "type": "gap_line",
            "segments": [
                text("poor – one "),
                gap("g7"),
                text(", cracked windscreen"),
            ],
        },
        {
            "label": "Length of time at site",
            "type": "gap_line",
            "segments": [gap("g8")],
        },
        {
            "label": "Land belongs to",
            "type": "gap_line",
            "segments": [gap("g9")],
        },
        {
            "label": "Last owner",
            "type": "static",
            "value": "no information available",
        },
        {
            "label": "Other notes",
            "type": "gap_line",
            "segments": [
                text("vehicle does not belong to a "),
                gap("g10"),
                text(" resident"),
            ],
        },
    ],
}

FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "g1",
        [
            "Lower Greene Street",
            "Lower Green Street",
            "Lower Greene St.",
            "Lower Green St.",
            "Lower Greene St",
            "Lower Green St",
            "Lower Green(e) Street",
            "Lower Green(e) St.",
        ],
        3,
    ),
    ("g2", ["01778 552387", "01778552387"], 2),
    ("g3", ["a field", "field"], 2),
    ("g4", ["a van", "van"], 2),
    ("g5", ["a Flyer 2000", "Flyer 2000"], 3),
    ("g6", ["blue"], 1),
    ("g7", ["flat tyre", "flat tire"], 2),
    ("g8", ["8 days", "eight days"], 2),
    ("g9", ["Hill Farm Estate"], 3),
    ("g10", ["local"], 1),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_SENTENCES: list[dict] = [
    {
        "prompt": (
            "Manjiro started work as a ______ when he was still a young boy."
        ),
        "correct": ["fisherman"],
    },
    {
        "prompt": (
            "He spent ______ on a deserted island before he was rescued."
        ),
        "correct": ["six months", "6 months"],
    },
    {
        "prompt": (
            "He became friends with William Whitfield, who was a ship's ______."
        ),
        "correct": ["captain"],
    },
    {
        "prompt": (
            "The cost of Manjiro's ______ in America was covered by the "
            "Whitfield family."
        ),
        "correct": ["education"],
    },
    {
        "prompt": (
            "Manjiro eventually returned to Japan, where he carried out "
            "important work as a teacher and ______."
        ),
        "correct": ["an interpreter", "interpreter"],
    },
    {
        "prompt": "Fairhaven and Tosashimizu are now officially ______.",
        "correct": ["sister cities"],
    },
    {
        "prompt": (
            "Every two years, the John Manjiro ______ is held in Fairhaven."
        ),
        "correct": ["Festival", "festival"],
    },
]

MAP_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

MAP_ITEMS: list[tuple[str, str]] = [
    ("Whitfield family house", "I"),
    ("Old Oxford School", "B"),
    ("School of Navigation", "E"),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_MCQ: list[dict] = [
    {
        "question": (
            "What is the main thing Julia feels she has gained from her "
            "experience in retail?"
        ),
        "options": [
            "better understanding of customer attitudes",
            "improved ability to predict fashion trends",
            "more skill in setting priorities in her work",
        ],
        "correct": "A",
    },
    {
        "question": "Why is Julia interested in doing the postgraduate course?",
        "options": [
            "It will enable her to develop new types of technology.",
            "It will allow her to specialise in a design area of her choice.",
            "It will provide managerial training focusing on her needs.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "What would Julia like to do after she has completed the "
            "postgraduate course?"
        ),
        "options": [
            "work overseas",
            "start her own business",
            "stay in an academic environment",
        ],
        "correct": "B",
    },
]

FACILITY_OPTIONS = [
    "A. laboratories",
    "B. rooms for individual study",
    "C. inter-disciplinary focus",
    "D. introductory course",
    "E. purpose-built premises",
    "F. cafeteria",
    "G. emphasis on creative use",
]

FACILITY_ITEMS: list[tuple[str, str]] = [
    ("Library", "D"),
    ("Computer Centre", "G"),
    ("Photomedia", "C"),
    ("Time Based Media", "E"),
]

SUMMARY3_STRUCTURE: dict = {
    "variant": "summary",
    "title": "MA in Fashion Design: Assessment",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "paragraphs": [
        {
            "segments": [
                text("Assessment includes three "),
                gap("s28"),
                text(
                    " which take place at the end of the stages of the degree. "
                    "Final assessment is based on a project, and includes the "
                    "student's "
                ),
                gap("s29"),
                text(
                    ", in the form of a written report, and the "
                ),
                gap("s30"),
                text(
                    ", to which representatives of fashion companies are invited."
                ),
            ]
        }
    ],
}

SUMMARY3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s28", ["progress reviews"], 2),
    ("s29", ["critical reflection", "reflection"], 2),
    ("s30", ["exhibition"], 1),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Laughter",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "The nature of laughter",
            "items": [
                {
                    "segments": [
                        text("laughter is a "),
                        gap("n31"),
                        text(" process – involves movement and sound"),
                    ]
                },
                {
                    "segments": [
                        text("it is controlled by our "),
                        gap("n32"),
                    ]
                },
            ],
        },
        {
            "heading": "Reasons for laughter",
            "items": [
                {
                    "segments": [
                        text(
                            "only 10% of laughter is caused by jokes / funny "
                            "stories"
                        )
                    ]
                },
                {
                    "segments": [
                        text("may have begun as sign of "),
                        gap("n33"),
                        text(" after a dangerous situation"),
                    ]
                },
                {
                    "segments": [
                        text("nowadays, may help to develop "),
                        gap("n34"),
                        text(" within a group"),
                    ]
                },
                {
                    "segments": [
                        text("connected to "),
                        gap("n35"),
                        text(
                            " (e.g. use of humour by politicians or bosses)"
                        ),
                    ]
                },
                {
                    "segments": [
                        text(
                            "may be related to male / female differences "
                            "(e.g. women laugh more at male speakers)"
                        )
                    ]
                },
                {
                    "segments": [
                        text("may be used in a "),
                        gap("n36"),
                        text(" way to keep someone out of a group"),
                    ]
                },
            ],
        },
        {
            "heading": "Benefits of laughter",
            "items": [
                {
                    "segments": [
                        text("safe method for the "),
                        gap("n37"),
                        text(
                            " of emotions such as anger and sadness"
                        ),
                    ]
                },
                {"segments": [text("provides good aerobic exercise")]},
                {
                    "segments": [
                        text("leads to drop in levels of stress-related "),
                        gap("n38"),
                    ]
                },
                {
                    "segments": [
                        text("improves the "),
                        gap("n39"),
                    ]
                },
                {
                    "segments": [
                        text("can stop "),
                        gap("n40"),
                        text(" and improve sleep"),
                    ]
                },
            ],
        },
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["physical"], 1),
    ("n32", ["instincts"], 1),
    ("n33", ["relief"], 1),
    ("n34", ["social bonds", "bonds"], 2),
    ("n35", ["power"], 1),
    ("n36", ["negative"], 1),
    ("n37", ["release"], 1),
    ("n38", ["hormones"], 1),
    ("n39", ["immune system"], 2),
    ("n40", ["bad dreams"], 2),
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

    async def sentences(
        self, instruction: str, items: list[dict], *, max_words: int
    ) -> None:
        group = await self._group(QuestionType.SENTENCE_COMPLETION, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.SENTENCE_COMPLETION,
                {"prompt": item["prompt"], "max_words": max_words},
                gap_answer_key(item["correct"], max_words=max_words),
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
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        FORM_STRUCTURE,
        FORM_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.sentences(
        "Complete the sentences below.\n"
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
        PART2_SENTENCES,
        max_words=2,
    )
    await w.map_labeling(
        "Label the map below.\n"
        "Write the correct letter A–I next to Questions 18–20.",
        MAP_OPTIONS,
        MAP_ITEMS,
        image_url=MAP_URL,
        subtitle="Fairhaven",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the best answer, A, B or C.", PART3_MCQ)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What does each university facility have?\n"
        "Choose your answers from the box and write the correct letter A–G "
        "next to Questions 24–27.",
        FACILITY_OPTIONS,
        FACILITY_ITEMS,
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

    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
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
