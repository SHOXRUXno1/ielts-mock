"""Seed Practice Set C Test 7 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 7. Keys from the printed
Answer Key. Teaching strategy pages are omitted.

Passage 1  Q1-3   diagram_labeling      Flexible pavement diagram
           Q4-7   true_false_ng
           Q8-13  table_completion      Bridge types table
Passage 2  Q14-18 matching_features     characteristics → species A/B/C
           Q19-23 matching_information  paragraphs A-G
           Q24-26 sentence_completion   NMT 3 words
Passage 3  Q27-31 yes_no_ng             The future of fish
           Q32-34 mcq
           Q35-40 summary_completion    word list A-J

Passage text lives in scripts/data/practice_c_t7/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t7_reading.py
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

TEST_NUMBER = 7


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

DIAGRAM1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Flexible Pavement",
    "instruction_words": "TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "sections": [
        {
            "heading": "Label the diagram",
            "items": [
                {
                    "segments": [
                        text("Surface layer \u2014 Tarmacadam ("),
                        gap("d1"),
                        text(" and stone chips)"),
                    ]
                },
                {
                    "segments": [
                        text("Middle layer ("),
                        gap("d2"),
                        text(" deep) \u2014 Crushed stone"),
                    ]
                },
                {
                    "segments": [
                        text("Foundation \u2014 Stone dust and "),
                        gap("d3"),
                    ]
                },
            ],
        }
    ],
}

DIAGRAM1_ANSWERS: list[tuple[str, list[str]]] = [
    ("d1", ["hot tar"]),
    ("d2", ["five centimetres", "5 centimetres", "5 cm"]),
    ("d3", ["water"]),
]

P1_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "Road construction improved continuously between the first and "
        "eighteenth centuries.",
        "False",
    ),
    (
        "In Britain, during the nineteenth century, only the very rich "
        "could afford to use toll roads.",
        "Not Given",
    ),
    (
        "Nineteenth-century road surfaces were inadequate for heavy motor "
        "traffic.",
        "True",
    ),
    (
        "Traffic speeds on long-distance highways were unregulated in "
        "the early part of the twentieth century.",
        "Not Given",
    ),
]

TABLE1_STRUCTURE: dict = {
    "variant": "table",
    "title": "Types of bridge",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "headers": [
        "Type of bridge",
        "Features",
        "Example(s)",
    ],
    "rows": [
        [
            {"variant": "plain", "segments": [text("Arched bridge")]},
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("Introduced by the "),
                            gap("t8"),
                        ]
                    },
                    {"segments": [text("Very strong")]},
                    {
                        "segments": [
                            text("Usually made of "),
                            gap("t9"),
                        ]
                    },
                ],
            },
            {
                "variant": "plain",
                "segments": [text("Alcantara, Spain\nIronbridge, UK")],
            },
        ],
        [
            {"variant": "plain", "segments": [text("Truss bridge")]},
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("Made of wood or metal")]},
                    {"segments": [text("Popular for railways")]},
                ],
            },
            {"variant": "plain", "segments": [text("")]},
        ],
        [
            {"variant": "plain", "segments": [text("Suspension bridge")]},
            {
                "variant": "bullets",
                "bullets": [
                    {"segments": [text("Has a suspended deck")]},
                    {
                        "segments": [
                            text("Strong but "),
                            gap("t10"),
                        ]
                    },
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    text(
                        "Clifton, UK\nAkashi Kaikyo, Japan "
                        "(currently the "
                    ),
                    gap("t11"),
                    text(")"),
                ],
            },
        ],
        [
            {"variant": "plain", "segments": [text("Cantilever bridge")]},
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("Made of "),
                            gap("t12"),
                        ]
                    },
                    {
                        "segments": [
                            text("More "),
                            gap("t13"),
                            text(" than the suspension bridge"),
                        ]
                    },
                ],
            },
            {
                "variant": "plain",
                "segments": [text("Quebec, Canada")],
            },
        ],
    ],
}

TABLE1_ANSWERS: list[tuple[str, list[str]]] = [
    ("t8", ["Romans"]),
    ("t9", ["stone"]),
    ("t10", ["light"]),
    ("t11", ["longest"]),
    ("t12", ["steel"]),
    ("t13", ["stable"]),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

SPECIES_OPTIONS = [
    "A. Homo neanderthalensis",
    "B. Homo sapiens",
    "C. both Homo neanderthalensis and Homo sapiens",
]

SPECIES_ITEMS: list[tuple[str, str]] = [
    ("Once lived in Europe and Asia.", "A"),
    ("Originated in Africa.", "B"),
    (
        "Did not survive long after the arrival of immigrants.",
        "A",
    ),
    ("Interbred with another species.", "C"),
    (
        "Appears not to have passed on mitochondrial DNA to another "
        "species.",
        "A",
    ),
]

P2_PARAGRAPH_OPTIONS = ["A", "B", "C", "D", "E", "F", "G"]

P2_INFORMATION_ITEMS: list[tuple[str, str]] = [
    ("an account of the rejection of a theory", "D"),
    (
        "reference to an unexplained link between two events",
        "B",
    ),
    (
        "the identification of a skill-related gene common to both "
        "Neanderthals and modern humans",
        "G",
    ),
    ("the announcement of a scientific breakthrough", "A"),
    ("an interesting gap in existing knowledge", "E"),
]

P2_SENTENCES: list[dict] = [
    {
        "prompt": (
            "Despite the length of time for which Homo sapiens and "
            "Homo neanderthalensis had developed separately, "
            "______ did take place."
        ),
        "correct": ["interbreeding", "inter-breeding", "crossbreeding"],
    },
    {
        "prompt": (
            "Genes which evolved after modern humans split from "
            "Neanderthals are connected with cognitive ability and "
            "skeletal ______."
        ),
        "correct": ["growth"],
    },
    {
        "prompt": (
            "The potential for this line of research to shed light on "
            "the nature of modern humans was further strengthened when "
            "analysis of a ______ led to the discovery of a new human "
            "species."
        ),
        "correct": ["little-finger bone", "little finger bone"],
    },
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "It is more than a thousand years since people started to catch "
        "fish for commercial use.",
        "Yes",
    ),
    (
        "In general, open access to the oceans is still regarded as "
        "desirable.",
        "Yes",
    ),
    (
        "Sea fishing is now completely banned in the majority of "
        "protected areas.",
        "No",
    ),
    (
        "People should be encouraged to reduce the amount of fish "
        "they eat.",
        "Not Given",
    ),
    (
        "The re-introduction of certain mammals to the Mediterranean "
        "is a straightforward task.",
        "No",
    ),
]

P3_MCQ: list[tuple[str, list[str], str]] = [
    (
        "What does the writer mean with the question, \u2018How much "
        "time have we got?\u2019 in the fifth paragraph?",
        [
            "Fisheries policies are currently based on uncertain "
            "estimates.",
            "Accurate predictions will allow governments to plan "
            "properly.",
            "Fisheries managers should provide clearer information.",
            "Action to protect fish stocks is urgently needed.",
        ],
        "D",
    ),
    (
        "What is the writer\u2019s comment on the Common Fisheries "
        "Policy?",
        [
            "Measures that it advocated were hastily implemented.",
            "Officials exaggerated some of its recommendations.",
            "It was based on predictions which were inaccurate.",
            "The policy makers acquired a good reputation.",
        ],
        "C",
    ),
    (
        "What is the writer\u2019s conclusion concerning the decline "
        "of marine resources?",
        [
            "The means of avoiding the worst outcomes needs to be "
            "prioritised.",
            "Measures already taken to avoid a crisis are probably "
            "sufficient.",
            "The situation is now so severe that there is no likely "
            "solution.",
            "It is no longer clear which measures would be most "
            "effective.",
        ],
        "A",
    ),
]

P3_SUMMARY_OPTIONS = [
    "A. action",
    "B. controls",
    "C. failure",
    "D. fish catches",
    "E. fish processing",
    "F. fishing techniques",
    "G. large boats",
    "H. marine reserves",
    "I. the land",
    "J. the past",
]

P3_SUMMARY_ITEMS: list[tuple[str, str]] = [
    (
        "It was unnecessary to introduce 35 ______ of any kind ...",
        "B",
    ),
    (
        "... as 36 ______ improved, this situation changed ...",
        "F",
    ),
    (
        "... policies were introduced to regulate 37 ______.",
        "D",
    ),
    (
        "Today, by comparison with 38 ______, the oceans have very "
        "little legal protection.",
        "I",
    ),
    (
        "Despite the doubts ... about the concept of 39 ______, "
        "these should be at the heart of any action taken.",
        "H",
    ),
    (
        "The consequences of further 40 ______ are very serious ...",
        "C",
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
        QuestionType.DIAGRAM_LABELING,
        "Label the diagram below.\n"
        "Choose NO MORE THAN TWO WORDS AND/OR A NUMBER from the passage "
        "for each answer.",
        DIAGRAM1_STRUCTURE,
        DIAGRAM1_ANSWERS,
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
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Use ONE WORD ONLY from the passage for each answer.",
        TABLE1_STRUCTURE,
        TABLE1_ANSWERS,
        max_words=1,
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
        QuestionType.MATCHING_FEATURES,
        "Look at the following characteristics (Questions 14\u201318) and "
        "the list of species below.\n"
        "Match each feature with the correct species, A, B or C.\n"
        "Write the correct letter, A, B or C.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        SPECIES_OPTIONS,
        SPECIES_ITEMS,
        options_heading="List of species",
    )
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 2 has SEVEN paragraphs, A\u2013G.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter, A\u2013G.",
        P2_PARAGRAPH_OPTIONS,
        P2_INFORMATION_ITEMS,
    )
    await w.sentences(
        "Complete the summary below.\n"
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
        "Complete the summary using the list of words/phrases, A\u2013J, "
        "below.\n"
        f"Write the correct letter, A\u2013J.\n{SCREEN_LETTER_HINT}",
        P3_SUMMARY_OPTIONS,
        P3_SUMMARY_ITEMS,
        options_heading="Words/phrases",
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
