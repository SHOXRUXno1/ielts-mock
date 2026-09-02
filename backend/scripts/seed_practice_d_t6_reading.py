"""Seed Practice Set D Test 6 Reading, all three passages (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 6.
Keys from the printed Answer Key (pp.232-237). Tip strips omitted.

Passage 1  Q1-2   mcq                   Management books A-D
           Q3-7   matching_information  paragraphs A-H
           Q8-13  matching_features     books A-E
Passage 2  Q14-18 matching_headings     Stadium Australia A-E, headings i-x
           Q19-22 true_false_ng         Stadium design statements
           Q23-26 diagram_labeling      Stadium Australia diagram
Passage 3  Q27-29 multi_select          Shopping study problems (THREE of A-F)
           Q30-37 yes_no_ng             Shopping theory statements
           Q38-40 short_answer          Sentence completion (THREE WORDS)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t6_reading.py
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
from seed_practice_d_common import (  # noqa: E402
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 6
DIAGRAM_IMAGE_URL = f"/media/images/practice_d_t{TEST_NUMBER}_reading_diagram.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 — How to run a… (Management books) ────────────────────────────

P1_MCQ: list[dict] = [
    {
        "question": (
            "What does the writer say about the increase in the "
            "number of management books published?"
        ),
        "options": [
            "A. It took the publishing industry by surprise.",
            "B. It is likely to continue.",
            "C. It has produced more profit than other areas of "
            "publishing.",
            "D. It could have been foreseen.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "What does the writer say about the genre of "
            "management books?"
        ),
        "options": [
            "A. It includes some books that cover topics of "
            "little relevance to anyone.",
            "B. It contains a greater proportion of practical "
            "than theoretical books.",
            "C. All sorts of people have felt that they should "
            "be represented in it.",
            "D. The best books in the genre are written by "
            "business people.",
        ],
        "correct": "C",
    },
]

P1_INFO_ITEMS: list[tuple[str, str]] = [
    ("reasons for the deserved success of some books", "H"),
    ("reasons why managers need advice", "E"),
    (
        "a belief that management books are highly likely to "
        "be very poor",
        "D",
    ),
    ("a reference to books not considered worth reviewing", "C"),
    (
        "an example of a group of people who write particularly "
        "poor books",
        "G",
    ),
]

P1_BOOK_OPTIONS = [
    "A. Guide to the Management Gurus",
    "B. The Leader\u2019s Edge",
    "C. The Next Big Idea",
    "D. In Search of Excellence",
    "E. Reengineering the Corporation",
]

P1_BOOK_ITEMS: list[tuple[str, str]] = [
    ("It examines the success of books in the genre.", "C"),
    (
        "Statements made in it were later proved incorrect.",
        "D",
    ),
    ("It fails to live up to claims made about it.", "B"),
    (
        "Advice given in it is seen to be actually harmful.",
        "E",
    ),
    (
        "It examines the theories of those who have developed "
        "management thinking.",
        "A",
    ),
    ("It states the obvious in an unappealing way.", "B"),
]


# ── Passage 2 — Stadium Australia ────────────────────────────────────────────

HEADING_OPTIONS = [
    "i. A strange combination",
    "ii. An overall requirement",
    "iii. A controversial decision",
    "iv. A strong contrast",
    "v. A special set-up",
    "vi. A promising beginning",
    "vii. A shift in attitudes",
    "viii. A strongly held belief",
    "ix. A change of plan",
    "x. A simple choice",
]

HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "viii"),
    ("Paragraph B", "iv"),
    ("Paragraph C", "vi"),
    ("Paragraph D", "v"),
    ("Paragraph E", "ii"),
]

P2_TFNG: list[tuple[str, str]] = [
    (
        "The public have been demanding a better quality of "
        "stadium design.",
        "Not Given",
    ),
    (
        "It is possible that stadium design has an effect on "
        "people\u2019s behaviour in life in general.",
        "True",
    ),
    (
        "Some stadiums have come in for a lot more criticism "
        "than others.",
        "Not Given",
    ),
    (
        "Designers of previous Olympic stadiums could easily "
        "have produced far better designs.",
        "False",
    ),
]

# Q23-26: diagram labels from passage paragraph E.
# 23 = natural lighting (public areas), 24 = mechanical air-conditioning,
# 25 = storm water (toilet flushing), 26 = pitch irrigation (rainwater).
# Q26 evidence: paragraph E "Rainwater collected from the roof ran off into
# storage tanks, where it could be tapped for pitch irrigation."
P2_DIAGRAM_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Stadium Australia",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "image_url": DIAGRAM_IMAGE_URL,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("(23)  "), gap("d23")]},
                {"segments": [text("(24)  "), gap("d24")]},
                {"segments": [text("(25)  "), gap("d25")]},
                {"segments": [text("(26)  "), gap("d26")]},
            ],
        },
    ],
}

P2_DIAGRAM_ANSWERS: list[tuple[str, list[str]]] = [
    ("d23", ["natural lighting"]),
    ("d24", [
        "mechanical air-conditioning",
        "mechanical air conditioning",
    ]),
    ("d25", ["storm water", "stormwater"]),
    ("d26", ["pitch irrigation"]),
]


# ── Passage 3 — A Theory of Shopping ─────────────────────────────────────────

P3_MULTI: dict = {
    "question": (
        "Which THREE of the following are problems the writer "
        "encountered when conducting his study?"
    ),
    "options": [
        "uncertainty as to what the focus of the study should be",
        "the difficulty of finding enough households to make the "
        "study worthwhile",
        "the diverse nature of the population of the area",
        "the reluctance of people to share information about "
        "their personal habits",
        "the fact that he was unable to study some people\u2019s "
        "habits as much as others",
        "people dropping out of the study after initially "
        "agreeing to take part",
    ],
    "correct": ["C", "D", "E"],
}

P3_YESNO: list[tuple[str, str]] = [
    (
        "Anthropological relativism is more widely applied than "
        "anthropological generalisation.",
        "Not Given",
    ),
    (
        "Shopping lends itself to analysis based on "
        "anthropological generalisation.",
        "Yes",
    ),
    ("Generalisations about shopping are possible.", "Yes"),
    (
        "The conclusions drawn from this study will confirm "
        "some of the findings of other research.",
        "No",
    ),
    (
        "Shopping should be regarded as a basically unselfish "
        "activity.",
        "Yes",
    ),
    (
        "People sometimes analyse their own motives when they "
        "are shopping.",
        "Not Given",
    ),
    (
        "The actual goods bought are the primary concern in "
        "the activity of shopping.",
        "No",
    ),
    (
        "It was possible to predict the outcome of the study "
        "before embarking on it.",
        "No",
    ),
]

P3_SENTENCES: list[tuple[str, list[str]]] = [
    (
        "The subject of written research the writer first "
        "thought was directly connected with his study was",
        ["thrift"],
    ),
    (
        "The research the writer has been most inspired by "
        "was carried out by",
        ["Hubert and Mauss"],
    ),
    (
        "The writer mostly does not use the meaning of "
        "\u2018sacrifice\u2019 that he regards as",
        [
            "colloquial/metaphorical",
            "colloquial",
            "metaphorical",
            "colloquial or metaphorical",
        ],
    ),
]


# ── writer helper ─────────────────────────────────────────────────────────────

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
    ) -> Question:
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
        return question

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str]]],
        *,
        max_words: int = 3,
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

    async def statements(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[tuple[str, str]],
    ) -> None:
        group = await self._group(question_type, instruction)
        for statement, correct in items:
            self._add(
                group,
                question_type,
                {"statement": statement},
                {"correct": correct},
            )

    async def short_answer(
        self,
        instruction: str,
        items: list[tuple[str, list[str]]],
        *,
        max_words: int = 3,
    ) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for question, variants in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                {"prompt": question, "max_words": max_words},
                gap_answer_key(variants, max_words=max_words),
            )

    async def mcq(
        self,
        instruction: str,
        items: list[dict],
    ) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {
                    "question": item["question"],
                    "options": item["options"],
                },
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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    counts: list[int] = []
    slots: list[int] = []

    # ── Passage 1 ──
    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = f"Passage 1 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 1 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P1_MCQ,
    )
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 1 has eight paragraphs A\u2013H.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter, A\u2013H, in boxes 3\u20137.\n"
        f"NB You may use any letter more than once.\n"
        f"{SCREEN_LETTER_HINT}",
        ["A", "B", "C", "D", "E", "F", "G", "H"],
        P1_INFO_ITEMS,
        options_heading="Paragraph",
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the statements (Questions 8\u201313) and the "
        "list of books below.\n"
        "Match each statement with the book it relates to.\n"
        "Write the correct letter, A\u2013E, in boxes 8\u201313.\n"
        f"NB You may use any letter more than once.\n"
        f"{SCREEN_LETTER_HINT}",
        P1_BOOK_OPTIONS,
        P1_BOOK_ITEMS,
        options_heading="List of Books",
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # ── Passage 2 ──
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 2 has five paragraphs A\u2013E.\n"
        "Choose the correct heading for each paragraph from "
        "the list of headings below.\n"
        "Write the correct number i\u2013x.\n"
        f"{SCREEN_LETTER_HINT}",
        HEADING_OPTIONS,
        HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information "
        "given in Reading Passage 2?\n"
        "Write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P2_TFNG,
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the diagram below.\n"
        "Choose NO MORE THAN THREE WORDS from the reading "
        "passage for each answer.",
        P2_DIAGRAM_STRUCTURE,
        P2_DIAGRAM_ANSWERS,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # ── Passage 3 ──
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = f"Passage 3 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 3 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.multi_select(
        "Choose THREE letters, A\u2013F.",
        P3_MULTI,
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of "
        "the writer in Reading Passage 3?\n"
        "Write\n"
        "YES if the statement agrees with the views of the "
        "writer\n"
        "NO if the statement contradicts the views of the "
        "writer\n"
        "NOT GIVEN if it is impossible to say what the writer "
        "thinks about this",
        P3_YESNO,
    )
    await w.short_answer(
        "Complete the sentences below with words taken from "
        "Reading Passage 3.\n"
        "Use NO MORE THAN THREE WORDS for each answer.",
        P3_SENTENCES,
        max_words=3,
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
        f"\nDone. Reading seeded: rows {counts} / slots {slots} "
        f"= {total_slots}."
    )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
