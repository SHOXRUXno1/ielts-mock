"""Seed Practice Set B Test 1 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 1. Every key is taken from the
printed Answer Key (p.167). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-9   note_completion   enquiry about bookcases
        Q10    mcq               which map is 41 Oak Rise
Part 2  Q11-13 summary           charity art sale
        Q14-20 table             four artists
Part 3  Q21-25 matching          project instructions A/B/C
        Q26-30 notes             other requirements + assessment
Part 4  Q31-33 mcq               extremophiles
        Q34-40 sentence          how they survive

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t1_listening.py
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

TEST_NUMBER = 1


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

NOTES1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "ENQUIRY ABOUT BOOKCASES",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "Example",
            "items": [
                {
                    "segments": [
                        text("Number of bookcases available: two"),
                    ]
                },
            ],
        },
        {
            "heading": "Both bookcases",
            "items": [
                {"segments": [text("Width: "), gap("n1")]},
                {"segments": [text("Made of: "), gap("n2")]},
            ],
        },
        {
            "heading": "First bookcase",
            "items": [
                {"segments": [text("Cost: "), gap("n3")]},
                {"segments": [text("Colour: "), gap("n4")]},
                {
                    "segments": [
                        text("Number of shelves: six (four are "),
                        gap("n5"),
                        text(")"),
                    ]
                },
            ],
        },
        {
            "heading": "Second bookcase",
            "items": [
                {"segments": [text("Colour: dark brown")]},
                {"segments": [text("Other features:")]},
                {"segments": [text("almost 80 years old")]},
                {
                    "segments": [
                        text("has a "),
                        gap("n6"),
                        text(" at the bottom"),
                    ]
                },
                {"segments": [text("has glass "), gap("n7")]},
                {"segments": [text("Cost: "), gap("n8")]},
            ],
        },
        {
            "heading": "Details of seller",
            "items": [
                {"segments": [text("Name: Mrs "), gap("n9")]},
                {"segments": [text("Address: 41 Oak Rise, Stanton.")]},
            ],
        },
    ],
}

NOTES1_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n1",
        ["75 cm", "75cm", "75 cms", "75 centimetres", "75 centimeters"],
        3,
    ),
    ("n2", ["wood"], 1),
    (
        "n3",
        ["£15.00", "£15", "15.00", "15 pounds", "fifteen pounds", "£15.00 pounds"],
        3,
    ),
    ("n4", ["cream"], 1),
    ("n5", ["adjustable"], 1),
    ("n6", ["cupboard"], 1),
    ("n7", ["doors"], 1),
    (
        "n8",
        [
            "£95.00",
            "£95",
            "95.00",
            "95 pounds",
            "ninety-five pounds",
            "ninety five pounds",
        ],
        3,
    ),
    ("n9", ["Blake"], 1),
]

Q10 = {
    "question": "Which map shows the correct location of the seller's house?",
    "options": ["A", "B", "C"],
    "correct": "B",
    "image_url": MAP_IMAGE_URL.format(test=TEST_NUMBER),
}


# ── Part 2 ───────────────────────────────────────────────────────────────────

SUMMARY2_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Charity Art Sale",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "paragraphs": [
        {
            "segments": [
                text("The paintings will be displayed in the Star Gallery and in a nearby "),
                gap("s11"),
                text(". The sale of pictures will begin at "),
                gap("s12"),
                text(" on Thursday, and there will be refreshments beforehand. The money raised will all be used to help "),
                gap("s13"),
                text(" children in New Zealand and other countries."),
            ]
        }
    ],
}

SUMMARY2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s11", ["café", "cafe"], 1),
    (
        "s12",
        [
            "7.30",
            "7.30pm",
            "7.30 pm",
            "7.30 p.m.",
            "7.30p.m.",
            "seven thirty",
            "half past seven",
        ],
        3,
    ),
    ("s13", ["disabled", "the disabled"], 2),
]

TABLE2_STRUCTURE: dict = {
    "variant": "table",
    "title": "",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["Artist", "Personal information", "Type of painting"],
    "rows": [
        [
            cell(text("Don Studley")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("daughter is recovering from a problem with her back")]},
                    {"segments": [text("self-taught artist")]},
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    text("pictures of the "),
                    gap("t14"),
                    text(" of New Zealand"),
                ],
            },
        ],
        [
            cell(text("James Chang")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("originally from Taiwan")]},
                    {
                        "segments": [
                            text("had a number of "),
                            gap("t15"),
                            text(" there"),
                        ]
                    },
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [gap("t16"), text(" paintings")]},
                    {"segments": [text("strong colours")]},
                ],
            },
        ],
        [
            cell(text("Natalie Stevens")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("has shown pictures in many countries")]},
                    {
                        "segments": [
                            text("is an artist and a website "),
                            gap("t17"),
                        ]
                    },
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("soft colours, various media")]},
                    {"segments": [text("mainly does "), gap("t18")]},
                ],
            },
        ],
        [
            cell(text("Christine Shin")),
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("lived in New Zealand for "),
                            gap("t19"),
                        ]
                    },
                    {"segments": [text("Korean")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("paintings are based on "),
                            gap("t20"),
                        ]
                    },
                    {"segments": [text("watercolours of New Zealand landscapes")]},
                ],
            },
        ],
    ],
}

TABLE2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t14", ["birds"], 1),
    ("t15", ["art exhibitions", "exhibitions"], 2),
    ("t16", ["abstract"], 1),
    ("t17", ["designer"], 1),
    ("t18", ["portraits"], 1),
    (
        "t19",
        ["two years", "2 years", "2 yrs", "two yrs", "2yrs"],
        2,
    ),
    ("t20", ["photographs", "photos"], 1),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

PROJECT_OPTIONS = [
    "they must do this",
    "they can do this if they want to",
    "they can't do this",
]

PROJECT_ITEMS: list[tuple[str, str]] = [
    ("Choose a writer from a list provided.", "A"),
    ("Get biographical information from the Internet.", "C"),
    ("Study a collection of poems.", "B"),
    ("Make a one-hour video.", "C"),
    ("Refer to key facts in the writer's life.", "B"),
]

NOTES3_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Other requirements for the project",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text(
                            "extract chosen from the author's work must reflect the "
                        ),
                        gap("n26"),
                        text(" of the author."),
                    ]
                },
                {
                    "segments": [
                        text("students must find sound effects and "),
                        gap("n27"),
                        text(" to match the texts they choose."),
                    ]
                },
                {
                    "segments": [
                        text("students must use a "),
                        gap("n28"),
                        text(" of computer software programs to make the video."),
                    ]
                },
                {
                    "segments": [
                        text("students must include information about the "),
                        gap("n29"),
                        text(" of all material"),
                    ]
                },
            ],
        },
        {
            "heading": "Criteria for assessment",
            "items": [
                {"segments": [text("completion of all components – 25%")]},
                {
                    "segments": [
                        gap("n30"),
                        text(" (must represent essence of author's work) – 50%"),
                    ]
                },
                {"segments": [text("artistic and technical design of video – 25%")]},
            ],
        },
    ],
}

NOTES3_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n26",
        ["interests and style", "style and interests", "interests style"],
        3,
    ),
    ("n27", ["visuals"], 1),
    ("n28", ["range"], 1),
    ("n29", ["source", "sources"], 1),
    ("n30", ["content"], 1),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

PART4_MCQ: list[dict] = [
    {
        "question": "'Extremophiles' are life forms that can live in",
        "options": [
            "isolated areas.",
            "hostile conditions.",
            "new habitats.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "The researchers think that some of the organisms they found "
            "in Antarctica are"
        ),
        "options": [
            "new species.",
            "ancient colonies.",
            "types of insects.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "The researchers were the first people to find life forms "
            "in Antarctica"
        ),
        "options": [
            "in the soil.",
            "under the rock surface.",
            "on the rocks.",
        ],
        "correct": "A",
    },
]

PART4_SENTENCES: list[dict] = [
    {
        "prompt": "Access to the sun's heat can create a ______ for some organisms.",
        "correct": ["microclimate"],
    },
    {
        "prompt": "The deeper the soil, the higher the ______ of salt.",
        "correct": ["concentration"],
    },
    {
        "prompt": (
            "Salt can protect organisms against the effects of ______, "
            "even at very low temperatures."
        ),
        "correct": ["frost"],
    },
    {
        "prompt": "All living things must have access to ______ water.",
        "correct": ["liquid"],
    },
    {
        "prompt": (
            "Salt plays a part in the process of ______, which prevents freezing."
        ),
        "correct": ["supercooling"],
    },
    {
        "prompt": (
            "The environment of ______ is similar to the dry valleys of Antarctica."
        ),
        "correct": ["Mars"],
    },
    {
        "prompt": (
            "This research may provide evidence of the existence of "
            "extraterrestrial life forms and their possible ______ on other planets."
        ),
        "correct": ["locations"],
    },
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

    async def mcq(
        self,
        instruction: str,
        items: list[dict],
        *,
        subtitle: str | None = None,
    ) -> None:
        group = await self._group(QuestionType.MCQ, instruction, subtitle=subtitle)
        for item in items:
            content = {"question": item["question"], "options": item["options"]}
            if item.get("image_url"):
                content["image_url"] = item["image_url"]
            self._add(
                group,
                QuestionType.MCQ,
                content,
                {"correct": item["correct"]},
                image_url=item.get("image_url"),
            )

    async def lettered(
        self,
        question_type: QuestionType,
        instruction: str,
        options: list[str],
        items: list[tuple[str, str]],
        *,
        options_heading: str | None = None,
        questions_heading: str | None = None,
    ) -> None:
        shared: dict = {"options": options}
        if options_heading:
            shared["options_heading"] = options_heading
        if questions_heading:
            shared["questions_heading"] = questions_heading
        group = await self._group(question_type, instruction, options_shared=shared)
        for question, correct in items:
            self._add(
                group, question_type, {"question": question}, {"correct": correct}
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        NOTES1_STRUCTURE,
        NOTES1_ANSWERS,
    )
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        [Q10],
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        SUMMARY2_STRUCTURE,
        SUMMARY2_ANSWERS,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        TABLE2_STRUCTURE,
        TABLE2_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What instructions were the students given about their project?\n"
        "Write the correct letter, A, B or C next to Questions 21-25.",
        PROJECT_OPTIONS,
        PROJECT_ITEMS,
        questions_heading="What instructions were the students given about their project?",
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        NOTES3_STRUCTURE,
        NOTES3_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the correct answer, A, B or C.", PART4_MCQ)
    await w.sentences(
        "Complete the sentences below.\nWrite ONE WORD for each answer.",
        PART4_SENTENCES,
        max_words=1,
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
