"""Seed Cambridge IELTS 15 Test 4 Reading (Q1–40).

Reuses the existing Test 4 record. Idempotent wipe of reading groups/questions.

Usage:
    python /app/scripts/seed_ielts15_t4_reading.py
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
from ielts15_t4_reading_passages import (  # noqa: E402
    P1_HUARANGO,
    P2_SILBO,
    P3_BIG_BUSINESS,
)

TEST_ID = uuid.UUID("8e84227c-abde-41f9-ab36-7ea51527b7e6")
PROTECTED_TEST_IDS = {
    uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590"),
    uuid.UUID("6074d5f2-70b8-4f31-9b59-10f861a3eadf"),
    uuid.UUID("3b766b14-d188-4c81-814f-77fadff4e3fa"),
}


def _text(value: str) -> dict:
    return {"type": "text", "value": value}


def _gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def _item(*parts: str | dict) -> dict:
    segments: list[dict] = []
    for part in parts:
        segments.append(_text(part) if isinstance(part, str) else part)
    return {"segments": segments}


def _plain(*parts: str | dict) -> dict:
    return {"variant": "plain", **_item(*parts)}


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
    order_start: int = 1,
) -> int:
    order = order_start
    for gap_id, variants in answers:
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section_id,
                question_group_id=group_id,
                order=order,
                question_type=qtype,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=max_words),
            )
        )
        print(f"    {gap_id} -> {variants}")
        order += 1
    return order


async def _add_statements(
    db: AsyncSession,
    *,
    section: Section,
    group: QuestionGroup,
    qtype: QuestionType,
    items: list[tuple[str, str]],
    label: str,
) -> None:
    for i, (statement, correct) in enumerate(items, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=i,
                question_type=qtype,
                content={"statement": statement},
                answer_key={"correct": correct},
            )
        )
        print(f"    {label} {i} -> {correct}")


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
    section.title = "The return of the huarango"
    section.passage = P1_HUARANGO
    section.passage_subtitle = (
        "The arid valleys of southern Peru are welcoming the return of a native plant"
    )
    await _wipe_section(db, section.id)

    notes = {
        "variant": "notes",
        "title": "The importance of the huarango tree",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "sections": [
            {
                "heading": "",
                "items": [
                    _item("its roots can extend as far as 80 metres into the soil"),
                    _item("can access ", _gap("g1"), " deep below the surface"),
                    _item(
                        "was a crucial part of local inhabitants' ",
                        _gap("g2"),
                        " a long time ago",
                    ),
                    _item("helped people to survive periods of ", _gap("g3")),
                    _item("prevents ", _gap("g4"), " of the soil"),
                    _item("prevents land from becoming a ", _gap("g5")),
                ],
            }
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
            ("g1", ["water"]),
            ("g2", ["diet"]),
            ("g3", ["drought"]),
            ("g4", ["erosion"]),
            ("g5", ["desert"]),
        ],
        max_words=1,
    )

    table = {
        "variant": "table",
        "title": "Traditional uses of the huarango tree",
        "instruction_words": "NO MORE THAN TWO WORDS",
        "max_words_per_gap": 2,
        "headers": ["Part of tree", "Traditional use"],
        "rows": [
            [_plain(_gap("g6")), _plain("fuel")],
            [_plain(_gap("g7"), " and ", _gap("g7")), _plain("medicine")],
            [_plain(_gap("g8")), _plain("construction")],
        ],
    }
    table_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.TABLE_COMPLETION.value,
        instruction=(
            "Complete the table below.\n"
            "Choose NO MORE THAN TWO WORDS from the passage for each answer.\n"
            "Write your answers in boxes 6-8 on your answer sheet."
        ),
        options_shared=table,
    )
    db.add(table_group)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=table_group.id,
        qtype=QuestionType.TABLE_COMPLETION,
        answers=[
            ("g6", ["branches", "its branches", "the branches", "huarango branches"]),
            (
                "g7",
                [
                    "leaves and bark",
                    "bark and leaves",
                    "leaves bark",
                    "bark leaves",
                ],
            ),
            ("g8", ["trunk", "its trunk", "the trunk", "huarango trunk"]),
        ],
        max_words=2,
        order_start=6,
    )

    tfng_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.TRUE_FALSE_NG.value,
        instruction=(
            "Do the following statements agree with the information given "
            "in Reading Passage 1?\n"
            "In boxes 9-13 on your answer sheet, write\n"
            "TRUE if the statement agrees with the information\n"
            "FALSE if the statement contradicts the information\n"
            "NOT GIVEN if there is no information on this"
        ),
    )
    db.add(tfng_group)
    await db.flush()
    await _add_statements(
        db,
        section=section,
        group=tfng_group,
        qtype=QuestionType.TRUE_FALSE_NG,
        items=[
            (
                "Local families have told Whaley about some traditional uses of huarango products.",
                "Not Given",
            ),
            (
                "Farmer Alberto Benevides is now making a good profit from growing huarangos.",
                "False",
            ),
            (
                "Whaley needs the co-operation of farmers to help preserve the area's wildlife.",
                "True",
            ),
            (
                "For Whaley's project to succeed, it needs to be extended over a very large area.",
                "False",
            ),
            (
                "Whaley has plans to go to Africa to set up a similar project.",
                "Not Given",
            ),
        ],
        label="TFNG",
    )


async def _seed_p2(db: AsyncSession, section: Section) -> None:
    section.title = "Silbo Gomero – the whistle 'language' of the Canary Islands"
    section.passage = P2_SILBO
    section.passage_subtitle = None
    await _wipe_section(db, section.id)

    tfng_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.TRUE_FALSE_NG.value,
        instruction=(
            "Do the following statements agree with the information given "
            "in Reading Passage 2?\n"
            "In boxes 14-19 on your answer sheet, write\n"
            "TRUE if the statement agrees with the information\n"
            "FALSE if the statement contradicts the information\n"
            "NOT GIVEN if there is no information on this"
        ),
    )
    db.add(tfng_group)
    await db.flush()
    await _add_statements(
        db,
        section=section,
        group=tfng_group,
        qtype=QuestionType.TRUE_FALSE_NG,
        items=[
            ("La Gomera is the most mountainous of all the Canary Islands.", "Not Given"),
            ("Silbo is only appropriate for short and simple messages.", "False"),
            (
                "In the brain-activity study, silbadores and non-whistlers produced different results.",
                "True",
            ),
            (
                "The Spanish introduced Silbo to the islands in the 15th century.",
                "False",
            ),
            (
                "There is precise data available regarding all of the whistle languages in existence today.",
                "False",
            ),
            ("The children of Gomera now learn Silbo.", "True"),
        ],
        label="TFNG",
    )

    notes = {
        "variant": "notes",
        "title": "Silbo Gomero",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "sections": [
            {
                "heading": "How Silbo is produced",
                "items": [
                    _item(
                        "high- and low-frequency tones represent different sounds in Spanish ",
                        _gap("g20"),
                    ),
                    _item(
                        "pitch of whistle is controlled using silbador's ",
                        _gap("g21"),
                    ),
                    _item(_gap("g22"), " is changed with a cupped hand"),
                ],
            },
            {
                "heading": "How Silbo is used",
                "items": [
                    _item(
                        "has long been used by shepherds and people living in secluded locations"
                    ),
                    _item(
                        "in everyday use for the transmission of brief ",
                        _gap("g23"),
                    ),
                    _item(
                        "can relay essential information quickly, e.g. to inform people about ",
                        _gap("g24"),
                    ),
                ],
            },
            {
                "heading": "The future of Silbo",
                "items": [
                    _item("future under threat because of new ", _gap("g25")),
                    _item(
                        "Canaries' authorities hoping to receive a UNESCO ",
                        _gap("g26"),
                        " to help preserve it",
                    ),
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
            ("g20", ["words"]),
            ("g21", ["finger"]),
            ("g22", ["direction"]),
            ("g23", ["commands"]),
            ("g24", ["fires"]),
            ("g25", ["technology"]),
            ("g26", ["award"]),
        ],
        max_words=1,
        order_start=20,
    )


async def _seed_p3(db: AsyncSession, section: Section) -> None:
    section.title = "Environmental practices of big businesses"
    section.passage = P3_BIG_BUSINESS
    section.passage_subtitle = None
    await _wipe_section(db, section.id)

    word_bank = [
        "A. funding",
        "B. trees",
        "C. rare species",
        "D. moral standards",
        "E. control",
        "F. involvement",
        "G. flooding",
        "H. overfishing",
        "I. worker support",
    ]
    summary = {
        "variant": "summary",
        "title": "big businesses",
        "instruction_words": "list of words A-I",
        "max_words_per_gap": 1,
        "options": word_bank,
        "paragraphs": [
            {
                "segments": [
                    {
                        "type": "text",
                        "value": (
                            "Many big businesses today are prepared to harm people "
                            "and the environment in order to make money, and they "
                            "appear to have no "
                        ),
                    },
                    {"type": "gap", "gap_id": "g27"},
                    {
                        "type": "text",
                        "value": ". Lack of ",
                    },
                    {"type": "gap", "gap_id": "g28"},
                    {
                        "type": "text",
                        "value": " by governments and lack of public ",
                    },
                    {"type": "gap", "gap_id": "g29"},
                    {
                        "type": "text",
                        "value": " can lead to environmental problems such as ",
                    },
                    {"type": "gap", "gap_id": "g30"},
                    {
                        "type": "text",
                        "value": " or the destruction of ",
                    },
                    {"type": "gap", "gap_id": "g31"},
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
            "Choose the correct letter, A-I, in boxes 27-31 on your answer sheet."
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
            ("g27", ["D", "moral standards"]),
            ("g28", ["E", "control"]),
            ("g29", ["F", "involvement"]),
            ("g30", ["H", "overfishing"]),
            ("g31", ["B", "trees"]),
        ],
        max_words=1,
        order_start=27,
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
            "The main idea of the third paragraph is that environmental damage",
            [
                "requires political action if it is to be stopped.",
                "is the result of ignorance on the part of the public.",
                "could be prevented by the action of ordinary people.",
                "can only be stopped by educating business leaders.",
            ],
            "C",
        ),
        (
            "In the fourth paragraph, the writer describes ways in which the public can",
            [
                "reduce their own individual impact on the environment.",
                "learn more about the impact of business on the environment.",
                "raise awareness of the effects of specific environmental disasters.",
                "influence the environmental policies of businesses and governments.",
            ],
            "D",
        ),
        (
            "What pressure was exerted by big business in the case of the disease BSE?",
            [
                "Meat packers stopped supplying hamburgers to fast-food chains.",
                "A fast-food company forced their meat suppliers to follow the law.",
                "Meat packers persuaded the government to reduce their expenses.",
                "A fast-food company encouraged the government to introduce legislation.",
            ],
            "B",
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

    yn = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.YES_NO_NG.value,
        instruction=(
            "Do the following statements agree with the claims of the writer "
            "in Reading Passage 3?\n"
            "In boxes 35-39 on your answer sheet, write\n"
            "YES if the statement agrees with the claims of the writer\n"
            "NO if the statement contradicts the claims of the writer\n"
            "NOT GIVEN if it is impossible to say what the writer thinks about this"
        ),
    )
    db.add(yn)
    await db.flush()
    await _add_statements(
        db,
        section=section,
        group=yn,
        qtype=QuestionType.YES_NO_NG,
        items=[
            (
                "The public should be prepared to fund good environmental practices.",
                "Yes",
            ),
            (
                "There is a contrast between the moral principles of different businesses.",
                "Not Given",
            ),
            (
                "It is important to make a clear distinction between acceptable and unacceptable behaviour.",
                "No",
            ),
            (
                "The public have successfully influenced businesses in the past.",
                "Yes",
            ),
            (
                "In the future, businesses will show more concern for the environment.",
                "Not Given",
            ),
        ],
        label="YNNG",
    )

    q40 = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MCQ.value,
        instruction="Choose the correct letter, A, B, C or D.",
    )
    db.add(q40)
    await db.flush()
    db.add(
        Question(
            id=uuid.uuid4(),
            section_id=section.id,
            question_group_id=q40.id,
            order=1,
            question_type=QuestionType.MCQ,
            content={
                "question": "What would be the best subheading for this passage?",
                "options": [
                    "Will the world survive the threat caused by big businesses?",
                    "How can big businesses be encouraged to be less driven by profit?",
                    "What environmental dangers are caused by the greed of businesses?",
                    "Are big businesses to blame for the damage they cause the environment?",
                ],
            },
            answer_key={"correct": "D"},
        )
    )
    print("    MCQ 40 -> D")


async def main() -> None:
    if TEST_ID in PROTECTED_TEST_IDS:
        raise SystemExit(f"Refusing to seed into protected test {TEST_ID}")

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
        print("\nDone. Cambridge IELTS 15 – Test 4 Reading Q1–40 seeded. Unpublished.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
