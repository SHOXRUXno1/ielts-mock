"""Seed Practice Set C Test 5 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 5. Every key is taken from the
printed Answer Key. Alternative spellings listed there (slash or bracket)
are accepted; nothing else is invented.

Part 1  Q1-2   note_completion       Advice on plumbers and decorators
        Q3-10  table_completion      plumber / plasterer comparison
Part 2  Q11-15 mcq                   Museum work placement
        Q16-20 map_labeling          Museum plan (A-I)
Part 3  Q21-26 matching_features     Company projects — tutor's opinion A-H
        Q27-28 multi_select          group assignment problems (TWO of A-E)
        Q29-30 multi_select          lecturer problems (TWO of A-E)
Part 4  Q31-40 note_completion       The Tawny Owl

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t5_listening.py
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

TEST_NUMBER = 5
MAP_URL = MAP_IMAGE_URL.format(test=TEST_NUMBER)


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

NOTES1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Advice on plumbers and decorators",
    "instruction_words": "ONE WORD",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("Make sure the company is: local")]},
                {
                    "segments": [
                        text("Don't call a plumber during the "),
                        gap("g1"),
                    ]
                },
                {
                    "segments": [
                        text("Look at trade website: www."),
                        gap("g2"),
                        text(".com"),
                    ]
                },
            ],
        },
    ],
}

NOTES1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["weekend", "weekends"], 1),
    ("g2", ["plasdeco"], 1),
]

TABLE1_STRUCTURE: dict = {
    "variant": "table",
    "title": "",
    "instruction_words": "ONE WORD",
    "max_words_per_gap": 1,
    "headers": ["Name", "Positive points", "Negative points"],
    "rows": [
        [
            cell(text("Peake's Plumbing")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("Pleasant and friendly")]},
                    {
                        "segments": [
                            text("Always gives "),
                            gap("t3"),
                            text(" information"),
                        ]
                    },
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("Tends to be "), gap("t4")]},
                ],
            },
        ],
        [
            cell(text("John Damerol\nPlumbing Services")),
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            gap("t5"),
                            text(" than other plumbers"),
                        ]
                    },
                    {"segments": [text("Reliable")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("Not very polite")]},
                    {"segments": [text("Tends to be "), gap("t6")]},
                ],
            },
        ],
        [
            cell(text("Simonson Plasterers")),
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("Able to do lots of different "),
                            gap("t7"),
                        ]
                    },
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("More "),
                            gap("t8"),
                            text(" than other companies"),
                        ]
                    },
                ],
            },
        ],
        [
            cell(text("H.L. Plastering")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("Reliable")]},
                    {"segments": [text("Also able to do "), gap("t9")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("Prefers not to use long "),
                            gap("t10"),
                        ]
                    },
                ],
            },
        ],
    ],
}

TABLE1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t3", ["clear"], 1),
    ("t4", ["late", "unreliable"], 1),
    ("t5", ["cheaper"], 1),
    ("t6", ["messy"], 1),
    ("t7", ["designs"], 1),
    ("t8", ["expensive"], 1),
    ("t9", ["painting"], 1),
    ("t10", ["ladder", "ladders"], 1),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_MCQ: list[dict] = [
    {
        "question": "On Monday, what will be the students' working day?",
        "options": [
            "9.00 a.m. \u2013 5.00 p.m.",
            "8.45 a.m. \u2013 5.00 p.m.",
            "9.00 a.m. \u2013 4.45 p.m.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "While working in the museum, students are encouraged to wear"
        ),
        "options": [
            "formal clothing such as a suit.",
            "a cap with the museum logo.",
            "their own casual clothes.",
        ],
        "correct": "C",
    },
    {
        "question": (
            "If students are ill or going to be late, they must inform"
        ),
        "options": [
            "the museum receptionist.",
            "their museum supervisor.",
            "their school placement tutor.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "The most popular task whilst on work placement is usually"
        ),
        "options": [
            "making presentations in local primary schools.",
            "talking to elderly people in care homes.",
            "conducting workshops in the museum.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "The best form of preparation before starting their work "
            "placement is to read"
        ),
        "options": [
            "the history of the museum on the website.",
            "the museum regulations and safety guidance.",
            "notes made by previous work placement students.",
        ],
        "correct": "C",
    },
]

MAP_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

MAP_ITEMS: list[tuple[str, str]] = [
    ("Sign-in office", "C"),
    ("Gallery 1", "I"),
    ("Keybox", "H"),
    ("Kitchen area", "D"),
    ("Staff noticeboard", "G"),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

OPINION_OPTIONS = [
    "A. It would be very rewarding for the student.",
    "B. It is too ambitious.",
    "C. It would be difficult to evaluate.",
    "D. It wouldn't be sufficiently challenging.",
    "E. It would involve extra costs.",
    "F. It is beyond the student's current ability.",
    "G. It is already being done by another student.",
    "H. It would probably have the greatest impact on the company.",
]

OPINION_ITEMS: list[tuple[str, str]] = [
    ("Customer database", "D"),
    ("Online sales catalogue", "B"),
    ("Payroll", "A"),
    ("Stock inventory", "H"),
    ("Internal security", "F"),
    ("Customer services", "E"),
]

PART3_MULTI_27 = {
    "question": (
        "Which TWO problems do Sam and the tutor identify concerning "
        "group assignments?"
    ),
    "options": [
        "Personal relationships.",
        "Cultural differences.",
        "Division of labour.",
        "Group leadership.",
        "Group size.",
    ],
    "correct": ["B", "E"],
}

PART3_MULTI_29 = {
    "question": (
        "Which TWO problems does Sam identify concerning the lecturers?"
    ),
    "options": [
        "Punctuality.",
        "Organisation.",
        "Accessibility.",
        "Helpfulness.",
        "Teaching materials.",
    ],
    "correct": ["A", "C"],
}


# ── Part 4 ───────────────────────────────────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The Tawny Owl",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Most "),
                        gap("n31"),
                        text(" owl species in UK"),
                    ]
                },
                {"segments": [text("Strongly nocturnal")]},
            ],
        },
        {
            "heading": "Habitat",
            "items": [
                {
                    "segments": [
                        text("Mainly lives in "),
                        gap("n32"),
                        text(
                            ", but can also be seen in urban areas, "
                            "e.g. parks"
                        ),
                    ]
                },
            ],
        },
        {
            "heading": "Adaptations",
            "items": [
                {
                    "segments": [
                        text("Short wings and "),
                        gap("n33"),
                        text(", for navigation"),
                    ]
                },
                {
                    "segments": [
                        text("Brown and "),
                        gap("n34"),
                        text(" feathers, for camouflage"),
                    ]
                },
                {
                    "segments": [
                        text("Large eyes (more effective than those of "),
                        gap("n35"),
                        text("), for good night vision"),
                    ]
                },
                {
                    "segments": [
                        text("Very good spatial "),
                        gap("n36"),
                        text(
                            ", for predicting where prey might be found"
                        ),
                    ]
                },
                {
                    "segments": [
                        text("Excellent "),
                        gap("n37"),
                        text(", for locating prey from a perch"),
                    ]
                },
            ],
        },
        {
            "heading": "Diet",
            "items": [
                {"segments": [text("Main food is small mammals")]},
                {
                    "segments": [
                        text("Owls in urban areas eat more "),
                        gap("n38"),
                    ]
                },
            ],
        },
        {
            "heading": "Survival",
            "items": [
                {
                    "segments": [
                        text("Two thirds of young owls die within a "),
                        gap("n39"),
                    ]
                },
                {
                    "segments": [
                        text("Owls don't disperse over long distances")
                    ]
                },
                {
                    "segments": [
                        text(
                            "Owls seem to dislike flying over large "
                            "areas of "
                        ),
                        gap("n40"),
                    ]
                },
            ],
        },
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["common"], 1),
    ("n32", ["woodland", "woodlands", "woods", "forest", "forests"], 1),
    ("n33", ["tail"], 1),
    ("n34", ["grey", "gray"], 1),
    ("n35", ["humans", "people"], 1),
    ("n36", ["memory"], 1),
    ("n37", ["hearing"], 1),
    ("n38", ["birds"], 1),
    ("n39", ["year"], 1),
    ("n40", ["water"], 1),
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

    # -- Part 1 --
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(
        f"\nPart 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN ONE WORD for each answer.",
        NOTES1_STRUCTURE,
        NOTES1_ANSWERS,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN ONE WORD for each answer.",
        TABLE1_STRUCTURE,
        TABLE1_ANSWERS,
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
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        PART2_MCQ,
    )
    await w.map_labeling(
        "Label the plan below.\n"
        "Write the correct letter, A\u2013I, next to questions 16\u201320.",
        MAP_OPTIONS,
        MAP_ITEMS,
        image_url=MAP_URL,
        subtitle="Museum Plan",
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
        "What is the tutor's opinion of the following company projects?\n"
        "Choose FIVE answers from the box and write the correct letter, "
        "A\u2013H, next to questions 21\u201326.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        OPINION_OPTIONS,
        OPINION_ITEMS,
        options_heading="Tutor's opinion",
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART3_MULTI_27,
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART3_MULTI_29,
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
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write ONE WORD ONLY for each answer.",
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
