"""Seed Practice Set B Test 6 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 6. Keys from the printed
Answer Key (pp.184-185). Teaching strategy pages are omitted.

Passage 1  Q1-5   note_completion       uses of freeze-drying
           Q6-9   diagram_labeling      freeze-drying machine
           Q10-13 summary_completion    freeze-drying advantages
Passage 2  Q14-19 true_false_ng         urban wildlife
           Q20-23 short_answer          gardens / birds
           Q24-26 multi_select          three benefits A-G
           Q27    mcq
Passage 3  Q28-33 matching_headings     paragraphs A-F
           Q34-40 matching_features     ideas → theories A-C

Passage text lives in scripts/data/practice_b_t6/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t6_reading.py
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

TEST_NUMBER = 6
DIAGRAM_IMAGE_URL = f"/media/images/practice_b_t{TEST_NUMBER}_reading_diagram.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Uses of freeze-drying",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("food preservation")]},
                {
                    "segments": [
                        text("easy "),
                        gap("n1"),
                        text(" of food items"),
                    ]
                },
                {
                    "segments": [
                        text("long-term storage of "),
                        gap("n2"),
                        text(" and biological samples"),
                    ]
                },
                {
                    "segments": [
                        text("preservation of precious "),
                        gap("n3"),
                    ]
                },
            ],
        },
        {
            "heading": "Freeze-drying",
            "items": [
                {
                    "segments": [
                        text("is based on process of "),
                        gap("n4"),
                    ]
                },
                {
                    "segments": [
                        text("is more efficient than "),
                        gap("n5"),
                    ]
                },
            ],
        },
    ],
}

P1_NOTES_ANSWERS: list[tuple[str, list[str]]] = [
    ("n1", ["transportation", "transport"]),
    ("n2", ["pharmaceuticals"]),
    ("n3", ["manuscripts"]),
    ("n4", ["sublimation"]),
    (
        "n5",
        [
            "simple drying",
            "simple drying techniques",
        ],
    ),
]

P1_DIAGRAM_STRUCTURE: dict = {
    "variant": "notes",
    "title": "A simplified freeze-drying machine",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "image_url": DIAGRAM_IMAGE_URL,
    "sections": [
        {
            "heading": "Write the word(s) for each numbered label on the diagram above.",
            "items": [
                {"segments": [text("(6)  "), gap("d6")]},
                {
                    "segments": [
                        text("(7)  "),
                        gap("d7"),
                        text(" with heating units"),
                    ]
                },
                {"segments": [text("(8)  "), gap("d8")]},
                {"segments": [text("(9)  "), gap("d9")]},
            ],
        }
    ],
}

P1_DIAGRAM_ANSWERS: list[tuple[str, list[str]]] = [
    (
        "d6",
        [
            "freeze-drying chamber",
            "chamber",
            "freeze drying chamber",
        ],
    ),
    ("d7", ["shelves"]),
    ("d8", ["freezing coil"]),
    (
        "d9",
        [
            "refrigerator compressor",
            "compressor",
        ],
    ),
]

P1_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "paragraphs": [
        {
            "segments": [
                text(
                    "Freeze-drying prevents food from going bad by stopping "
                    "the activity of microorganisms or "
                ),
                gap("s10"),
                text(
                    ". Its advantages are that the food tastes and feels the "
                    "same as the original because both the "
                ),
                gap("s11"),
                text(
                    " are preserved. The process is carried out slowly in "
                    "order to ensure that "
                ),
                gap("s12"),
                text(
                    " does not take place. The people of one ancient mountain "
                    "civilisation were able to use this method of food "
                    "preservation because the conditions needed were present "
                    "at "
                ),
                gap("s13"),
                text("."),
            ]
        }
    ],
}

P1_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s10", ["enzymes"]),
    (
        "s11",
        [
            "composition and structure",
            "structure and composition",
        ],
    ),
    ("s12", ["overheating"]),
    ("s13", ["high altitudes"]),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "There is now more wildlife in UK cities than in the countryside.",
        "Not Given",
    ),
    (
        "Rural wildlife has been reduced by the use of pesticides on farms.",
        "True",
    ),
    (
        "In the past, hedges on farms used to link up different habitats.",
        "True",
    ),
    (
        "New urban environments are planned to provide ecological corridors "
        "for wildlife.",
        "Not Given",
    ),
    (
        "Public parks and gardens are being expanded to encourage wildlife.",
        "Not Given",
    ),
    (
        "Old industrial wastelands have damaged wildlife habitats in urban "
        "areas.",
        "False",
    ),
]

P2_SHORT_ITEMS: list[dict] = [
    {
        "prompt": "Which type of wildlife benefits most from urban gardens?",
        "correct": ["woodland species"],
        "max_words": 3,
    },
    {
        "prompt": "What type of garden plants can benefit birds and insects?",
        "correct": ["exotic flowers"],
        "max_words": 3,
    },
    {
        "prompt": "What represents a threat to wildlife in urban gardens?",
        "correct": ["domestic cats", "cats"],
        "max_words": 3,
    },
    {
        "prompt": (
            "At the last count, how many species of bird were spotted in "
            "urban gardens?"
        ),
        "correct": ["81"],
        "max_words": 3,
    },
]

P2_MULTI = {
    "question": (
        "In which THREE ways can wildlife habitats benefit people living in "
        "urban areas?"
    ),
    "options": [
        "They can make the cities greener.",
        "They can improve the climate.",
        "They can promote human well-being.",
        "They can extend the flowering season.",
        "They can absorb excess water.",
        "They can attract wildlife.",
        "They can help clean the urban atmosphere.",
    ],
    "correct": ["C", "E", "G"],
}

P2_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "The writer believes that sustainable development is dependent on",
        [
            "urban economic policy.",
            "large restoration schemes.",
            "active nature conservation.",
            "government projects.",
        ],
        "C",
    ),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_HEADINGS = [
    "i. Avoiding tiredness in athletes",
    "ii. Puzzling evidence raises a question",
    "iii. Traditional explanations",
    "iv. Interpreting the findings",
    "v. Developing muscle fibres",
    "vi. A new hypothesis",
    "vii. Description of a new test",
    "viii. Surprising results in an endurance test",
]

P3_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "iii"),
    ("Paragraph B", "vi"),
    ("Paragraph C", "ii"),
    ("Paragraph D", "vii"),
    ("Paragraph E", "viii"),
    ("Paragraph F", "iv"),
]

P3_THEORY_OPTIONS = [
    "A. the Limitations Theory",
    "B. the Central Governor Theory",
    "C. both the Limitations Theory and the Central Governor Theory",
]

P3_THEORY_ITEMS: list[tuple[str, str]] = [
    ("Lactic acid is produced in muscles during exercise.", "C"),
    (
        "Athletes can keep going until they use up all their available "
        "resources.",
        "A",
    ),
    ("Mental processes control the symptoms of tiredness.", "B"),
    (
        "The physiological signals from an athlete's muscles are linked to "
        "fatigue.",
        "C",
    ),
    (
        "The brain plans and regulates muscle performance in advance of a "
        "run.",
        "B",
    ),
    (
        "Athletes' performance during a race may be affected by lactic acid "
        "build-up.",
        "A",
    ),
    (
        "Humans are genetically programmed to keep some energy reserves.",
        "B",
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
    slots: list[int] = []

    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "Freeze-drying is a technique that can help to provide food for "
        "astronauts. But it also has other applications nearer home."
    )
    print(
        f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each answer.\n"
        "Write your answers in boxes 1–5 on your answer sheet.",
        P1_NOTES_STRUCTURE,
        P1_NOTES_ANSWERS,
        max_words=3,
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Label the diagram below.\n"
        "Choose NO MORE THAN TWO WORDS from the passage for each answer.\n"
        "Write your answers in boxes 6–9 on your answer sheet.",
        P1_DIAGRAM_STRUCTURE,
        P1_DIAGRAM_ANSWERS,
        max_words=2,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose NO MORE THAN THREE WORDS AND/OR A NUMBER from the passage "
        "for each answer.\n"
        "Write your answers in boxes 10–13 on your answer sheet.",
        P1_SUMMARY_STRUCTURE,
        P1_SUMMARY_ANSWERS,
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
        "The countryside is no longer the place to see wildlife, according to "
        "Chris Barnes. These days you are more likely to find impressive "
        "numbers of skylarks, dragonflies and toads in your own back garden."
    )
    print(
        f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information given in "
        "Reading Passage 2?\n"
        "In boxes 14–19 on your answer sheet write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P2_TFNG_ITEMS,
    )
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "Answer the questions below, using NO MORE THAN THREE WORDS AND/OR "
        "A NUMBER from the passage for each answer.\n"
        "Write your answers in boxes 20–23 on your answer sheet.",
        P2_SHORT_ITEMS,
    )
    await w.multi_select(
        "Choose THREE letters A–G.\n"
        "Write your answers in boxes 24–26 on your answer sheet.",
        P2_MULTI,
    )
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
        "Write your answer in box 27 on your answer sheet.",
        P2_MCQ_ITEMS,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "A revolutionary new theory in sports physiology."
    )
    print(
        f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 3 has eleven paragraphs A–K.\n"
        "Choose the correct heading for Paragraphs A–F from the list of "
        "headings below.\n"
        "Write the correct number (i–viii) in boxes 28–33 on your answer sheet.",
        P3_HEADINGS,
        P3_HEADING_ITEMS,
        options_heading="List of headings",
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Classify the following ideas as relating to\n"
        "A the Limitations Theory\n"
        "B the Central Governor Theory\n"
        "C both the Limitations Theory and the Central Governor Theory\n"
        "Write the correct letter, A, B or C, in boxes 34–40 on your answer "
        "sheet.\n"
        "NB You may use any letter more than once.",
        P3_THEORY_OPTIONS,
        P3_THEORY_ITEMS,
        options_heading="List of theories",
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
