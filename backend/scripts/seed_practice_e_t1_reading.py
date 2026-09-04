"""Seed Practice Set E Test 1 Reading, all three passages (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 1.
Keys from the printed Explanatory Answer Key (pp.126-130).

Passage 1  Q1-5   matching_headings    paragraphs B-G (headings i-x)
           Q6-7   short_answer         space biomedicine (THREE WORDS)
           Q8-12  yes_no_ng
           Q13-14  table_completion    space research applications (THREE WORDS)
Passage 2  Q15-19 summary_completion   Mediterranean discovery (THREE WORDS)
           Q20-22 matching_features    sentence endings (A-G)
           Q23-27 mcq                  Ryan and Hsü (A-D)
Passage 3  Q28-31 matching_information paragraphs A-J
           Q32-35 multi_select         choose FOUR from A-H
           Q36-40 matching_features    dog uses by nationality (A-F)

Passage text lives in scripts/data/practice_e_t1/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t1_reading.py
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

TEST_NUMBER = 1


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 — Space travel and health ──────────────────────────────────────

P1_HEADINGS = [
    "i. The problem of dealing with emergencies in space",
    "ii. How space biomedicine can help patients on Earth",
    "iii. Why accidents are so common in outer space",
    "iv. What is space biomedicine?",
    "v. The psychological problems of astronauts",
    "vi. Conducting space biomedical research on Earth",
    "vii. The internal damage caused to the human body by space travel",
    "viii. How space biomedicine first began",
    "ix. The visible effects of space travel on the human body",
    "x. Why space biomedicine is now necessary",
]

P1_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "x"),
    ("Paragraph C", "ix"),
    ("Paragraph D", "vii"),
    ("Paragraph E", "i"),
    ("Paragraph G", "vi"),
]

P1_SHORT_Q6_7: list[tuple[str, list[str]]] = [
    (
        "Where, apart from Earth, can space travellers find water?",
        ["(on) Mars", "Mars", "(from) Mars", "on Mars", "from Mars"],
    ),
    (
        "What happens to human legs during space travel?",
        ["they become thinner", "(they) become thinner",
         "become thinner"],
    ),
]

P1_YESNO: list[tuple[str, str]] = [
    (
        "The obstacles to going far into space are now medical, "
        "not technological.",
        "Yes",
    ),
    (
        "Astronauts cannot survive more than two years in space.",
        "Not Given",
    ),
    (
        "It is morally wrong to spend so much money on space "
        "biomedicine.",
        "No",
    ),
    (
        "Some kinds of surgery are more successful when performed "
        "in space.",
        "Not Given",
    ),
    (
        "Space biomedical research can only be done in space.",
        "No",
    ),
]

P1_TABLE_STRUCTURE: dict = {
    "variant": "table",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "headers": [
        "Research area",
        "Application in space",
        "Application on Earth",
    ],
    "rows": [
        [
            {"variant": "plain", "segments": [text("Telemedicine")]},
            {"variant": "plain", "segments": [text("treating astronauts")]},
            {
                "variant": "plain",
                "segments": [
                    gap("t13"),
                    text(" in remote areas"),
                ],
            },
        ],
        [
            {"variant": "plain", "segments": [text("Sterilization")]},
            {
                "variant": "plain",
                "segments": [text("sterilizing waste water")],
            },
            {
                "variant": "plain",
                "segments": [
                    gap("t14"),
                    text(" in disaster zones"),
                ],
            },
        ],
        [
            {"variant": "plain", "segments": [text("Miniaturization")]},
            {"variant": "plain", "segments": [text("saving weight")]},
            {
                "variant": "plain",
                "segments": [
                    text("wearing small monitors comfortably"),
                ],
            },
        ],
    ],
}

P1_TABLE_ANSWERS: list[tuple[str, list[str]]] = [
    (
        "t13",
        [
            "communicating with patients",
            "communicate with patients",
        ],
    ),
    (
        "t14",
        [
            "filtering contaminated water",
            "filter contaminated water",
        ],
    ),
]


# ── Passage 2 — Vanished ─────────────────────────────────────────────────────

P2_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "The Discovery",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "paragraphs": [
        {
            "segments": [
                text(
                    "The 1960s discovery of "
                ),
                gap("s15"),
                text(
                    " in the bedrock of the Mediterranean, as well as "
                    "deep caves beneath Malta, suggested something "
                    "strange had happened in the region, as these "
                    "features must have been formed "
                ),
                gap("s16"),
                text(
                    " sea level. Subsequent examination of the "
                ),
                gap("s17"),
                text(
                    " off Majorca provided more proof. Rock "
                    "samples from 2000 metres down contained both "
                    "vegetation and "
                ),
                gap("s18"),
                text(
                    " that could not have lived in deep water, as "
                    "well as "
                ),
                gap("s19"),
                text(
                    " originally transported by river."
                ),
            ]
        },
    ],
}

P2_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s15", ["(deep) canyons", "deep canyons", "canyons"]),
    ("s16", ["above"]),
    ("s17", ["sea floor"]),
    ("s18", ["shellfish", "(shallow-water) shellfish"]),
    ("s19", ["silt", "sand and mud"]),
]

P2_ENDINGS = [
    "A. Africa and Europe crashed into each other.",
    "B. water started flowing from the Mediterranean.",
    "C. the sea was cut off from the ocean.",
    "D. all the fish and plant life in the Mediterranean died.",
    "E. the Earth started to become colder.",
    "F. the channel grew bigger, creating the waterfalls.",
    "G. all the ice on earth melted.",
]

P2_ENDING_ITEMS: list[tuple[str, str]] = [
    (
        "The extra ice did not absorb the heat from the sun, so \u2026",
        "E",
    ),
    (
        "The speed of the water from the Atlantic increased as \u2026",
        "F",
    ),
    (
        "The Earth and its oceans became warmer when \u2026",
        "B",
    ),
]

P2_MCQ: list[dict] = [
    {
        "question": (
            "What, according to Ryan and Hs\u00fc, happened about "
            "5.8 million years ago?"
        ),
        "options": [
            "Movement of the continents suddenly closed the "
            "Straits of Gibraltar.",
            "The water level of the Atlantic Ocean gradually fell.",
            "The flow of water into the Mediterranean was "
            "immediately cut off.",
            "Water stopped flowing from the Mediterranean to the "
            "Atlantic.",
        ],
        "correct": "D",
    },
    {
        "question": (
            "Why did most of the animal and plant life in the "
            "Mediterranean die?"
        ),
        "options": [
            "The water became too salty.",
            "There was such a lot of bacteria in the water.",
            "The rivers did not provide salt water.",
            "The sea became a desert.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "According to the text, the events at Gibraltar led to"
        ),
        "options": [
            "a permanent cooling of the Earth.",
            "the beginning and the end of an ice age.",
            "the formation of waterfalls elsewhere in the world.",
            "a lack of salt in the oceans that continues to this day.",
        ],
        "correct": "B",
    },
    {
        "question": "More recent studies show that",
        "options": [
            "Ryan and Hs\u00fc\u2019s theory was correct in every detail.",
            "the Mediterranean was never cut off from the Atlantic.",
            "it may have been cut off more than once.",
            "it might once have been a freshwater lake.",
        ],
        "correct": "C",
    },
    {
        "question": (
            "At the end of the article, Ryan suggests that"
        ),
        "options": [
            "the Mediterranean will never dry up again.",
            "humans will have the technology to prevent it drying "
            "up again.",
            "the Mediterranean is certain to dry up again one day.",
            "humans will never see the Mediterranean dry up.",
        ],
        "correct": "D",
    },
]


# ── Passage 3 — Dogs: a love story ──────────────────────────────────────────

P3_MATCHING_INFO_ITEMS: list[tuple[str, str]] = [
    (
        "Which paragraph explains how dogs became different in "
        "appearance from wolves?",
        "F",
    ),
    (
        "Which paragraph describes the classification of dogs "
        "into many different types?",
        "J",
    ),
    (
        "Which paragraph states the basic similarity between "
        "wolves and dogs?",
        "A",
    ),
    (
        "Which paragraph gives examples of greater human concern "
        "for animals than for people?",
        "I",
    ),
]

P3_MULTI = {
    "question": (
        "Which FOUR of the following statements are made in the text?"
    ),
    "options": [
        "In a typical camp there were many more wolves than humans.",
        "Neither the wolves nor the humans lived in one place for long.",
        "Some wolves learned to obey human leaders.",
        "Humans chose the most dangerous wolves to help them hunt.",
        "There was very little for early humans to eat.",
        "Wolves got food from early humans.",
        "Wolves started living with humans when agriculture began.",
        "Early humans especially liked very young wolves.",
    ],
    "correct": ["B", "C", "F", "H"],
}

NATIONALITY_OPTIONS = [
    "A. the Greeks",
    "B. the French",
    "C. the Egyptians",
    "D. the Romans",
    "E. the English",
    "F. the Native Americans",
]

P3_NATIONALITY_ITEMS: list[tuple[str, str]] = [
    ("in war", "D"),
    ("as a source of energy", "E"),
    ("as food", "F"),
    ("to hunt other animals", "A"),
    ("to work with farm animals", "E"),
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
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 1 has seven paragraphs A\u2013G.\n"
        "Choose the correct heading for paragraphs B\u2013E and G "
        "from the list of headings below.\n"
        "Write the correct number, i\u2013x.",
        P1_HEADINGS,
        P1_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.short_answer(
        "Answer the questions below using NO MORE THAN THREE WORDS "
        "for each answer.",
        P1_SHORT_Q6_7,
        max_words=3,
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the "
        "writer in Reading Passage 1?\n"
        "Write\n"
        "YES if the statement agrees with the views of the writer\n"
        "NO if the statement does not agree with the views of the "
        "writer\n"
        "NOT GIVEN if there is no information about this in the "
        "passage",
        P1_YESNO,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for "
        "each answer.",
        P1_TABLE_STRUCTURE,
        P1_TABLE_ANSWERS,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 2 --
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = (
        "Who pulled the plug on the Mediterranean? "
        "And could it happen again?"
    )
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for "
        "each answer.",
        P2_SUMMARY_STRUCTURE,
        P2_SUMMARY_ANSWERS,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each of the following statements with the best "
        "ending from the box below.\n"
        "Write the appropriate letters A\u2013G.\n"
        f"{SCREEN_LETTER_HINT}",
        P2_ENDINGS,
        P2_ENDING_ITEMS,
        options_heading="Endings",
    )
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P2_MCQ,
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
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 3 has ten paragraphs labelled A\u2013J.\n"
        "Write the correct letters A\u2013J in boxes 28\u201331.\n"
        f"{SCREEN_LETTER_HINT}",
        ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
        P3_MATCHING_INFO_ITEMS,
        options_heading="Paragraph",
    )
    await w.multi_select(
        "Choose FOUR letters, A\u2013H.",
        P3_MULTI,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "From the information in the text, indicate who used dogs "
        "in the ways listed below.\n"
        "Write the correct letter, A\u2013F.\n"
        "NB You may use any letter more than once.\n"
        f"{SCREEN_LETTER_HINT}",
        NATIONALITY_OPTIONS,
        P3_NATIONALITY_ITEMS,
        options_heading="Used by",
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
