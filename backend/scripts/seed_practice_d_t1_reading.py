"""Seed Practice Set D Test 1 Reading, all three passages (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 1.
Keys from the printed Answer Key.

Passage 1  Q1-5   summary_completion   John Lomax (THREE WORDS)
           Q6-10  matching_information sections A-G
           Q11-13 multi_select         difficulties (THREE of A-F)
Passage 2  Q14-20 matching_headings    paragraphs A-G (headings i-x)
           Q21-26 yes_no_ng
Passage 3  Q27-32 short_answer         birth of modern minds (THREE WORDS)
           Q33-40 classification       time periods A-D

Passage text lives in scripts/data/practice_d_t1/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t1_reading.py
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

TEST_NUMBER = 1


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "John Lomax\u2019s Project",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "paragraphs": [
        {
            "segments": [
                text(
                    "Lomax began the research for this project by looking "
                    "at "
                ),
                gap("s1"),
                text(
                    " that were not available in book form, as well as "
                    "at certain books. While he was doing this research, "
                    "he met someone who ran a department at the "
                ),
                gap("s2"),
                text(
                    " in Washington. As a result of this contact, he was "
                    "provided with the very latest kind of "
                ),
                gap("s3"),
                text(" for his project."),
            ]
        },
        {
            "segments": [
                text(
                    "Lomax believed that the places he should concentrate "
                    "on were "
                ),
                gap("s4"),
                text(
                    " in the South of the US. While he and his son were "
                    "on their trip, they added "
                ),
                gap("s5"),
                text(
                    " to the list of places where they could find what "
                    "they were looking for."
                ),
            ]
        },
    ],
}

P1_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s1", ["song collections", "(unpublished) song collections"]),
    ("s2", ["Library of Congress"]),
    ("s3", ["portable recording machine"]),
    ("s4", ["rural areas"]),
    ("s5", ["prisons and penitentiaries"]),
]

P1_MATCHING_ITEMS: list[tuple[str, str]] = [
    (
        "a reference to the speed with which Lomax responded to a demand",
        "D",
    ),
    (
        "a reason why Lomax doubted the effectiveness of a certain approach",
        "F",
    ),
    (
        "reasons why Lomax was considered suitable for a particular "
        "official post",
        "D",
    ),
    (
        "reference to a change of plan on Lomax\u2019s part",
        "B",
    ),
    (
        "a reference to one of Lomax\u2019s theories being confirmed",
        "E",
    ),
]

P1_MULTI = {
    "question": (
        "Which THREE of the following difficulties for Lomax are "
        "mentioned by the writer of the text?"
    ),
    "options": [
        "finding a publisher for his research",
        "deciding exactly what kind of music to collect",
        "the scepticism of others concerning his methods",
        "the reluctance of people to participate in his project",
        "making sure that participants in his project were not exploited",
        "factors resulting from his choice of locations for recording",
    ],
    "correct": ["D", "E", "F"],
}


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_HEADINGS = [
    "i. Optimistic beliefs held by the writers of children\u2019s literature",
    "ii. The attitudes of certain adults towards children\u2019s literature",
    "iii. The attraction of children\u2019s literature",
    "iv. A contrast that categorises a book as children\u2019s literature",
    "v. A false assumption made about children\u2019s literature",
    "vi. The conventional view of children\u2019s literature",
    "vii. Some good and bad features of children\u2019s literature",
    "viii. Classifying a book as children\u2019s literature",
    "ix. The treatment of various themes in children\u2019s literature",
    "x. Another way of looking at children\u2019s literature",
]

P2_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "vi"),
    ("Paragraph B", "x"),
    ("Paragraph C", "iii"),
    ("Paragraph D", "viii"),
    ("Paragraph E", "i"),
    ("Paragraph F", "iv"),
    ("Paragraph G", "ix"),
]

P2_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "Adults often fail to recognise the subversive elements in "
        "books their children read.",
        "Not Given",
    ),
    (
        "In publishing, the definition of certain genres has become "
        "inconsistent.",
        "No",
    ),
    (
        "Characters in The Secret Garden are a good example of the "
        "norm in children\u2019s literature.",
        "Yes",
    ),
    (
        "Despite the language used in A High Wind in Jamaica, it "
        "should be considered a children\u2019s book.",
        "No",
    ),
    (
        "The character of Tiny Tim contrasts with that of the child "
        "in Little Lord Fauntleroy.",
        "Yes",
    ),
    (
        "A more realistic view of money should be given in children\u2019s "
        "books.",
        "Not Given",
    ),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_SHORT_ANSWER: list[tuple[str, list[str]]] = [
    (
        "According to the current view, what does NOT indicate the "
        "first appearance of the modern human?",
        ["Stone Age technology"],
    ),
    (
        "What type of evidence does Lord Renfrew question in general?",
        ["genetic", "genetics"],
    ),
    (
        "What, apart from art, were the developments in the creation "
        "of 40,000 years ago?",
        ["tools"],
    ),
    (
        "What kind of cave art in Britain is referred to?",
        ["engravings"],
    ),
    (
        "What TWO things does Lord Renfrew believe to have been "
        "established 10,000 years ago?",
        [
            "permanent villages; agriculture",
            "agriculture; permanent villages",
            "permanent villages and agriculture",
            "agriculture and permanent villages",
            "permanent villages, agriculture",
            "agriculture, permanent villages",
        ],
    ),
    (
        "What TWO things did the notion of personal possessions lead to?",
        [
            "mathematics; written language",
            "written language; mathematics",
            "mathematics and written language",
            "written language and mathematics",
            "mathematics, written language",
            "written language, mathematics",
        ],
    ),
]

PERIOD_OPTIONS = [
    "A. 10,000 years ago",
    "B. 40,000 years ago",
    "C. 60,000 years ago",
    "D. 70,000 years ago",
]

P3_CLASSIFY_ITEMS: list[tuple[str, str]] = [
    (
        "The brain was completely formed physically but was not capable "
        "of all the functions of the modern mind.",
        "C",
    ),
    (
        "There was a major change in the attitude of humans to each other.",
        "A",
    ),
    (
        "A huge amount of art in different forms began to appear.",
        "B",
    ),
    (
        "Development of the human mind occurred at the same time as "
        "a migration.",
        "B",
    ),
    (
        "Art from the period casts doubt on the conventional view of "
        "the development of the human mind.",
        "D",
    ),
    (
        "The modern mind developed in a different location from the "
        "one normally assumed.",
        "A",
    ),
    (
        "The only significant change in the development of man is "
        "shown in the art produced.",
        "B",
    ),
    (
        "Further research into the period is essential for accurate "
        "conclusions to be drawn on human development.",
        "A",
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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    counts: list[int] = []
    slots: list[int] = []

    # -- Passage 1 --
    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = f"Passage 1 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = "How John Lomax set out to record American folk music"
    print(
        f"\nPassage 1 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each answer.",
        P1_SUMMARY_STRUCTURE,
        P1_SUMMARY_ANSWERS,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 1 has seven sections labelled A\u2013G.\n"
        "Which section contains the following information?\n"
        "Write the correct letter, A\u2013G, in boxes 6\u201310.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        ["A", "B", "C", "D", "E", "F", "G"],
        P1_MATCHING_ITEMS,
        options_heading="Section",
    )
    await w.multi_select(
        "Choose THREE letters, A\u2013F.",
        P1_MULTI,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 2 --
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
        "Reading Passage 2 has seven paragraphs, A\u2013G.\n"
        "Choose the correct heading for each paragraph from the list of "
        "headings below.\n"
        "Write the correct number, i\u2013x.",
        P2_HEADINGS,
        P2_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer "
        "in Reading Passage 2?\n"
        "Write\n"
        "YES if the statement agrees with the views of the writer\n"
        "NO if the statement contradicts the views of the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks "
        "about this",
        P2_YNNG_ITEMS,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 3 --
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = f"Passage 3 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = (
        "When did we begin to use symbols to communicate? "
        "Roger Highfield reports on a challenge to prevailing ideas"
    )
    print(
        f"\nPassage 3 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.short_answer(
        "Answer the questions below using NO MORE THAN THREE WORDS "
        "for each answer.",
        P3_SHORT_ANSWER,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Classify the following statements as referring to the period\n"
        "A 10,000 years ago\n"
        "B 40,000 years ago\n"
        "C 60,000 years ago\n"
        "D 70,000 years ago\n\n"
        "Write the correct letter, A\u2013D, in boxes 33\u201340.\n"
        f"{SCREEN_LETTER_HINT}",
        PERIOD_OPTIONS,
        P3_CLASSIFY_ITEMS,
        options_heading="Time period",
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
