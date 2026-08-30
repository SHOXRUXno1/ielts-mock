"""Seed Practice Set B Test 2 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 2. Every key is taken from the
printed Answer Key (p.170). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-3   mcq               renting a flat: Martin's occupation, etc.
        Q4-10  table_completion  details of two flats
Part 2  Q11-15 sentence_completion  the British Library — facts
        Q16-20 diagram_labeling     British Library floor plan
Part 3  Q21-25 mcq               Dave's project on work placement
        Q26-30 note_completion   Dr Green's notes on the project
Part 4  Q31-35 sentence_completion  bilingualism — lecture
        Q36-40 mcq                  Dr Bialystok's experiments

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t2_listening.py
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

TEST_NUMBER = 2


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


# ── Part 1 ───────────────────────────────────────────────────────────────────

PART1_MCQ: list[dict] = [
    {
        "question": "What is Martin's occupation?",
        "options": [
            "He works in a car factory.",
            "He works in a bank.",
            "He is a college student.",
        ],
        "correct": "B",
    },
    {
        "question": "The friends would prefer somewhere with",
        "options": [
            "four bedrooms.",
            "three bedrooms.",
            "two bathrooms.",
        ],
        "correct": "A",
    },
    {
        "question": "Phil would rather live in",
        "options": [
            "the east suburbs.",
            "the city centre.",
            "the west suburbs.",
        ],
        "correct": "C",
    },
]

TABLE1_STRUCTURE: dict = {
    "variant": "table",
    "title": "Details of flats available",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": ["Location", "Features", "Good (✓) and bad (✗) points"],
    "rows": [
        [
            {
                "variant": "plain",
                "segments": [
                    text("Bridge Street, near the "),
                    gap("t4"),
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("3 bedrooms")]},
                    {"segments": [text("very big living room")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("✓ £"), gap("t5"), text(" a month")]},
                    {"segments": [text("✓ transport links")]},
                    {"segments": [text("✗ no shower")]},
                    {"segments": [text("✗ could be "), gap("t6")]},
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [gap("t7")],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("4 bedrooms")]},
                    {"segments": [text("living room")]},
                    {"segments": [gap("t8")]},
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("✓ "), gap("t9"), text(" and well equipped")]},
                    {"segments": [text("✓ shower")]},
                    {"segments": [text("✓ will be "), gap("t10")]},
                    {"segments": [text("✗ £800 a month")]},
                ],
            },
        ],
    ],
}

TABLE1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t4", ["bus station"], 2),
    (
        "t5",
        ["450", "£450", "450 pounds", "four hundred and fifty pounds"],
        3,
    ),
    ("t6", ["noisy"], 1),
    ("t7", ["Hills Avenue"], 2),
    ("t8", ["dining room"], 2),
    ("t9", ["very modern", "modern"], 2),
    ("t10", ["quiet"], 1),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_SENTENCES: list[dict] = [
    {
        "prompt": "The reading rooms are only open for group visits on ______.",
        "correct": ["Sundays"],
    },
    {
        "prompt": "The library was officially opened in ______.",
        "correct": ["1998"],
    },
    {
        "prompt": "All the library rooms together cover ______ m².",
        "correct": [
            "100,000",
            "100000",
            "one hundred thousand",
            "a hundred thousand",
        ],
    },
    {
        "prompt": "The library is financed by the ______.",
        "correct": ["government"],
    },
    {
        "prompt": "The main function of the library is to provide resources for people doing ______.",
        "correct": ["research"],
    },
]

PLAN_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Plan of the British Library",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "image_url": MAP_IMAGE_URL.format(test=TEST_NUMBER),
    "sections": [
        {
            "heading": "Write the name of each numbered area on the plan above.",
            "items": [{"segments": [gap(f"m{n}")]} for n in (16, 17, 18, 19, 20)],
        }
    ],
}

PLAN_ANSWERS: list[tuple[str, list[str], int]] = [
    ("m16", ["Conference Centre", "Conference Center"], 2),
    ("m17", ["Information Desk"], 2),
    ("m18", ["bookshop"], 1),
    ("m19", ["King's Library", "Kings Library"], 2),
    ("m20", ["stamp display"], 2),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_MCQ: list[dict] = [
    {
        "question": "The main aim of Dave's project is to",
        "options": [
            "describe a policy.",
            "investigate an assumption.",
            "identify a problem.",
        ],
        "correct": "B",
    },
    {
        "question": "Dave's project is based on schemes in",
        "options": [
            "schools.",
            "colleges.",
            "universities.",
        ],
        "correct": "C",
    },
    {
        "question": "How many academic organisations returned Dave's questionnaire?",
        "options": ["15", "50", "150"],
        "correct": "A",
    },
    {
        "question": "Dave wanted his questionnaires to be completed by company",
        "options": [
            "Human Resources Managers.",
            "Line Managers.",
            "owners.",
        ],
        "correct": "B",
    },
    {
        "question": "Dr Green wants Dave to provide a full list of",
        "options": [
            "respondents.",
            "appendices.",
            "companies.",
        ],
        "correct": "A",
    },
]

NOTES3_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Notes on project",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Introduction",
            "items": [
                {
                    "segments": [
                        text("improve the "),
                        gap("n26"),
                        text(" of ideas"),
                    ]
                },
                {
                    "segments": [
                        text("include a "),
                        gap("n27"),
                        text(" of 'Work Placement'"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "have separate sections for literature survey and research "
                        ),
                        gap("n28"),
                        text(" and methods"),
                    ]
                },
            ],
        },
        {
            "heading": "Findings",
            "items": [
                {"segments": [text("Preparation stage – add summary")]},
                {
                    "segments": [
                        gap("n29"),
                        text(" development – good"),
                    ]
                },
                {
                    "segments": [
                        text("Constraints on learning – provide better links to the "),
                        gap("n30"),
                        text(" from research"),
                    ]
                },
            ],
        },
    ],
}

NOTES3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n26", ["organisation", "organization"], 1),
    ("n27", ["definition"], 1),
    ("n28", ["aims"], 1),
    ("n29", ["Key Skills", "key skills"], 2),
    ("n30", ["evidence"], 1),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

PART4_SENTENCES: list[dict] = [
    {
        "prompt": "Bilingualism can be defined as having an equal level of communicative ______ in two or more languages.",
        "correct": ["proficiency"],
    },
    {
        "prompt": "Early research suggested that bilingualism caused problems with ______ and mental development.",
        "correct": ["learning"],
    },
    {
        "prompt": "Early research into bilingualism is now rejected because it did not consider the ______ backgrounds of the children.",
        "correct": [
            "social and economic",
            "social economic",
            "economic and social",
        ],
    },
    {
        "prompt": "It is now thought that there is a ______ relationship between bilingualism and cognitive skills in children.",
        "correct": ["positive"],
    },
    {
        "prompt": "Research done by Ellen Bialystok in Canada now suggests that the effects of bilingualism also apply to ______.",
        "correct": ["adults"],
    },
]

PART4_MCQ: list[dict] = [
    {
        "question": "In Dr Bialystok's experiment, the subjects had to react according to",
        "options": [
            "the colour of the square on the screen.",
            "the location of the square on the screen.",
            "the location of the shift key on the keyboard.",
        ],
        "correct": "A",
    },
    {
        "question": "The experiment demonstrated the 'Simon effect' because it involved a conflict between",
        "options": [
            "seeing something and reacting to it.",
            "producing fast and slow reactions.",
            "demonstrating awareness of shape and colour.",
        ],
        "correct": "A",
    },
    {
        "question": "The experiment shows that, compared with the monolingual subjects, the bilingual subjects",
        "options": [
            "were more intelligent.",
            "had faster reaction times overall.",
            "had more problems with the 'Simon effect'.",
        ],
        "correct": "B",
    },
    {
        "question": "The results of the experiment indicate that bilingual people may be better at",
        "options": [
            "doing different types of tasks at the same time.",
            "thinking about several things at once.",
            "focusing only on what is needed to do a task.",
        ],
        "correct": "C",
    },
    {
        "question": "Dr Bialystok's first and second experiments both suggest that bilingualism may",
        "options": [
            "slow down the effects of old age on the brain.",
            "lead to mental confusion among old people.",
            "help old people to stay in better physical condition.",
        ],
        "correct": "A",
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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        PART1_MCQ,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        TABLE1_STRUCTURE,
        TABLE1_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.sentences(
        "Complete the sentences below.\nWrite NO MORE THAN THREE WORDS for each answer.",
        PART2_SENTENCES,
        max_words=3,
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the plan below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        PLAN_STRUCTURE,
        PLAN_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq(
        "Choose the correct answer, A, B or C.",
        PART3_MCQ,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        NOTES3_STRUCTURE,
        NOTES3_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.sentences(
        "Complete the sentences below.\nWrite NO MORE THAN THREE WORDS for each answer.",
        PART4_SENTENCES,
        max_words=3,
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
