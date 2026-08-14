"""Seed IELTS 16 Test 1 Reading Passages 1–3 (Q1–40).

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_ielts16_t1_reading.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test
from app.services.seed_compound import gap_answer_key, next_group_order

# Same-folder import when run as `python scripts/seed_....py`
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ielts16_t1_reading_passages import (  # noqa: E402
    P1_POLAR_BEARS,
    P2_STEP_PYRAMID,
    P3_FUTURE_OF_WORK,
)

TEST_ID = uuid.UUID("4cdab44f-db90-4122-a02b-d7df41fc400a")
P1_ID = uuid.UUID("696e5587-d043-4c48-bdb6-8e30e739a6bb")
P2_ID = uuid.UUID("130f50e8-61b6-447b-a5b5-6b2650372ac7")
P3_ID = uuid.UUID("8a4d77a4-2f13-4e5e-933d-09eb4fd9f78c")


async def _wipe(db: AsyncSession, section_id: uuid.UUID) -> int:
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


async def _seed_p1(db: AsyncSession, section: Section) -> None:
    section.title = "Why we need to protect polar bears"
    section.passage = P1_POLAR_BEARS
    await _wipe(db, P1_ID)

    tfng_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P1_ID,
        order=await next_group_order(db, P1_ID),
        question_type=QuestionType.TRUE_FALSE_NG.value,
        instruction=(
            "Do the following statements agree with the information given "
            "in Reading Passage 1?\n"
            "In boxes 1-7 on your answer sheet, choose\n"
            "TRUE if the statement agrees with the information\n"
            "FALSE if the statement contradicts the information\n"
            "NOT GIVEN if there is no information on this"
        ),
    )
    db.add(tfng_group)
    await db.flush()

    tfng = [
        (
            "Polar bears suffer from various health problems due to the "
            "build-up of fat under their skin.",
            "False",
        ),
        (
            "The study done by Liu and his colleagues compared different "
            "groups of polar bears.",
            "False",
        ),
        (
            "Liu and colleagues were the first researchers to compare "
            "polar bears and brown bears genetically.",
            "Not Given",
        ),
        (
            "Polar bears are able to control their levels of 'bad' "
            "cholesterol by genetic means.",
            "True",
        ),
        (
            "Female polar bears are able to survive for about six months "
            "without food.",
            "True",
        ),
        (
            "It was found that the bones of female polar bears were very "
            "weak when they came out of their dens in spring.",
            "False",
        ),
        (
            "The polar bear's mechanism for increasing bone density could "
            "also be used by people one day.",
            "True",
        ),
    ]
    for i, (statement, correct) in enumerate(tfng, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=P1_ID,
                question_group_id=tfng_group.id,
                order=i,
                question_type=QuestionType.TRUE_FALSE_NG,
                content={"statement": statement},
                answer_key={"correct": correct},
            )
        )
        print(f"  P1 TFNG Q{i} -> {correct}")

    notes_structure = {
        "variant": "notes",
        "title": "Reasons why polar bears should be protected",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "sections": [
            {
                "heading": "",
                "items": [
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": "People think of bears as unintelligent and ",
                            },
                            {"type": "gap", "gap_id": "g1"},
                            {"type": "text", "value": "."},
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": "However, this may not be correct. For example:",
                            }
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": "In Tennoji Zoo, a bear has been seen using a branch as a ",
                            },
                            {"type": "gap", "gap_id": "g2"},
                            {"type": "text", "value": ". This allowed him to knock down some "},
                            {"type": "gap", "gap_id": "g3"},
                            {"type": "text", "value": "."},
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": (
                                    "A wild polar bear worked out a method of "
                                    "reaching a platform where a "
                                ),
                            },
                            {"type": "gap", "gap_id": "g4"},
                            {"type": "text", "value": " was located."},
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": (
                                    "Polar bears have displayed behaviour such as "
                                    "conscious manipulation of objects and activity "
                                    "similar to a "
                                ),
                            },
                            {"type": "gap", "gap_id": "g5"},
                            {"type": "text", "value": "."},
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": "Bears may also display emotions. For example:",
                            }
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": "They may make movements suggesting ",
                            },
                            {"type": "gap", "gap_id": "g6"},
                            {
                                "type": "text",
                                "value": " if disappointed when hunting.",
                            },
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": "They may form relationships with other species.",
                            }
                        ]
                    },
                ],
            }
        ],
    }
    notes_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P1_ID,
        order=await next_group_order(db, P1_ID),
        question_type=QuestionType.NOTE_COMPLETION.value,
        instruction=(
            "Complete the notes below.\n"
            "Choose ONE WORD ONLY from the passage for each answer."
        ),
        options_shared=notes_structure,
    )
    db.add(notes_group)
    await db.flush()
    answers = [
        ("g1", ["violent"]),
        ("g2", ["tool"]),
        ("g3", ["meat"]),
        ("g4", ["photographer"]),
        ("g5", ["game"]),
        ("g6", ["frustration"]),
    ]
    for i, (gap_id, variants) in enumerate(answers, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=P1_ID,
                question_group_id=notes_group.id,
                order=i,
                question_type=QuestionType.NOTE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
        )
        print(f"  P1 notes Q{7 + i} {gap_id} -> {variants}")


async def _seed_p2(db: AsyncSession, section: Section) -> None:
    section.title = "The Step Pyramid of Djoser"
    section.passage = P2_STEP_PYRAMID
    await _wipe(db, P2_ID)

    headings = [
        "i. The areas and artefacts within the pyramid itself",
        "ii. A difficult task for those involved",
        "iii. A king who saved his people",
        "iv. A single certainty among other less definite facts",
        "v. An overview of the external buildings and areas",
        "vi. A pyramid design that others copied",
        "vii. An idea for changing the design of burial structures",
        "viii. An incredible experience despite the few remains",
        "ix. The answers to some unexpected questions",
    ]
    heading_answers = [
        ("Paragraph A", "iv"),
        ("Paragraph B", "vii"),
        ("Paragraph C", "ii"),
        ("Paragraph D", "v"),
        ("Paragraph E", "i"),
        ("Paragraph F", "viii"),
        ("Paragraph G", "vi"),
    ]
    h_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P2_ID,
        order=await next_group_order(db, P2_ID),
        question_type=QuestionType.MATCHING_HEADINGS.value,
        instruction=(
            "Reading Passage 2 has seven paragraphs, A-G.\n"
            "Choose the correct heading for each paragraph from the list "
            "of headings below.\n"
            "Write the correct number, i-ix, in boxes 14-20 on your answer sheet."
        ),
        options_shared={"options": headings},
    )
    db.add(h_group)
    await db.flush()
    for i, (label, correct) in enumerate(heading_answers, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=P2_ID,
                question_group_id=h_group.id,
                order=i,
                question_type=QuestionType.MATCHING_HEADINGS,
                content={"question": label},
                answer_key={"correct": correct},
            )
        )
        print(f"  P2 heading Q{13 + i} {label} -> {correct}")

    notes_structure = {
        "variant": "notes",
        "title": "The Step Pyramid of Djoser",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "sections": [
            {
                "heading": "",
                "items": [
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": (
                                    "The complex that includes the Step Pyramid "
                                    "and its surroundings is considered to be as "
                                    "big as an Egyptian "
                                ),
                            },
                            {"type": "gap", "gap_id": "g1"},
                            {"type": "text", "value": " of the past."},
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": (
                                    "The area outside the pyramid included "
                                    "accommodation that was occupied by "
                                ),
                            },
                            {"type": "gap", "gap_id": "g2"},
                            {
                                "type": "text",
                                "value": ", along with many other buildings and features.",
                            },
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": (
                                    "A wall ran around the outside of the complex "
                                    "and a number of false entrances were built "
                                    "into this. In addition, a long "
                                ),
                            },
                            {"type": "gap", "gap_id": "g3"},
                            {"type": "text", "value": " encircled the wall."},
                        ]
                    },
                    {
                        "segments": [
                            {
                                "type": "text",
                                "value": (
                                    "As a result, any visitors who had not been "
                                    "invited were cleverly prevented from entering "
                                    "the pyramid grounds unless they knew the "
                                ),
                            },
                            {"type": "gap", "gap_id": "g4"},
                            {"type": "text", "value": " of the real entrance."},
                        ]
                    },
                ],
            }
        ],
    }
    notes_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P2_ID,
        order=await next_group_order(db, P2_ID),
        question_type=QuestionType.NOTE_COMPLETION.value,
        instruction=(
            "Complete the notes below.\n"
            "Choose ONE WORD ONLY from the passage for each answer."
        ),
        options_shared=notes_structure,
    )
    db.add(notes_group)
    await db.flush()
    for i, (gap_id, variants) in enumerate(
        [
            ("g1", ["city"]),
            ("g2", ["priests"]),
            ("g3", ["trench"]),
            ("g4", ["location"]),
        ],
        start=1,
    ):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=P2_ID,
                question_group_id=notes_group.id,
                order=i,
                question_type=QuestionType.NOTE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
        )
        print(f"  P2 notes Q{20 + i} {gap_id} -> {variants}")

    multi_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P2_ID,
        order=await next_group_order(db, P2_ID),
        question_type=QuestionType.MULTI_SELECT.value,
        instruction="Choose TWO letters, A-E.",
    )
    db.add(multi_group)
    await db.flush()
    db.add(
        Question(
            id=uuid.uuid4(),
            section_id=P2_ID,
            question_group_id=multi_group.id,
            order=1,
            question_type=QuestionType.MULTI_SELECT,
            content={
                "choose_n": 2,
                "question": (
                    "Which TWO of the following points does the writer "
                    "make about King Djoser?"
                ),
                "options": [
                    "Initially he had to be persuaded to build in stone rather than clay.",
                    "There is disagreement concerning the length of his reign.",
                    "He failed to appreciate Imhotep's part in the design of the Step Pyramid.",
                    "A few of his possessions were still in his tomb when archaeologists found it.",
                    "He criticised the design and construction of other pyramids in Egypt.",
                ],
            },
            answer_key={"correct": ["B", "D"]},
        )
    )
    print("  P2 multi Q25-26 -> ['B', 'D']")


async def _seed_p3(db: AsyncSession, section: Section) -> None:
    section.title = "The future of work"
    section.passage = P3_FUTURE_OF_WORK
    await _wipe(db, P3_ID)

    mcq_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P3_ID,
        order=await next_group_order(db, P3_ID),
        question_type=QuestionType.MCQ.value,
        instruction="Choose the correct letter, A, B, C or D.",
    )
    db.add(mcq_group)
    await db.flush()
    mcqs = [
        (
            "The first paragraph tells us about",
            [
                "the kinds of jobs that will be most affected by the growth of AI.",
                "the extent to which AI will alter the nature of the work that people do.",
                "the proportion of the world's labour force who will have jobs in AI in the future.",
                "the difference between ways that embodied and disembodied AI will impact on workers.",
            ],
            "B",
        ),
        (
            "According to the second paragraph, what is Stella Pachidi's view of the 'knowledge economy'?",
            [
                "It is having an influence on the number of jobs available.",
                "It is changing people's attitudes towards their occupations.",
                "It is the main reason why the production sector is declining.",
                "It is a key factor driving current developments in the workplace.",
            ],
            "D",
        ),
        (
            "What did Pachidi observe at the telecommunications company?",
            [
                "staff disagreeing with the recommendations of AI",
                "staff feeling resentful about the intrusion of AI in their work",
                "staff making sure that AI produces the results that they want",
                "staff allowing AI to carry out tasks they ought to do themselves",
            ],
            "C",
        ),
        (
            "In his recently published research, Ewan McGaughey",
            [
                "challenges the idea that redundancy is a negative thing.",
                "shows the profound effect of mass unemployment on society.",
                "highlights some differences between past and future job losses.",
                "illustrates how changes in the job market can be successfully handled.",
            ],
            "D",
        ),
    ]
    for i, (question, options, correct) in enumerate(mcqs, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=P3_ID,
                question_group_id=mcq_group.id,
                order=i,
                question_type=QuestionType.MCQ,
                content={"question": question, "options": options},
                answer_key={"correct": correct},
            )
        )
        print(f"  P3 MCQ Q{26 + i} -> {correct}")

    word_bank = [
        "A. pressure",
        "B. satisfaction",
        "C. intuition",
        "D. promotion",
        "E. reliance",
        "F. confidence",
        "G. information",
    ]
    summary_structure = {
        "variant": "summary",
        "title": "The 'algorithmication' of jobs",
        "instruction_words": "list of words A-G",
        "max_words_per_gap": 1,
        "options": word_bank,
        "paragraphs": [
            {
                "segments": [
                    {
                        "type": "text",
                        "value": (
                            "Stella Pachidi of Cambridge Judge Business School "
                            "has been focusing on the 'algorithmication' of jobs "
                            "which rely not on production but on "
                        ),
                    },
                    {"type": "gap", "gap_id": "g1"},
                    {
                        "type": "text",
                        "value": (
                            ".\n\nWhile monitoring a telecommunications company, "
                            "Pachidi observed a growing "
                        ),
                    },
                    {"type": "gap", "gap_id": "g2"},
                    {
                        "type": "text",
                        "value": (
                            " on the recommendations made by AI, as workers begin "
                            "to learn through the 'algorithm's eyes'. Meanwhile, "
                            "staff are deterred from experimenting and using "
                            "their own "
                        ),
                    },
                    {"type": "gap", "gap_id": "g3"},
                    {
                        "type": "text",
                        "value": (
                            ", and are therefore prevented from achieving "
                            "innovation.\n\nTo avoid the kind of situations which "
                            "Pachidi observed, researchers are trying to make "
                            "AI's decision-making process easier to comprehend, "
                            "and to increase users' "
                        ),
                    },
                    {"type": "gap", "gap_id": "g4"},
                    {
                        "type": "text",
                        "value": " with regard to the technology.",
                    },
                ]
            }
        ],
    }
    summary_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P3_ID,
        order=await next_group_order(db, P3_ID),
        question_type=QuestionType.SUMMARY_COMPLETION.value,
        instruction=(
            "Complete the summary using the list of words, A-G, below.\n"
            "Write the correct letter, A-G, in boxes 31-34 on your answer sheet."
        ),
        options_shared=summary_structure,
    )
    db.add(summary_group)
    await db.flush()
    for i, (gap_id, variants) in enumerate(
        [
            ("g1", ["G", "information"]),
            ("g2", ["E", "reliance"]),
            ("g3", ["C", "intuition"]),
            ("g4", ["F", "confidence"]),
        ],
        start=1,
    ):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=P3_ID,
                question_group_id=summary_group.id,
                order=i,
                question_type=QuestionType.SUMMARY_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
        )
        print(f"  P3 summary Q{30 + i} {gap_id} -> {variants}")

    people = [
        "A. Stella Pachidi",
        "B. Hamish Low",
        "C. Ewan McGaughey",
    ]
    match_items = [
        ("Greater levels of automation will not result in lower employment.", "B"),
        ("There are several reasons why AI is appealing to businesses.", "A"),
        (
            "AI's potential to transform people's lives has parallels with "
            "major cultural shifts which occurred in previous eras.",
            "C",
        ),
        ("It is important to be aware of the range of problems that AI causes.", "A"),
        (
            "People are going to follow a less conventional career path "
            "than in the past.",
            "B",
        ),
        (
            "Authorities should take measures to ensure that there will be "
            "adequately paid work for everyone.",
            "C",
        ),
    ]
    match_group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=P3_ID,
        order=await next_group_order(db, P3_ID),
        question_type=QuestionType.MATCHING_FEATURES.value,
        instruction=(
            "Look at the following statements (Questions 35-40) and the list "
            "of people below.\n"
            "Match each statement with the correct person, A-C.\n"
            "NB You may use any letter more than once."
        ),
        subtitle="List of People",
        options_shared={"options": people},
    )
    db.add(match_group)
    await db.flush()
    for i, (statement, correct) in enumerate(match_items, start=1):
        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=P3_ID,
                question_group_id=match_group.id,
                order=i,
                question_type=QuestionType.MATCHING_FEATURES,
                content={"question": statement},
                answer_key={"correct": correct},
            )
        )
        print(f"  P3 match Q{34 + i} -> {correct}")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")
        print(f"Test: {test.title}")

        for sid, name, seeder in (
            (P1_ID, "Passage 1", _seed_p1),
            (P2_ID, "Passage 2", _seed_p2),
            (P3_ID, "Passage 3", _seed_p3),
        ):
            section = await db.get(Section, sid)
            if section is None or section.test_id != TEST_ID:
                raise SystemExit(f"{name} section {sid} not found")
            print(f"\n=== {name} ({section.id}) ===")
            await seeder(db, section)

        await db.commit()
        print("\nDone. Reading Passages 1–3 seeded (Q1–40).")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
