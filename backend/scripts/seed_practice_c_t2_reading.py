"""Seed Practice Set C Test 2 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 2. Keys from the printed
Answer Key (pp.176-177). Teaching strategy pages are omitted.

Passage 1  Q1-5   flow_chart_completion history of sports science
           Q6-13  true_false_ng
Passage 2  Q14-20 matching_headings     paragraphs A-G
           Q21-22 multi_select          micro-turbine statements
           Q23-26 sentence_completion
Passage 3  Q27-28 mcq
           Q29-32 matching_features     sentence endings A-F
           Q33-38 yes_no_ng
           Q39-40 mcq

Passage text lives in scripts/data/practice_c_t2/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t2_reading.py
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
    read_passage,
)

TEST_NUMBER = 2


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_FLOW_STRUCTURE: dict = {
    "variant": "flow",
    "title": "The history of sports and physical science in Australia",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "steps": [
        {
            "segments": [
                text("A lot of people identified as being "),
                gap("f1"),
            ]
        },
        {
            "segments": [
                text("Introduction of PE to "),
                gap("f2"),
            ]
        },
        {
            "segments": [
                text("Special training programmes for "),
                gap("f3"),
            ]
        },
        {
            "segments": [
                gap("f4"),
                text(" of PE graduates"),
            ]
        },
        {
            "segments": [
                text("Identification of alternative "),
                gap("f5"),
            ]
        },
        {"segments": [text("Diversification of course delivery")]},
    ],
}

P1_FLOW_ANSWERS: list[tuple[str, list[str]]] = [
    ("f1", ["unfit"]),
    ("f2", ["schools"]),
    ("f3", ["PE teachers"]),
    ("f4", ["surplus"]),
    ("f5", ["employment opportunities", "careers", "routes"]),
]

P1_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "Sport is generally regarded as a profitable area for investment.",
        "True",
    ),
    (
        "Rupert Murdoch has a personal as well as a business interest in sport.",
        "Not Given",
    ),
    (
        "The range of career opportunities available to sport graduates is "
        "increasing.",
        "True",
    ),
    (
        "The interests of business and the interests of universities are linked.",
        "True",
    ),
    (
        "Governments have been focusing too much attention on preventative "
        "medicine.",
        "False",
    ),
    (
        "It is inevitable that government priorities for health spending "
        "will change.",
        "True",
    ),
    (
        "Existing degree courses are unsuitable for careers in community "
        "health.",
        "False",
    ),
    (
        "Funding for sport science and related degrees has been increased "
        "considerably.",
        "Not Given",
    ),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_HEADINGS = [
    "i. A better use for large sums of money.",
    "ii. The environmental costs of manufacture and installation.",
    "iii. Estimates of the number of micro-turbines in use.",
    "iv. The environmental benefits of running a micro-turbine.",
    "v. The size and output of the largest type of micro-turbine.",
    "vi. A limited case for subsidising micro-turbines.",
    "vii. Recent improvements in the design of micro-turbines.",
    "viii. An indirect method of reducing carbon emissions.",
    "ix. The financial benefits of running a micro-turbine.",
]

P2_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "v"),
    ("Paragraph B", "ii"),
    ("Paragraph C", "iv"),
    ("Paragraph D", "ix"),
    ("Paragraph E", "i"),
    ("Paragraph F", "vi"),
    ("Paragraph G", "viii"),
]

P2_MULTI = {
    "question": (
        "The list below contains some possible statements about micro "
        "wind-turbines.\n"
        "Which TWO of these statements are made by the writer of the passage?"
    ),
    "options": [
        "In certain areas, permission is required to install them.",
        "Their exact energy output depends on their position.",
        "They probably take less energy to make than other engines.",
        "The UK government contributes towards their purchase cost.",
        "They can produce more energy than a household needs.",
    ],
    "correct": ["B", "E"],
}

P2_SENTENCES: list[dict] = [
    {
        "prompt": (
            "______ would be a more effective target for government "
            "investment than micro-turbines."
        ),
        "correct": ["offshore wind farms"],
    },
    {
        "prompt": (
            "An indirect benefit of subsidising micro-turbines is the "
            "support it provides for ______."
        ),
        "correct": ["developing technology"],
    },
    {
        "prompt": "Most spending has a ______ effect on the environment.",
        "correct": ["negative"],
    },
    {
        "prompt": (
            "If people buy a micro-turbine, they have less money to spend "
            "on things like foreign holidays and ______."
        ),
        "correct": ["cars"],
    },
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_MCQ_EARLY: list[tuple[str, list[str], str]] = [
    (
        "What does the writer say about items of pottery excavated at Akrotiri?",
        [
            "There was very little duplication.",
            "They would have met a big variety of needs.",
            "Most of them had been imported from other places.",
            "The intended purpose of each piece was unclear.",
        ],
        "B",
    ),
    (
        "The assumption that pottery from Akrotiri was produced by specialists "
        "is partly based on",
        [
            "the discovery of kilns.",
            "the central location of workshops.",
            "the sophistication of decorative patterns.",
            "the wide range of shapes represented.",
        ],
        "D",
    ),
]

P3_ENDING_OPTIONS = [
    "A. the discovery of a collection of metal discs.",
    "B. the size and type of the sailing ships in use.",
    "C. variations in the exact shape and thickness of similar containers.",
    "D. the physical characteristics of workmen.",
    "E. marks found on wine containers.",
    "F. the variety of commodities for which they would have been used.",
]

P3_ENDING_ITEMS: list[tuple[str, str]] = [
    (
        "The assumption that standard units of weight were in use could be "
        "based on",
        "A",
    ),
    (
        "Evidence of the use of standard units of volume is provided by",
        "E",
    ),
    (
        "The size of certain types of containers would have been restricted by",
        "D",
    ),
    (
        "Attempts to identify the intended capacity of containers are "
        "complicated by",
        "C",
    ),
]

P3_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "There are plans to excavate new areas of the archaeological site "
        "in the near future.",
        "Not Given",
    ),
    (
        "Some of the evidence concerning pottery production in ancient "
        "Akrotiri comes from written records.",
        "No",
    ),
    (
        "Pots for transporting liquids would have held no more than about "
        "20 litres.",
        "Yes",
    ),
    (
        "It would have been hard for merchants to calculate how much wine "
        "was on their ships.",
        "No",
    ),
    (
        "The capacity of containers intended to hold the same amounts "
        "differed by up to 20 percent.",
        "Yes",
    ),
    (
        "Regular trading of goods around the Aegean would have led to the "
        "general standardisation of quantities.",
        "Yes",
    ),
]

P3_MCQ_LATE: list[tuple[str, list[str], str]] = [
    (
        "What does the writer say about the standardisation of container sizes?",
        [
            "Containers which looked the same from the outside often varied "
            "in capacity.",
            "The instruments used to control container size were unreliable.",
            "The unsystematic use of different types of clay resulted in "
            "size variations.",
            "Potters usually discarded containers which were of a "
            "non-standard size.",
        ],
        "A",
    ),
    (
        "What is probably the main purpose of Reading Passage 3?",
        [
            "To evaluate the quality of pottery containers found in "
            "prehistoric Akrotiri.",
            "To suggest how features of pottery production at Akrotiri "
            "reflected other developments in the region.",
            "To outline the development of pottery-making skills in "
            "ancient Greece.",
            "To describe methods for storing and transporting household "
            "goods in prehistoric societies.",
        ],
        "B",
    ),
]


# ── writing helpers ──────────────────────────────────────────────────────────


class PassageWriter:
    def __init__(self, db: AsyncSession, section: Section) -> None:
        self.db = db
        self.section = section
        self.order = 1
        self.group_order = 1
        self.count = 0
        self.slots = 0

    async def _group(
        self,
        question_type: QuestionType,
        instruction: str,
        *,
        options_shared: dict | None = None,
    ) -> QuestionGroup:
        if options_shared is not None and "variant" in options_shared:
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
    ) -> None:
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
        self.count += 1
        self.slots += scoring_slots_for_question(question)

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

    async def statements(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[tuple[str, str]],
    ) -> None:
        group = await self._group(question_type, instruction)
        for statement, correct in items:
            self._add(
                group, question_type, {"statement": statement}, {"correct": correct}
            )

    async def mcq(
        self, instruction: str, items: list[tuple[str, list[str], str]]
    ) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for question, options, correct in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": question, "options": options},
                {"correct": correct},
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

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str]]],
        *,
        max_words: int = 2,
    ) -> None:
        group = await self._group(
            question_type, instruction, options_shared=structure
        )
        for gap_id, variants in answers:
            self._add(
                group,
                question_type,
                {"gap_id": gap_id},
                gap_answer_key(variants, max_words=max_words),
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    counts: list[int] = []
    slots: list[int] = []

    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = f"Passage 1 — {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 1 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Choose NO MORE THAN TWO WORDS from the passage for each answer.",
        P1_FLOW_STRUCTURE,
        P1_FLOW_ANSWERS,
        max_words=2,
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information given in "
        "Reading Passage 1?\n"
        "Write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P1_TFNG_ITEMS,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 — {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 2 has SEVEN paragraphs, A–G.\n"
        "Choose the correct heading for each paragraph from the list of "
        "headings below.\n"
        "Write the correct number, i–ix.",
        P2_HEADINGS,
        P2_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.multi_select("Choose TWO letters, A–E.", P2_MULTI)
    await w.sentences(
        "Complete the sentences below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each answer.",
        P2_SENTENCES,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = f"Passage 3 — {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 3 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P3_MCQ_EARLY,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending, A–F, below.\n"
        f"Write the correct letter, A–F.\n{SCREEN_LETTER_HINT}",
        P3_ENDING_OPTIONS,
        P3_ENDING_ITEMS,
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer in "
        "Reading Passage 3?\n"
        "Write\n"
        "YES if the statement agrees with the views of the writer\n"
        "NO if the statement contradicts the views of the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P3_YNNG_ITEMS,
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P3_MCQ_LATE,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    total_slots = sum(slots)
    if total_slots != 40:
        raise SystemExit(
            f"expected 40 reading scoring slots, got {total_slots} "
            f"(question rows {counts})"
        )

    await db.commit()
    print(
        f"\nDone. Reading seeded: rows {counts} / slots {slots} = {total_slots}."
    )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
