"""Seed Practice Set E Test 4 Reading, all three passages (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 4.
Keys from the printed Explanatory Answer Key (pp.162-165).

Passage 1  Q1-5   matching_features     Causes → Effects (A-H)
           Q6-10  yes_no_ng
           Q11-13 short_answer          THREE WORDS
Passage 2  Q14-16 true_false_ng
           Q17-21 matching_features     People A-D
           Q22-27 summary_completion    ONE WORD from passage
Passage 3  Q28-33 matching_headings     Paragraphs B-G (i-x)
           Q34-36 multi_select          THREE from A-F
           Q37-40 mcq

Passage text lives in scripts/data/practice_e_t4/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t4_reading.py
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
from seed_practice_e_common import (  # noqa: E402
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 4


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 — The nature of light ──────────────────────────────────────────

P1_EFFECTS = [
    "A. Nearly all living creatures can detect it.",
    "B. There is a dark gap between rainbows.",
    "C. Light from Earth could power a spacecraft.",
    "D. Shadows are totally black.",
    "E. We cannot return to the past.",
    "F. We don\u2019t really notice or think about it.",
    "G. Certain creatures can detect infra-red light.",
    "H. We instantly become aware of it.",
]

P1_CAUSE_ITEMS: list[tuple[str, str]] = [
    ("Much of the time, visible light is all around us.", "F"),
    ("Light can sometimes appear in an interesting way.", "H"),
    ("Visible light carries a lot of essential information.", "A"),
    (
        "Without an atmosphere, light is not reflected onto "
        "solid surfaces.",
        "D",
    ),
    ("Only light can exceed 186,282 miles per second.", "E"),
]

P1_YNNG: list[tuple[str, str]] = [
    (
        "It is difficult to find a single word to say exactly "
        "what light is.",
        "Yes",
    ),
    (
        "Thinking about the physics of light can make an object "
        "seem even more beautiful.",
        "No",
    ),
    (
        "Light from the sun makes it possible for life to exist "
        "on other planets.",
        "Not Given",
    ),
    (
        "It is more practical for humans to detect visible light "
        "rather than radio waves.",
        "Yes",
    ),
    (
        "David Lynch sometimes notices things that other people "
        "don\u2019t.",
        "Yes",
    ),
]

P1_SHORT: list[tuple[str, list[str]]] = [
    (
        "What appearance can the land have when seen from a distance?",
        ["a little blue", "little blue"],
    ),
    (
        "In what have some people imagined travelling?",
        ["a spaceship", "spaceship"],
    ),
    (
        "In what substance did light go faster than previously "
        "thought possible?",
        ["cesium gas", "caesium gas"],
    ),
]


# ── Passage 2 — BA or not to MBA? ────────────────────────────────────────────

P2_TFNG: list[tuple[str, str]] = [
    (
        "British employers are more interested in what potential "
        "recruits can do than what they know.",
        "True",
    ),
    (
        "A recruit with a specialist masters usually earns as much "
        "as an experienced employee with a good MBA.",
        "False",
    ),
    (
        "The writer claims that undergraduates often plan to do a "
        "masters because they can\u2019t decide what career to follow.",
        "Not Given",
    ),
]

P2_PEOPLE = [
    "A. Anthony Hesketh",
    "B. Carol Blackman",
    "C. Nunzio Quacquarelli",
    "D. Nic Beech",
]

P2_PEOPLE_ITEMS: list[tuple[str, str]] = [
    (
        "Employees with postgraduate qualifications earn more "
        "because they are older and expect more.",
        "C",
    ),
    (
        "It can be difficult to convince an employer that the "
        "extra time spent at university was necessary.",
        "A",
    ),
    (
        "One type of course focuses on a particular aspect of "
        "business, whereas the other is more general in approach.",
        "B",
    ),
    (
        "Graduates who have neither worked in nor studied business "
        "are suited to our programme.",
        "D",
    ),
    (
        "There is evidence that companies may prefer to employ "
        "people without a masters degree.",
        "A",
    ),
]

P2_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "According to Sheena Maberly",
    "instruction_words": "ONE WORD",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                text(
                    "According to Sheena Maberly, a second degree can "
                    "improve the "
                ),
                gap("w22"),
                text(
                    " prospects of graduates in any subject. Taking a "
                    "management MA gives them the "
                ),
                gap("w23"),
                text(
                    " companies are looking for, and lets them get "
                    "straight on with the job as soon as they start "
                    "work. It also shows they have the "
                ),
                gap("w24"),
                text(
                    " that companies seek. First, however, it is "
                    "important to consider the "
                ),
                gap("w25"),
                text(
                    ": whether to start right away on a carefully "
                    "chosen postgraduate course, or to do so after a "
                    "few years\u2019 work, preferably with financial "
                    "assistance from the "
                ),
                gap("w26"),
                text(
                    ". Whichever they decide, they should think about "
                    "the "
                ),
                gap("w27"),
                text(", and what the company wants."),
            ]
        },
    ],
}

P2_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("w22", ["job"]),
    ("w23", ["skills"]),
    ("w24", ["motivation"]),
    ("w25", ["options"]),
    ("w26", ["company"]),
    ("w27", ["future"]),
]


# ── Passage 3 — Dendrochronology ─────────────────────────────────────────────

P3_HEADINGS = [
    "i. Looking at a particular decade",
    "ii. Studying trees frozen in ice",
    "iii. Bringing different studies together",
    "iv. Records of different species compared",
    "v. What dendrochronology is",
    "vi. A war that affected the climate",
    "vii. Showing how trees record volcanic activity",
    "viii. A unique record of other times and places",
    "ix. Local records covering thousands of years",
    "x. How tree rings are formed",
]

P3_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "ix"),
    ("Paragraph C", "iii"),
    ("Paragraph D", "vii"),
    ("Paragraph E", "iv"),
    ("Paragraph F", "i"),
    ("Paragraph G", "viii"),
]

P3_MULTI = {
    "question": (
        "Which THREE of the following are features of "
        "dendrochronology?"
    ),
    "options": [
        "It provides a complete record of the weather in any "
        "part of the world.",
        "It involves the study of ring patterns in trees of "
        "different ages.",
        "A piece of wood cut a long time ago can form part of "
        "the record.",
        "Studies show that trees of the same type all have the "
        "same number of rings.",
        "As a science it has existed for over 5,000 years.",
        "The oldest records are mostly of one type of tree in "
        "one place.",
    ],
    "correct": ["B", "C", "F"],
}

P3_MCQ: list[dict] = [
    {
        "question": (
            "What was the result of extending the research to "
            "the European oak?"
        ),
        "options": [
            "It added information to that obtained from studying "
            "conifers.",
            "It contradicted all the findings from the study of "
            "conifers.",
            "It showed exactly the same results as those for "
            "conifers.",
            "It proved that the world has cooled considerably "
            "since 1400 AD.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "Which of these happened as a result of the eruption "
            "at Tambora?"
        ),
        "options": [
            "Agricultural production fell significantly.",
            "There was an earthquake in North America.",
            "Part of the polar ice caps melted.",
            "The outcome of a war changed.",
        ],
        "correct": "A",
    },
    {
        "question": "By studying tree rings, we may discover",
        "options": [
            "whole new areas of human history.",
            "proof of events said to have happened.",
            "how earlier civilizations treated the environment.",
            "the truth about the nature of religious belief.",
        ],
        "correct": "B",
    },
    {
        "question": "A suitable title for this passage would be",
        "options": [
            "How volcanoes and earthquakes changed history",
            "The influence of trees on the world\u2019s climate",
            "The role of trees in human history",
            "How trees can tell us more about the past",
        ],
        "correct": "D",
    },
]


# ── writer helpers ───────────────────────────────────────────────────────────


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

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": item["question"], "options": item["options"]},
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
                {"question": question},
                gap_answer_key(variants, max_words=max_words),
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

    # -- Passage 1: The nature of light --
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
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Reading Passage 1 describes a number of cause and effect "
        "relationships. Match each Cause (1\u20135) in List A with "
        "its Effect (A\u2013H) in List B.\n"
        "Write your answers (A\u2013H).\n"
        "There are more Effects in List B than you will need.\n"
        f"{SCREEN_LETTER_HINT}",
        P1_EFFECTS,
        P1_CAUSE_ITEMS,
        options_heading="List B Effects",
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the "
        "writer in Reading Passage 1?\n"
        "Write\n"
        "YES if the statement agrees with the views of the writer\n"
        "NO if the statement does not agree with the views of "
        "the writer\n"
        "NOT GIVEN if there is no information about this in "
        "the passage",
        P1_YNNG,
    )
    await w.short_answer(
        "Answer the following questions using NO MORE THAN "
        "THREE WORDS for each answer.",
        P1_SHORT,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 2: BA or not to MBA? --
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
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "The text quotes various individuals. Match the four "
        "people A\u2013D with the points made in Questions "
        "17\u201321. You may use any of the people more than once.\n"
        f"{SCREEN_LETTER_HINT}",
        P2_PEOPLE,
        P2_PEOPLE_ITEMS,
        options_heading="List of people",
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose ONE WORD from Reading Passage 2 for each answer.",
        P2_SUMMARY_STRUCTURE,
        P2_SUMMARY_ANSWERS,
        max_words=1,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 3: Dendrochronology --
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
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 3 has seven paragraphs A\u2013G.\n"
        "Choose the most suitable headings for paragraphs B\u2013G "
        "from the list of headings below.\n"
        "Write the correct number i\u2013x.\n"
        "Example: Paragraph A \u2014 v",
        P3_HEADINGS,
        P3_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.multi_select(
        "Which THREE of the following are features of "
        "dendrochronology?\n"
        "Write the appropriate letters A\u2013F.",
        P3_MULTI,
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P3_MCQ,
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
