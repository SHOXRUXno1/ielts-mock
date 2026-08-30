"""Seed Practice Set B Test 2 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 2. Keys from the printed
Answer Key (pp.170-173). Teaching strategy pages are omitted.

Passage 1  Q1-6   matching_headings     paragraphs B and D-H
           Q7-10  mcq                   Kahneman's work / house-owners / etc.
           Q11-13 short_answer          two occupations / practical skill / business type
Passage 2  Q14-18 true_false_ng         inventors of cinema / directors / western countries
           Q19-25 note_completion       Chinese / Indian / Japanese cinema
           Q26    mcq                   main idea / title
Passage 3  Q27-32 matching_information  paragraph containing information
           Q33-35 diagram_labeling      cross section of Kuijpers' road
           Q36-40 table_completion      components and function (word bank A-K)

Passage text lives in scripts/data/practice_b_t2/ so the prose stays
proofreadable instead of buried in string literals.

Idempotent: each passage section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t2_reading.py
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
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_b_common import (  # noqa: E402
    SNOWGUN_IMAGE_URL,
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

P1_HEADINGS = [
    "i. Not identifying the correct priorities",
    "ii. A solution for the long term",
    "iii. The difficulty of changing your mind",
    "iv. Why looking back is unhelpful",
    "v. Strengthening inner resources",
    "vi. A successful approach to the study of decision-making",
    "vii. The danger of trusting a global market",
    "viii. Reluctance to go beyond the familiar",
    "ix. The power of the first number",
    "x. The need for more effective risk assessment",
    "xi. Underestimating the difficulties ahead",
]

# Paragraph A is the printed example (x). Paragraph C is also given (xi).
P1_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "vi"),
    ("Paragraph D", "ix"),
    ("Paragraph E", "iii"),
    ("Paragraph F", "viii"),
    ("Paragraph G", "i"),
    ("Paragraph H", "iv"),
]

P1_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "People initially found Kahneman's work unusual because he",
        [
            "saw mistakes as following predictable patterns.",
            "was unaware of behavioural approaches.",
            "dealt with irrational types of practice.",
            "applied psychology to finance and economics.",
        ],
        "D",
    ),
    (
        "The writer mentions house-owners' attitudes towards the value of their "
        "homes to illustrate that",
        [
            "past failures may destroy an optimistic attitude.",
            "people tend to exaggerate their chances of success.",
            "optimism may be justified in certain circumstances.",
            "people are influenced by the success of others.",
        ],
        "B",
    ),
    (
        "Stubbornness and inflexibility can cause problems when people",
        [
            "think their financial difficulties are just due to bad luck.",
            "avoid seeking advice from experts and analysts.",
            "refuse to invest in the early stages of a project.",
            "are unwilling to give up unsuccessful activities or beliefs.",
        ],
        "D",
    ),
    (
        "Why do many Americans and Europeans fail to spread their financial "
        "risks when investing?",
        [
            "They feel safer dealing in a context which is close to home.",
            "They do not understand the benefits of diversification.",
            "They are over-influenced by the successes of their relatives.",
            "They do not have sufficient knowledge of one another's countries.",
        ],
        "A",
    ),
]

P1_SHORT_ITEMS: list[dict] = [
    {
        "prompt": "Which two occupations may benefit from being over-optimistic?",
        "correct": [
            "managers and sportsmen",
            "managers or sportsmen",
            "managers sportsmen",
            "sportsmen and managers",
        ],
        "max_words": 3,
    },
    {
        "prompt": "Which practical skill are many people over-confident about?",
        "correct": ["driving"],
        "max_words": 3,
    },
    {
        "prompt": "Which type of business has a generally good attitude to dealing with uncertainty?",
        "correct": [
            "Pharmaceutical companies",
            "pharmaceutical companies",
            "pharmaceutical",
            "drug companies",
        ],
        "max_words": 3,
    },
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_TFNG_ITEMS: list[tuple[str, str]] = [
    ("The inventors of cinema regarded it as a minor attraction.", "True"),
    (
        "Some directors were aware of cinema's artistic possibilities from the "
        "very beginning.",
        "False",
    ),
    ("The development of cinema's artistic potential depended on technology.", "Not Given"),
    (
        "Cinema's possibilities were developed in varied ways in different "
        "western countries.",
        "True",
    ),
    (
        "Western businessmen were concerned about the emergence of film industries "
        "in other parts of the world.",
        "False",
    ),
]

P2_WORD_BANK = [
    "A. emotional",
    "B. negative",
    "C. expensive",
    "D. silent",
    "E. social",
    "F. outstanding",
    "G. little",
    "H. powerful",
    "I. realistic",
    "J. stylistic",
    "K. economic",
]

P2_NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "",
    "instruction_words": "list of words A-K",
    "max_words_per_gap": 3,
    "options": P2_WORD_BANK,
    "sections": [
        {
            "heading": "Chinese cinema",
            "items": [
                {
                    "segments": [
                        text("large number of "),
                        gap("n19"),
                        text(" films produced in 1930s"),
                    ]
                },
                {
                    "segments": [
                        text("some early films still generally regarded as "),
                        gap("n20"),
                    ]
                },
            ],
        },
        {
            "heading": "Indian cinema",
            "items": [
                {"segments": [text("films included musical interludes")]},
                {
                    "segments": [
                        text("films avoided "),
                        gap("n21"),
                        text(" topics"),
                    ]
                },
            ],
        },
        {
            "heading": "Japanese cinema",
            "items": [
                {
                    "segments": [
                        text("unusual because film director was very "),
                        gap("n22"),
                    ]
                },
                {"segments": [text("two important directors:")]},
                {
                    "segments": [
                        text("Mizoguchi – focused on the "),
                        gap("n23"),
                        text(" restrictions faced by women"),
                    ]
                },
                {
                    "segments": [
                        text("- camera movement related to "),
                        gap("n24"),
                        text(" content of film"),
                    ]
                },
                {
                    "segments": [
                        text("Ozu – "),
                        gap("n25"),
                        text(" camera movement"),
                    ]
                },
            ],
        },
    ],
}

P2_NOTES_ANSWERS: list[tuple[str, list[str]]] = [
    ("n19", ["D", "silent"]),
    ("n20", ["F", "outstanding"]),
    ("n21", ["B", "negative"]),
    ("n22", ["H", "powerful"]),
    ("n23", ["E", "social"]),
    ("n24", ["A", "emotional"]),
    ("n25", ["G", "little"]),
]

P2_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "Which of the following is the most suitable title for Reading Passage 2?",
        [
            "Blind to change: how is it that the west has ignored Asian cinema for so long?",
            "A different basis: how has the cinema of Asian countries been shaped by their cultures and beliefs?",
            "Outside Asia: how did the origins of cinema affect its development worldwide?",
            "Two cultures: how has western cinema tried to come to terms with the challenge of the Asian market?",
        ],
        "B",
    ),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_PARAGRAPH_OPTIONS = [
    "A. Paragraph A",
    "B. Paragraph B",
    "C. Paragraph C",
    "D. Paragraph D",
    "E. Paragraph E",
    "F. Paragraph F",
    "G. Paragraph G",
    "H. Paragraph H",
    "I. Paragraph I",
    "J. Paragraph J",
]

P3_INFORMATION_ITEMS: list[tuple[str, str]] = [
    (
        "a description of the form in which Kuijpers' road surface is taken to "
        "its destination",
        "G",
    ),
    ("an explanation of how Kuijpers makes a smooth road surface", "D"),
    ("something that has to be considered when evaluating Kuijpers' proposal", "J"),
    ("various economic reasons for reducing road noise", "B"),
    ("a generalisation about the patterns of use of vehicles on major roads", "I"),
    ("a summary of the different things affecting levels of noise on roads", "C"),
]

P3_ROAD_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Cross section of Kuijpers' proposed noise-reducing road",
    "instruction_words": "NO MORE THAN ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "image_url": SNOWGUN_IMAGE_URL.format(test=TEST_NUMBER),
    "sections": [
        {
            "heading": "Write the word(s) or number for each numbered label on the diagram above.",
            "items": [
                {"segments": [text("(33)  "), gap("d33")]},
                {"segments": [text("(34)  stones (approx. "), gap("d34"), text(" mm diameter)")]},
                {"segments": [text("(35)  "), gap("d35")]},
            ],
        }
    ],
}

P3_ROAD_ANSWERS: list[tuple[str, list[str]]] = [
    ("d33", ["asphalt"]),
    ("d34", ["9", "nine"]),
    ("d35", ["concrete"]),
]

P3_TABLE_BANK = [
    "A. frequencies",
    "B. the engine",
    "C. rubbish",
    "D. resonators",
    "E. air flow",
    "F. dissipation",
    "G. sound energy",
    "H. pores",
    "I. lanes",
    "J. drainage",
    "K. sources",
]

P3_TABLE_STRUCTURE: dict = {
    "variant": "table",
    "title": "Kuijpers' noise-reducing road: components and function",
    "instruction_words": "list of words A-K",
    "max_words_per_gap": 3,
    "options": P3_TABLE_BANK,
    "headers": ["Layer", "Component", "Function"],
    "rows": [
        [
            {"variant": "plain", "segments": [text("upper and lower")]},
            {"variant": "plain", "segments": [text("stones")]},
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("reduce oscillations caused by "),
                            gap("t36"),
                        ]
                    },
                    {
                        "segments": [
                            text("create pores which help "),
                            gap("t37"),
                        ]
                    },
                ],
            },
        ],
        [
            {"variant": "plain", "segments": [text("foundation")]},
            {"variant": "plain", "segments": [text("slots")]},
            {
                "variant": "bullets",
                "bullets": [
                    {
                        "segments": [
                            text("convert "),
                            gap("t38"),
                            text(" to heat"),
                        ]
                    },
                    {
                        "segments": [
                            text("help to remove "),
                            gap("t39"),
                        ]
                    },
                    {
                        "segments": [
                            text("can be adapted to absorb different "),
                            gap("t40"),
                        ]
                    },
                ],
            },
        ],
    ],
}

P3_TABLE_ANSWERS: list[tuple[str, list[str]]] = [
    ("t36", ["E", "air flow"]),
    ("t37", ["J", "drainage"]),
    ("t38", ["G", "sound energy"]),
    ("t39", ["C", "rubbish"]),
    ("t40", ["A", "frequencies"]),
]


# ── writing helpers (mirror t1_reading) ──────────────────────────────────────


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

    async def mcq(self, instruction: str, items: list[tuple[str, list[str], str]]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for question, options, correct in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": question, "options": options},
                {"correct": correct},
            )

    async def free_text(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[dict],
    ) -> None:
        group = await self._group(question_type, instruction)
        for item in items:
            self._add(
                group,
                question_type,
                {
                    "prompt": item["prompt"],
                    "question": item["prompt"],
                    "max_words": item["max_words"],
                },
                {
                    "correct": item["correct"],
                    "max_words": item["max_words"],
                    "case_sensitive": False,
                },
            )

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str]]],
        *,
        max_words: int,
    ) -> None:
        group = await self._group(question_type, instruction, options_shared=structure)
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

    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = "Human intuition is a bad guide to handling risk"
    print(f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 1 has nine paragraphs A-I.\n"
        "Choose the correct heading for Paragraphs B and D-H from the list of "
        "headings below.\n"
        "Write the correct number (i-xi) in boxes 1-6 on your answer sheet.\n"
        "Example: Paragraph A — x    Paragraph C — xi",
        P1_HEADINGS,
        P1_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
        "Write your answers in boxes 7-10 on your answer sheet.",
        P1_MCQ_ITEMS,
    )
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "Answer the questions below, using NO MORE THAN THREE WORDS for each answer.\n"
        "Write your answers in boxes 11-13 on your answer sheet.",
        P1_SHORT_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information given in "
        "Reading Passage 2?\n"
        "In boxes 14-18 on your answer sheet write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P2_TFNG_ITEMS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below using the list of words A-K from the box below.\n"
        "Write the correct letters in boxes 19-25 on your answer sheet.",
        P2_NOTES_STRUCTURE,
        P2_NOTES_ANSWERS,
        max_words=3,
    )
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
        "Write your answer in box 26 on your answer sheet.",
        P2_MCQ_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "The roar of passing vehicles could soon be a thing of the past"
    )
    print(f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 3 has ten paragraphs labelled A-J.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter A-J in boxes 27-32 on your answer sheet.",
        P3_PARAGRAPH_OPTIONS,
        P3_INFORMATION_ITEMS,
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the diagram below.\n"
        "Choose NO MORE THAN ONE WORD AND/OR A NUMBER from the passage for each answer.\n"
        "Write your answers in boxes 33-35 on your answer sheet.",
        P3_ROAD_STRUCTURE,
        P3_ROAD_ANSWERS,
        max_words=2,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below using the list of words A-K from the box below.\n"
        "Write the correct letters in boxes 36-40 on your answer sheet.",
        P3_TABLE_STRUCTURE,
        P3_TABLE_ANSWERS,
        max_words=3,
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
