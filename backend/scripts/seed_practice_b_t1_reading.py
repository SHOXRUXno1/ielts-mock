"""Seed Practice Set B Test 1 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 1. Keys from the printed
Answer Key (pp.168-169). Teaching strategy pages are omitted.

Passage 1  Q1-5   matching_headings     paragraphs C-G
           Q6-8   diagram_labeling      the snow gun
           Q9-13  sentence_completion
Passage 2  Q14-18 matching_information  paragraphs A-G
           Q19-23 true_false_ng
           Q24-26 mcq
Passage 3  Q27-32 matching_features     sentence endings A-H
           Q33-37 yes_no_ng
           Q38-40 summary_completion    letters A-I

Passage text lives in scripts/data/practice_b_t1/ so the prose stays
proofreadable instead of buried in string literals.

Idempotent: each passage section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t1_reading.py
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

TEST_NUMBER = 1


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_HEADINGS = [
    "i. Considering ecological costs",
    "ii. Modifications to the design of the snow gun",
    "iii. The need for different varieties of snow",
    "iv. Local concern over environmental issues",
    "v. A problem and a solution",
    "vi. Applications beyond the ski slopes",
    "vii. Converting wet snow to dry snow",
    "viii. New method for calculating modifications",
    "ix. Artificial process, natural product",
    "x. Snow formation in nature",
]

# Paragraphs A (v) and B (x) are printed examples and are not asked.
P1_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph C", "ix"),
    ("Paragraph D", "iii"),
    ("Paragraph E", "viii"),
    ("Paragraph F", "i"),
    ("Paragraph G", "vi"),
]

SNOWGUN_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The snow gun",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "image_url": SNOWGUN_IMAGE_URL.format(test=TEST_NUMBER),
    "sections": [
        {
            "heading": "Write the word(s) for each numbered label on the diagram above.",
            "items": [
                {"segments": [text("(6)  "), gap("d6")]},
                {"segments": [text("(7)  "), gap("d7")]},
                {"segments": [text("(8)  "), gap("d8")]},
            ],
        }
    ],
}

SNOWGUN_ANSWERS: list[tuple[str, list[str]]] = [
    ("d6", ["compressed"]),
    ("d7", ["droplets", "tiny droplets"]),
    ("d8", ["ice crystals"]),
]

P1_SENTENCE_ITEMS: list[dict] = [
    {
        "prompt": (
            "Dry snow is used to give slopes a level surface, while wet snow "
            "is used to increase the ______ on busy slopes."
        ),
        "correct": ["depth"],
        "max_words": 3,
    },
    {
        "prompt": (
            "To calculate the required snow consistency, the ______ and ______ "
            "of the atmosphere must first be measured."
        ),
        "correct": [
            "temperature and humidity",
            "temperature humidity",
            "humidity and temperature",
        ],
        "max_words": 3,
    },
    {
        "prompt": (
            "The machinery used in the process of making the snow consumes a "
            "lot of ______, which is damaging to the environment."
        ),
        "correct": ["energy"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Artificial snow is used in agriculture as a type of ______ for "
            "plants in cold conditions."
        ),
        "correct": ["insulation"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Artificial snow may also be used in carrying out safety checks "
            "on ______."
        ),
        "correct": ["aircraft"],
        "max_words": 3,
    },
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_PARAGRAPH_OPTIONS = [
    "A. Paragraph A",
    "B. Paragraph B",
    "C. Paragraph C",
    "D. Paragraph D",
    "E. Paragraph E",
    "F. Paragraph F",
    "G. Paragraph G",
]

P2_INFORMATION_ITEMS: list[tuple[str, str]] = [
    ("a rejected explanation of why tiger attacks on humans are rare", "C"),
    (
        "a reason why tiger attacks on humans might be expected to happen more "
        "often than they do",
        "A",
    ),
    (
        "examples of situations in which humans are more likely to be attacked "
        "by tigers",
        "F",
    ),
    ("a claim about the relative frequency of tiger attacks on humans", "B"),
    (
        "an explanation of tiger behaviour based on the principles of ethology",
        "E",
    ),
]

P2_TFNG_ITEMS: list[tuple[str, str]] = [
    ("Tigers in the Bandhavgarh National Park are a protected species.", "Not Given"),
    (
        "Some writers of fiction have exaggerated the danger of tigers to man.",
        "True",
    ),
    ("The fear of humans may be passed down in a tiger's genes.", "True"),
    (
        "Konrad Lorenz claimed that some animals are more intelligent than humans.",
        "Not Given",
    ),
    (
        "Ethology involves applying principles of human behaviour to animals.",
        "False",
    ),
]

P2_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "Why do tigers rarely attack people in cars?",
        [
            "They have learned that cars are not dangerous.",
            "They realise that people in cars cannot be harmed.",
            "They do not think people in cars are living creatures.",
            "They do not want to put their cubs at risk.",
        ],
        "C",
    ),
    (
        "The writer says that tigers rarely attack a man who is standing up because",
        [
            "they are afraid of the man's height.",
            "they are confused by the man's shape.",
            "they are puzzled by the man's lack of movement.",
            "they are unable to look at the man directly.",
        ],
        "B",
    ),
    (
        "A human is more vulnerable to tiger attack when squatting because",
        [
            "he may be unaware of the tiger's approach.",
            "he cannot easily move his head to see behind him.",
            "his head becomes a better target for the tiger.",
            "his back appears longer in relation to his height.",
        ],
        "D",
    ),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_ENDING_OPTIONS = [
    "A. the discovery of new medical applications.",
    "B. the negative effects of publicity.",
    "C. the large pharmaceutical companies.",
    "D. the industrial revolution.",
    "E. the medical uses of a particular tree.",
    "F. the limited availability of new drugs.",
    "G. the chemical found in the willow tree.",
    "H. commercial advertising campaigns.",
]

P3_ENDING_ITEMS: list[tuple[str, str]] = [
    ("Ancient Egyptian and Greek doctors were aware of", "E"),
    ("Frederick Bayer & Co were able to reproduce", "G"),
    ("The development of aspirin was partly due to the effects of", "D"),
    (
        "The creation of a market for aspirin as a painkiller was achieved through",
        "H",
    ),
    ("Aspirin might have become unavailable without", "A"),
    (
        "The way in which aspirin actually worked was not investigated by",
        "C",
    ),
]

P3_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "For nineteenth-century scientists, small-scale research was enough to "
        "make important discoveries.",
        "Yes",
    ),
    (
        "The nineteenth-century industrial revolution caused a change in the "
        "focus of scientific research.",
        "Not Given",
    ),
    (
        "The development of aspirin in the nineteenth century followed a "
        "structured pattern of development.",
        "No",
    ),
    (
        "In the 1970s sales of new analgesic drugs overtook sales of aspirin.",
        "Not Given",
    ),
    (
        "Commercial companies may have both good and bad effects on the "
        "availability of pharmaceutical products.",
        "Yes",
    ),
]

P3_WORD_BANK = [
    "A. useful",
    "B. cheap",
    "C. state",
    "D. international",
    "E. major drug companies",
    "F. profitable",
    "G. commercial",
    "H. public sector scientists",
    "I. health officials",
]

P3_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Research into aspirin",
    "instruction_words": "list of words A-I",
    "max_words_per_gap": 3,
    "options": P3_WORD_BANK,
    "paragraphs": [
        {
            "segments": [
                text("Jeffreys argues that the reason why "),
                gap("s38"),
                text(
                    " did not find out about new uses of aspirin is that aspirin "
                    "is no longer a "
                ),
                gap("s39"),
                text(
                    " drug. He therefore suggests that there should be "
                ),
                gap("s40"),
                text(
                    " support for further research into the possible applications "
                    "of the drug."
                ),
            ]
        }
    ],
}

P3_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s38", ["E", "major drug companies"]),
    ("s39", ["F", "profitable"]),
    ("s40", ["C", "state"]),
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
    section.passage_subtitle = (
        "Skiing is big business nowadays. But what can ski resort owners do "
        "if the snow doesn't come?"
    )
    print(f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 1 has seven paragraphs A-G.\n"
        "Choose the correct heading for each paragraph from the list of "
        "headings below.\n"
        "Write the correct number (i-x) in boxes 1-5 on your answer sheet.\n"
        "NB There are more headings than paragraphs, so you will not use them all.\n"
        "Example: Paragraph A — v    Paragraph B — x",
        P1_HEADINGS,
        P1_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the diagram below.\n"
        "Choose NO MORE THAN TWO WORDS from the passage for each answer.\n"
        "Write your answers in boxes 6-8 on your answer sheet.",
        SNOWGUN_STRUCTURE,
        SNOWGUN_ANSWERS,
        max_words=2,
    )
    await w.free_text(
        QuestionType.SENTENCE_COMPLETION,
        "Complete the sentences below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each answer.\n"
        "Write your answers in boxes 9-13 on your answer sheet.",
        P1_SENTENCE_ITEMS,
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
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 2 has seven paragraphs labelled A-G.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter A-G in boxes 14-18 on your answer sheet.",
        P2_PARAGRAPH_OPTIONS,
        P2_INFORMATION_ITEMS,
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information given in "
        "Reading Passage 2?\n"
        "In boxes 19-23 on your answer sheet write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P2_TFNG_ITEMS,
    )
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
        "Write your answers in boxes 24-26 on your answer sheet.",
        P2_MCQ_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "The history of aspirin is a product of a rollercoaster ride through "
        "time, of accidental discoveries, intuitive reasoning and intense "
        "corporate rivalry"
    )
    print(f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending A-H from the box below.\n"
        "Write the correct letter A-H in boxes 27-32 on your answer sheet.",
        P3_ENDING_OPTIONS,
        P3_ENDING_ITEMS,
        options_heading="Endings",
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer in "
        "Reading Passage 3?\n"
        "In boxes 33-37 on your answer sheet write\n"
        "YES if the statement agrees with the views of the writer\n"
        "NO if the statement contradicts the views of the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P3_YNNG_ITEMS,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below using the list of words A-I below.\n"
        "Write the correct letter A-I in boxes 38-40 on your answer sheet.",
        P3_SUMMARY_STRUCTURE,
        P3_SUMMARY_ANSWERS,
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
