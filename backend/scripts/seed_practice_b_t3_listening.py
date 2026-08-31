"""Seed Practice Set B Test 3 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 3. Every key is taken from the
printed Answer Key (pp.175-176). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-10  form_completion     Council Youth Scheme funding form
Part 2  Q11-15 mcq               Darwin — visitors / culture / cycling / swimming
        Q16-20 matching_features places → attractions A-H
Part 3  Q21-23 sentence_completion  weather and mood research
        Q24-27 matching_features    writers → information A-F
        Q28-30 multi_select         three remaining decisions A-H
Part 4  Q31-32 multi_select      two education concerns A-F
        Q33-34 multi_select      two advantages of smaller classes A-F
        Q35-40 table_completion  USA class-size research projects

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t3_listening.py
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

TEST_NUMBER = 3


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 ───────────────────────────────────────────────────────────────────

FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "Council Youth Scheme — Application for Funding for Group Project",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "fields": [
        {"label": "Example Name", "type": "static", "value": "Ralph Pearson"},
        {
            "label": "Contact address",
            "type": "gap_line",
            "segments": [gap("g1"), text(", Drayton DR6 8AB")],
        },
        {"label": "Telephone number", "type": "static", "value": "01453 586098"},
        {
            "label": "Name of group",
            "type": "static",
            "value": "Community Youth Theatre Group",
        },
        {
            "label": "Description of group",
            "type": "gap_line",
            "segments": [
                text("amateur theatre group ("),
                gap("g2"),
                text(" members) involved in drama "),
                gap("g3"),
                text(" and ...................."),
            ],
        },
        {
            "label": "Amount of money requested",
            "type": "gap_line",
            "segments": [text("£"), gap("g4")],
        },
        {
            "label": "Description of project",
            "type": "gap_line",
            "segments": [
                text("to produce a short "),
                gap("g5"),
                text(" play for young children"),
            ],
        },
        {
            "label": "Money needed for",
            "type": "gap_line",
            "segments": [
                text("• "),
                gap("g6"),
                text(" for scenery"),
                text("\n• costumes"),
                text("\n• cost of "),
                gap("g7"),
                text("\n• "),
                gap("g8"),
                text("\n• sundries"),
            ],
        },
        {
            "label": "How source of funding will be credited",
            "type": "gap_line",
            "segments": [
                text("acknowledged in the "),
                gap("g9"),
                text(" given to audience"),
            ],
        },
        {
            "label": "Other organisations approached for funding (and outcome)",
            "type": "gap_line",
            "segments": [
                text("National Youth Services – money was "),
                gap("g10"),
            ],
        },
    ],
}

FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["230 South Road"], 3),
    ("g2", ["18"], 1),
    (
        "g3",
        [
            "activities and workshops",
            "activities & workshops",
            "activities workshops",
        ],
        3,
    ),
    ("g4", ["250", "£250", "250 pounds"], 2),
    ("g5", ["interactive"], 1),
    ("g6", ["material", "materials"], 1),
    ("g7", ["insurance"], 1),
    ("g8", ["publicity"], 1),
    ("g9", ["programme", "program"], 1),
    (
        "g10",
        ["not available", "unavailable"],
        2,
    ),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

PART2_MCQ: list[dict] = [
    {
        "question": "Joanne says that visitors to Darwin are often surprised by",
        "options": [
            "the number of young people.",
            "the casual atmosphere.",
            "the range of cultures.",
        ],
        "correct": "A",
    },
    {
        "question": "To enjoy cultural activities, the people of Darwin tend to",
        "options": [
            "travel to southern Australia.",
            "bring in artists from other areas.",
            "involve themselves in production.",
        ],
        "correct": "C",
    },
    {
        "question": "The Chinese temple in Darwin",
        "options": [
            "is no longer used for its original purpose.",
            "was rebuilt after its destruction in a storm.",
            "was demolished to make room for new buildings.",
        ],
        "correct": "B",
    },
    {
        "question": "The main problem with travelling by bicycle is",
        "options": [
            "the climate.",
            "the traffic.",
            "the hills.",
        ],
        "correct": "A",
    },
    {
        "question": "What does Joanne say about swimming in the sea?",
        "options": [
            "It is essential to wear a protective suit.",
            "Swimming is only safe during the winter.",
            "You should stay in certain restricted areas.",
        ],
        "correct": "C",
    },
]

DARWIN_OPTIONS = [
    "A. a flower market",
    "B. a chance to feed the fish",
    "C. good nightlife",
    "D. international arts and crafts",
    "E. good cheap international food",
    "F. a trip to catch fish",
    "G. shops and seafood restaurants",
    "H. a wide range of different plants",
]

DARWIN_ITEMS: list[tuple[str, str]] = [
    ("'Aquascene'", "B"),
    ("Smith Street Mall", "E"),
    ("Cullen Bay Marina", "G"),
    ("Fannie Bay", "H"),
    ("Mitchell Street", "C"),
]


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_SENTENCES: list[dict] = [
    {
        "prompt": (
            "Phil and Stella's goal is to ______ the hypothesis that weather "
            "has an effect on a person's mood."
        ),
        "correct": ["investigate"],
    },
    {
        "prompt": (
            "They expect to find that 'good' weather (weather which is ______) "
            "has a positive effect on a person's mood."
        ),
        "correct": [
            "sunny and warm",
            "sunny & warm",
            "warm and sunny",
            "warm & sunny",
        ],
    },
    {
        "prompt": (
            "Stella defines 'effect on mood' as a ______ in the way a person feels."
        ),
        "correct": ["change"],
    },
]

WRITER_OPTIONS = [
    "A. the benefits of moving to a warmer environment",
    "B. the type of weather with the worst effect on mood",
    "C. how past events affect attitudes to weather",
    "D. the important effect of stress on mood",
    "E. the important effect of hours of sunshine on mood",
    "F. psychological problems due to having to cope with bad weather",
]

WRITER_ITEMS: list[tuple[str, str]] = [
    ("Vickers", "F"),
    ("Whitebourne", "D"),
    ("Haverton", "C"),
    ("Stanfield", "B"),
]

PART3_MULTI = {
    "question": "Which THREE things do Phil and Stella still have to decide on?",
    "options": [
        "how to analyse their results",
        "their methods of presentation",
        "the design of their questionnaire",
        "the location of their survey",
        "weather variables to be measured",
        "the dates of their survey",
        "the size of their survey",
        "the source of data on weather variables",
    ],
    "correct": ["B", "F", "H"],
}


# ── Part 4 ───────────────────────────────────────────────────────────────────

PART4_MULTI_31 = {
    "question": (
        "Which two of the following problems are causing concern to educational "
        "authorities in the USA?"
    ),
    "options": [
        "differences between rich and poor students",
        "high numbers dropping out of education",
        "falling standards of students",
        "poor results compared with other nationalities",
        "low scores of overseas students",
        "differences between rural and urban students",
    ],
    "correct": ["A", "D"],
}

PART4_MULTI_33 = {
    "question": (
        "According to the speaker, what are two advantages of reducing class sizes?"
    ),
    "options": [
        "more employment for teachers",
        "improvement in general health of the population",
        "reduction in number of days taken off sick by teachers",
        "better use of existing buildings and resources",
        "better level of education of workforce",
        "availability of better qualified teachers",
    ],
    "correct": ["B", "E"],
}

TABLE4_STRUCTURE: dict = {
    "variant": "table",
    "title": "USA RESEARCH PROJECTS INTO CLASS SIZES",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "headers": [
        "State",
        "Schools involved",
        "Number of students participating",
        "Key findings",
        "Problems",
    ],
    "rows": [
        [
            {"variant": "plain", "segments": [text("Tennessee")]},
            {"variant": "plain", "segments": [text("about 70 schools")]},
            {
                "variant": "plain",
                "segments": [text("in total "), gap("t35")],
            },
            {
                "variant": "plain",
                "segments": [
                    text("significant benefit especially for "),
                    gap("t36"),
                    text(" pupils"),
                ],
            },
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("lack of agreement on implications of data")
                        ]
                    }
                ],
            },
        ],
        [
            {"variant": "plain", "segments": [text("California")]},
            {
                "variant": "plain",
                "segments": [gap("t37"), text(" schools")],
            },
            {"variant": "plain", "segments": [text("1.8 million")]},
            {"variant": "plain", "segments": [text("very little benefit")]},
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("shortage of "),
                            gap("t38"),
                            text(", especially in poorer areas"),
                        ]
                    },
                    {
                        "segments": [
                            text("no proper method for "),
                            gap("t39"),
                            text(" of project"),
                        ]
                    },
                ],
            },
        ],
        [
            {"variant": "plain", "segments": [text("Wisconsin")]},
            {
                "variant": "plain",
                "segments": [
                    text("14 schools (with pupils from "),
                    gap("t40"),
                    text(" families)"),
                ],
            },
            {"variant": "plain", "segments": [text("")]},
            {
                "variant": "plain",
                "segments": [text("similar results to Tennessee project")],
            },
            {"variant": "plain", "segments": [text("")]},
        ],
    ],
}

TABLE4_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "t35",
        ["12,000", "12000", "12 000", "twelve thousand"],
        2,
    ),
    ("t36", ["minority"], 1),
    ("t37", ["all"], 1),
    ("t38", ["teachers"], 1),
    (
        "t39",
        ["evaluation", "the evaluation"],
        2,
    ),
    ("t40", ["poor"], 1),
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
    await w.mcq("Choose the correct answer, A, B or C.", PART2_MCQ)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What can you find at each of the places below?\n"
        "Choose your answers from the box and write the correct letter A–H "
        "next to Questions 16–20.",
        DARWIN_OPTIONS,
        DARWIN_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.sentences(
        "Complete the sentences below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        PART3_SENTENCES,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What information was given by each writer?\n"
        "Choose your answers from the box and write the letters A–F next to "
        "Questions 24–27.",
        WRITER_OPTIONS,
        WRITER_ITEMS,
    )
    await w.multi_select("Choose THREE letters A–H.", PART3_MULTI)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.multi_select("Choose TWO letters A–F.", PART4_MULTI_31)
    await w.multi_select("Choose TWO letters A–F.", PART4_MULTI_33)
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
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
