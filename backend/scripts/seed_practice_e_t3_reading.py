"""Seed Practice Set E Test 3 Reading, all three passages (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 3.
Keys from the printed Explanatory Answer Key (pp.150-153).

Passage 1  Q1-4   matching_information  Unmasking skin paragraphs (A-J)
           Q5-6   mcq                   skin/touch effects (A-D)
           Q7-11  matching_endings      sentence completion (A-I)
           Q12-14 true_false_ng
Passage 2  Q15-19 matching_headings     How Lock Picking Works (i-x)
           Q20-22 short_answer          cylinder lock diagram (THREE WORDS)
           Q23-25 short_answer          lock picking notes (THREE WORDS)
           Q26-27 short_answer          lock types table (THREE WORDS)
Passage 3  Q28-31 yes_no_ng             management models
           Q32-37 summary_completion    US model in Britain (word list)
           Q38-39 short_answer          European model notes (THREE WORDS)
           Q40    mcq                   writer's main purpose (A-D)

Passage text lives in scripts/data/practice_e_t3/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t3_reading.py
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

TEST_NUMBER = 3


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 — Unmasking skin ───────────────────────────────────────────────

# Q1-4: Matching information — which paragraph contains …?
P1_PARAGRAPH_OPTIONS = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
]

P1_PARAGRAPH_ITEMS: list[tuple[str, str]] = [
    ("the features of human skin, on and below the surface", "B"),
    ("an experiment in which the writer can see what is happening", "H"),
    ("advice on how you can avoid damage to the skin", "J"),
    ("cruel research methods used in the past", "D"),
]

# Q5-6: MCQ
P1_MCQ: list[dict] = [
    {
        "question": "How does a lack of affectionate touching affect children?",
        "options": [
            "It makes them apathetic.",
            "They are more likely to become violent adults.",
            "They will be less aggressive when they grow up.",
            "We do not really know.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "After the \u2018wetness\u2019 experiments, the writer says that"
        ),
        "options": [
            "his skin is not normal.",
            "his skin was wet when it felt wet.",
            "he knew why it felt wet when it was dry.",
            "the experiments taught him nothing new.",
        ],
        "correct": "C",
    },
]

# Q7-11: Complete each sentence with the correct ending A-I
P1_ENDINGS = [
    "A. because it is both cold and painful.",
    "B. because the outer layer of the skin can mend itself.",
    "C. because it can be extremely thin.",
    "D. because there is light pressure on the skin.",
    "E. because we do not need the others to survive.",
    "F. because there is a good blood supply to the skin.",
    "G. because of a small amount of pain.",
    "H. because there is a low temperature and pressure.",
    "I. because it is hurting a lot.",
]

P1_ENDING_ITEMS: list[tuple[str, str]] = [
    ("Touch is unique among the five senses", "E"),
    ("A substance may feel wet", "H"),
    ("Something may tickle", "D"),
    ("The skin may itch", "G"),
    ("A small cut heals up quickly", "B"),
]

# Q12-14: True/False/Not Given
P1_TFNG: list[tuple[str, str]] = [
    (
        "Even scientists have difficulty understanding how "
        "our sense of touch works.",
        "True",
    ),
    (
        "The skin is more sensitive to pressure than to "
        "temperature or pain.",
        "Not Given",
    ),
    (
        "The human skin is always good at repairing itself.",
        "False",
    ),
]


# ── Passage 2 — How Lock Picking Works ───────────────────────────────────────

# Q15-19: Matching headings to sections A-E
P2_HEADINGS = [
    "i. How to make the locks in your home more secure",
    "ii. How to open a lock without a key",
    "iii. Choosing the right tools to open locks",
    "iv. The cylinder and the bolt",
    "v. How to open a lock with a different key",
    "vi. Lock varieties",
    "vii. How a basic deadbolt system works",
    "viii. The people who open locks without a key",
    "ix. How a cylinder lock works",
    "x. How to pick different kinds of lock",
]

P2_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Section A", "viii"),
    ("Section B", "vii"),
    ("Section C", "ix"),
    ("Section D", "ii"),
    ("Section E", "vi"),
]

# Q20-22: Diagram completion — cylinder lock (THREE WORDS)
P2_DIAGRAM: list[tuple[str, list[str]]] = [
    (
        "What is the outer part of the lock which does not move?",
        ["(the) housing", "housing"],
    ),
    (
        "What is in the middle of the lock, turned by the key?",
        ["(the) cylinder", "cylinder"],
    ),
    (
        "What are the pairs of metal objects of varying length "
        "inside the shafts?",
        ["(metal) pins", "pins"],
    ),
]

# Q23-25: Notes completion — picking a lock (THREE WORDS)
P2_PICKING_NOTES: list[tuple[str, list[str]]] = [
    (
        "What do you insert and turn to slightly offset the cylinder?",
        ["(a/the) (tension) wrench", "(the) tension wrench",
         "tension wrench", "(a) tension wrench", "a tension wrench",
         "the tension wrench", "(a/the) wrench", "wrench"],
    ),
    (
        "What do you slide in while applying pressure on the cylinder?",
        ["(a/the) pick", "pick", "a pick", "the pick"],
    ),
    (
        "Where is the upper pin held after it falls into position?",
        ["(the) ledge", "ledge", "(the) ledge (in shaft)",
         "the ledge in shaft", "ledge in shaft"],
    ),
]

# Q26-27: Table completion — lock types (THREE WORDS)
P2_TABLE_ITEMS: list[tuple[str, list[str]]] = [
    (
        "How secure are pin locks?",
        ["moderate security", "moderate(ly) security",
         "moderately secure"],
    ),
    (
        "What type of lock is found in most cars?",
        ["wafer", "(the) wafer (lock)", "wafer lock"],
    ),
]


# ── Passage 3 — Managing cultural diversity ──────────────────────────────────

# Q28-31: Yes/No/Not Given
P3_YNNG: list[tuple[str, str]] = [
    (
        "Attempts by British and mainland European firms "
        "to work together often fail.",
        "Yes",
    ),
    (
        "Project management principles discourage "
        "consideration of long-term issues.",
        "Yes",
    ),
    (
        "There are good opportunities for promotion within "
        "segmented companies.",
        "No",
    ),
    (
        "The European model gives more freedom of action "
        "to junior managers.",
        "No",
    ),
]

# Q32-37: Summary completion from word list
P3_WORD_LIST = [
    "argument", "temperature", "reach", "manufacturing",
    "increasing", "able", "office", "pressure",
    "negative", "predict", "declining", "agreement",
    "discussion", "no", "willing", "unwilling",
]

P3_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Effects of the US model in Britain",
    "instruction_words": "from the box",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                text(
                    "Adopting the US model in Britain has had negative "
                    "effects. These include the "
                ),
                gap("w32"),
                text(
                    " hours spent at work, as small sections of large "
                    "organizations struggle to "
                ),
                gap("w33"),
                text(
                    " unrealistic short-term objectives. Nor is there "
                ),
                gap("w34"),
                text(
                    " on how to calculate the productivity of "
                    "professional, technical, and clerical staff, "
                    "who cannot be assessed in the same way as "
                ),
                gap("w35"),
                text(
                    " employees. In addition, managers within this "
                    "culture are finding the "
                ),
                gap("w36"),
                text(
                    " of work too great, with 80% reported to be "
                ),
                gap("w37"),
                text(
                    " to carry on working until the normal "
                    "retirement age."
                ),
            ]
        },
    ],
}

P3_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("w32", ["increasing"]),
    ("w33", ["reach"]),
    ("w34", ["agreement"]),
    ("w35", ["manufacturing"]),
    ("w36", ["pressure"]),
    ("w37", ["unwilling"]),
]

# Q38-39: Notes completion (THREE WORDS)
P3_NOTES: list[tuple[str, list[str]]] = [
    (
        "Working conditions in mainland Europe are in practice "
        "more likely to be \u2026",
        ["family-friendly", "family friendly"],
    ),
    (
        "UK managers working to tight deadlines probably "
        "give up some of their \u2026",
        ["(annual) leave", "annual leave", "leave"],
    ),
]

# Q40: MCQ
P3_MCQ: list[dict] = [
    {
        "question": (
            "Which of the following statements best describes the "
            "writer\u2019s main purpose in Reading Passage 3?"
        ),
        "options": [
            "to argue that Britain should have adopted the "
            "Japanese model of management many years ago",
            "to criticize Britain\u2019s adoption of the US model, "
            "as compared to the European model",
            "to propose a completely new model that would be "
            "neither American nor European",
            "to point out the negative effects of the existing "
            "model on the management of hospitals in Britain",
        ],
        "correct": "B",
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

    # -- Passage 1: Unmasking skin --
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
        QuestionType.MATCHING_INFORMATION,
        "The passage has 10 paragraphs A\u2013J.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter A\u2013J.",
        P1_PARAGRAPH_OPTIONS,
        P1_PARAGRAPH_ITEMS,
        options_heading="Paragraph",
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P1_MCQ,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending "
        "A\u2013I from the box below.\n"
        f"{SCREEN_LETTER_HINT}",
        P1_ENDINGS,
        P1_ENDING_ITEMS,
        options_heading="Sentence endings",
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information "
        "given in Reading Passage 1?\n"
        "Write TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P1_TFNG,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 2: How Lock Picking Works --
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
        "Reading Passage 2 has five sections A\u2013E.\n"
        "Choose the most suitable heading for each section "
        "from the list below.\n"
        "Write the correct number i\u2013x.",
        P2_HEADINGS,
        P2_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.short_answer(
        "Complete the diagram below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage "
        "for each answer.",
        P2_DIAGRAM,
        max_words=3,
    )
    await w.short_answer(
        "Complete the notes below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage "
        "for each answer.",
        P2_PICKING_NOTES,
        max_words=3,
    )
    await w.short_answer(
        "Complete the table below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage "
        "for each answer.",
        P2_TABLE_ITEMS,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 3: Managing cultural diversity --
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
        "Do the following statements agree with the writer\u2019s "
        "views in Reading Passage 3?\n"
        "Write YES if the statement agrees with the views "
        "of the writer\n"
        "NO if the statement does not agree with the views "
        "of the writer\n"
        "NOT GIVEN if there is no information about this "
        "in the passage",
        P3_YNNG,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose the answers from the box and write the "
        "corresponding words in boxes 32\u201337.",
        P3_SUMMARY_STRUCTURE,
        P3_SUMMARY_ANSWERS,
        max_words=1,
    )
    await w.short_answer(
        "Complete the notes below.\n"
        "Choose NO MORE THAN THREE WORDS from Reading "
        "Passage 3 for each answer.",
        P3_NOTES,
        max_words=3,
    )
    await w.mcq(
        "Choose the correct letter A, B, C or D.",
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
