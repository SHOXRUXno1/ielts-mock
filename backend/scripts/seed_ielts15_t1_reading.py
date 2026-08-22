"""Seed Cambridge IELTS 15 Test 1 Reading (Q1–40).

Keeps existing passage text. Idempotent wipe of reading groups/questions.

Usage (prod container):
    python /tmp/seed_ielts15_t1_reading.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test
from app.services.scoring import scoring_slots_for_question
from app.services.seed_compound import gap_answer_key, next_group_order

TEST_ID = uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590")
P1_ID = uuid.UUID("bd3ddfd6-136a-4f91-b30f-7186923edea8")
P2_ID = uuid.UUID("7033fa98-47b1-42c7-b0f9-e3754f2745c8")
P3_ID = uuid.UUID("fb6f5f58-5ce8-4194-8c0e-915f87a07da8")


def _plain(text: str) -> dict:
    return {"variant": "plain", "segments": [{"type": "text", "value": text}]}


def _plain_gap(before: str, gap_id: str, after: str = "") -> dict:
    segments: list[dict] = []
    if before:
        segments.append({"type": "text", "value": before})
    segments.append({"type": "gap", "gap_id": gap_id})
    if after:
        segments.append({"type": "text", "value": after})
    return {"variant": "plain", "segments": segments}


async def _wipe_section(db: AsyncSession, section_id: uuid.UUID) -> int:
    from sqlalchemy import delete as sa_delete

    from app.models.answer import Answer

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


async def _seed_p1(db: AsyncSession, section: Section) -> None:
    section.title = "Nutmeg – a valuable spice"
    await _wipe_section(db, section.id)

    notes_structure = {
        "variant": "notes",
        "title": "The nutmeg tree and fruit",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "sections": [
            {
                "heading": "",
                "items": [
                    {
                        "segments": [
                            {"type": "text", "value": "the leaves of the tree are "},
                            {"type": "gap", "gap_id": "g1"},
                            {"type": "text", "value": " in shape"},
                        ]
                    },
                    {
                        "segments": [
                            {"type": "text", "value": "the "},
                            {"type": "gap", "gap_id": "g2"},
                            {
                                "type": "text",
                                "value": (
                                    " surrounds the fruit and breaks open "
                                    "when the fruit is ripe"
                                ),
                            },
                        ]
                    },
                    {
                        "segments": [
                            {"type": "text", "value": "the "},
                            {"type": "gap", "gap_id": "g3"},
                            {
                                "type": "text",
                                "value": " is used to produce the spice nutmeg",
                            },
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": (
                                    "the covering known as the aril "
                                    "is used to produce "
                                ),
                            },
                            {"type": "gap", "gap_id": "g4"},
                        ]
                    },
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
        options_shared=notes_structure,
    )
    db.add(notes_group)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=notes_group.id,
        qtype=QuestionType.NOTE_COMPLETION,
        answers=[
            ("g1", ["oval"]),
            ("g2", ["husk"]),
            ("g3", ["seed"]),
            ("g4", ["mace"]),
        ],
        max_words=1,
    )

    tfng_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.TRUE_FALSE_NG.value,
        instruction=(
            "Do the following statements agree with the information given "
            "in Reading Passage 1?\n"
            "In boxes 5-7 on your answer sheet, write\n"
            "TRUE if the statement agrees with the information\n"
            "FALSE if the statement contradicts the information\n"
            "NOT GIVEN if there is no information on this"
        ),
    )
    db.add(tfng_group)
    await db.flush()
    tfng = [
        (
            "In the Middle Ages, most Europeans knew where nutmeg was grown.",
            "False",
        ),
        ("The VOC was the world's first major trading company.", "Not Given"),
        (
            "Following the Treaty of Breda, the Dutch had control of all "
            "the islands where nutmeg grew.",
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

    table_structure = {
        "variant": "table",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "headers": ["Period", "Event"],
        "rows": [
            [
                _plain("Middle Ages"),
                _plain_gap("Nutmeg was brought to Europe by the ", "g8"),
            ],
            [
                _plain("16th century"),
                _plain("European nations took control of the nutmeg trade"),
            ],
            [
                _plain("17th century"),
                {
                    "variant": "bullets",
                    "bullets": [
                        {
                            "segments": [
                                {
                                    "type": "text",
                                    "value": (
                                        "Demand for nutmeg grew, as it was "
                                        "believed to be effective against the "
                                        "disease known as the "
                                    ),
                                },
                                {"type": "gap", "gap_id": "g9"},
                            ]
                        },
                        {"segments": [{"type": "text", "value": "The Dutch"}]},
                        {
                            "segments": [
                                {
                                    "type": "text",
                                    "value": "took control of the Banda Islands",
                                }
                            ]
                        },
                        {
                            "segments": [
                                {
                                    "type": "text",
                                    "value": (
                                        "restricted nutmeg production "
                                        "to a few areas"
                                    ),
                                }
                            ]
                        },
                        {
                            "segments": [
                                {"type": "text", "value": "put "},
                                {"type": "gap", "gap_id": "g10"},
                                {
                                    "type": "text",
                                    "value": (
                                        " on nutmeg to avoid it being "
                                        "cultivated outside the islands"
                                    ),
                                },
                            ]
                        },
                        {
                            "segments": [
                                {
                                    "type": "text",
                                    "value": "finally obtained the island of ",
                                },
                                {"type": "gap", "gap_id": "g11"},
                                {"type": "text", "value": " from the British"},
                            ]
                        },
                    ],
                },
            ],
            [
                _plain("Late 18th century"),
                {
                    "variant": "bullets",
                    "bullets": [
                        {
                            "segments": [
                                {
                                    "type": "text",
                                    "value": (
                                        "1770 – nutmeg plants were secretly "
                                        "taken to "
                                    ),
                                },
                                {"type": "gap", "gap_id": "g12"},
                            ]
                        },
                        {
                            "segments": [
                                {
                                    "type": "text",
                                    "value": (
                                        "1778 – half the Banda Islands' "
                                        "nutmeg plantations were destroyed "
                                        "by a "
                                    ),
                                },
                                {"type": "gap", "gap_id": "g13"},
                            ]
                        },
                    ],
                },
            ],
        ],
    }
    table_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.TABLE_COMPLETION.value,
        instruction=(
            "Complete the table below.\n"
            "Choose ONE WORD ONLY from the passage for each answer."
        ),
        options_shared=table_structure,
    )
    db.add(table_group)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=table_group.id,
        qtype=QuestionType.TABLE_COMPLETION,
        answers=[
            ("g8", ["Arabs"]),
            ("g9", ["plague"]),
            ("g10", ["lime"]),
            ("g11", ["Run"]),
            ("g12", ["Mauritius"]),
            ("g13", ["tsunami"]),
        ],
        max_words=1,
    )


async def _seed_p2(db: AsyncSession, section: Section) -> None:
    section.title = "Driverless cars"
    await _wipe_section(db, section.id)

    mi_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MATCHING_INFORMATION.value,
        instruction=(
            "Reading Passage 2 has seven paragraphs, A-G.\n"
            "Which section contains the following information?\n"
            "Write the correct letter, A-G, in boxes 14-18 on your answer sheet."
        ),
        subtitle="List of Paragraphs",
        options_shared={"options": list("ABCDEFG")},
    )
    db.add(mi_group)
    await db.flush()
    mi_items = [
        ("reference to the amount of time when a car is not in use", "C"),
        (
            "mention of several advantages of driverless vehicles "
            "for individual road-users",
            "B",
        ),
        (
            "reference to the opportunity of choosing the most "
            "appropriate vehicle for each trip",
            "E",
        ),
        (
            "an estimate of how long it will take to overcome "
            "a number of problems",
            "G",
        ),
        (
            "a suggestion that the use of driverless cars may have "
            "no effect on the number of vehicles manufactured",
            "D",
        ),
    ]
    for i, (stem, letter) in enumerate(mi_items, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=mi_group.id,
                order=i,
                question_type=QuestionType.MATCHING_INFORMATION,
                content={"question": stem},
                answer_key={"correct": letter},
            )
        )
        print(f"    MI {i} -> {letter}")

    summary_structure = {
        "variant": "summary",
        "title": "The impact of driverless cars",
        "instruction_words": "NO MORE THAN TWO WORDS",
        "max_words_per_gap": 2,
        "paragraphs": [
            {
                "segments": [
                    {
                        "type": "text",
                        "value": (
                            "Figures from the Transport Research Laboratory "
                            "indicate that most motor accidents are partly "
                            "due to "
                        ),
                    },
                    {"type": "gap", "gap_id": "g19"},
                    {
                        "type": "text",
                        "value": (
                            ", so the introduction of driverless vehicles "
                            "will result in greater safety. In addition to "
                            "the direct benefits of automation, it may "
                            "bring other advantages. For example, schemes "
                            "for "
                        ),
                    },
                    {"type": "gap", "gap_id": "g20"},
                    {
                        "type": "text",
                        "value": (
                            " will be more workable, especially in towns "
                            "and cities, resulting in fewer cars on the "
                            "road. According to the University of Michigan "
                            "Transportation Research Institute, there "
                            "could be a 43 percent drop in "
                        ),
                    },
                    {"type": "gap", "gap_id": "g21"},
                    {
                        "type": "text",
                        "value": (
                            " of cars. However, this would mean that the "
                            "yearly "
                        ),
                    },
                    {"type": "gap", "gap_id": "g22"},
                    {
                        "type": "text",
                        "value": (
                            " of each car would, on average, be twice as "
                            "high as it currently is. This would lead to a "
                            "higher turnover of vehicles, and therefore no "
                            "reduction in automotive manufacturing."
                        ),
                    },
                ]
            }
        ],
    }
    summary_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.SUMMARY_COMPLETION.value,
        instruction=(
            "Complete the summary below.\n"
            "Choose NO MORE THAN TWO WORDS from the passage for each answer."
        ),
        options_shared=summary_structure,
    )
    db.add(summary_group)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=summary_group.id,
        qtype=QuestionType.SUMMARY_COMPLETION,
        answers=[
            ("g19", ["human error"]),
            ("g20", ["car sharing", "car-sharing"]),
            ("g21", ["ownership", "vehicle ownership"]),
            ("g22", ["mileage"]),
        ],
        max_words=2,
    )

    for question, options, correct in (
        (
            "Which TWO benefits of automated vehicles does the writer mention?",
            [
                "Car travellers could enjoy considerable cost savings.",
                "It would be easier to find parking spaces in urban areas.",
                "Travellers could spend journeys doing something other than driving.",
                "People who find driving physically difficult could travel independently.",
                "A reduction in the number of cars would mean a reduction in pollution.",
            ],
            ["C", "D"],
        ),
        (
            "Which TWO challenges to automated vehicle development does the writer mention?",
            [
                "making sure the general public has confidence in automated vehicles",
                "managing the pace of transition from conventional to automated vehicles",
                "deciding how to compensate professional drivers who become redundant",
                "setting up the infrastructure to make roads suitable for automated vehicles",
                "getting automated vehicles to adapt to various different driving conditions",
            ],
            ["A", "E"],
        ),
    ):
        g = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=await next_group_order(db, section.id),
            question_type=QuestionType.MULTI_SELECT.value,
            instruction="Choose TWO letters, A-E.",
        )
        db.add(g)
        await db.flush()
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=g.id,
                order=1,
                question_type=QuestionType.MULTI_SELECT,
                content={
                    "choose_n": 2,
                    "question": question,
                    "options": options,
                },
                answer_key={"correct": correct},
            )
        )
        print(f"    multi -> {correct}")


async def _seed_p3(db: AsyncSession, section: Section) -> None:
    section.title = "What is exploration?"
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
            "The writer refers to visitors to New York to illustrate the point that",
            [
                "exploration is an intrinsic element of being human.",
                "most people are enthusiastic about exploring.",
                "exploration can lead to surprising results.",
                "most people find exploration daunting.",
            ],
            "A",
        ),
        (
            "According to the second paragraph, what is the writer's view of explorers?",
            [
                "Their discoveries have brought both benefits and disadvantages.",
                "Their main value is in teaching others.",
                "They act on an urge that is common to everyone.",
                "They tend to be more attracted to certain professions than to others.",
            ],
            "C",
        ),
        (
            "The writer refers to a description of Egdon Heath to suggest that",
            [
                "Hardy was writing about his own experience of exploration.",
                "Hardy was mistaken about the nature of exploration.",
                "Hardy's aim was to investigate people's emotional states.",
                "Hardy's aim was to show the attraction of isolation.",
            ],
            "C",
        ),
        (
            "In the fourth paragraph, the writer refers to 'a golden age' to suggest that",
            [
                "the amount of useful information produced by exploration has decreased.",
                "fewer people are interested in exploring than in the 19th century.",
                "recent developments have made exploration less exciting.",
                "we are wrong to think that exploration is no longer necessary.",
            ],
            "D",
        ),
        (
            "In the sixth paragraph, when discussing the definition of exploration, the writer argues that",
            [
                "people tend to relate exploration to their own professional interests.",
                "certain people are likely to misunderstand the nature of exploration.",
                "the generally accepted definition has changed over time.",
                "historians and scientists have more valid definitions than the general public.",
            ],
            "A",
        ),
        (
            "In the last paragraph, the writer explains that he is interested in",
            [
                "how someone's personality is reflected in their choice of places to visit.",
                "the human ability to cast new light on places that may be familiar.",
                "how travel writing has evolved to meet changing demands.",
                "the feelings that writers develop about the places that they explore.",
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

    match_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.MATCHING_FEATURES.value,
        instruction=(
            "Look at the following statements (Questions 33-37) and the "
            "list of explorers below.\n"
            "Match each statement with the correct explorer, A-E.\n"
            "NB You may use any letter more than once."
        ),
        subtitle="List of Explorers",
        options_shared={
            "options": [
                "A. Peter Fleming",
                "B. Ran Fiennes",
                "C. Chris Bonington",
                "D. Robin Hanbury-Tenison",
                "E. Wilfred Thesiger",
            ]
        },
    )
    db.add(match_group)
    await db.flush()
    match_items = [
        ("He referred to the relevance of the form of transport used.", "E"),
        ("He described feelings on coming back home after a long journey.", "A"),
        ("He worked for the benefit of specific groups of people.", "D"),
        (
            "He did not consider learning about oneself an essential "
            "part of exploration.",
            "E",
        ),
        (
            "He defined exploration as being both unique and of value to others.",
            "B",
        ),
    ]
    for i, (stem, letter) in enumerate(match_items, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=match_group.id,
                order=i,
                question_type=QuestionType.MATCHING_FEATURES,
                content={"question": stem},
                answer_key={"correct": letter},
            )
        )
        print(f"    match {i} -> {letter}")

    summary_structure = {
        "variant": "summary",
        "title": "The writer's own bias",
        "instruction_words": "NO MORE THAN TWO WORDS",
        "max_words_per_gap": 2,
        "paragraphs": [
            {
                "segments": [
                    {
                        "type": "text",
                        "value": "The writer has experience of a large number of ",
                    },
                    {"type": "gap", "gap_id": "g38"},
                    {
                        "type": "text",
                        "value": (
                            ", and was the first stranger that certain "
                            "previously "
                        ),
                    },
                    {"type": "gap", "gap_id": "g39"},
                    {
                        "type": "text",
                        "value": (
                            " people had encountered. He believes there "
                            "is no need for further exploration of Earth's "
                        ),
                    },
                    {"type": "gap", "gap_id": "g40"},
                    {
                        "type": "text",
                        "value": (
                            " except to answer specific questions such as "
                            "how buffalo eat."
                        ),
                    },
                ]
            }
        ],
    }
    summary_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=await next_group_order(db, section.id),
        question_type=QuestionType.SUMMARY_COMPLETION.value,
        instruction=(
            "Complete the summary below.\n"
            "Choose NO MORE THAN TWO WORDS from the passage for each answer."
        ),
        options_shared=summary_structure,
    )
    db.add(summary_group)
    await db.flush()
    await _add_gaps(
        db,
        section_id=section.id,
        group_id=summary_group.id,
        qtype=QuestionType.SUMMARY_COMPLETION,
        answers=[
            ("g38", ["expeditions", "unique expeditions"]),
            ("g39", ["uncontacted", "isolated"]),
            ("g40", ["surface", "land surface"]),
        ],
        max_words=2,
    )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")
        print(f"Test: {test.title} ({test.id})")

        for sid, name, seeder in (
            (P1_ID, "Passage 1", _seed_p1),
            (P2_ID, "Passage 2", _seed_p2),
            (P3_ID, "Passage 3", _seed_p3),
        ):
            section = await db.get(Section, sid)
            if section is None or section.test_id != TEST_ID:
                raise SystemExit(f"{name} {sid} not found")
            if not (section.passage or "").strip():
                raise SystemExit(f"{name} has empty passage — abort")
            print(f"\n=== {name}: {section.title} (keep passage {len(section.passage)} chars) ===")
            await seeder(db, section)

        print("\nVerify scoring slots")
        total = 0
        for sid, name in ((P1_ID, "P1"), (P2_ID, "P2"), (P3_ID, "P3")):
            qs = (
                await db.execute(
                    select(Question)
                    .where(Question.section_id == sid)
                    .order_by(Question.order)
                )
            ).scalars().all()
            slots = sum(scoring_slots_for_question(q) for q in qs)
            total += slots
            print(f"  {name}: {len(qs)} rows, {slots} slots")
        if total != 40:
            raise SystemExit(f"Expected 40 reading slots, got {total}")

        await db.commit()
        print("\nDone. IELTS 15 Test 1 Reading Q1–40 seeded. Passages unchanged.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
