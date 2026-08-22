"""Seed Practice Set A Test 5 Reading, all three passages (Q1-40).

Passage 1  Q1-4   matching_headings    paragraphs B-E
           Q5     diagram_labeling     the fire triangle
           Q6-9   short_answer
           Q10-13 sentence_completion
Passage 2  Q14-21 matching_features    who said what, by initials
           Q22-27 true_false_ng
Passage 3  Q28-34 yes_no_ng
           Q35-40 matching_features    events matched to dates

Passage text lives in scripts/data/practice_a_t5/ so the prose stays
proofreadable instead of buried in string literals.

Two misprints in the paper are corrected here rather than reproduced: the
Questions 5-9 rubric points at "Reading Passage 2" when the questions are all
on Passage 1, and the Questions 14-21 rubric numbers the views "25 - 32".

Idempotent: each passage section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t5_reading.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.services.compound import validate_compound_structure  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_a_common import (  # noqa: E402
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 5

TRIANGLE_IMAGE_URL = "/media/images/practice_a_t5_reading_fire_triangle.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_HEADINGS = [
    "i. Climate Conditions",
    "ii. Solutions from the Air",
    "iii. Fire Starters",
    "iv. Battling the Blaze",
    "v. The Lie of the Land",
    "vi. Rain – The Natural Saviour",
    "vii. Fuelling the Flames",
    "viii. Fires and Trees",
]

# Paragraph A is given as the example (iii) and is not asked.
P1_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "vii"),
    ("Paragraph C", "i"),
    ("Paragraph D", "v"),
    ("Paragraph E", "iv"),
]

# The paper draws the triangle with two pillars already labelled, so the figure
# is the question; without it there is nothing to say which pillar is missing.
P1_TRIANGLE_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The fire triangle",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "image_url": TRIANGLE_IMAGE_URL,
    "sections": [
        {
            "heading": "Complete the last pillar of the fire triangle.",
            "items": [{"segments": [gap("d5")]}],
        }
    ],
}

P1_TRIANGLE_ANSWERS: list[tuple[str, list[str], int]] = [
    ("d5", ["oxygen", "air", "air/oxygen", "oxygen source", "air source"], 3),
]

P1_SHORT_ANSWER_ITEMS: list[dict] = [
    {
        "prompt": "What is measured in tons per acre?",
        "correct": ["the fuel load", "fuel load"],
    },
    {
        "prompt": "When do wildfires burn at their fiercest?",
        "correct": ["in the afternoon", "the afternoon", "afternoon"],
    },
    {
        "prompt": (
            "What can travel in the wind to create fires at some distance from "
            "the initial fire?"
        ),
        "correct": ["embers", "ember"],
    },
    {
        "prompt": (
            "Name a method using an additional fire that fire fighters use to "
            "control wild fires."
        ),
        "correct": ["backfires", "backfire", "a backfire", "backfiring"],
    },
]

P1_SENTENCE_ITEMS: list[dict] = [
    {
        "prompt": (
            "The most important factor in how quickly a wildfire catches fire "
            "is the surface to volume ______."
        ),
        "correct": ["ratio", "ratio of fuel", "ratio of the fuel"],
    },
    {
        "prompt": (
            "The most significant weather factor to affect wildfires' actions "
            "is ______."
        ),
        "correct": ["the wind", "wind"],
    },
    {
        "prompt": "Fires on the tops of trees are known as ______.",
        "correct": ["crown fires", "crown fire", "a crown fire"],
    },
    {
        "prompt": (
            "Wildfires usually travel much faster ______ because of the "
            "typical direction of prevailing winds."
        ),
        "correct": ["uphill"],
    },
]

# ── Passage 2 ────────────────────────────────────────────────────────────────

# The paper identifies speakers by their initials rather than by letter, so the
# options carry those initials as the prefix the dropdown offers.
P2_PEOPLE_OPTIONS = [
    "MM. Mike Muller",
    "FR. Frank Rijsbereman",
    "ME. Mark Evans",
    "LG. Liane Greef",
    "GB. Graham Bennetts",
]

P2_PEOPLE_ITEMS: list[tuple[str, str]] = [
    ("Water needs to be utilised more prudently by some people.", "LG"),
    ("South Africa has almost completed its plans for building dams.", "MM"),
    (
        "Local government has excluded some South African households from "
        "getting free water for not meeting their bills.",
        "LG",
    ),
    (
        "The World Summit in Johannesburg will soon have its aims on hygiene "
        "agreed among all participants.",
        "ME",
    ),
    (
        "Faster development of water supply in South Africa is limited by the "
        "facilities of community administrations.",
        "GB",
    ),
    (
        "Water use is more efficient than in South Africa in some foreign food "
        "production.",
        "FR",
    ),
    (
        "Government should be answerable for water delivery and not private "
        "companies.",
        "LG",
    ),
    (
        "The water question's importance has been increased due to the risk of "
        "global weather temperature rises.",
        "ME",
    ),
]

P2_TFNG_ITEMS: list[tuple[str, str]] = [
    ("Some African countries are currently at war over water resources.", "Not Given"),
    (
        "A recent report says by 2025 that 25 African countries will suffer "
        "from water scarcity alone.",
        "False",
    ),
    ("Vocal environment activists were arrested at the World Summit.", "Not Given"),
    (
        "Questions at the World Summit over including water sanitation have "
        "not yet been agreed.",
        "True",
    ),
    (
        "The World Summit had many good ideas but had little contribution on "
        "how to put the ideas into practice.",
        "False",
    ),
    ("Plants are being introduced that can flourish with little water.", "True"),
]

# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "The printing of paper money in the UK has always been done by the "
        "same company.",
        "No",
    ),
    (
        "Early paper making in Europe was at its peak in Holland in the 18th "
        "century.",
        "Not Given",
    ),
    (
        "18th Century developments in moulds led to the improvement of a "
        "flatter, more even paper.",
        "Yes",
    ),
    (
        "Chlorine bleaching proved the answer to the need for more white paper "
        "in the 18th and 19th centuries.",
        "No",
    ),
    (
        "The first mechanised process that had any success still used elements "
        "of the hand made paper-making process.",
        "Yes",
    ),
    ("Modern paper making machines are still based on John Dickinson's 1809 "
     "patent.", "Yes"),
    (
        "The development of bigger mills near larger towns was so that mill "
        "owners could take advantage of potential larger workforces.",
        "No",
    ),
]

P3_DATE_OPTIONS = [
    "A. 1803",
    "B. 1757",
    "C. 1821",
    "D. 1697",
    "E. 1799",
    "F. 1670",
    "G. 1694",
]

P3_DATE_ITEMS: list[tuple[str, str]] = [
    ("Invention of the rag engine.", "F"),
    ("A new method for drying paper patented.", "C"),
    ("First successful machine for making paper put into production.", "A"),
    ("Manufacture of the first woven paper.", "B"),
    ("Watermarks first used for paper money.", "D"),
    ("The first machine for making paper patented.", "E"),
]


# ── writing helpers ──────────────────────────────────────────────────────────


class PassageWriter:
    def __init__(self, db: AsyncSession, section: Section) -> None:
        self.db = db
        self.section = section
        self.order = 1
        self.group_order = 1
        self.count = 0

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
        self.db.add(
            Question(
                id=uuid.uuid4(),
                section_id=self.section.id,
                question_group_id=group.id,
                order=self.order,
                question_type=question_type,
                content=content,
                answer_key=answer_key,
            )
        )
        self.order += 1
        self.count += 1

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
            self._add(group, question_type, {"question": question}, {"correct": correct})

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

    async def prompts(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[dict],
        *,
        max_words: int,
    ) -> None:
        group = await self._group(question_type, instruction)
        for item in items:
            self._add(
                group,
                question_type,
                {"prompt": item["prompt"], "max_words": max_words},
                gap_answer_key(item["correct"], max_words=max_words),
            )

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str], int]],
    ) -> None:
        group = await self._group(question_type, instruction, options_shared=structure)
        for gap_id, variants, max_words in answers:
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

    # Passage 1
    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 1 has 5 paragraphs (A-E).\n"
        "From the list of headings below choose the most suitable headings for "
        "paragraphs B-E.\n"
        "Write the appropriate number (i-viii) in boxes 1-4 on your answer sheet.\n"
        "NB There are more headings than paragraphs, so you will not use them all.\n"
        "Example: Paragraph A — iii",
        P1_HEADINGS,
        P1_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Using NO MORE THAN THREE WORDS from Reading Passage 1, label the "
        "diagram below.",
        P1_TRIANGLE_STRUCTURE,
        P1_TRIANGLE_ANSWERS,
    )
    await w.prompts(
        QuestionType.SHORT_ANSWER,
        "Using NO MORE THAN THREE WORDS from Reading Passage 1, answer the "
        "following questions.\n"
        "Write your answers in boxes 6-9 on your answer sheet.",
        P1_SHORT_ANSWER_ITEMS,
        max_words=3,
    )
    await w.prompts(
        QuestionType.SENTENCE_COMPLETION,
        "Complete each of the following statements with words taken from "
        "Reading Passage 1.\n"
        "Write NO MORE THAN THREE WORDS for each answer.\n"
        "Write your answers in boxes 10-13 on your answer sheet.",
        P1_SENTENCE_ITEMS,
        max_words=3,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    # Passage 2
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = "Problems With Water"
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Match the views (14-21) with the people listed below.\n"
        "Write the appropriate initials in boxes 14-21 on your answer sheet.",
        P2_PEOPLE_OPTIONS,
        P2_PEOPLE_ITEMS,
        options_heading="List of People",
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Read the passage about problems with water again and look at the "
        "statements below.\n"
        "In boxes 22-27 on your answer sheet write\n"
        "TRUE if the statement is true\n"
        "FALSE if the statement is false\n"
        "NOT GIVEN if the information is not given in the passage",
        P2_TFNG_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    # Passage 3
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer of the "
        "reading passage on The History of Papermaking in the U.K.?\n"
        "In boxes 28-34 write\n"
        "YES if the statement agrees with the writer\n"
        "NO if the statement doesn't agree with the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P3_YNNG_ITEMS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Match the events (35-40) with the dates (A-G) listed below.\n"
        "Write the appropriate letters in boxes 35-40 on your answer sheet.",
        P3_DATE_OPTIONS,
        P3_DATE_ITEMS,
        options_heading="Dates",
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    total = sum(counts)
    if total != 40:
        raise SystemExit(f"expected 40 reading questions, got {total}")

    await db.commit()
    print(f"\nDone. Reading seeded: {counts} = {total} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
