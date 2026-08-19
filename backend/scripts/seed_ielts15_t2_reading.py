"""Seed Cambridge IELTS 15 Test 2 Reading (Q1–40).

Reuses the existing Test 2 record. Idempotent wipe of reading groups/questions.

Usage:
    python /app/scripts/seed_ielts15_t2_reading.py
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
from ielts15_t2_reading_passages import (  # noqa: E402
    P1_URBAN_DANCE,
    P2_DE_EXTINCTION,
    P3_HAVING_A_LAUGH,
)

TEST_ID = uuid.UUID("6074d5f2-70b8-4f31-9b59-10f861a3eadf")


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
    section.title = "Could urban engineers learn from dance?"
    section.passage = P1_URBAN_DANCE
    section.passage_subtitle = None
    await _wipe_section(db, section.id)

    mi_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MATCHING_INFORMATION.value,
        instruction=(
            "Reading Passage 1 has seven paragraphs, A-G.\n"
            "Which paragraph contains the following information?\n"
            "Write the correct letter, A-G, in boxes 1-6 on your answer sheet."
        ),
        subtitle="List of Paragraphs",
        options_shared={"options": list("ABCDEFG")},
    )
    db.add(mi_group)
    await db.flush()
    await _add_letter_items(
        db,
        section=section,
        group=mi_group,
        qtype=QuestionType.MATCHING_INFORMATION,
        items=[
            (
                "reference to an appealing way of using dance that the writer is not proposing",
                "B",
            ),
            (
                "an example of a contrast between past and present approaches to building",
                "C",
            ),
            ("mention of an objective of both dance and engineering", "F"),
            (
                "reference to an unforeseen problem arising from ignoring the climate",
                "D",
            ),
            ("why some measures intended to help people are being reversed", "E"),
            ("reference to how transport has an impact on human lives", "A"),
        ],
        label="MI",
    )

    summary = {
        "variant": "summary",
        "title": "Guard rails",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "paragraphs": [
            {
                "segments": [
                    {"type": "text", "value": "Guard rails were introduced on British roads to improve the "},
                    {"type": "gap", "gap_id": "g7"},
                    {"type": "text", "value": " of pedestrians, while ensuring that the movement of "},
                    {"type": "gap", "gap_id": "g8"},
                    {"type": "text", "value": " is not disrupted. Pedestrians are led to access points, and encouraged to cross one "},
                    {"type": "gap", "gap_id": "g9"},
                    {"type": "text", "value": " at a time. An unintended effect is to create psychological difficulties in crossing the road, particularly for less "},
                    {"type": "gap", "gap_id": "g10"},
                    {"type": "text", "value": " people. Another result is that some people cross the road in a "},
                    {"type": "gap", "gap_id": "g11"},
                    {"type": "text", "value": " way. The guard rails separate "},
                    {"type": "gap", "gap_id": "g12"},
                    {"type": "text", "value": ", and make it more difficult to introduce forms of transport that are "},
                    {"type": "gap", "gap_id": "g13"},
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
            ("g7", ["safety"]),
            ("g8", ["traffic"]),
            ("g9", ["carriageway"]),
            ("g10", ["mobile"]),
            ("g11", ["dangerous"]),
            ("g12", ["communities"]),
            ("g13", ["healthy"]),
        ],
        max_words=1,
    )


async def _seed_p2(db: AsyncSession, section: Section) -> None:
    section.title = "Should we try to bring extinct species back to life?"
    section.passage = P2_DE_EXTINCTION
    section.passage_subtitle = None
    await _wipe_section(db, section.id)

    mi_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MATCHING_INFORMATION.value,
        instruction=(
            "Reading Passage 2 has six paragraphs, A-F.\n"
            "Which paragraph contains the following information?\n"
            "Write the correct letter, A-F, in boxes 14-17 on your answer sheet.\n"
            "NB You may use any letter more than once."
        ),
        subtitle="List of Paragraphs",
        options_shared={"options": list("ABCDEF")},
    )
    db.add(mi_group)
    await db.flush()
    await _add_letter_items(
        db,
        section=section,
        group=mi_group,
        qtype=QuestionType.MATCHING_INFORMATION,
        items=[
            (
                "a reference to how further disappearance of multiple species could be avoided",
                "F",
            ),
            (
                "explanation of a way of reproducing an extinct animal using the DNA of only that species",
                "A",
            ),
            (
                "reference to a habitat which has suffered following the extinction of a species",
                "D",
            ),
            (
                "mention of the exact point at which a particular species became extinct",
                "A",
            ),
        ],
        label="MI",
    )

    summary = {
        "variant": "summary",
        "title": "The woolly mammoth revival project",
        "instruction_words": "NO MORE THAN TWO WORDS",
        "max_words_per_gap": 2,
        "paragraphs": [
            {
                "segments": [
                    {"type": "text", "value": "Professor George Church and his team are trying to identify the "},
                    {"type": "gap", "gap_id": "g18"},
                    {"type": "text", "value": " which enabled mammoths to survive in the tundra. Introducing Asian elephants to the tundra would require physical adaptations to minimise "},
                    {"type": "gap", "gap_id": "g19"},
                    {"type": "text", "value": ". To survive in the tundra, the species would need the mammoth-like features of thicker hair, "},
                    {"type": "gap", "gap_id": "g20"},
                    {"type": "text", "value": " of a reduced size and more "},
                    {"type": "gap", "gap_id": "g21"},
                    {"type": "text", "value": ". Repopulating the tundra could help to reduce temperatures and decrease "},
                    {"type": "gap", "gap_id": "g22"},
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
            "Choose NO MORE THAN TWO WORDS from the passage for each answer."
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
            ("g18", ["genetic traits"]),
            ("g19", ["heat loss"]),
            ("g20", ["ears"]),
            ("g21", ["fat", "insulating fat"]),
            ("g22", ["emissions", "carbon emissions"]),
        ],
        max_words=2,
    )

    match = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MATCHING_FEATURES.value,
        instruction=(
            "Look at the following statements (Questions 23-26) and the list of people below.\n"
            "Match each statement with the correct person, A-C.\n"
            "NB You may use any letter more than once."
        ),
        subtitle="List of People",
        options_shared={
            "options": [
                "A. Ben Novak",
                "B. Michael Archer",
                "C. Beth Shapiro",
            ]
        },
    )
    db.add(match)
    await db.flush()
    await _add_letter_items(
        db,
        section=section,
        group=match,
        qtype=QuestionType.MATCHING_FEATURES,
        items=[
            (
                "Reintroducing an extinct species to its original habitat could improve the health of a particular species living there.",
                "B",
            ),
            ("It is important to concentrate on the causes of an animal's extinction.", "C"),
            (
                "A species brought back from extinction could have an important beneficial impact on the vegetation of its habitat.",
                "A",
            ),
            ("Our current efforts at preserving biodiversity are insufficient.", "C"),
        ],
        label="match",
    )


async def _seed_p3(db: AsyncSession, section: Section) -> None:
    section.title = "Having a laugh"
    section.passage = P3_HAVING_A_LAUGH
    section.passage_subtitle = (
        "The findings of psychological scientists reveal the importance of humour"
    )
    await _wipe_section(db, section.id)

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
            "When referring to laughter in the first paragraph, the writer emphasises",
            [
                "its impact on language.",
                "its function in human culture.",
                "its value to scientific research.",
                "its universality in animal societies.",
            ],
            "C",
        ),
        (
            "What does the writer suggest about Charley Douglass?",
            [
                "He understood the importance of enjoying humour in a group setting.",
                "He believed that TV viewers at home needed to be told when to laugh.",
                "He wanted his shows to appeal to audiences across the social spectrum.",
                "He preferred shows where audiences were present in the recording studio.",
            ],
            "A",
        ),
        (
            "What makes the Santa Cruz study particularly significant?",
            [
                "the various different types of laughter that were studied",
                "the similar results produced by a wide range of cultures",
                "the number of different academic disciplines involved",
                "the many kinds of people whose laughter was recorded",
            ],
            "B",
        ),
        (
            "Which of the following happened in the San Diego study?",
            [
                "Some participants became very upset.",
                "Participants exchanged roles.",
                "Participants who had not met before became friends.",
                "Some participants were unable to laugh.",
            ],
            "B",
        ),
        (
            "In the fifth paragraph, what did the results of the San Diego study suggest?",
            [
                "It is clear whether a dominant laugh is produced by a high- or low-status person.",
                "Low-status individuals in a position of power will still produce submissive laughs.",
                "The submissive laughs of low- and high-status individuals are surprisingly similar.",
                "High-status individuals can always be identified by their way of laughing.",
            ],
            "D",
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

    word_bank = [
        "A. laughter",
        "B. relaxing",
        "C. boring",
        "D. anxiety",
        "E. stimulating",
        "F. emotion",
        "G. enjoyment",
        "H. amusing",
    ]
    summary = {
        "variant": "summary",
        "title": "The benefits of humour",
        "instruction_words": "list of words A-H",
        "max_words_per_gap": 1,
        "options": word_bank,
        "paragraphs": [
            {
                "segments": [
                    {"type": "text", "value": "In one study at Australian National University, randomly chosen groups of participants were shown one of three videos, each designed to generate a different kind of "},
                    {"type": "gap", "gap_id": "g32"},
                    {"type": "text", "value": ". When all participants were then given a deliberately frustrating task to do, it was found that those who had watched the "},
                    {"type": "gap", "gap_id": "g33"},
                    {"type": "text", "value": " video persisted with the task for longer and tried harder to accomplish the task than either of the other two groups. A second study in which participants were asked to perform a particularly "},
                    {"type": "gap", "gap_id": "g34"},
                    {"type": "text", "value": " task produced similar results. According to researchers David Cheng and Lu Wang, these findings suggest that humour not only reduces "},
                    {"type": "gap", "gap_id": "g35"},
                    {"type": "text", "value": " and helps build social connections but it may also have a "},
                    {"type": "gap", "gap_id": "g36"},
                    {"type": "text", "value": " effect on the body and mind."},
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
            "Complete the summary using the list of words, A-H, below.\n"
            "Write the correct letter, A-H, in boxes 32-36 on your answer sheet."
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
            ("g32", ["F", "emotion"]),
            ("g33", ["H", "amusing"]),
            ("g34", ["C", "boring"]),
            ("g35", ["D", "anxiety"]),
            ("g36", ["E", "stimulating"]),
        ],
        max_words=1,
    )

    yn = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.YES_NO_NG.value,
        instruction=(
            "Do the following statements agree with the claims of the writer "
            "in Reading Passage 3?\n"
            "In boxes 37-40 on your answer sheet, write\n"
            "YES if the statement agrees with the claims of the writer\n"
            "NO if the statement contradicts the claims of the writer\n"
            "NOT GIVEN if it is impossible to say what the writer thinks about this"
        ),
    )
    db.add(yn)
    await db.flush()
    yn_items = [
        (
            "Participants in the Santa Cruz study were more accurate at identifying the laughs of friends than those of strangers.",
            "NOT GIVEN",
        ),
        (
            "The researchers in the San Diego study were correct in their predictions regarding the behaviour of the high-status individuals.",
            "YES",
        ),
        (
            "The participants in the Australian National University study were given a fixed amount of time to complete the task focusing on employee profiles.",
            "NO",
        ),
        (
            "Cheng and Wang’s conclusions were in line with established notions regarding task performance.",
            "NO",
        ),
    ]
    for i, (statement, correct) in enumerate(yn_items, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=yn.id,
                order=i,
                question_type=QuestionType.YES_NO_NG,
                content={"statement": statement},
                answer_key={"correct": correct},
            )
        )
        print(f"    YNNG {i} -> {correct}")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")
        print(f"Test: {test.title} ({test.id})")

        p1, p2, p3 = await _reading_sections(db, test.id)
        print("\nPassage 1")
        await _seed_p1(db, p1)
        print("\nPassage 2")
        await _seed_p2(db, p2)
        print("\nPassage 3")
        await _seed_p3(db, p3)

        await db.flush()
        for name, section in (("P1", p1), ("P2", p2), ("P3", p3)):
            qs = (
                await db.execute(
                    select(Question).where(Question.section_id == section.id)
                )
            ).scalars().all()
            slots = sum(scoring_slots_for_question(q) for q in qs)
            print(f"  {name} scoring slots: {slots}")
        total = 0
        for section in (p1, p2, p3):
            qs = (
                await db.execute(
                    select(Question).where(Question.section_id == section.id)
                )
            ).scalars().all()
            total += sum(scoring_slots_for_question(q) for q in qs)
        if total != 40:
            raise SystemExit(f"Reading must have 40 slots, got {total}")

        await db.commit()
        print("\nDone. Cambridge IELTS 15 – Test 2 Reading Q1–40 seeded.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
