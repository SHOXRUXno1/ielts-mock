"""Seed Practice Set B Test 5 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 5. Keys from the printed
Answer Key (pp.181-183). Teaching strategy pages are omitted.

Passage 1  Q1-5   mcq                   Eastgate / termite mounds
           Q6-10  sentence_completion   building features
           Q11-13 note_completion       three cultural features (any order)
Passage 2  Q14-19 matching_headings     paragraphs B-G
           Q20-22 matching_features     people → opinions A-F
           Q23-26 summary_completion    neuromarketing
Passage 3  Q27-32 true_false_ng         Ascension island
           Q33-37 matching_features     sentence endings A-G
           Q38-40 mcq

Passage text lives in scripts/data/practice_b_t5/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t5_reading.py
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
from seed_practice_b_common import (  # noqa: E402
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

P1_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "Why do termite mounds have a system of vents?",
        [
            "to allow the termites to escape from predators",
            "to enable the termites to produce food",
            "to allow the termites to work efficiently",
            "to enable the termites to survive at night",
        ],
        "B",
    ),
    (
        "Why was Eastgate cheaper to build than a conventional building?",
        [
            "Very few materials were imported.",
            "Its energy consumption was so low.",
            "Its tenants contributed to the costs.",
            "No air conditioners were needed.",
        ],
        "D",
    ),
    (
        "Why would a building like Eastgate not work efficiently in New York?",
        [
            "Temperature change occurs seasonally rather than daily.",
            "Pollution affects the storage of heat in the atmosphere.",
            "Summer and winter temperatures are too extreme.",
            "Levels of humidity affect cloud coverage.",
        ],
        "A",
    ),
    (
        "What does Ove Arup's data suggest about Eastgate's temperature "
        "control system?",
        [
            "It allows a relatively wide range of temperatures.",
            "The only problems are due to human error.",
            "It functions well for most of the year.",
            "The temperature in the atrium may fall too low.",
        ],
        "C",
    ),
    (
        "Pearce believes that his building would be improved by",
        [
            "becoming more of a habitat for wildlife.",
            "even closer links with the history of Zimbabwe.",
            "giving people more space to interact with nature.",
            "better protection from harmful organisms.",
        ],
        "A",
    ),
]

P1_SENTENCES: list[dict] = [
    {
        "prompt": "Warm air leaves the offices through ______.",
        "correct": ["ceiling vents", "ceiling vent"],
    },
    {
        "prompt": "The warm air leaves the building through ______.",
        "correct": [
            "brick chimneys",
            "the brick chimneys",
            "chimneys",
            "the chimneys",
            "forty-eight brick chimneys",
        ],
    },
    {
        "prompt": (
            "Heat from the sun is prevented from reaching the windows by ______."
        ),
        "correct": ["cement arches", "arches"],
    },
    {
        "prompt": (
            "When the outside temperature drops, ______ bring air in from "
            "outside."
        ),
        "correct": ["the big fans", "big fans", "fans"],
    },
    {
        "prompt": (
            "On cold days, ______ raise the temperature in the offices."
        ),
        "correct": [
            "the small heaters",
            "small heaters",
            "the heaters",
            "heaters",
        ],
    },
]

# Paper: three cultural features in any order. Same pool on each gap.
CULTURE_POOL = [
    "the entrances",
    "entrances",
    "the elevators",
    "elevators",
    "the fan covers",
    "fan covers",
]

P1_CULTURE_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Eastgate Building features reflecting Zimbabwe's history and culture",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "The three answers may be given in any order.",
            "items": [{"segments": [gap(f"c{n}")]} for n in (11, 12, 13)],
        }
    ],
}

P1_CULTURE_ANSWERS: list[tuple[str, list[str]]] = [
    (f"c{n}", CULTURE_POOL) for n in (11, 12, 13)
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_HEADINGS = [
    "i. A description of the procedure",
    "ii. An international research project",
    "iii. An experiment to investigate consumer responses",
    "iv. Marketing an alternative name",
    "v. A misleading name?",
    "vi. A potentially profitable line of research",
    "vii. Medical dangers of the technique",
    "viii. Drawbacks to marketing tools",
    "ix. Broadening applications",
    "x. What is neuromarketing?",
]

P2_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "v"),
    ("Paragraph C", "i"),
    ("Paragraph D", "ix"),
    ("Paragraph E", "viii"),
    ("Paragraph F", "iii"),
    ("Paragraph G", "vi"),
]

P2_OPINIONS = [
    "A. Neuromarketing could be used to contribute towards the cost of "
    "medical technology.",
    "B. Neuromarketing could use introspection as a tool in marketing research.",
    "C. Neuromarketing could be a means of treating medical problems.",
    "D. Neuromarketing could make an existing problem worse.",
    "E. Neuromarketing could lead to the misuse of medical equipment.",
    "F. Neuromarketing could be used to prevent the exploitation of consumers.",
]

P2_OPINION_ITEMS: list[tuple[str, str]] = [
    ("Steven Quartz", "F"),
    ("Gary Ruskin", "D"),
    ("Tim Ambler", "A"),
]

P2_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                text(
                    "Neuromarketing can provide valuable information on "
                    "attitudes to particular "
                ),
                gap("s23"),
                text(
                    ". It may be more reliable than surveys, where people "
                    "can be "
                ),
                gap("s24"),
                text(
                    ", or focus groups, where they may be influenced by "
                    "others. It also allows researchers to identify the "
                    "subject's "
                ),
                gap("s25"),
                text(
                    " thought patterns. However, some people are concerned "
                    "that it could lead to problems such as an increase in "
                    "disease among "
                ),
                gap("s26"),
                text("."),
            ]
        }
    ],
}

P2_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s23", ["brands"]),
    ("s24", ["untruthful"]),
    ("s25", ["unconscious"]),
    ("s26", ["children"]),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "When Peter Osbeck visited Ascension, he found no inhabitants on "
        "the island.",
        "Not Given",
    ),
    (
        "The natural vegetation on the island contained some species which "
        "were found nowhere else.",
        "True",
    ),
    (
        "Joseph Hooker assumed that human activity had caused the decline "
        "in the island's plant life.",
        "False",
    ),
    (
        "British sailors on the island took part in a major tree planting "
        "project.",
        "True",
    ),
    (
        "Hooker sent details of his planting scheme to a number of different "
        "countries.",
        "Not Given",
    ),
    (
        "The bamboo and prickly pear seeds sent from England were unsuitable "
        "for Ascension.",
        "False",
    ),
]

P3_ENDINGS = [
    "A. other rainforests may have originally been planted by man.",
    "B. many of the island's original species were threatened with destruction.",
    "C. the species in the original rainforest were more successful than the "
    "newer arrivals.",
    "D. rainforests can only develop through a process of slow and complex "
    "evolution.",
    "E. steps should be taken to prevent the destruction of the original "
    "ecosystem.",
    "F. randomly introduced species can coexist together.",
    "G. the introduced species may have less ecological significance than the "
    "original ones.",
]

P3_ENDING_ITEMS: list[tuple[str, str]] = [
    (
        "The reason for modern conservationists' concern over Hooker's tree "
        "planting programme is that",
        "B",
    ),
    (
        "David Wilkinson says the creation of the rainforest in Ascension is "
        "important because it shows that",
        "F",
    ),
    (
        "Wilkinson says the existence of Ascension's rainforest challenges "
        "the theory that",
        "D",
    ),
    (
        "Alan Gray questions Wilkinson's theory, claiming that",
        "G",
    ),
    (
        "Additional support for Wilkinson's theory comes from findings that",
        "A",
    ),
]

P3_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "Wilkinson suggests that conservationists' concern about the island "
        "is misguided because",
        [
            "it is based on economic rather than environmental principles.",
            "it is not focusing on the most important question.",
            "it is encouraging the destruction of endemic species.",
            "it is not supported by the local authorities.",
        ],
        "B",
    ),
    (
        "According to Wilkinson, studies of insects on the island could "
        "demonstrate",
        [
            "the possibility of new ecological relationships.",
            "a future threat to the ecosystem of the island.",
            "the existence of previously unknown species.",
            "a chance for the survival of rainforest ecology.",
        ],
        "A",
    ),
    (
        "Overall, what feature of the Ascension rainforest does the writer "
        "stress?",
        [
            "the conflict of natural and artificial systems",
            "the unusual nature of its ecological structure",
            "the harm done by interfering with nature",
            "the speed and success of its development",
        ],
        "D",
    ),
]


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
    slots: list[int] = []

    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "Termite mounds were the inspiration for an innovative design in "
        "sustainable living"
    )
    print(
        f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
        "Write your answers in boxes 1–5 on your answer sheet.",
        P1_MCQ_ITEMS,
    )
    await w.sentences(
        "Complete the sentences below with words taken from Reading Passage 1.\n"
        "Use NO MORE THAN THREE WORDS for each answer.\n"
        "Write your answers in boxes 6–10 on your answer sheet.",
        P1_SENTENCES,
        max_words=3,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Answer the question below, using NO MORE THAN THREE WORDS from the "
        "passage for each answer.\n"
        "Write your answers in boxes 11–13 on your answer sheet.\n"
        "Which three parts of the Eastgate Building reflect important features "
        "of Zimbabwe's history and culture?",
        P1_CULTURE_STRUCTURE,
        P1_CULTURE_ANSWERS,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "Could brain-scanning technology provide an accurate way to assess "
        "the appeal of new products and the effectiveness of advertising?"
    )
    print(
        f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 2 has ten paragraphs A–J.\n"
        "Choose the correct heading for Paragraphs B–G from the list of "
        "headings below.\n"
        "Write the correct number (i–x) in boxes 14–19 on your answer sheet.",
        P2_HEADINGS,
        P2_HEADING_ITEMS,
        options_heading="List of headings",
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the following people (Questions 20–22) and the list of "
        "opinions below.\n"
        "Match each person with the opinion credited to him.\n"
        "Write the correct letter A–F in boxes 20–22 on your answer sheet.",
        P2_OPINIONS,
        P2_OPINION_ITEMS,
        options_heading="List of opinions",
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below using words from the passage.\n"
        "Choose ONE WORD ONLY from the passage for each answer.\n"
        "Write your answers in boxes 23–26 on your answer sheet.",
        P2_SUMMARY_STRUCTURE,
        P2_SUMMARY_ANSWERS,
        max_words=1,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "According to ecological theory, rainforests are supposed to develop "
        "slowly over millions of years. But now ecologists are being forced "
        "to reconsider their ideas"
    )
    print(
        f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information given in "
        "Reading Passage 3?\n"
        "In boxes 27–32 on your answer sheet write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P3_TFNG_ITEMS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending A–G from the box "
        "below.\n"
        "Write the correct letter A–G in boxes 33–37 on your answer sheet.",
        P3_ENDINGS,
        P3_ENDING_ITEMS,
        options_heading="List of endings",
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.\n"
        "Write your answers in boxes 38–40 on your answer sheet.",
        P3_MCQ_ITEMS,
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
        f"\nDone. Reading seeded: rows {counts} / slots {slots} = {total_slots}."
    )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
