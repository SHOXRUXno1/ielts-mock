"""Seed Practice Set C Test 5 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 5. Keys from the printed
Answer Key. Teaching strategy pages are omitted.

Passage 1  Q1-7   true_false_ng        The economic importance of coral reefs
           Q8-13  note_completion      How coral-reef-based resources protect people
Passage 2  Q14-19 matching_headings    paragraphs A-F
           Q20-21 multi_select         Piaget statements (TWO of A-E)
           Q22-23 multi_select         Howe 8-12-year-olds (TWO of A-E)
           Q24-26 summary_completion   How children learn (from passage)
Passage 3  Q27-29 mcq                  Learning lessons from the past
           Q30-34 yes_no_ng
           Q35-39 matching_features    sentence endings A-F
           Q40    mcq

Passage text lives in scripts/data/practice_c_t5/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t5_reading.py
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

TEST_NUMBER = 5


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "In most places, coral-reef gleaning is normally carried out by men.",
        "False",
    ),
    (
        "Involvement in coral-reef-based occupations raises the status "
        "of women.",
        "True",
    ),
    (
        "Coral reefs provide valuable learning opportunities for young "
        "children.",
        "True",
    ),
    (
        "The women of Ulithi Atoll have some control over how fish "
        "catches are shared out.",
        "True",
    ),
    (
        "Boats for use by the inhabitants of Ulithi are constructed on "
        "Yap Island.",
        "Not Given",
    ),
    (
        "In coral reef fisheries, only male traders can apply for finance.",
        "False",
    ),
    (
        "Coral reefs provide a less constant source of income than "
        "near-shore sea fisheries.",
        "False",
    ),
]

P1_NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "How coral-reef-based resources protect people during difficult times",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Coral reefs can provide",
            "items": [
                {
                    "segments": [
                        text(
                            "a resource bank, e.g. for keeping clams and "
                        ),
                        gap("n8"),
                    ]
                },
                {
                    "segments": [
                        text("a seasonal back-up, when "),
                        gap("n9"),
                        text(
                            " products are insufficient, e.g. in "
                            "northern Mozambique"
                        ),
                    ]
                },
                {
                    "segments": [
                        text("a tourist attraction, e.g. "),
                        gap("n10"),
                        text(" tours in the Caribbean"),
                    ]
                },
            ],
        },
        {
            "heading": "Benefits for local people include",
            "items": [
                {"segments": [text("The creation of jobs")]},
                {
                    "segments": [
                        text("Improvements to roads and "),
                        gap("n11"),
                    ]
                },
            ],
        },
        {
            "heading": "Important considerations",
            "items": [
                {
                    "segments": [
                        text(
                            "Development must be based on appropriate "
                            "principles"
                        )
                    ]
                },
                {
                    "segments": [
                        gap("n12"),
                        text(" is a key requirement"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Poorly-planned development can create "
                        ),
                        gap("n13"),
                        text(" with local fishers"),
                    ]
                },
            ],
        },
    ],
}

P1_NOTES_ANSWERS: list[tuple[str, list[str]]] = [
    ("n8", ["sea cucumbers"]),
    ("n9", ["agricultural"]),
    ("n10", ["scuba diving", "scuba-diving"]),
    ("n11", ["communications"]),
    ("n12", ["sustainability"]),
    ("n13", ["conflict"]),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_HEADINGS = [
    "i. A suggested modification to a theory about learning.",
    "ii. The problem of superficial understanding.",
    "iii. The relationship between scientific understanding and age.",
    "iv. The rejection of a widely held theory.",
    "v. The need to develop new concepts in daily life.",
    "vi. The claim that a perceived contradiction can assist mental development.",
    "vii. Implications for the training of science teachers.",
    "viii. An experiment to assess the benefits of exchanging views with a partner.",
    "ix. Evidence for the delayed benefits of disagreement between pupils.",
]

P2_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "v"),
    ("Paragraph B", "ii"),
    ("Paragraph C", "vi"),
    ("Paragraph D", "i"),
    ("Paragraph E", "ix"),
    ("Paragraph F", "viii"),
]

P2_MULTI_20 = {
    "question": (
        "The list below contains some possible statements about learning.\n"
        "Which TWO of these statements are attributed to Piaget by the "
        "writer of the passage?"
    ),
    "options": [
        "Teachers can assist learning by explaining difficult concepts.",
        "Mental challenge is a stimulus to learning.",
        "Repetition and consistency of input aid cognitive development.",
        "Children sometimes reject evidence that conflicts with their "
        "preconceptions.",
        "Children can help each other make cognitive progress.",
    ],
    "correct": ["B", "D"],
}

P2_MULTI_22 = {
    "question": (
        "Which TWO of these statements describe Howe's experiment with "
        "8\u201312-year-olds?"
    ),
    "options": [
        "The children were assessed on their ability to understand a "
        "scientific problem.",
        "All the children were working in mixed-ability groups.",
        "The children who were the most talkative made the least progress.",
        "The teacher helped the children to understand a scientific problem.",
        "The children were given a total of three tests, at different times.",
    ],
    "correct": ["A", "E"],
}

P2_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "How children learn",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "paragraphs": [
        {
            "segments": [
                text(
                    "Piaget proposed that learning takes place when "
                    "children encounter ideas that do not correspond to "
                    "their current beliefs. The application of this theory "
                    "gave rise to a teaching method known as "
                ),
                gap("s24"),
                text(
                    ". At first this approach only focused on the "
                    "relationship between individual pupils and their "
                ),
                gap("s25"),
                text(
                    ". Later, researchers such as Perret-Clermont became "
                    "interested in the role that interaction with "
                ),
                gap("s26"),
                text(" might also play in a pupil's development."),
            ]
        },
    ],
}

P2_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s24", ["discovery learning"]),
    ("s25", ["teacher", "teachers"]),
    ("s26", ["peers", "friends"]),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_MCQ_EARLY: list[tuple[str, list[str], str]] = [
    (
        "When the writer describes the impact of monumental ruins today, "
        "he emphasises",
        [
            "the income they generate from tourism.",
            "the area of land they occupy.",
            "their archaeological value.",
            "their romantic appeal.",
        ],
        "D",
    ),
    (
        "Recent findings concerning vanished civilisations have",
        [
            "overturned long-held beliefs.",
            "caused controversy amongst scientists.",
            "come from a variety of disciplines.",
            "identified one main cause of environmental damage.",
        ],
        "C",
    ),
    (
        "What does the writer say about ways in which former societies "
        "collapsed?",
        [
            "The pace of decline was usually similar.",
            "The likelihood of collapse would have been foreseeable.",
            "Deterioration invariably led to total collapse.",
            "Individual citizens could sometimes influence the course "
            "of events.",
        ],
        "A",
    ),
]

P3_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "It is widely believed that environmental problems represent the "
        "main danger faced by the modern world.",
        "Yes",
    ),
    (
        "The accumulation of poisonous substances is a relatively modern "
        "problem.",
        "Yes",
    ),
    (
        "There is general agreement that the threats posed by environmental "
        "problems are very serious.",
        "No",
    ),
    (
        "Some past societies resembled present-day societies more closely "
        "than others.",
        "Not Given",
    ),
    (
        "We should be careful when drawing comparisons between past and "
        "present.",
        "Yes",
    ),
]

P3_ENDING_OPTIONS = [
    "A. is not necessarily valid.",
    "B. provides grounds for an optimistic outlook.",
    "C. exists in the form of physical structures.",
    "D. is potentially both positive and negative.",
    "E. will not provide direct solutions for present problems.",
    "F. is greater now than in the past.",
]

P3_ENDING_ITEMS: list[tuple[str, str]] = [
    (
        "Evidence of the greatness of some former civilisations",
        "C",
    ),
    (
        "The parallel between an individual's life and the life of a "
        "society",
        "A",
    ),
    (
        "The number of environmental problems that societies face",
        "F",
    ),
    (
        "The power of technology",
        "D",
    ),
    (
        "A consideration of historical events and trends",
        "E",
    ),
]

P3_MCQ_LATE: list[tuple[str, list[str], str]] = [
    (
        "What is the main argument of Reading Passage 3?",
        [
            "There are differences as well as similarities between past "
            "and present societies.",
            "More should be done to preserve the physical remains of "
            "earlier civilisations.",
            "Some historical accounts of great civilisations are "
            "inaccurate.",
            "Modern societies are dependent on each other for their "
            "continuing survival.",
        ],
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

    # -- Passage 1 --
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
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Choose NO MORE THAN TWO WORDS from the passage for each answer.",
        P1_NOTES_STRUCTURE,
        P1_NOTES_ANSWERS,
        max_words=2,
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
        "Reading Passage 2 has SIX paragraphs, A\u2013F.\n"
        "Choose the correct heading for each paragraph from the list of "
        "headings below.\n"
        "Write the correct number, i\u2013ix.",
        P2_HEADINGS,
        P2_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        P2_MULTI_20,
    )
    await w.multi_select(
        "Choose TWO letters, A\u2013E.",
        P2_MULTI_22,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose NO MORE THAN TWO WORDS from the passage for each answer.",
        P2_SUMMARY_STRUCTURE,
        P2_SUMMARY_ANSWERS,
        max_words=2,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 3 --
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
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P3_MCQ_EARLY,
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer in "
        "Reading Passage 3?\n"
        "Write\n"
        "YES if the statement agrees with the claims of the writer\n"
        "NO if the statement contradicts the claims of the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about "
        "this",
        P3_YNNG_ITEMS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending, A\u2013F, below.\n"
        f"Write the correct letter, A\u2013F.\n{SCREEN_LETTER_HINT}",
        P3_ENDING_OPTIONS,
        P3_ENDING_ITEMS,
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
