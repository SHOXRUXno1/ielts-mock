"""Seed Practice Set D Test 4 Reading, all three passages (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 4.
Keys from the printed Answer Key (pp.227-228). Tip strips omitted.

Passage 1  Q1-4   yes_no_ng            Groucho Marx / Sheekman
           Q5-8   note_completion       categories of essays (THREE WORDS)
           Q9-13  matching_features     letter dates A-G
Passage 2  Q14-17 matching_features     sentence endings A-G
           Q18-22 note_completion       diagram labels (THREE WORDS)
           Q23-26 short_answer          Vine & Matthews
Passage 3  Q27-30 short_answer          happiness sentences (THREE WORDS)
           Q31-36 summary_completion    Seligman word box
           Q37-40 matching_information  paragraphs A-H

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t4_reading.py
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

TEST_NUMBER = 4


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 — Groucho Marx & Arthur Sheekman ──────────────────────────────

P1_YESNO: list[tuple[str, str]] = [
    (
        "Groucho\u2019s work as a writer was sometimes better than his "
        "work in other media.",
        "Not Given",
    ),
    (
        "Groucho\u2019s relationship with Sheekman cast doubt on his own "
        "abilities as a writer.",
        "Yes",
    ),
    (
        "Money was occasionally a source of disagreement between "
        "Groucho and Sheekman.",
        "No",
    ),
    (
        "Groucho occasionally regretted his involvement with Sheekman.",
        "Not Given",
    ),
]

P1_NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Groucho\u2019s essays in the early 1940s",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [
                    text("Category 1: Sheekman had "),
                    gap("n5"),
                ]},
                {"segments": [
                    text("Category 2: Sheekman provided "),
                    gap("n6"),
                ]},
                {"segments": [
                    text("Category 3: "),
                    gap("n7"),
                    text(" with varying degrees of input from Groucho"),
                ]},
                {"segments": [
                    text("Groucho rewrote paragraphs to inject "),
                    gap("n8"),
                ]},
            ],
        },
    ],
}

P1_NOTES_ANSWERS: list[tuple[str, list[str]]] = [
    ("n5", ["no input"]),
    ("n6", ["editorial assistance"]),
    ("n7", ["Sheekman compositions"]),
    ("n8", ["his own style"]),
]

P1_LETTERS = [
    "A. July 1, 1940",
    "B. March 17, 1941",
    "C. July 20, 1940",
    "D. October 10, 1940",
    "E. July 25, 1942",
    "F. July 10, 1940",
    "G. May 29, 1940",
]

P1_LETTER_ITEMS: list[tuple[str, str]] = [
    (
        "Groucho referred to his own inadequacy with regard to use of "
        "language.",
        "E",
    ),
    (
        "Groucho explained his reason for amending an essay.",
        "G",
    ),
    (
        "Groucho agreed that part of an essay needed revising.",
        "D",
    ),
    (
        "Groucho drew Sheekman\u2019s attention to an essay soon to be "
        "published.",
        "B",
    ),
    (
        "Groucho suggested that an essay should adopt a negative point "
        "of view.",
        "F",
    ),
]


# ── Passage 2 — An earth-shaking discovery ──────────────────────────────────

P2_ENDINGS = [
    "A. matters that had not received much attention for some time",
    "B. something which could not possibly be true",
    "C. something misunderstood at first but later seen as a breakthrough",
    "D. matters beyond simply the movement of continents",
    "E. something that had already been observed",
    "F. something arrived at by intuition that could not be demonstrated",
    "G. matters requiring different research techniques",
]

P2_ENDING_ITEMS: list[tuple[str, str]] = [
    (
        "The work done by Vine and Matthews has had implications "
        "concerning",
        "D",
    ),
    (
        "Wegener attempted to provide an explanation of",
        "E",
    ),
    (
        "Wegener\u2019s conclusions were greeted as",
        "B",
    ),
    (
        "The theories presented by both Holmes and Hess concerned",
        "F",
    ),
]

P2_DIAGRAM_STRUCTURE: dict = {
    "variant": "notes",
    "title": "THE DISCOVERIES OF VINE AND MATTHEWS \u2014 The Ocean Floor",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [
                    text("New ocean floor created at the "),
                    gap("d18"),
                ]},
                {"segments": [
                    gap("d19"),
                    text(" at mid-ocean ridges, creating new floor"),
                ]},
                {"segments": [
                    text("Rock magnetised parallel to the "),
                    gap("d20"),
                ]},
                {"segments": [
                    text("Resulting in "),
                    gap("d21"),
                    text(" around the ridge"),
                ]},
                {"segments": [
                    text("Continents "),
                    gap("d22"),
                ]},
            ],
        },
    ],
}

P2_DIAGRAM_ANSWERS: list[tuple[str, list[str]]] = [
    ("d18", [
        "mid-ocean ridge",
        "mid-ocean ridges",
        "mid ocean ridge",
        "mid ocean ridges",
        "ridge crests",
        "ridge crest",
    ]),
    ("d19", ["molten rock rose"]),
    ("d20", [
        "Earth's magnetic field",
        "magnetic field",
        "Earths magnetic field",
    ]),
    ("d21", [
        "parallel zebra stripes",
        "symmetrical stripes",
        "magnetic stripes",
        "zebra stripes",
        "parallel stripes",
        "symmetrical magnetic stripes",
    ]),
    ("d22", [
        "pushed aside",
        "further apart",
        "pushed further apart",
    ]),
]

P2_SHORT: list[tuple[str, list[str]]] = [
    (
        "What is the name of the theory concerning the structure of the "
        "Earth that developed from the demonstration of sea floor "
        "spreading?",
        ["plate tectonics"],
    ),
    (
        "According to Vine, what has the movement of continents had a "
        "big influence on?",
        ["climates"],
    ),
    (
        "What branch of science has emerged as a result of the work "
        "done by Vine and Matthews?",
        ["Earth Systems Science"],
    ),
    (
        "Which word does Vine use to describe the way in which he "
        "believes study of the Earth should be conducted?",
        ["integrated"],
    ),
]


# ── Passage 3 — Think happy ─────────────────────────────────────────────────

P3_SHORT: list[tuple[str, list[str]]] = [
    (
        "At the conference, research into happiness was referred to as "
        "the \u2026",
        ["science of wellbeing", "science of well-being"],
    ),
    (
        "Baylis and others intend to use \u2026 to find out what makes "
        "people happy or unhappy.",
        ["scientifically rigorous methods"],
    ),
    (
        "Baylis gives classes on the subject of \u2026",
        ["positive psychology"],
    ),
    (
        "Baylis says he should not be categorised among the \u2026 who "
        "do not have academic credentials.",
        ["self-help gurus"],
    ),
]

P3_WORDBOX = [
    "confidence", "entertainment", "incentive", "leadership",
    "thrill", "perseverance", "illusion", "effort",
    "ability", "theory", "celebration", "participation",
    "ego", "permanence", "leadership", "encouragement",
    "exaggeration", "concept", "conviction", "support",
]

P3_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Seligman\u2019s categories of happiness",
    "instruction_words": "ONE WORD",
    "max_words_per_gap": 1,
    "word_box": P3_WORDBOX,
    "paragraphs": [
        {"segments": [
            text(
                "Seligman\u2019s first type of happiness involves the "
                "enjoyment of pleasures such as "
            ),
            gap("w31"),
            text(
                ". He believes that people should not be under the "
            ),
            gap("w32"),
            text(
                " that such things lead to happiness that is not just "
                "temporary. His second type is related to "
            ),
            gap("w33"),
            text(
                ". Identification of this should lead to "
            ),
            gap("w34"),
            text(
                " and the result is \u2018the good life\u2019. His "
                "third type involves having a strong "
            ),
            gap("w35"),
            text(
                " and doing something about it for the benefit of "
                "others. This, according to Seligman, leads to "
                "happiness that has some "
            ),
            gap("w36"),
            text("."),
        ]},
    ],
}

P3_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("w31", ["entertainment"]),
    ("w32", ["illusion"]),
    ("w33", ["ability"]),
    ("w34", ["participation"]),
    ("w35", ["conviction"]),
    ("w36", ["permanence"]),
]

P3_INFO_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H"]

P3_INFO_ITEMS: list[tuple[str, str]] = [
    (
        "a view that complete happiness may not be a desirable goal",
        "H",
    ),
    (
        "a reference to the potential wider outcomes of conducting "
        "research into happiness",
        "C",
    ),
    (
        "an implication of the fact that the conference was held at all",
        "B",
    ),
    (
        "a statement concerning the possible outcome of expressing a "
        "certain view in public",
        "E",
    ),
]


# ── writer helper ─────────────────────────────────────────────────────────────

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

    # ── Passage 1 ──
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
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements reflect the claims of the writer "
        "of Reading Passage 1?\n"
        "Write\n"
        "YES if the statement agrees with the claims of the writer\n"
        "NO if the statement contradicts the claims of the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks "
        "about this",
        P1_YESNO,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each "
        "answer.",
        P1_NOTES_STRUCTURE,
        P1_NOTES_ANSWERS,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the following statements (Questions 9\u201313) and "
        "the list of dates of letters sent by Groucho to Sheekman "
        "below.\n"
        "Match each statement with the letter it relates to.\n"
        "Write the correct letter A\u2013G.\n"
        f"{SCREEN_LETTER_HINT}",
        P1_LETTERS,
        P1_LETTER_ITEMS,
        options_heading="List of Letters Sent by Groucho to Sheekman",
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # ── Passage 2 ──
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = (
        "The discovery of sea floor spreading is earth-shaking, "
        "yet those responsible are forgotten"
    )
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending A\u2013G "
        "from the box below.\n"
        "Write the correct letter A\u2013G.\n"
        f"{SCREEN_LETTER_HINT}",
        P2_ENDINGS,
        P2_ENDING_ITEMS,
        options_heading="Endings",
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Label the diagram below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for each "
        "answer.",
        P2_DIAGRAM_STRUCTURE,
        P2_DIAGRAM_ANSWERS,
        max_words=3,
    )
    await w.short_answer(
        "Answer the questions below using NO MORE THAN THREE WORDS "
        "for each answer.",
        P2_SHORT,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # ── Passage 3 ──
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = f"Passage 3 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = (
        "It\u2019s no joke: even scientists at the Royal Society are "
        "now taking the search for the source of happiness very seriously"
    )
    print(
        f"\nPassage 3 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.short_answer(
        "Complete the sentences below with words taken from Reading "
        "Passage 3.\n"
        "Use NO MORE THAN THREE WORDS for each answer.",
        P3_SHORT,
        max_words=3,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below using words from the box.",
        P3_SUMMARY_STRUCTURE,
        P3_SUMMARY_ANSWERS,
        max_words=1,
    )
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 3 has eight paragraphs labelled A\u2013H.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter A\u2013H.\n"
        f"{SCREEN_LETTER_HINT}",
        P3_INFO_OPTIONS,
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
