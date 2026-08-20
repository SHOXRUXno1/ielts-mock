"""Seed Cambridge IELTS 15 Test 3 Reading (Q1–40).

Reuses the existing Test 3 record. Idempotent wipe of reading groups/questions.

Usage:
    python /app/scripts/seed_ielts15_t3_reading.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.answer import Answer
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test
from app.services.scoring import scoring_slots_for_question
from app.services.seed_compound import gap_answer_key, next_group_order

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ielts15_t3_reading_passages import (  # noqa: E402
    P1_HENRY_MOORE,
    P2_DESOLENATOR,
    P3_FAIRY_TALES,
)

TEST_ID = uuid.UUID("3b766b14-d188-4c81-814f-77fadff4e3fa")
PROTECTED_TEST_IDS = {
    uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590"),
    uuid.UUID("6074d5f2-70b8-4f31-9b59-10f861a3eadf"),
}


def _item(*parts: str | dict) -> dict:
    segments: list[dict] = []
    for part in parts:
        if isinstance(part, str):
            segments.append({"type": "text", "value": part})
        else:
            segments.append(part)
    return {"segments": segments}


def _gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


async def _wipe_section(db: AsyncSession, section_id: uuid.UUID) -> int:
    qids = (
        await db.execute(select(Question.id).where(Question.section_id == section_id))
    ).scalars().all()
    if qids:
        await db.execute(sa_delete(Answer).where(Answer.question_id.in_(qids)))
        await db.flush()

    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == section_id)
        )
    ).scalars().all()
    n = 0
    for g in groups:
        qs = (
            await db.execute(
                select(Question).where(Question.question_group_id == g.id)
            )
        ).scalars().all()
        for q in qs:
            await db.delete(q)
        await db.flush()
        await db.delete(g)
        n += 1
    leftovers = (
        await db.execute(select(Question).where(Question.section_id == section_id))
    ).scalars().all()
    for q in leftovers:
        await db.delete(q)
        n += 1
    if n:
        await db.flush()
    return n


async def _add_gaps(
    db: AsyncSession,
    *,
    section_id: uuid.UUID,
    group_id: uuid.UUID,
    qtype: QuestionType,
    answers: list[tuple[str, list[str]]],
    max_words: int,
) -> None:
    for i, (gap_id, variants) in enumerate(answers, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section_id,
                question_group_id=group_id,
                order=i,
                question_type=qtype,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=max_words),
            )
        )
        print(f"    {gap_id} -> {variants}")


async def _add_letter_items(
    db: AsyncSession,
    *,
    section: Section,
    group: QuestionGroup,
    qtype: QuestionType,
    items: list[tuple[str, str]],
    label: str,
) -> None:
    for i, (stem, letter) in enumerate(items, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=i,
                question_type=qtype,
                content={"question": stem},
                answer_key={"correct": letter},
            )
        )
        print(f"    {label} {i} -> {letter}")


async def _reading_sections(db: AsyncSession, test_id: uuid.UUID) -> list[Section]:
    rows = (
        await db.execute(
            select(Section)
            .where(Section.test_id == test_id, Section.type == SectionType.READING)
            .order_by(Section.order)
        )
    ).scalars().all()
    if len(rows) < 3:
        raise SystemExit(f"Expected 3 reading sections, found {len(rows)}")
    return list(rows[:3])


async def _seed_p1(db: AsyncSession, section: Section) -> None:
    section.title = "Henry Moore (1898-1986)"
    section.passage = P1_HENRY_MOORE
    section.passage_subtitle = (
        "The British sculptor Henry Moore was a leading figure "
        "in the 20th-century art world"
    )
    await _wipe_section(db, section.id)

    tfng_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.TRUE_FALSE_NG.value,
        instruction=(
            "Do the following statements agree with the information given "
            "in Reading Passage 1?\n"
            "In boxes 1-7 on your answer sheet, write\n"
            "TRUE if the statement agrees with the information\n"
            "FALSE if the statement contradicts the information\n"
            "NOT GIVEN if there is no information on this"
        ),
    )
    db.add(tfng_group)
    await db.flush()
    tfng = [
        ("On leaving school, Moore did what his father wanted him to do.", "True"),
        (
            "Moore began studying sculpture in his first term at the Leeds School of Art.",
            "False",
        ),
        (
            "When Moore started at the Royal College of Art, its reputation for teaching sculpture was excellent.",
            "Not Given",
        ),
        (
            "Moore became aware of ancient sculpture as a result of visiting London museums.",
            "True",
        ),
        (
            "The Trocadero Museum's Mayan sculpture attracted a lot of public interest.",
            "Not Given",
        ),
        (
            "Moore thought the Mayan sculpture was similar in certain respects to other stone sculptures.",
            "False",
        ),
        (
            "The artists who belonged to Unit One wanted to make modern art and architecture more popular.",
            "True",
        ),
    ]
    for i, (statement, correct) in enumerate(tfng, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=tfng_group.id,
                order=i,
                question_type=QuestionType.TRUE_FALSE_NG,
                content={"statement": statement},
                answer_key={"correct": correct},
            )
        )
        print(f"    TFNG {i} -> {correct}")

    notes = {
        "variant": "notes",
        "title": "Moore's career as an artist",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "sections": [
            {
                "heading": "1930s",
                "items": [
                    _item(
                        "Moore's exhibition at the Leicester Galleries is criticised by the press"
                    ),
                    _item(
                        "Moore is urged to offer his ",
                        _gap("g8"),
                        " and leave the Royal College",
                    ),
                ],
            },
            {
                "heading": "1940s",
                "items": [
                    _item(
                        "Moore turns to drawing because ",
                        _gap("g9"),
                        " for sculpting are not readily available",
                    ),
                    _item(
                        "While visiting his hometown, Moore does some drawings of ",
                        _gap("g10"),
                    ),
                    _item(
                        "Moore is employed to produce a sculpture of a ",
                        _gap("g11"),
                    ),
                    _item(_gap("g12"), " start to buy Moore's work"),
                    _item(
                        "Moore's increased ",
                        _gap("g13"),
                        " makes it possible for him to do more ambitious sculptures",
                    ),
                ],
            },
            {
                "heading": "1950s",
                "items": [
                    _item(
                        "Moore's series of bronze figures marks a further change in his style"
                    )
                ],
            },
        ],
    }
    notes_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.NOTE_COMPLETION.value,
        instruction=(
            "Complete the notes below.\n"
            "Choose ONE WORD ONLY from the passage for each answer."
        ),
        options_shared=notes,
    )
    db.add(notes_group)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=notes_group.id,
        qtype=QuestionType.NOTE_COMPLETION,
        answers=[
            ("g8", ["resignation"]),
            ("g9", ["materials"]),
            ("g10", ["miners"]),
            ("g11", ["family"]),
            ("g12", ["collectors"]),
            ("g13", ["income"]),
        ],
        max_words=1,
    )


async def _seed_p2(db: AsyncSession, section: Section) -> None:
    section.title = "The Desolenator: producing clean water"
    section.passage = P2_DESOLENATOR
    section.passage_subtitle = None
    await _wipe_section(db, section.id)

    headings = [
        "i. Getting the finance for production",
        "ii. An unexpected benefit",
        "iii. From initial inspiration to new product",
        "iv. The range of potential customers for the device",
        "v. What makes the device different from alternatives",
        "vi. Cleaning water from a range of sources",
        "vii. Overcoming production difficulties",
        "viii. Profit not the primary goal",
        "ix. A warm welcome for the device",
        "x. The number of people affected by water shortages",
    ]
    h_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MATCHING_HEADINGS.value,
        instruction=(
            "Reading Passage 2 has seven sections, A-G.\n"
            "Choose the correct heading for each section from the list of headings below.\n"
            "Choose the correct number, i-x, in boxes 14-20 on your answer sheet."
        ),
        options_shared={"options": headings},
    )
    db.add(h_group)
    await db.flush()
    await _add_letter_items(
        db,
        section=section,
        group=h_group,
        qtype=QuestionType.MATCHING_HEADINGS,
        items=[
            ("Section A", "iii"),
            ("Section B", "vi"),
            ("Section C", "v"),
            ("Section D", "x"),
            ("Section E", "iv"),
            ("Section F", "viii"),
            ("Section G", "i"),
        ],
        label="heading",
    )

    summary = {
        "variant": "summary",
        "title": "How the Desolenator works",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "paragraphs": [
            {
                "segments": [
                    {
                        "type": "text",
                        "value": (
                            "The energy required to operate the Desolenator comes from sunlight. "
                            "The device can be used in different locations, as it has "
                        ),
                    },
                    {"type": "gap", "gap_id": "g21"},
                    {
                        "type": "text",
                        "value": ". Water is fed into a pipe, and a ",
                    },
                    {"type": "gap", "gap_id": "g22"},
                    {
                        "type": "text",
                        "value": (
                            " of water flows over a solar panel. The water then enters "
                            "a boiler, where it turns into steam. Any particles in the "
                            "water are caught in a "
                        ),
                    },
                    {"type": "gap", "gap_id": "g23"},
                    {
                        "type": "text",
                        "value": (
                            ". The purified water comes out through one tube, and all "
                            "types of "
                        ),
                    },
                    {"type": "gap", "gap_id": "g24"},
                    {
                        "type": "text",
                        "value": (
                            " come out through another. A screen displays the "
                        ),
                    },
                    {"type": "gap", "gap_id": "g25"},
                    {
                        "type": "text",
                        "value": (
                            " of the device, and transmits the information to the "
                            "company so that they know when the Desolenator requires "
                        ),
                    },
                    {"type": "gap", "gap_id": "g26"},
                    {"type": "text", "value": "."},
                ]
            }
        ],
    }
    g = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.SUMMARY_COMPLETION.value,
        instruction=(
            "Complete the summary below.\n"
            "Choose ONE WORD ONLY from the passage for each answer."
        ),
        options_shared=summary,
    )
    db.add(g)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=g.id,
        qtype=QuestionType.SUMMARY_COMPLETION,
        answers=[
            ("g21", ["wheels"]),
            ("g22", ["film"]),
            ("g23", ["filter"]),
            ("g24", ["waste"]),
            ("g25", ["performance"]),
            ("g26", ["servicing"]),
        ],
        max_words=1,
    )


async def _seed_p3(db: AsyncSession, section: Section) -> None:
    section.title = "Why fairy tales are really scary tales"
    section.passage = P3_FAIRY_TALES
    section.passage_subtitle = (
        "Some people think that fairy tales are just stories to amuse children, "
        "but their universal and enduring appeal may be due to more serious reasons"
    )
    await _wipe_section(db, section.id)

    endings = [
        "A. may be provided through methods used in biological research.",
        "B. are the reason for their survival.",
        "C. show considerable global variation.",
        "D. contain animals which transform to become humans.",
        "E. were originally spoken rather than written.",
        "F. have been developed without factual basis.",
    ]
    match = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MATCHING_FEATURES.value,
        instruction=(
            "Complete each sentence with the correct ending, A-F, below.\n"
            "Choose the correct letter, A-F, next to Questions 27-31."
        ),
        subtitle="\u00a0",
        options_shared={"options": endings},
    )
    db.add(match)
    await db.flush()
    await _add_letter_items(
        db,
        section=section,
        group=match,
        qtype=QuestionType.MATCHING_FEATURES,
        items=[
            ("In fairy tales, details of the plot", "C"),
            (
                "Tehrani rejects the idea that the useful lessons for life in fairy tales",
                "B",
            ),
            (
                "Various theories about the social significance of fairy tales",
                "F",
            ),
            ("Insights into the development of fairy tales", "A"),
            ("All the fairy tales analysed by Tehrani", "E"),
        ],
        label="ending",
    )

    word_bank = [
        "A. ending",
        "B. events",
        "C. warning",
        "D. links",
        "E. records",
        "F. variations",
        "G. horror",
        "H. people",
        "I. plot",
    ]
    summary = {
        "variant": "summary",
        "title": "Phylogenetic analysis of Little Red Riding Hood",
        "instruction_words": "list of words A-I",
        "max_words_per_gap": 1,
        "options": word_bank,
        "paragraphs": [
            {
                "segments": [
                    {
                        "type": "text",
                        "value": (
                            "Tehrani used techniques from evolutionary biology "
                            "to find out if "
                        ),
                    },
                    {"type": "gap", "gap_id": "g32"},
                    {
                        "type": "text",
                        "value": (
                            " existed among 58 stories from around the world. "
                            "He also wanted to know which aspects of the stories "
                            "had fewest "
                        ),
                    },
                    {"type": "gap", "gap_id": "g33"},
                    {
                        "type": "text",
                        "value": (
                            ", as he believed these aspects would be the most "
                            "important ones. Contrary to other beliefs, he found "
                            "that some "
                        ),
                    },
                    {"type": "gap", "gap_id": "g34"},
                    {
                        "type": "text",
                        "value": (
                            " that were included in a story tended to change over "
                            "time, and that the middle of a story seemed no more "
                            "important than the other parts. He was also surprised "
                            "that parts of a story which seemed to provide some "
                            "sort of "
                        ),
                    },
                    {"type": "gap", "gap_id": "g35"},
                    {
                        "type": "text",
                        "value": (
                            " were unimportant. The aspect that he found most "
                            "important in a story's survival was "
                        ),
                    },
                    {"type": "gap", "gap_id": "g36"},
                    {"type": "text", "value": "."},
                ]
            }
        ],
    }
    sg = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.SUMMARY_COMPLETION.value,
        instruction=(
            "Complete the summary using the list of words or phrases below.\n"
            "Choose the correct letter, A-I, in boxes 32-36 on your answer sheet."
        ),
        options_shared=summary,
    )
    db.add(sg)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=sg.id,
        qtype=QuestionType.SUMMARY_COMPLETION,
        answers=[
            ("g32", ["D", "links"]),
            ("g33", ["F", "variations"]),
            ("g34", ["B", "events"]),
            ("g35", ["C", "warning"]),
            ("g36", ["G", "horror"]),
        ],
        max_words=1,
    )

    mcq_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MCQ.value,
        instruction="Choose the correct letter, A, B, C or D.",
    )
    db.add(mcq_group)
    await db.flush()
    mcqs = [
        (
            "What method did Jamie Tehrani use to test his ideas about fairy tales?",
            [
                "He compared oral and written forms of the same stories.",
                "He looked at many different forms of the same basic story.",
                "He looked at unrelated stories from many different countries.",
                "He contrasted the development of fairy tales with that of living creatures.",
            ],
            "B",
        ),
        (
            "When discussing Tehrani's views, Jack Zipes suggests that",
            [
                "Tehrani ignores key changes in the role of women.",
                "stories which are too horrific are not always taken seriously.",
                "Tehrani overemphasises the importance of violence in stories.",
                "features of stories only survive if they have a deeper significance.",
            ],
            "D",
        ),
        (
            "Why does Tehrani refer to Chinese and Japanese fairy tales?",
            [
                "to indicate that Jack Zipes' theory is incorrect",
                "to suggest that crime is a global problem",
                "to imply that all fairy tales have a similar meaning",
                "to add more evidence for Jack Zipes' ideas",
            ],
            "A",
        ),
        (
            "What does Mathias Clasen believe about fairy tales?",
            [
                "They are a safe way of learning to deal with fear.",
                "They are a type of entertainment that some people avoid.",
                "They reflect the changing values of our society.",
                "They reduce our ability to deal with real-world problems.",
            ],
            "A",
        ),
    ]
    for i, (question, options, correct) in enumerate(mcqs, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=mcq_group.id,
                order=i,
                question_type=QuestionType.MCQ,
                content={"question": question, "options": options},
                answer_key={"correct": correct},
            )
        )
        print(f"    MCQ {i} -> {correct}")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")
        if test.id in PROTECTED_TEST_IDS:
            raise SystemExit(f"Refusing to seed into protected test {test.id}")
        print(f"Test: {test.title} ({test.id})")

        p1, p2, p3 = await _reading_sections(db, test.id)
        print("\nPassage 1")
        await _seed_p1(db, p1)
        print("\nPassage 2")
        await _seed_p2(db, p2)
        print("\nPassage 3")
        await _seed_p3(db, p3)

        await db.flush()
        total = 0
        for name, section in (("P1", p1), ("P2", p2), ("P3", p3)):
            qs = (
                await db.execute(
                    select(Question).where(Question.section_id == section.id)
                )
            ).scalars().all()
            slots = sum(scoring_slots_for_question(q) for q in qs)
            print(f"  {name} scoring slots: {slots}")
            total += slots
        if total != 40:
            raise SystemExit(f"Reading must have 40 slots, got {total}")

        await db.commit()
        print("\nDone. Cambridge IELTS 15 – Test 3 Reading Q1–40 seeded. Unpublished.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
