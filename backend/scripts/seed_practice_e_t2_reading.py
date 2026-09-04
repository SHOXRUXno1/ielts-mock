"""Seed Practice Set E Test 2 Reading, all three passages (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 2.
Keys from the printed Explanatory Answer Key (pp.138-141).

Passage 1  Q1-5   classification       textile/insects cases (A/B/C)
           Q6-8   flow_chart_completion evolutionary purpose (TWO WORDS)
           Q9-13  true_false_ng
           Q14    mcq                   best alternative title (A-E)
Passage 2  Q15-19 matching_headings     Anderton Boat Lift (a-j)
           Q20-24 sentence_completion   1908 lift diagram (THREE WORDS)
           Q25-27 sentence_completion   notes completion (THREE WORDS)
Passage 3  Q28-34 summary_completion    astrobiology summary (word list)
           Q35-38 matching_features     writers A-C
           Q39-40 mcq                   writer's views (A-D)

Passage text lives in scripts/data/practice_e_t2/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t2_reading.py
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

TEST_NUMBER = 2


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 — Imaginary bites and parasites ───────────────────────────────

# Q1-5: Classification A=laboratory, B=factory, C=office
P1_CLASSIFICATION_OPTIONS = [
    "A. the laboratory",
    "B. the factory",
    "C. the office",
]

P1_CLASSIFICATION_ITEMS: list[tuple[str, str]] = [
    ("Workers who met each other socially suffered from the condition.", "B"),
    ("The victims were all working with old documents.", "C"),
    ("They tried to kill the insects they thought were responsible.", "A"),
    ("They said the creatures had come in material from abroad.", "B"),
    ("Employees\u2019 families were affected by the condition.", "A"),
]

# Q6-8: Flow chart completion — evolutionary purpose (TWO WORDS)
FLOW1_STRUCTURE: dict = {
    "variant": "flow",
    "title": "Evolutionary purpose theory",
    "instruction_words": "TWO WORDS",
    "max_words_per_gap": 2,
    "steps": [
        {
            "segments": [
                text("parasite / insect bite"),
            ]
        },
        {
            "segments": [
                gap("f6"),
            ]
        },
        {
            "segments": [
                gap("f7"),
            ]
        },
        {
            "segments": [
                text("group scratching"),
            ]
        },
        {
            "segments": [
                text("mutual grooming"),
            ]
        },
        {
            "segments": [
                gap("f8"),
            ]
        },
    ],
}

FLOW1_ANSWERS: list[tuple[str, list[str]]] = [
    ("f6", ["individual scratching"]),
    ("f7", ["alerted others"]),
    ("f8", ["bonding"]),
]

# Q9-13: True/False/Not Given
P1_TFNG: list[tuple[str, str]] = [
    (
        "Some keep scratching because they know it will enable "
        "them to stop work.",
        "False",
    ),
    (
        "The laboratory, factory and office employees all had "
        "boring jobs.",
        "True",
    ),
    (
        "The human skin is extremely sensitive to irritants.",
        "Not Given",
    ),
    (
        "In many cases, people no longer believe what medical "
        "professionals say.",
        "True",
    ),
    (
        "It is impossible to prevent the condition becoming an "
        "Internet epidemic.",
        "False",
    ),
]

# Q14: MCQ — best alternative title
P1_TITLE_MCQ: list[dict] = [
    {
        "question": (
            "From the list below choose the most suitable alternative "
            "title for Reading Passage 1."
        ),
        "options": [
            "The benefits of itching and scratching",
            "Increasing complaints about insects",
            "Scratching, yawning and laughing",
            "Imaginary bites and parasites",
            "Computer bites and Internet itches",
        ],
        "correct": "D",
    },
]


# ── Passage 2 — The Anderton Boat Lift ──────────────────────────────────────

# Q15-19: Matching headings to sections II-VI
P2_HEADINGS = [
    "a. The lift in use",
    "b. The first and second lifts",
    "c. Restoring the lift",
    "d. The new canal",
    "e. Mechanical problems",
    "f. Why the lift was needed",
    "g. The supports of the second lift",
    "h. A new framework and machinery",
    "i. How the original lift worked",
    "j. A completely new lift",
]

P2_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Section II", "i"),
    ("Section III", "e"),
    ("Section IV", "h"),
    ("Section V", "a"),
    ("Section VI", "c"),
]

# Q20-24: Diagram/sentence completion — 1908 lift (THREE WORDS)
P2_DIAGRAM_SHORT: list[tuple[str, list[str]]] = [
    (
        "What formed the top of the framework of the new lift?",
        ["platform", "(the) platform"],
    ),
    (
        "What was at either side of the new lift to support the platform?",
        ["A-frames", "A-frame", "A frames", "strong A-frames"],
    ),
    (
        "What did the wire ropes run around at the top of the lift?",
        ["pulley(s)", "pulleys", "pulley"],
    ),
    (
        "What was suspended on wire ropes?",
        ["(boat carrying) tank", "boat carrying tank", "tank",
         "(boat-carrying) tank", "boat-carrying tank"],
    ),
    (
        "What was at the side of the structure to counterbalance the tanks?",
        ["(cast iron) weights", "cast iron weights", "cast-iron weights",
         "weights"],
    ),
]

# Q25-27: Notes completion (THREE WORDS)
P2_NOTES_SHORT: list[tuple[str, list[str]]] = [
    (
        "Similar lifts to the Anderton were later built in \u2026",
        ["France and Belgium"],
    ),
    (
        "Extra power to move the tanks came from \u2026",
        ["a hydraulic pump", "hydraulic pump"],
    ),
    (
        "Using water from the canal harmed the \u2026",
        ["cylinders and pistons"],
    ),
]


# ── Passage 3 — Life, but not as we know it ─────────────────────────────────

# Q28-34: Summary completion from word list
P3_WORD_LIST = [
    "location", "principles", "previous",
    "narrow", "galaxy", "frequently",
    "discussing", "rarely", "defining",
    "never", "composition", "size",
    "definition", "planet", "extending",
    "mistake", "breakthrough",
    "basing", "regulations",
]

P3_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Life, but not as we know it",
    "instruction_words": "from the box",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                text(
                    "The same biological and chemical principles determine "
                    "the make-up of all terrestrial life forms, whatever "
                    "their "
                ),
                gap("w28"),
                text(
                    ". We often assume that this is the case throughout "
                    "the universe, as we have "
                ),
                gap("w29"),
                text(
                    " observed other kinds of organism. Scientists "
                    "therefore make the "
                ),
                gap("w30"),
                text(
                    " of searching for indications of Earth-style "
                    "living things when examining material from "
                    "another "
                ),
                gap("w31"),
                text(
                    " where the nature of any life may lie far "
                    "outside their own "
                ),
                gap("w32"),
                text(
                    " definition. On the other hand, if the focus "
                    "is not on "
                ),
                gap("w33"),
                text(
                    " but on behaviour, there is a risk of "
                ),
                gap("w34"),
                text(" life much too broadly."),
            ]
        },
    ],
}

P3_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("w28", ["size"]),
    ("w29", ["never"]),
    ("w30", ["mistake"]),
    ("w31", ["planet"]),
    ("w32", ["narrow"]),
    ("w33", ["composition"]),
    ("w34", ["defining"]),
]

# Q35-38: Matching opinions to writers A/B/C
P3_WRITER_OPTIONS = [
    "A. Aldiss",
    "B. Banks",
    "C. Cohen & Stewart",
]

P3_WRITER_ITEMS: list[tuple[str, str]] = [
    (
        "Other life forms may fit a definition of life but be "
        "quite unlike anything on Earth.",
        "C",
    ),
    (
        "People instinctively want to believe in extraterrestrial "
        "life forms.",
        "A",
    ),
    (
        "There could be life within life on an immense scale.",
        "B",
    ),
    (
        "Humans are inevitably limited in their ability to find "
        "life beyond Earth.",
        "C",
    ),
]

# Q39-40: MCQ
P3_MCQ: list[dict] = [
    {
        "question": "The writer believes that astrobiology",
        "options": [
            "may now be the second most fashionable science.",
            "is very similar to exobiology.",
            "has proved that a meteorite from Mars contains fossils.",
            "is not taken seriously by scientific publications.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "Which of the following statements best describes the "
            "writer\u2019s main purpose in Reading Passage 3?"
        ),
        "options": [
            "to describe the latest scientific developments in the "
            "study of the universe",
            "to explain why there is growing interest in the study "
            "of astrobiology",
            "to show that science fiction writers have nothing useful "
            "to say about aliens",
            "to suggest that astrobiology may not help us find "
            "extraterrestrial life",
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

    async def mcq(
        self, instruction: str, items: list[dict],
    ) -> None:
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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    counts: list[int] = []
    slots: list[int] = []

    # -- Passage 1: Imaginary bites and parasites --
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
        "Classify statements 1\u20135 according to whether they "
        "apply to\n"
        "A the laboratory\n"
        "B the factory\n"
        "C the office\n"
        f"{SCREEN_LETTER_HINT}",
        P1_CLASSIFICATION_OPTIONS,
        P1_CLASSIFICATION_ITEMS,
        options_heading="Workplace",
    )
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the notes below with words taken from "
        "Reading Passage 1.\n"
        "Use NO MORE THAN TWO WORDS for each answer.",
        FLOW1_STRUCTURE,
        FLOW1_ANSWERS,
        max_words=2,
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "In boxes 9\u201313 on your answer sheet write\n"
        "TRUE if the statement is true according to the passage\n"
        "FALSE if the statement is false according to the passage\n"
        "NOT GIVEN if the statement is not given in the passage",
        P1_TFNG,
    )
    await w.mcq(
        "From the list below choose the most suitable alternative "
        "title for Reading Passage 1.\n"
        "Write the appropriate letter A\u2013E.",
        P1_TITLE_MCQ,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 2: The Anderton Boat Lift --
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
        "Reading Passage 2 has six sections I\u2013VI.\n"
        "Choose the most suitable heading for each section "
        "II\u2013VI from the list below.\n"
        "Write the appropriate letters a\u2013j.",
        P2_HEADINGS,
        P2_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.short_answer(
        "Complete the diagram below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage "
        "for each answer.",
        P2_DIAGRAM_SHORT,
        max_words=3,
    )
    await w.short_answer(
        "Complete the notes below.\n"
        "Choose NO MORE THAN THREE WORDS from Reading "
        "Passage 2 for each answer.",
        P2_NOTES_SHORT,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 3: Life, but not as we know it --
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
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose the answers from the box and write the "
        "corresponding words in boxes 28\u201334.",
        P3_SUMMARY_STRUCTURE,
        P3_SUMMARY_ANSWERS,
        max_words=1,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "The text refers to the ideas of various science fiction "
        "writers.\n"
        "Match writers A\u2013C with the points in 35\u201338.\n"
        "You may use any of the writers more than once.\n"
        f"{SCREEN_LETTER_HINT}",
        P3_WRITER_OPTIONS,
        P3_WRITER_ITEMS,
        options_heading="Writer",
    )
    await w.mcq(
        "Choose the appropriate letters A\u2013D.",
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
