"""Seed Practice Set B Test 5 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 5. Every key is taken from the
printed Answer Key (p.181). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-7   mcq                  library volunteer interview
        Q8-10  multi_select         three volunteer requirements A-G
Part 2  Q11-14 sentence_completion  Canadian Clean Air Day
        Q15-20 note_completion      Reducing Air Pollution
Part 3  Q21-30 note_completion      Field Trip to Kenya
Part 4  Q31-34 flow_chart_completion Research methodology
        Q35-40 mcq                  supermarket website (+ pie charts Q35-36)

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t5_listening.py
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

TEST_NUMBER = 5
Q35_IMAGE_URL = f"/media/images/practice_b_t{TEST_NUMBER}_listening_q35.png"
Q36_IMAGE_URL = f"/media/images/practice_b_t{TEST_NUMBER}_listening_q36.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 ───────────────────────────────────────────────────────────────────

PART1_MCQ: list[dict] = [
    {
        "question": "The librarian says that training always includes",
        "options": [
            "computer skills.",
            "basic medical skills.",
            "interpersonal skills.",
        ],
        "correct": "B",
    },
    {
        "question": "All library service volunteers have to",
        "options": [
            "record their arrival and departure.",
            "stay within 'staff only' sections.",
            "wear a uniform.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "The woman would be entitled to a contribution towards the cost of"
        ),
        "options": [
            "transport by minibus.",
            "parking at the library.",
            "public transport.",
        ],
        "correct": "C",
    },
    {
        "question": "One recent library project involved",
        "options": [
            "labelling historical objects.",
            "protecting historical photographs.",
            "cataloguing historical documents.",
        ],
        "correct": "B",
    },
    {
        "question": "At present, the library is looking for people to",
        "options": [
            "record books onto CD.",
            "tell stories to children.",
            "read books to the blind.",
        ],
        "correct": "A",
    },
    {
        "question": "The woman says she is interested in a project involving",
        "options": [
            "taking library books to people in hospital.",
            "delivering library books to people at home.",
            "driving the disabled to the library.",
        ],
        "correct": "A",
    },
    {
        "question": "The woman agrees to work for",
        "options": [
            "two hours per week.",
            "four hours per week.",
            "six hours per week.",
        ],
        "correct": "B",
    },
]

PART1_MULTI = {
    "question": "Which THREE of the following must be provided by all volunteers?",
    "options": [
        "civil conviction check",
        "signed copy of commitment",
        "certificates to indicate qualifications",
        "emergency contact information",
        "date of birth",
        "signature of parent or guardian",
        "referees",
    ],
    "correct": ["B", "D", "G"],
}


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_SENTENCES: list[dict] = [
    {
        "prompt": "'Canadian Clean Air Day' will be held on ______.",
        "correct": [
            "June 6th",
            "June 6",
            "6th June",
            "6 June",
            "June the 6th",
        ],
    },
    {
        "prompt": (
            "Air pollution may be responsible for ______ deaths every year "
            "in Canada."
        ),
        "correct": ["5,000", "5000", "5 000"],
    },
    {
        "prompt": (
            "The sector most responsible for smog-producing pollutants is ______."
        ),
        "correct": ["transportation", "transport"],
    },
    {
        "prompt": (
            "Scientists now know that even ______ of pollutants can be harmful."
        ),
        "correct": ["low levels", "low level"],
    },
]

NOTES2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Reducing Air Pollution",
    "instruction_words": "NO MORE THAN TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Individual action",
            "items": [
                {
                    "segments": [
                        text("respond to the "),
                        gap("n15"),
                        text(" 'Challenge'"),
                    ]
                },
                {"segments": [text("walk, cycle or car-pool to work")]},
                {"segments": [text("use public transit")]},
                {"segments": [gap("n16")]},
                {
                    "segments": [
                        gap("n17"),
                        text(" your domestic equipment"),
                    ]
                },
            ],
        },
        {
            "heading": "Government action",
            "items": [
                {
                    "segments": [
                        text("emission reduction in the "),
                        gap("n18"),
                        text(" region of US and Canada"),
                    ]
                },
                {
                    "segments": [
                        text("move towards "),
                        gap("n19"),
                        text(" (e.g. less sulphur in gasoline & diesel)"),
                    ]
                },
                {
                    "segments": [
                        text("reduction of pollutants from "),
                        gap("n20"),
                        text(" and power plants"),
                    ]
                },
            ],
        },
    ],
}

NOTES2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n15", ["Commuter", "commuter"], 1),
    ("n16", ["plant trees", "planting trees"], 2),
    ("n17", ["upgrade"], 1),
    ("n18", ["border"], 1),
    (
        "n19",
        [
            "cleaner fuels",
            "clean fuels",
            "clean(er) fuels",
        ],
        2,
    ),
    ("n20", ["factories"], 1),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

NOTES3_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Field Trip to Kenya",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Area of country: the "),
                        gap("n21"),
                        text(" of Kenya"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Accommodation: Marich Pass Field Studies Centre"
                        )
                    ]
                },
                {
                    "segments": [
                        text("in traditional 'bandas' (bring mosquito "),
                        gap("n22"),
                        text(")"),
                    ]
                },
                {
                    "segments": [
                        text("study areas: "),
                        gap("n23"),
                        text(", lecture room, outdoor areas"),
                    ]
                },
                {
                    "segments": [
                        text("Type of environment: both "),
                        gap("n24"),
                        text(" and semi-arid plains"),
                    ]
                },
            ],
        },
        {
            "heading": "Activities",
            "items": [
                {"segments": [text("interviews (with interpreters)")]},
                {
                    "segments": [
                        gap("n25"),
                        text(" (environment and culture)"),
                    ]
                },
                {"segments": [text("morphological mapping")]},
                {
                    "segments": [
                        text("projects (all connected with "),
                        gap("n26"),
                        text(" issues)"),
                    ]
                },
            ],
        },
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Jack's group did project on: "),
                        gap("n27"),
                        text(" supply and quality issues"),
                    ]
                },
            ],
        },
        {
            "heading": "Expeditions",
            "items": [
                {
                    "segments": [
                        text("to Sigor (a "),
                        gap("n28"),
                        text(") to study distribution"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "to the Wei Wei valley to study agricultural "
                            "production"
                        )
                    ]
                },
                {
                    "segments": [
                        text("to a "),
                        gap("n29"),
                    ]
                },
            ],
        },
        {
            "heading": "Evaluation",
            "items": [
                {"segments": [text("logistics – well run")]},
                {"segments": [text("gave insight into lives of others")]},
                {
                    "segments": [
                        text("provided input for his "),
                        gap("n30"),
                    ]
                },
            ],
        },
    ],
}

NOTES3_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n21",
        [
            "north-west",
            "northwest",
            "north west",
            "north(-)west",
        ],
        2,
    ),
    ("n22", ["spray"], 1),
    (
        "n23",
        [
            "a small library",
            "small library",
            "a library",
            "library",
        ],
        3,
    ),
    ("n24", ["mountains"], 1),
    ("n25", ["field observation"], 2),
    ("n26", ["development"], 1),
    ("n27", ["water"], 1),
    ("n28", ["market town"], 2),
    ("n29", ["national park"], 2),
    ("n30", ["dissertation"], 1),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

FLOW4_STRUCTURE: dict = {
    "variant": "flow",
    "title": "Research methodology",
    "instruction_words": "ONE WORD",
    "max_words_per_gap": 1,
    "steps": [
        {
            "segments": [
                text(
                    "Discussion with supermarket department manager to decide "
                    "on the store's "
                ),
                gap("f31"),
                text(" for the website"),
            ]
        },
        {
            "segments": [
                text("Decision to investigate website use as a "),
                gap("f32"),
                text(" way for customers to communicate problems"),
            ]
        },
        {
            "segments": [
                text(
                    "Design of questionnaire to identify customers' "
                    "experiences and "
                ),
                gap("f33"),
                text(" to problems"),
            ]
        },
        {
            "segments": [
                text("Data collected from "),
                gap("f34"),
                text(
                    " with customers in four branches of the supermarket"
                ),
            ]
        },
        {"segments": [text("Analysis of responses")]},
    ],
}

FLOW4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("f31", ["requirements"], 1),
    ("f32", ["private"], 1),
    ("f33", ["attitudes"], 1),
    ("f34", ["interviews"], 1),
]

PART4_MCQ: list[dict] = [
    {
        "question": (
            "Which pie chart shows the percentage of respondents who "
            "experienced a problem in the supermarket?"
        ),
        "options": ["A", "B", "C"],
        "correct": "B",
        "image_url": Q35_IMAGE_URL,
    },
    {
        "question": (
            "Which pie chart shows the reasons why customers failed to report "
            "the problem directly to supermarket staff?"
        ),
        "options": ["A", "B", "C"],
        "correct": "C",
        "image_url": Q36_IMAGE_URL,
    },
    {
        "question": (
            "How might the student's website help the supermarket, according "
            "to the manager?"
        ),
        "options": [
            "It would support the expansion of the company.",
            "It would allow the identification of problem areas.",
            "It would make the company appear more professional.",
        ],
        "correct": "B",
    },
    {
        "question": "The student says one problem is that some customers",
        "options": [
            "do not have computer skills.",
            "do not have their own computer.",
            "do not have access to a computer.",
        ],
        "correct": "B",
    },
    {
        "question": "Further observation of website use is necessary because of",
        "options": [
            "the small size of the sample.",
            "the need to evaluate the objectives.",
            "the unrepresentative nature of the respondents.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "One positive result of the website for the supermarket staff "
            "could be"
        ),
        "options": [
            "greater support from management.",
            "less chance of unfair complaints.",
            "greater cooperation between staff.",
        ],
        "correct": "C",
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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the correct letter, A, B or C.", PART1_MCQ)
    await w.multi_select("Choose THREE letters A–G.", PART1_MULTI)
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
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
        NOTES2_STRUCTURE,
        NOTES2_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
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
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Write ONE WORD for each answer.",
        FLOW4_STRUCTURE,
        FLOW4_ANSWERS,
    )
    await w.mcq("Choose the correct letter, A, B or C.", PART4_MCQ)
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
