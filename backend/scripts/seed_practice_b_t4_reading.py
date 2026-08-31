"""Seed Practice Set B Test 4 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 4. Keys from the printed
Answer Key (pp.178-180). Teaching strategy pages are omitted.

Passage 1  Q1-10  matching_information  paragraphs A-H (AFM / green sand)
           Q11-14 summary_completion    Green sand
Passage 2  Q15-19 true_false_ng         shade-grown coffee / cocoa
           Q20-23 matching_features     opinions → people A-E
           Q24-27 matching_features     features → shade / full-sun / both
Passage 3  Q28-33 matching_headings     paragraphs A-F
           Q34-37 flow_chart_completion Aboriginal painting timeline
           Q38-40 mcq

Passage text lives in scripts/data/practice_b_t4/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t4_reading.py
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

TEST_NUMBER = 4


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_PARAGRAPH_OPTIONS = [
    "A. Paragraph A",
    "B. Paragraph B",
    "C. Paragraph C",
    "D. Paragraph D",
    "E. Paragraph E",
    "F. Paragraph F",
    "G. Paragraph G",
    "H. Paragraph H",
]

P1_INFORMATION_ITEMS: list[tuple[str, str]] = [
    ("a description of plans to expand production of AFM", "D"),
    ("the identification of a potential danger in the raw material for AFM", "E"),
    ("an example of AFM use in the export market", "G"),
    ("a comparison of the value of green glass and other types of glass", "B"),
    ("a list of potential applications of AFM in the domestic market", "D"),
    (
        "the conclusions drawn from laboratory checks on the process of AFM "
        "production",
        "F",
    ),
    ("identification of current funding for the production of green sand", "A"),
    ("an explanation of the chosen brand name for crushed green glass", "C"),
    ("a description of plans for exporting AFM", "G"),
    (
        "a description of what has to happen before AFM is accepted for "
        "general use",
        "E",
    ),
]

P1_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Green sand",
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    "paragraphs": [
        {
            "segments": [
                text(
                    "The use of crushed green glass (AFM) may have two "
                    "significant impacts: it may help to save a diminishing "
                ),
                gap("s11"),
                text(
                    " while at the same time solving a major problem for the "
                ),
                gap("s12"),
                text(
                    " in the UK. However, according to Howard Dryden, only "
                    "glass from bottles that have been used for "
                ),
                gap("s13"),
                text(
                    " can be used in the production process. AFM is more "
                    "effective than "
                ),
                gap("s14"),
                text(" as a water filter, and also has other uses."),
            ]
        }
    ],
}

P1_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s11", ["natural resource"]),
    ("s12", ["recycling industry"]),
    (
        "s13",
        [
            "drinkable liquids",
            "beverages",
            "drinkable liquid",
        ],
    ),
    ("s14", ["real sand", "sand"]),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "More species survive on the farms studied by the researchers than in "
        "the natural El Salvador forests.",
        "Not Given",
    ),
    (
        "Nearly three-quarters of the Earth's wildlife species can be found "
        "in shade-coffee plantations.",
        "False",
    ),
    (
        "Farmers in El Salvador who have tried both methods prefer "
        "shade-grown plantations.",
        "Not Given",
    ),
    (
        "Shade plantations are important for migrating birds in both Africa "
        "and the Americas.",
        "True",
    ),
    (
        "Full-sun cultivation can increase the costs of farming.",
        "True",
    ),
]

P2_PEOPLE = [
    "A. Alex Munro",
    "B. Paul Donald",
    "C. Robert Rice",
    "D. John Rappole",
    "E. Stacey Philpott",
]

P2_OPINION_ITEMS: list[tuple[str, str]] = [
    (
        "Encouraging shade growing may lead to farmers using the natural "
        "forest for their plantations.",
        "D",
    ),
    (
        "If shade-coffee farms match the right criteria, they can be good "
        "for wildlife.",
        "E",
    ),
    (
        "There may be as many species of bird found on shade farms in a "
        "particular area, as in natural habitats there.",
        "C",
    ),
    (
        "Currently, many shade-coffee farmers earn very little.",
        "A",
    ),
]

P2_METHOD_OPTIONS = [
    "A. the shade-grown method",
    "B. the full-sun method",
    "C. both shade-grown and full-sun methods",
]

P2_METHOD_ITEMS: list[tuple[str, str]] = [
    ("can be used on either coffee or cocoa plantations", "C"),
    ("is expected to produce bigger crops", "B"),
    ("documentation may be used to encourage sales", "A"),
    ("can reduce wildlife diversity", "B"),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_HEADINGS = [
    "i. Amazing results from a project",
    "ii. New religious ceremonies",
    "iii. Community art centres",
    "iv. Early painting techniques and marketing systems",
    "v. Mythology and history combined",
    "vi. The increasing acclaim for Aboriginal art",
    "vii. Belief in continuity",
    "viii. Oppression of a minority people",
]

P3_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "vi"),
    ("Paragraph B", "v"),
    ("Paragraph C", "viii"),
    ("Paragraph D", "i"),
    ("Paragraph E", "iv"),
    ("Paragraph F", "vii"),
]

P3_FLOW_STRUCTURE: dict = {
    "variant": "flow",
    "title": "",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "steps": [
        {
            "segments": [
                text("For "),
                gap("f34"),
                text(", Aborigines produced ground and rock paintings."),
            ]
        },
        {
            "segments": [
                text("Early twentieth century: churches first promoted the use of "),
                gap("f35"),
                text(" for paintings."),
            ]
        },
        {
            "segments": [
                text("Mid-twentieth century: Aboriginal paintings were seen in "),
                gap("f36"),
                text("."),
            ]
        },
        {
            "segments": [
                text(
                    "Early 1970s: Aborigines painted traditional patterns on "
                ),
                gap("f37"),
                text(" in one community."),
            ]
        },
    ],
}

P3_FLOW_ANSWERS: list[tuple[str, list[str]]] = [
    ("f34", ["thousands of years"]),
    ("f35", ["tree bark", "bark"]),
    ("f36", ["overseas museums"]),
    ("f37", ["school walls"]),
]

P3_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "In Paragraph G, the writer suggests that an important feature of "
        "Aboriginal art is",
        [
            "its historical context.",
            "its significance to the group.",
            "its religious content.",
            "its message about the environment.",
        ],
        "B",
    ),
    (
        "In Aboriginal beliefs, there is a significant relationship between",
        [
            "communities and lifestyles.",
            "images and techniques.",
            "culture and form.",
            "ancestors and territory.",
        ],
        "D",
    ),
    (
        "In Paragraph I, the writer suggests that Aboriginal art invites "
        "Westerners to engage with",
        [
            "the Australian land.",
            "their own art.",
            "Aboriginal culture.",
            "their own history.",
        ],
        "C",
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
        "Revolution in glass recycling could help keep water clean"
    )
    print(
        f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 1 has eight paragraphs labelled A–H.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter A–H in boxes 1–10 on your answer sheet.\n"
        "NB You may use any letter more than once.",
        P1_PARAGRAPH_OPTIONS,
        P1_INFORMATION_ITEMS,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose NO MORE THAN TWO WORDS from the passage for each answer.\n"
        "Write your answers in boxes 11–14 on your answer sheet.",
        P1_SUMMARY_STRUCTURE,
        P1_SUMMARY_ANSWERS,
        max_words=2,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "What's the connection between your morning coffee, wintering North "
        "American birds and the cool shade of a tree?"
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
        "In boxes 15–19 on your answer sheet write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P2_TFNG_ITEMS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the following opinions (Questions 20–23) and the list of "
        "people below.\n"
        "Match each opinion to the person credited with it.\n"
        "Write the correct letter A–E in boxes 20–23 on your answer sheet.\n"
        "NB You can write any letter more than once.",
        P2_PEOPLE,
        P2_OPINION_ITEMS,
        options_heading="List of People",
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Classify the features described below as applying to\n"
        "A the shade-grown method\n"
        "B the full-sun method\n"
        "C both shade-grown and full-sun methods\n"
        "Write the correct letter A–C in boxes 24–27 on your answer sheet.",
        P2_METHOD_OPTIONS,
        P2_METHOD_ITEMS,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "The world's fascination with the mystique of Australian Aboriginal art"
    )
    print(
        f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 3 has nine paragraphs A–I.\n"
        "Choose the most suitable heading for paragraphs A–F from the list of "
        "headings below.\n"
        "Write the correct number (i–viii) in boxes 28–33 on your answer sheet.",
        P3_HEADINGS,
        P3_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each answer.\n"
        "Write your answers in boxes 34–37 on your answer sheet.",
        P3_FLOW_STRUCTURE,
        P3_FLOW_ANSWERS,
        max_words=3,
    )
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
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
