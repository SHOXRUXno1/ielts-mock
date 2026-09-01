"""Seed Practice Set C Test 6 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 6. Every key is taken from the
printed Answer Key. Alternative spellings listed there (slash or bracket)
are accepted; nothing else is invented.

Part 1  Q1-10  table_completion      Holiday rentals
Part 2  Q11-14 mcq                   DIY painting / Community RePaint
        Q15-16 multi_select          advice about paint (TWO of A-E)
        Q17-18 multi_select          advice about preparation (TWO of A-E)
        Q19-20 multi_select          advice about painting (TWO of A-E)
Part 3  Q21-26 mcq                   Student work placement
        Q27-30 matching_features     books → opinions A-F
Part 4  Q31-40 note_completion       Origin of medieval manuscripts

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t6_listening.py
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


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

TABLE1_STRUCTURE: dict = {
    "variant": "table",
    "title": "HOLIDAY RENTALS",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 1,
    "headers": [
        "Name of Property",
        "Location",
        "Features",
        "Disadvantage(s)",
        "Booking details",
    ],
    "rows": [
        [
            cell(gap("t1")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("rural")]},
                    {"segments": [text("surrounded by "), gap("t2")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("apartment")]},
                    {"segments": [text("two bedrooms")]},
                    {"segments": [text("open plan")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("distance from "), gap("t3")]},
                ],
            },
            cell(text("")),
        ],
        [
            cell(text("Kingfisher")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("rural")]},
                    {"segments": [text("next to the "), gap("t5")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("house")]},
                    {"segments": [text("three bedrooms")]},
                    {"segments": [text("has "), gap("t4")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("no "), gap("t6"), text(" room")]},
                ],
            },
            cell(
                text("Phone the owner\n(01752 669218)")
            ),
        ],
        [
            cell(text("Sunnybanks")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("in a village")]},
                    {"segments": [text("next to the "), gap("t7")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("house")]},
                    {"segments": [text("has private "), gap("t8")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("no "), gap("t9")]},
                ],
            },
            cell(
                text("Contact the "),
                gap("t10"),
            ),
        ],
    ],
}

TABLE1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t1", ["Moonfleet"], 1),
    ("t2", ["fields"], 1),
    ("t3", ["shops"], 1),
    ("t4", ["summerhouses"], 1),
    ("t5", ["river"], 1),
    ("t6", ["dining"], 1),
    ("t7", ["sea"], 1),
    ("t8", ["garden"], 1),
    ("t9", ["parking"], 1),
    ("t10", ["agent"], 1),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_MCQ: list[dict] = [
    {
        "question": (
            "According to the speaker, why is it a good time for "
            "D-I-Y painting?"
        ),
        "options": [
            "There are better products available now.",
            "Materials cost less than they used to.",
            "People have more free time than before.",
        ],
        "correct": "A",
    },
    {
        "question": "What happened in 2009 in the UK?",
        "options": [
            "A record volume of paint was sold.",
            "A large amount of paint was wasted.",
            "There was a major project to repaint public buildings.",
        ],
        "correct": "B",
    },
    {
        "question": "What does the speaker say about paint quantity?",
        "options": [
            "It\u2019s not necessary to have exact room measurements.",
            "It\u2019s better to overestimate than to underestimate.",
            "An automatic calculator can be downloaded from the Internet.",
        ],
        "correct": "C",
    },
    {
        "question": "What does Community RePaint do?",
        "options": [
            "It paints people\u2019s houses without payment.",
            "It collects unwanted paint and gives it away.",
            "It sells unused paint and donates the money to charity.",
        ],
        "correct": "B",
    },
]

PART2_MULTI_15 = {
    "question": (
        "What TWO pieces of advice does the speaker give about paint?"
    ),
    "options": [
        "Don\u2019t buy expensive paint.",
        "Test the colour before buying a lot.",
        "Choose a light colour.",
        "Use water-based paint.",
        "Buy enough paint for more than one application.",
    ],
    "correct": ["B", "D"],
}

PART2_MULTI_17 = {
    "question": (
        "What TWO pieces of advice does the speaker give about preparation?"
    ),
    "options": [
        "Replace any loose plaster.",
        "Don\u2019t spend too long preparing surfaces.",
        "Use decorators\u2019 soap to remove grease from walls.",
        "Wash dirty walls with warm water.",
        "Paint over cracks and small holes.",
    ],
    "correct": ["A", "C"],
}

PART2_MULTI_19 = {
    "question": (
        "What TWO pieces of advice does the speaker give about painting?"
    ),
    "options": [
        "Put a heater in the room.",
        "Wash brushes in cold water.",
        "Use a roller with a short pile.",
        "Apply paint directly from the tin.",
        "Open doors and windows.",
    ],
    "correct": ["B", "E"],
}


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_MCQ: list[dict] = [
    {
        "question": (
            "Why is Matthew considering a student work placement?"
        ),
        "options": [
            "He was informed about an interesting vacancy.",
            "He needs some extra income.",
            "He wants to try out a career option.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "Which part of the application process did Linda find "
            "most interesting?"
        ),
        "options": [
            "The psychometric test.",
            "The group activity.",
            "The individual task.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "During her work placement, Linda helped find ways to"
        ),
        "options": [
            "speed up car assembly.",
            "process waste materials.",
            "calculate the cost of design faults.",
        ],
        "correct": "A",
    },
    {
        "question": "Why did Linda find her work placement tiring?",
        "options": [
            "She wasn\u2019t used to full-time work.",
            "The working hours were very long.",
            "She felt she had to prove her worth.",
        ],
        "correct": "C",
    },
    {
        "question": (
            "What did Linda\u2019s employers give her formal feedback on?"
        ),
        "options": [
            "engineering ability",
            "organisational skills",
            "team working",
        ],
        "correct": "B",
    },
    {
        "question": (
            "What was the main benefit of Linda\u2019s work placement?"
        ),
        "options": [
            "Improved academic skills.",
            "An offer of work.",
            "The opportunity to use new software.",
        ],
        "correct": "B",
    },
]

OPINION_OPTIONS = [
    "A. helpful illustrations",
    "B. easy to understand",
    "C. up-to-date",
    "D. comprehensive",
    "E. specialised",
    "F. useful case studies",
]

OPINION_ITEMS: list[tuple[str, str]] = [
    ("The Science of Materials", "B"),
    ("Materials Engineering", "A"),
    ("Engineering Basics", "D"),
    ("Evolution of Materials", "C"),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Researching the origin of medieval manuscripts",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Background",
            "items": [
                {
                    "segments": [
                        text(
                            "Medieval manuscripts \u2014 handwritten books "
                            "produced between the fifth and fifteenth centuries"
                        )
                    ]
                },
                {
                    "segments": [
                        text(
                            "Origin of many manuscripts unknown until 2009; "
                            "scientists started using DNA testing"
                        )
                    ]
                },
            ],
        },
        {
            "heading": "Animal hides \u2014 two types",
            "items": [
                {
                    "segments": [
                        text(
                            "Parchment \u2014 sheep skin: white in colour "
                            "and "
                        ),
                        gap("n31"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Greasy \u2014 writing can\u2019t be erased so "
                            "often used for "
                        ),
                        gap("n32"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Vellum \u2014 calf skin: most popular for "
                            "prestigious work because you can get "
                        ),
                        gap("n33"),
                        text(" lettering"),
                    ]
                },
            ],
        },
        {
            "heading": "Preparation of hides",
            "items": [
                {
                    "segments": [
                        text(
                            "Treated in barrels of lime \u2014 where this "
                            "was not available, skins were "
                        ),
                        gap("n34"),
                    ]
                },
                {"segments": [text("Stretched tight on a frame")]},
                {
                    "segments": [
                        text("Scraped to create same "),
                        gap("n35"),
                    ]
                },
                {
                    "segments": [
                        text("Vellum was "),
                        gap("n36"),
                    ]
                },
            ],
        },
        {
            "heading": "Genetic testing \u2014 finding origins",
            "items": [
                {
                    "segments": [
                        text(
                            "Previously \u2014 analysed handwriting and "
                        ),
                        gap("n37"),
                        text(" used by the writer"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Now \u2014 using genetic data from \u2018known "
                            "manuscripts\u2019 to create a "
                        ),
                        gap("n38"),
                    ]
                },
            ],
        },
        {
            "heading": "Uses of new data",
            "items": [
                {
                    "segments": [
                        text("Gives information on individual books")
                    ]
                },
                {
                    "segments": [
                        text("Shows the "),
                        gap("n39"),
                        text(" of the book industry"),
                    ]
                },
                {
                    "segments": [
                        text("Helps define "),
                        gap("n40"),
                        text(" in medieval period"),
                    ]
                },
            ],
        },
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["(very) thin", "very thin", "thin"], 2),
    ("n32", ["court documents"], 2),
    ("n33", ["high-quality", "high quality"], 2),
    ("n34", ["buried"], 1),
    ("n35", ["thickness"], 1),
    ("n36", ["bleached", "whitened", "bleached/whitened"], 1),
    ("n37", ["dialect"], 1),
    ("n38", ["baseline"], 1),
    ("n39", ["evolution"], 1),
    ("n40", ["trade routes"], 2),
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
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write ONE WORD AND/OR A NUMBER for each answer.",
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
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART2_MULTI_15,
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART2_MULTI_17,
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART2_MULTI_19,
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
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        PART3_MCQ,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What does Linda think about the books on Matthew\u2019s reading "
        "list?\n"
        "Choose FOUR answers from the box and write the correct letter, "
        "A\u2013F, next to questions 27\u201330.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        OPINION_OPTIONS,
        OPINION_ITEMS,
        options_heading="Opinions",
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
