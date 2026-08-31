"""Seed Practice Set B Test 4 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 4. Every key is taken from the
printed Answer Key (pp.178-179). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-6   table_completion     Budget accommodation in Queenstown
        Q7-10  matching_features    activities → who wants them A-C
Part 2  Q11-14 mcq                  CitiCyclist
        Q15-17 note_completion      three organisation types (any order)
        Q18-20 note_completion      contact / cost / course length
Part 3  Q21-23 short_answer         presentation strengths / weaknesses
        Q24-27 mcq                  class feedback (+ bar-chart image Q27)
        Q28-30 sentence_completion  tutor comments
Part 4  Q31-33 note_completion      WHO healthy city
        Q34-40 table_completion     Sri Lanka / Mali / Egypt projects

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t4_listening.py
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
from seed_practice_b_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 4
Q27_IMAGE_URL = f"/media/images/practice_b_t{TEST_NUMBER}_listening_q27.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

TABLE1_STRUCTURE: dict = {
    "variant": "table",
    "title": "Budget accommodation in Queenstown, New Zealand",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["Accommodation", "Price (dormitory)", "Comments"],
    "rows": [
        [
            cell(text("Travellers' Lodge")),
            cell(text("")),
            cell(text("Example: fully booked")),
        ],
        [
            cell(text("Bingley's")),
            cell(text("US$ "), gap("t1")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("in town centre")]},
                    {
                        "segments": [
                            text("café with regular "),
                            gap("t2"),
                            text(" nights"),
                        ]
                    },
                    {"segments": [text("sundeck")]},
                ],
            },
        ],
        [
            cell(text("Chalet Lodge")),
            cell(text("US$ 18.00")),
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("located in a "),
                            gap("t3"),
                            text(" alpine setting"),
                        ]
                    },
                    {"segments": [text("10 mins from town centre")]},
                    {
                        "segments": [
                            gap("t4"),
                            text(" are welcome"),
                        ]
                    },
                ],
            },
        ],
        [
            cell(text("Globetrotters")),
            cell(text("US$ 18.50")),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("in town centre")]},
                    {
                        "segments": [
                            gap("t5"),
                            text(" included"),
                        ]
                    },
                    {
                        "segments": [
                            text("chance to win a "),
                            gap("t6"),
                        ]
                    },
                ],
            },
        ],
    ],
}

TABLE1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t1", ["19.75", "19.75 dollars", "US$19.75", "$19.75"], 2),
    ("t2", ["theme"], 1),
    ("t3", ["quiet"], 1),
    ("t4", ["children"], 1),
    (
        "t5",
        ["breakfast", "breakfast is"],
        2,
    ),
    (
        "t6",
        [
            "free sky-dive",
            "free skydive",
            "free sky dive",
            "sky-dive",
            "skydive",
            "sky dive",
        ],
        3,
    ),
]

ACTIVITY_OPTIONS = [
    "A. only Jacinta",
    "B. only Lewis",
    "C. both Jacinta and Lewis",
]

ACTIVITY_ITEMS: list[tuple[str, str]] = [
    ("bungee jump", "A"),
    ("white-water rafting", "C"),
    ("jet-boat ride", "B"),
    ("trekking on wilderness trail", "C"),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_MCQ: list[dict] = [
    {
        "question": "Jack says that in London these days, many people",
        "options": [
            "see cycling as a foolish activity.",
            "have no experience of cycling.",
            "take too many risks when cycling.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "If people want to cycle to school or work, CitiCyclist helps them by"
        ),
        "options": [
            "giving cycling lessons on the route they take.",
            "advising them on the safest route to choose.",
            "teaching them basic skills on quiet roads first.",
        ],
        "correct": "A",
    },
    {
        "question": "Jack works with some advanced cyclists who want to develop",
        "options": [
            "international competitive riding skills.",
            "knowledge of advanced equipment.",
            "confidence in complex road systems.",
        ],
        "correct": "C",
    },
    {
        "question": "CitiCyclist supports the view that cyclists should",
        "options": [
            "have separate sections of the road from motor traffic.",
            "always wear protective clothing when cycling.",
            "know how to ride confidently on busy roads.",
        ],
        "correct": "C",
    },
]

# Paper: list three organisation types in any order. Same pool on each gap.
ORG_POOL = [
    "schools",
    "local councils",
    "companies",
]

ORGS_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Organisations CitiCyclist provides services for",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "The three answers may be given in any order.",
            "items": [{"segments": [gap(f"o{n}")]} for n in (15, 16, 17)],
        }
    ],
}

ORGS_ANSWERS: list[tuple[str, list[str], int]] = [
    (f"o{n}", ORG_POOL, 3) for n in (15, 16, 17)
]

NOTES2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "CitiCyclist",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("website address: citicyclist.co.uk")]},
                {"segments": [text("phone: "), gap("n18")]},
                {
                    "segments": [
                        text("cost (single person): "),
                        gap("n19"),
                        text(" per lesson"),
                    ]
                },
                {
                    "segments": [
                        text("usual length of course: "),
                        gap("n20"),
                        text(" (except complete beginners)"),
                    ]
                },
            ],
        }
    ],
}

NOTES2_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n18",
        [
            "020 7562 4028",
            "02075624028",
            "020-7562-4028",
        ],
        3,
    ),
    (
        "n19",
        ["£27.50", "27.50", "£27.50 pounds", "27.50 pounds"],
        2,
    ),
    (
        "n20",
        ["3 hours", "3 hrs", "three hours"],
        2,
    ),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_SHORT: list[dict] = [
    {
        "prompt": (
            "What do Sharon and Xiao Li agree was the strongest aspect of "
            "their presentation?"
        ),
        "correct": [
            "technique",
            "the technique",
            "their technique",
        ],
        "max_words": 3,
    },
    {
        "prompt": "Which part of their presentation was Xiao Li least happy with?",
        "correct": [
            "answering questions",
            "answering the questions",
            "questions",
            "the questions",
            "students' questions",
            "the students' questions",
            "answering students' questions",
        ],
        "max_words": 3,
    },
    {
        "prompt": (
            "Which section does Sharon feel they should have discussed in "
            "more depth?"
        ),
        "correct": [
            "solutions",
            "the solutions",
            "their solutions",
        ],
        "max_words": 3,
    },
]

PART3_MCQ: list[dict] = [
    {
        "question": "Sharon and Xiao Li were surprised when the class said",
        "options": [
            "they spoke too quickly.",
            "they included too much information.",
            "their talk was not well organised.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "The class gave Sharon and Xiao Li conflicting feedback on their"
        ),
        "options": [
            "timing.",
            "use of visuals.",
            "use of eye contact.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "The class thought that the presentation was different from the "
            "others because"
        ),
        "options": [
            "the analysis was more detailed.",
            "the data collection was more wide-ranging.",
            "the background reading was more extensive.",
        ],
        "correct": "B",
    },
    {
        "question": "Which bar chart represents the marks given by the tutor?",
        "options": ["A", "B", "C"],
        "correct": "C",
        "image_url": Q27_IMAGE_URL,
    },
]

PART3_SENTENCES: list[dict] = [
    {
        "prompt": (
            "The tutor says that the ______ of the presentation seemed "
            "rather sudden."
        ),
        "correct": ["end", "ending"],
    },
    {
        "prompt": (
            "The tutor praises the students' discussion of the ______ of "
            "their results."
        ),
        "correct": ["limitations"],
    },
    {
        "prompt": (
            "The tutor suggests that they could extend the ______ review in "
            "their report."
        ),
        "correct": ["literature"],
    },
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The World Health Organisation says a healthy city must",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("• have a "),
                        gap("n31"),
                        text(" environment"),
                    ]
                },
                {
                    "segments": [
                        text("• meet the "),
                        gap("n32"),
                        text(" of all its inhabitants"),
                    ]
                },
                {
                    "segments": [
                        text("• provide easily accessible health services")
                    ]
                },
                {
                    "segments": [
                        text("• encourage ordinary people to take part in "),
                        gap("n33"),
                    ]
                },
            ],
        }
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n31",
        [
            "clean and safe",
            "safe and clean",
            "clean safe",
            "safe clean",
        ],
        3,
    ),
    ("n32", ["basic needs"], 2),
    ("n33", ["local government"], 2),
]

TABLE4_STRUCTURE: dict = {
    "variant": "table",
    "title": "",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "headers": ["Place / Project", "Aim", "Method", "Achievement"],
    "rows": [
        [
            cell(text("Sri Lanka\nCommunity Contracts System")),
            cell(text("to upgrade squatter settlements")),
            cell(
                text("the "),
                gap("t34"),
                text(" constructed infrastructure, e.g. drains, paths"),
            ),
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("better housing and infrastructure")]},
                    {
                        "segments": [
                            text("provided better "),
                            gap("t35"),
                            text(" opportunities"),
                        ]
                    },
                ],
            },
        ],
        [
            cell(text("Mali\ncooperative")),
            cell(text("to improve sanitation in city")),
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            gap("t36"),
                            text(" graduates organising garbage collection"),
                        ]
                    },
                    {
                        "segments": [
                            text(
                                "public education campaign via "
                            ),
                            gap("t37"),
                            text(" and discussion groups"),
                        ]
                    },
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("greater environmental awareness")]},
                    {"segments": [text("improved living conditions")]},
                ],
            },
        ],
        [
            cell(text("Egypt (Mokattam)\n"), gap("t38")),
            cell(text("to support disadvantaged women")),
            cell(
                text("women provided with the "),
                gap("t39"),
                text(" and equipment for sewing and weaving"),
            ),
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("rise in the "),
                            gap("t40"),
                            text(" and quality of life of young women"),
                        ]
                    }
                ],
            },
        ],
    ],
}

TABLE4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t34", ["residents"], 1),
    ("t35", ["economic"], 1),
    ("t36", ["secondary school"], 2),
    ("t37", ["films"], 1),
    (
        "t38",
        ["Women's Centre", "Womens Centre", "Women's Center", "Womens Center"],
        2,
    ),
    ("t39", ["skills"], 1),
    ("t40", ["status"], 1),
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

    async def short_answer(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                {
                    "prompt": item["prompt"],
                    "question": item["prompt"],
                    "max_words": item["max_words"],
                },
                gap_answer_key(item["correct"], max_words=item["max_words"]),
            )

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
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
    ) -> None:
        shared: dict = {"options": options}
        if options_heading:
            shared["options_heading"] = options_heading
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
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        TABLE1_STRUCTURE,
        TABLE1_ANSWERS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Who wants to do each of the activities below?\n"
        "Write the correct letter, A, B or C, next to Questions 7–10.",
        ACTIVITY_OPTIONS,
        ACTIVITY_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the correct letter, A, B or C.", PART2_MCQ)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "List THREE types of organisations for which CitiCyclist provides "
        "services.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        ORGS_STRUCTURE,
        ORGS_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        NOTES2_STRUCTURE,
        NOTES2_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.short_answer(
        "Answer the questions below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        PART3_SHORT,
    )
    await w.mcq("Choose the correct letter, A, B or C.", PART3_MCQ)
    await w.sentences(
        "Complete the sentences below.\n"
        "Write ONE WORD ONLY for each answer.",
        PART3_SENTENCES,
        max_words=1,
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
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        TABLE4_STRUCTURE,
        TABLE4_ANSWERS,
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
