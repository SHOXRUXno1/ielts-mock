"""Seed Practice Set C Test 6 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 6. Keys from the printed
Answer Key. Teaching strategy pages are omitted.

Passage 1  Q1-7   note_completion       Indian fashion: 1950-2000
           Q8-13  true_false_ng
Passage 2  Q14-19 matching_information   paragraphs A-I
           Q20-23 matching_features      places → statements A-F
           Q24-26 sentence_completion    NMT 3 words
Passage 3  Q27-32 yes_no_ng              Language diversity
           Q33-37 mcq
           Q38-40 matching_features      sentence endings A-E

Passage text lives in scripts/data/practice_c_t6/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t6_reading.py
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

TEST_NUMBER = 6


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Indian fashion: 1950\u20132000",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "1950s",
            "items": [
                {
                    "segments": [
                        text("No well-known designers, models or "),
                        gap("n1"),
                    ]
                },
                {"segments": [text("Elegant clothing cost little")]},
                {
                    "segments": [
                        text(
                            "Women were pleased to get clothes for a "
                        ),
                        gap("n2"),
                        text(" price"),
                    ]
                },
            ],
        },
        {
            "heading": "1960s",
            "items": [
                {
                    "segments": [
                        text("New materials, e.g. "),
                        gap("n3"),
                        text(" and polyester"),
                    ]
                },
                {
                    "segments": [
                        text("Fitted clothing and tall hairstyles")
                    ]
                },
            ],
        },
        {
            "heading": "1970s",
            "items": [
                {
                    "segments": [
                        text("Overseas sales of "),
                        gap("n4"),
                        text(" fabrics rose"),
                    ]
                },
                {
                    "segments": [
                        text("Influence of international fashion")
                    ]
                },
            ],
        },
        {
            "heading": "1980s",
            "items": [
                {
                    "segments": [
                        text("Opening of fashion store in Mumbai")
                    ]
                },
                {
                    "segments": [
                        text("Popularity of American designers")
                    ]
                },
                {
                    "segments": [
                        text("Clothing had a "),
                        gap("n5"),
                        text(" shape"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Designers tried to attract attention by "
                            "presenting "
                        ),
                        gap("n6"),
                        text(" clothes and mixing with stars"),
                    ]
                },
            ],
        },
        {
            "heading": "1990s",
            "items": [
                {
                    "segments": [
                        text("Fall in demand for expensive fashion wear")
                    ]
                },
                {
                    "segments": [
                        text("Return of "),
                        gap("n7"),
                        text(" clothing"),
                    ]
                },
            ],
        },
    ],
}

P1_NOTES_ANSWERS: list[tuple[str, list[str]]] = [
    ("n1", ["labels"]),
    ("n2", ["bargain"]),
    ("n3", ["plastic"]),
    ("n4", ["traditional"]),
    ("n5", ["masculine"]),
    ("n6", ["showy"]),
    ("n7", ["ethnic"]),
]

P1_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "At the start of the 21st century, key elements in the Indian "
        "fashion industry changed.",
        "True",
    ),
    (
        "India now exports more than half of the cotton it produces.",
        "Not Given",
    ),
    (
        "Conditions in India are generally well suited to the manufacture "
        "of clothing.",
        "True",
    ),
    (
        "Indian clothing exports have suffered from changes in the value "
        "of its currency.",
        "False",
    ),
    (
        "Modern machinery accounts for the high quality of Chapa\u2019s silk.",
        "False",
    ),
    (
        "Some types of Indian craftwork which are internationally popular "
        "had humble origins.",
        "True",
    ),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_PARAGRAPH_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

P2_INFORMATION_ITEMS: list[tuple[str, str]] = [
    (
        "reference to the way the council\u2019s report is organised",
        "H",
    ),
    (
        "the reason why inhabitants in one part of Didcot are isolated",
        "D",
    ),
    (
        "a statement concerning future sources of investment",
        "G",
    ),
    (
        "the identification of two major employers at Didcot",
        "C",
    ),
    (
        "reference to groups who will be consulted about a new "
        "development plan",
        "I",
    ),
    (
        "an account of how additional town centre facilities were "
        "previously funded",
        "E",
    ),
]

P2_PLACE_OPTIONS = [
    "A. It provided extra facilities for shopping and cars.",
    "B. Its location took a long time to agree.",
    "C. Its layout was unsuitable.",
    "D. Its construction was held up due to funding problems.",
    "E. It was privately funded.",
    "F. It failed to get Council approval at first.",
]

P2_PLACE_ITEMS: list[tuple[str, str]] = [
    ("Broadway", "C"),
    ("Market Place", "E"),
    ("Orchard Centre", "A"),
    ("Marsh Bridge", "D"),
]

P2_SENTENCES: list[dict] = [
    {
        "prompt": (
            "A certain proportion of houses in any new development now "
            "have to be of the ______ type."
        ),
        "correct": ["low cost", "low-cost", "affordable"],
    },
    {
        "prompt": (
            "The government is keen to ensure that adequate ______ will "
            "be provided for future housing developments."
        ),
        "correct": ["infrastructure"],
    },
    {
        "prompt": (
            "The views of Didcot\u2019s inhabitants and others will form "
            "the basis of a ______ for the town."
        ),
        "correct": ["strategic master plan"],
    },
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "In the final decades of the twentieth century, a single theory "
        "of language learning was dominant.",
        "Yes",
    ),
    (
        "The majority of UG rules proposed by linguists do apply to all "
        "human languages.",
        "No",
    ),
    (
        "There is disagreement amongst linguists about an aspect of "
        "Straits Salish grammar.",
        "Yes",
    ),
    (
        "The search for new universal language rules has largely ended.",
        "Not Given",
    ),
    (
        "If Evans and Levinson are right, people develop in the same way "
        "no matter what language they speak.",
        "No",
    ),
    (
        "The loss of any single language might have implications for the "
        "human race.",
        "Yes",
    ),
]

P3_MCQ: list[tuple[str, list[str], str]] = [
    (
        "Which of the following views about language are held by Evans "
        "and Levinson?",
        [
            "Each of the world\u2019s languages develops independently.",
            "The differences between languages outweigh the similarities.",
            "Only a few language features are universal.",
            "Each language is influenced by the characteristics of other "
            "languages.",
        ],
        "C",
    ),
    (
        "According to Evans and Levinson, apparent similarities between "
        "languages could be due to",
        [
            "close social contact.",
            "faulty analysis.",
            "shared modes of perception.",
            "narrow descriptive systems.",
        ],
        "C",
    ),
    (
        "In the eighth paragraph, what does the reference to a middle-ear "
        "infection serve as?",
        [
            "A justification for something.",
            "A contrast with something.",
            "The possible cause of something.",
            "The likely result of something.",
        ],
        "C",
    ),
    (
        "What does the writer suggest about Evans\u2019 and Levinson\u2019s "
        "theory of language development?",
        [
            "It had not been previously considered.",
            "It is presented in a convincing way.",
            "It has been largely rejected by other linguists.",
            "It is not supported by the evidence.",
        ],
        "B",
    ),
    (
        "Which of the following best describes the writer\u2019s purpose?",
        [
            "To describe progress in the field of cognitive science.",
            "To defend a long-held view of language learning.",
            "To identify the similarities between particular languages.",
            "To outline opposing views concerning the nature of language.",
        ],
        "D",
    ),
]

P3_ENDING_OPTIONS = [
    "A. words of a certain grammatical type.",
    "B. a sequence of sounds predicted by UG.",
    "C. words which can have more than one meaning.",
    "D. the language feature regarded as the most basic.",
    "E. sentences beyond a specified length.",
]

P3_ENDING_ITEMS: list[tuple[str, str]] = [
    (
        "The Arrernte language breaks a \u2018rule\u2019 concerning",
        "B",
    ),
    (
        "The Lao language has been identified as lacking",
        "A",
    ),
    (
        "It has now been suggested that Amazonian Pirah\u00e3 does not have",
        "D",
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
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Choose ONE WORD ONLY from the passage for each answer.",
        P1_NOTES_STRUCTURE,
        P1_NOTES_ANSWERS,
        max_words=1,
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
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 2 has NINE paragraphs, A\u2013I.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter, A\u2013I.",
        P2_PARAGRAPH_OPTIONS,
        P2_INFORMATION_ITEMS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the following places (Questions 20\u201323) and the list "
        "of statements below.\n"
        "Match each place with the correct statement, A\u2013F.\n"
        f"Write the correct letter, A\u2013F.\n{SCREEN_LETTER_HINT}",
        P2_PLACE_OPTIONS,
        P2_PLACE_ITEMS,
        options_heading="List of statements",
    )
    await w.sentences(
        "Complete the sentences below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each answer.",
        P2_SENTENCES,
        max_words=3,
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
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P3_MCQ,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending, A\u2013E, below.\n"
        f"Write the correct letter, A\u2013E.\n{SCREEN_LETTER_HINT}",
        P3_ENDING_OPTIONS,
        P3_ENDING_ITEMS,
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
