"""Seed Practice Set C Test 7 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 7. Every key is taken from the
printed Answer Key. Alternative spellings listed there (slash or bracket)
are accepted; nothing else is invented.

Part 1  Q1-10  note_completion       Notes for holiday
Part 2  Q11-16 mcq                   Camber's Theme Park
        Q17-20 matching_features     rides → special conditions A-F
Part 3  Q21-22 multi_select          listening in groups (TWO of A-E)
        Q23-24 multi_select          goal-setting (TWO of A-E)
        Q25-26 multi_select          conflict resolution (TWO of A-E)
        Q27-30 matching_features     preparation tasks → actions A-F
Part 4  Q31-40 note_completion       Engineering for sustainable development

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t7_listening.py
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

TEST_NUMBER = 7


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

NOTES1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Notes for holiday",
    "instruction_words": "TWO WORDS OR A NUMBER",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Travel information",
            "items": [
                {
                    "segments": [
                        text("must find out which "),
                        gap("n1"),
                    ]
                },
                {
                    "segments": [
                        text("best taxi company "),
                        gap("n2"),
                    ]
                },
                {
                    "segments": [
                        text("Note: Simon lives in the "),
                        gap("n3"),
                        text(" of the city"),
                    ]
                },
                {
                    "segments": [
                        text("Simon\u2019s cell phone number: "),
                        gap("n4"),
                    ]
                },
            ],
        },
        {
            "heading": "What to pack",
            "items": [
                {"segments": [text("(to wear)")]},
                {"segments": [text("casual clothes")]},
                {
                    "segments": [
                        text("one smart dress \u2014 to wear at a/the "),
                        gap("n5"),
                    ]
                },
                {
                    "segments": [
                        text("a good "),
                        gap("n6"),
                    ]
                },
                {
                    "segments": [
                        text("tough "),
                        gap("n7"),
                    ]
                },
                {"segments": [text("(to read)")]},
                {
                    "segments": [
                        text("try to find book named "),
                        gap("n8"),
                        text(" by Rex Campbell"),
                    ]
                },
            ],
        },
        {
            "heading": "Presents",
            "items": [
                {
                    "segments": [
                        text("for Janice: "),
                        gap("n9"),
                    ]
                },
                {
                    "segments": [
                        text("for Alec: "),
                        gap("n10"),
                        text(" (with racing pictures)"),
                    ]
                },
            ],
        },
    ],
}

NOTES1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n1", ["terminal"], 1),
    ("n2", ["Pantera"], 1),
    ("n3", ["east"], 1),
    ("n4", ["07765 328411", "07765328411"], 2),
    ("n5", ["hotel restaurant", "hotel (restaurant)"], 2),
    ("n6", ["raincoat"], 1),
    ("n7", ["walking shoes", "(walking) shoes", "shoes"], 2),
    ("n8", ["Mountain Lives"], 2),
    ("n9", ["chocolate", "chocolates", "chocolate(s)"], 1),
    ("n10", ["calendar", "a calendar", "(a) calendar"], 2),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_MCQ: list[dict] = [
    {
        "question": (
            "According to the speaker, in what way is Camber\u2019s "
            "different from other theme parks?"
        ),
        "options": [
            "It\u2019s suitable for different age groups.",
            "It offers lots to do in wet weather.",
            "It has a focus on education.",
        ],
        "correct": "C",
    },
    {
        "question": "The Park first opened in",
        "options": [
            "1980.",
            "1997.",
            "2004.",
        ],
        "correct": "B",
    },
    {
        "question": "What\u2019s included in the entrance fee?",
        "options": [
            "most rides and parking",
            "all rides and some exhibits",
            "parking and all rides",
        ],
        "correct": "A",
    },
    {
        "question": "Becoming a member of the Adventurers Club means",
        "options": [
            "you can avoid queuing so much.",
            "you can enter the Park free for a year.",
            "you can visit certain zones closed to other people.",
        ],
        "correct": "A",
    },
    {
        "question": "The Future Farm zone encourages visitors to",
        "options": [
            "buy animals as pets.",
            "learn about the care of animals.",
            "get close to the animals.",
        ],
        "correct": "C",
    },
    {
        "question": "When is hot food available in the park?",
        "options": [
            "10.00 a.m. \u2013 5.30 p.m.",
            "11.00 a.m. \u2013 5.00 p.m.",
            "10.30 a.m. \u2013 5.00 p.m.",
        ],
        "correct": "B",
    },
]

RIDE_OPTIONS = [
    "A. Must be over a certain age",
    "B. Must use special safety equipment",
    "C. Must avoid it if they have health problems",
    "D. Must wear a particular type of clothing",
    "E. Must be over a certain height",
    "F. Must be accompanied by an adult if under 16",
]

RIDE_ITEMS: list[tuple[str, str]] = [
    ("River Adventure", "F"),
    ("Jungle Jim Rollercoaster", "B"),
    ("Swoop Slide", "D"),
    ("Zip Go-carts", "E"),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_MULTI_21 = {
    "question": (
        "What TWO things do Brad and Helen agree to say about listening "
        "in groups?"
    ),
    "options": [
        "Listening skills are often overlooked in business training.",
        "Learning to listen well is a skill that\u2019s easy for most "
        "people to learn.",
        "It\u2019s sometimes acceptable to argue against speakers.",
        "Body language is very important when listening.",
        "Listeners should avoid interrupting speakers.",
    ],
    "correct": ["A", "D"],
}

PART3_MULTI_23 = {
    "question": (
        "What TWO things does the article say about goal-setting?"
    ),
    "options": [
        "Meetings should start with a clear statement of goals.",
        "It\u2019s important for each individual\u2019s goals to be "
        "explained.",
        "Everybody in the group should have the same goals.",
        "Goals should be a mix of the realistic and the ideal.",
        "Goals must always be achievable within a set time.",
    ],
    "correct": ["B", "E"],
}

PART3_MULTI_25 = {
    "question": (
        "What TWO things do Brad and Helen agree are weak points in "
        "the article\u2019s section on conflict resolution?"
    ),
    "options": [
        "It doesn\u2019t explore the topic in enough detail.",
        "It only discusses conservative views.",
        "It says nothing about the potential value of conflict.",
        "It talks too much about \u2018winners and losers\u2019.",
        "It doesn\u2019t provide definitions of key terms.",
    ],
    "correct": ["B", "C"],
}

ACTION_OPTIONS = [
    "A. Contact the tutor for clarification",
    "B. Check the assignment specifications",
    "C. Leave it until the last task",
    "D. Ask a course-mate to help",
    "E. Find information on the Internet",
    "F. Look through course handbooks",
]

ACTION_ITEMS: list[tuple[str, str]] = [
    ("Preparing the powerpoint", "C"),
    ("Using direct quotations", "B"),
    ("Creating a handout", "D"),
    ("Drawing up a bibliography", "F"),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

NOTES4_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Engineering for sustainable development",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "The Greenhouse Project (Himalayan mountain region)",
            "items": [
                {"segments": [text("Problem")]},
                {
                    "segments": [
                        text(
                            "Short growing season because of high "
                            "altitude and low "
                        ),
                        gap("n31"),
                    ]
                },
                {
                    "segments": [
                        text("Fresh vegetables imported by lorry or by "),
                        gap("n32"),
                        text(" \u2014 expensive"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Need to use sunlight to prevent local "
                            "plants from "
                        ),
                        gap("n33"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Previous programmes to provide greenhouses "
                            "were "
                        ),
                        gap("n34"),
                    ]
                },
            ],
        },
        {
            "heading": "New greenhouse",
            "items": [
                {"segments": [text("Meets criteria for sustainability")]},
                {
                    "segments": [
                        text("Simple and "),
                        gap("n35"),
                        text(" to build"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Made mainly from local materials "
                            "(mud or stone for the walls, wood and "
                        ),
                        gap("n36"),
                        text(" for the roof)"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Building and maintenance done by local "
                            "craftsmen"
                        )
                    ]
                },
                {
                    "segments": [
                        text("Runs solely on "),
                        gap("n37"),
                        text(" energy"),
                    ]
                },
                {
                    "segments": [
                        text("Only families who have a suitable "),
                        gap("n38"),
                        text(" can own one"),
                    ]
                },
            ],
        },
        {
            "heading": "Design",
            "items": [
                {"segments": [text("Long side faces south")]},
                {"segments": [text("Strong polythene cover")]},
                {
                    "segments": [
                        text("Inside, "),
                        gap("n39"),
                        text(" are painted black or white"),
                    ]
                },
            ],
        },
        {
            "heading": "Social benefits",
            "items": [
                {
                    "segments": [
                        text("Owners\u2019 status is improved")
                    ]
                },
                {
                    "segments": [
                        text("Rural "),
                        gap("n40"),
                        text(" have greater opportunities"),
                    ]
                },
                {"segments": [text("More children are educated")]},
            ],
        },
    ],
}

NOTES4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n31", ["rainfall"], 1),
    ("n32", ["airplane", "plane", "air plane"], 1),
    ("n33", ["freezing"], 1),
    ("n34", ["unsuccessful"], 1),
    ("n35", ["cheap", "inexpensive"], 1),
    ("n36", ["grass"], 1),
    ("n37", ["solar"], 1),
    ("n38", ["site", "location", "place"], 1),
    ("n39", ["walls"], 1),
    ("n40", ["women"], 1),
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
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS OR A NUMBER for each answer.",
        NOTES1_STRUCTURE,
        NOTES1_ANSWERS,
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
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What special conditions apply to the following rides?\n"
        "Choose FOUR answers from the box and write the correct letter, "
        "A\u2013F, next to questions 17\u201320.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        RIDE_OPTIONS,
        RIDE_ITEMS,
        options_heading="Special conditions for visitors",
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
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART3_MULTI_21,
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART3_MULTI_23,
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        PART3_MULTI_25,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What actions do Brad and Helen agree to do regarding the "
        "following preparation tasks?\n"
        "Choose FOUR answers from the box and write the correct letter, "
        "A\u2013F, next to the number.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        ACTION_OPTIONS,
        ACTION_ITEMS,
        options_heading="Action",
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
