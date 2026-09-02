"""Seed Practice Set D Test 3 Reading, all three passages (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 3.
Keys from the printed Answer Key (pp.220-221). Tip strips omitted.

Passage 1  Q1-5   flow_chart / summary   subtitling process
           Q6-9   true_false_ng
           Q10-13 sentence completion
Passage 2  Q14-19 matching people A-E
           Q20-22 matching endings A-F
           Q23-26 classify A-D therapies
Passage 3  Q27-32 matching_headings
           Q33-36 diagram / short labels
           Q37-40 matching_information A-F

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t3_reading.py
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
from seed_practice_d_common import (  # noqa: E402
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


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_FLOW_STRUCTURE: dict = {
    "variant": "flow",
    "title": "THE SUBTITLING PROCESS",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "steps": [
        {"segments": [text("Stage 1: Translate and adapt the script")]},
        {
            "segments": [
                text("Stage 2: "),
                gap("f1"),
                text(" \u2014 matching the subtitles to what is said"),
            ]
        },
        {
            "segments": [
                text("involves recording time codes by using the "),
                gap("f2"),
                text(" and "),
                gap("f2b"),
            ]
        },
        {
            "segments": [
                text("Stage 3: "),
                gap("f3"),
            ]
        },
        {
            "segments": [
                text("\u2014 in order to make the "),
                gap("f4"),
            ]
        },
        {
            "segments": [
                text(
                    "Multi-lingual projects \u2014 Stage 1: Produce "
                    "something known as a "
                ),
                gap("f5"),
                text(" and translate that"),
            ]
        },
    ],
}

# Q2 is insert AND delete — one mark with two words. Model as one gap.
P1_FLOW_STRUCTURE_FLAT: dict = {
    "variant": "flow",
    "title": "THE SUBTITLING PROCESS",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "steps": [
        {"segments": [text("Stage 1: Translate and adapt the script")]},
        {
            "segments": [
                text("Stage 2: "),
                gap("f1"),
                text(" \u2014 matching the subtitles to what is said"),
            ]
        },
        {
            "segments": [
                text(
                    "involves recording time codes by using the "
                ),
                gap("f2"),
            ]
        },
        {
            "segments": [
                text("Stage 3: "),
                gap("f3"),
            ]
        },
        {
            "segments": [
                text("\u2014 in order to make / improve the "),
                gap("f4"),
            ]
        },
        {
            "segments": [
                text(
                    "Multi-lingual projects \u2014 Stage 1: Produce "
                    "something known as a "
                ),
                gap("f5"),
                text(" and translate that"),
            ]
        },
    ],
}

P1_FLOW_ANSWERS: list[tuple[str, list[str]]] = [
    ("f1", ["timing"]),
    (
        "f2",
        [
            "insert and delete",
            "insert; delete",
            "delete and insert",
            "insert key and delete key",
            "insert / delete",
        ],
    ),
    (
        "f3",
        [
            "a manual review",
            "manual review",
            "(a) manual review",
        ],
    ),
    (
        "f4",
        ["synchronisation", "synchronization"],
    ),
    ("f5", ["spotting list", "a spotting list"]),
]

P1_TFNG: list[tuple[str, str]] = [
    (
        "For translators, all subtitling work on films is desirable.",
        "True",
    ),
    (
        "Subtitling work involves a requirement that does not apply to "
        "other translation work.",
        "True",
    ),
    (
        "Some subtitling techniques work better than others.",
        "False",
    ),
    (
        "Few people are completely successful at subtitling comedies.",
        "Not Given",
    ),
]

P1_SENTENCES: list[tuple[str, list[str]]] = [
    (
        "Poor subtitling can be a result of the subtitler not being "
        "excellent at",
        ["the source language", "source language"],
    ),
    (
        "To create subtitles for a video version of a film, it may be "
        "necessary to",
        ["reformat the timing"],
    ),
    (
        "Subtitles usually have a \u2026 around them.",
        ["thin black border", "a thin black border"],
    ),
    (
        "Speakers can be distinguished from each other for the benefit of",
        ["the hearing impaired", "hearing impaired"],
    ),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_PEOPLE = [
    "A. Dr Romke Bron",
    "B. a molecular biologist from the University of Warwick",
    "C. Dr Stephen Nurrish",
    "D. a neuroscientist at King\u2019s College London",
    "E. Professor David Moore",
]

P2_PEOPLE_ITEMS: list[tuple[str, str]] = [
    (
        "Complementary medicine provides something that conventional "
        "medicine no longer does.",
        "C",
    ),
    (
        "It is hard for people to know whether they are being told the "
        "truth or not.",
        "A",
    ),
    (
        "Certain kinds of complementary and alternative medicine are "
        "taken seriously because of the number of people making money "
        "from them.",
        "D",
    ),
    (
        "Nothing can be considered a form of medicine unless it has "
        "been proved effective.",
        "E",
    ),
    (
        "It seems likely that some forms of alternative medicine do work.",
        "B",
    ),
    (
        "One particular kind of alternative medicine is a deliberate "
        "attempt to cheat the public.",
        "A",
    ),
]

P2_ENDINGS = [
    "A. whether alternative medicine should be investigated scientifically",
    "B. how many people use various kinds of complementary medicine",
    "C. the extent to which attitudes to alternative medicine are changing",
    "D. what makes people use complementary rather than conventional medicine",
    "E. how many scientists themselves use complementary and alternative medicine",
    "F. research into the use of complementary and conventional medicine together",
]

# Letters follow answer-key NOTES (OCR letter labels on p221 were inconsistent).
P2_ENDING_ITEMS: list[tuple[str, str]] = [
    (
        "The British Association for the Advancement of Science will be "
        "discussing the issue of",
        "A",
    ),
    (
        "A recent survey conducted by a certain organisation addressed "
        "the issue of",
        "B",
    ),
    (
        "The survey in which the writer of the article was involved gave "
        "information on",
        "E",
    ),
]

P2_THERAPY_OPTIONS = [
    "A. acupuncture",
    "B. aromatherapy",
    "C. herbalism",
    "D. homoeopathy",
]

P2_THERAPY_ITEMS: list[tuple[str, str]] = [
    (
        "Scientists believe that it is ineffective but harmless.",
        "D",
    ),
    (
        "Scientists felt that it could be added to the group of therapies "
        "that deserved to be provided with resources for further "
        "investigation.",
        "C",
    ),
    (
        "Scientists felt that it deserved to be taken seriously because "
        "of the organised way in which it has developed.",
        "A",
    ),
    (
        "A number of scientists had used it, but harsh criticism was "
        "expressed about it.",
        "D",
    ),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_HEADINGS = [
    "i. An easily understood system",
    "ii. Doubts dismissed",
    "iii. Not a totally unconventional view",
    "iv. Theories compared",
    "v. A momentous occasion",
    "vi. A controversial use of terminology",
    "vii. Initial confusion",
    "viii. Previous beliefs replaced",
    "ix. More straightforward than expected",
    "x. An obvious thing to do",
]

P3_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "v"),
    ("Paragraph B", "viii"),
    ("Paragraph C", "iii"),
    ("Paragraph D", "ix"),
    ("Paragraph E", "i"),
    ("Paragraph F", "x"),
]

P3_DIAGRAM_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Balloon ascent into cloud",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Reaching situation known as the "),
                        gap("d33"),
                    ]
                },
                {
                    "segments": [
                        text("Middle of a "),
                        gap("d34"),
                    ]
                },
                {
                    "segments": [
                        text("Air\u2019s "),
                        gap("d35"),
                        text(" concentration thins"),
                    ]
                },
                {
                    "segments": [
                        text("Temperature falls "),
                        gap("d36"),
                        text(" per thousand / 1000 metres"),
                    ]
                },
            ],
        },
    ],
}

# Q36 is "6.5°C" for the rate; paper may have two gaps. Use one gap for 6.5°C
# and accept combined forms.
P3_DIAGRAM_ANSWERS: list[tuple[str, list[str]]] = [
    ("d33", ["dizzy heights"]),
    ("d34", ["major cumulus cloud"]),
    ("d35", ["oxygen"]),
    (
        "d36",
        [
            "6.5°C",
            "6.5 C",
            "6.5 degrees C",
            "6.5°C per thousand metres",
            "6.5°C; thousand metres",
            "6.5°C / 1000 metres",
        ],
    ),
]

P3_INFO_ITEMS: list[tuple[str, str]] = [
    (
        "an example of a modification made to work done by Howard",
        "E",
    ),
    (
        "a comparison between Howard\u2019s work and another classification "
        "system",
        "F",
    ),
    (
        "a reference to the fact that Howard presented a very large "
        "amount of information",
        "A",
    ),
    (
        "an assumption that the audience asked themselves a question",
        "F",
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
    ) -> Question:
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
        return question

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
                {"prompt": question, "max_words": max_words},
                gap_answer_key(variants, max_words=max_words),
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    counts: list[int] = []
    slots: list[int] = []

    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = f"Passage 1 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = (
        "Melanie Leyshon talks to Virginie Verdier about film subtitling"
    )
    print(
        f"\nPassage 1 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Use NO MORE THAN THREE WORDS from the passage for each answer.",
        P1_FLOW_STRUCTURE_FLAT,
        P1_FLOW_ANSWERS,
        max_words=3,
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information given "
        "in Reading Passage 1?\n"
        "Write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P1_TFNG,
    )
    await w.short_answer(
        "Complete the sentences below with words from Reading Passage 1.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        P1_SENTENCES,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = (
        "What do scientists in Britain think about \u2018alternative\u2019 "
        "therapies?"
    )
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the following views (Questions 14\u201319) and the list "
        "of people below them.\n"
        "Match each view with the person expressing it in the passage.\n"
        "Write the correct letter A\u2013E.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        P2_PEOPLE,
        P2_PEOPLE_ITEMS,
        options_heading="List of People",
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending A\u2013F from "
        "the box below.\n"
        f"Write the correct letter A\u2013F.\n{SCREEN_LETTER_HINT}",
        P2_ENDINGS,
        P2_ENDING_ITEMS,
        options_heading="Endings",
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Classify the following information as being given about\n"
        "A acupuncture\n"
        "B aromatherapy\n"
        "C herbalism\n"
        "D homoeopathy\n\n"
        "Write the correct letter, A, B, C or D.\n"
        f"{SCREEN_LETTER_HINT}",
        P2_THERAPY_OPTIONS,
        P2_THERAPY_ITEMS,
        options_heading="Therapy",
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

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
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 3 has six paragraphs, A\u2013F.\n"
        "Choose the correct heading for each paragraph from the list of "
        "headings below.\n"
        "Write the correct number, i\u2013x.",
        P3_HEADINGS,
        P3_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Label the diagram below.\n"
        "Choose NO MORE THAN THREE WORDS AND/OR A NUMBER from the "
        "passage for each answer.",
        P3_DIAGRAM_STRUCTURE,
        P3_DIAGRAM_ANSWERS,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 3 has six paragraphs labelled A\u2013F.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter A\u2013F.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        ["A", "B", "C", "D", "E", "F"],
        P3_INFO_ITEMS,
        options_heading="Paragraph",
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
