"""Seed IELTS 11 Test 2 Reading Passage 1 — Raising the Mary Rose (Q1-13).

Groups:
  1. true_false_ng Q1-4
  2. matching_features Q5-8 (list of dates)
  3. diagram_labeling Q9-13 (upload diagram image in admin)
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test
from app.services.seed_compound import (
    delete_compound_groups,
    gap_answer_key,
    next_group_order,
)

TEST_ID = uuid.UUID("d82ada15-3d93-40f9-912f-5c1af6d2ce8b")  # Ielts 11 #2
PASSAGE1_ID = uuid.UUID("c8409ec2-2f79-4546-ad89-9aa86292a32b")

TITLE = "Raising the Mary Rose"
SUBTITLE = "How a sixteenth-century warship was recovered from the seabed"

PASSAGE = """\
On 19 July 1545, English and French fleets were engaged in a sea battle off the coast of southern England in the area of water called the Solent, between Portsmouth and the Isle of Wight. Among the English vessels was a warship by the name of Mary Rose. Built in Portsmouth some 35 years earlier, she had had a long and successful fighting career, and was a favourite of King Henry VIII. Accounts of what happened to the ship vary: while witnesses agree that she was not hit by the French, some maintain that she was outdated, overladen and sailing too low in the water, others that she was mishandled by undisciplined crew. What is undisputed, however, is that the Mary Rose sank into the Solent that day, taking at least 500 men with her. After the battle, attempts were made to recover the ship, but these failed.

The Mary Rose came to rest on the seabed, lying on her starboard (right) side at an angle of approximately 60 degrees. The hull (the body of the ship) acted as a trap for the sand and mud carried by Solent currents. As a result, the starboard side filled rapidly, leaving the exposed port (left) side to be eroded by marine organisms and mechanical degradation. Because of the way the ship sank, nearly all of the starboard half survived intact. During the seventeenth and eighteenth centuries, the entire site became covered with a layer of hard grey clay, which minimised further erosion.

Then, on 16 June 1836, some fishermen in the Solent found that their equipment was caught on an underwater obstruction, which turned out to be the Mary Rose. Diver John Deane happened to be exploring another sunken ship nearby, and the fishermen approached him, asking him to free their gear. Deane dived down, and found the equipment caught on a timber protruding slightly from the seabed. Exploring further, he uncovered several other timbers and a bronze gun. Deane continued diving on the site intermittently until 1840, recovering several more guns, two bows, various timbers, part of a pump and various other small finds.

The Mary Rose then faded into obscurity for another hundred years. But in 1965, military historian and amateur diver Alexander McKee, in conjunction with the British Sub-Aqua Club, initiated a project called 'Solent Ships'. While on paper this was a plan to examine a number of known wrecks in the Solent, what McKee really hoped for was to find the Mary Rose. Ordinary search techniques proved unsatisfactory, so McKee entered into collaboration with Harold E. Edgerton, professor of electrical engineering at the Massachusetts Institute of Technology. In 1967, Edgerton's side-scan sonar systems revealed a large, unusually shaped object, which McKee believed was the Mary Rose.

Further excavations revealed stray pieces of timber and an iron gun. But the climax to the operation came when, on 5 May 1971, part of the ship's frame was uncovered. McKee and his team now knew for certain that they had found the wreck, but were as yet unaware that it also housed a treasure trove of beautifully preserved artefacts. Interest in the project grew, and in 1979, The Mary Rose Trust was formed, with Prince Charles as its President and Dr Margaret Rule its Archaeological Director. The decision whether or not to salvage the wreck was not an easy one, although an excavation in 1978 had shown that it might be possible to raise the hull. While the original aim was to raise the hull if at all feasible, the operation was not given the go-ahead until January 1982, when all the necessary information was available.

An important factor in trying to salvage the Mary Rose was that the remaining hull was an open shell. This led to an important decision being taken: namely to carry out the lifting operation in three very distinct stages. The hull was attached to a lifting frame via a network of bolts and lifting wires. The problem of the hull being sucked back downwards into the mud was overcome by using 12 hydraulic jacks. These raised it a few centimetres over a period of several days, as the lifting frame rose slowly up its four legs. It was only when the hull was hanging freely from the lifting frame, clear of the seabed and the suction effect of the surrounding mud, that the salvage operation progressed to the second stage. In this stage, the lifting frame was fixed to a hook attached to a crane, and the hull was lifted completely clear of the seabed and transferred underwater into the lifting cradle. This required precise positioning to locate the legs into the 'stabbing guides' of the lifting cradle. The lifting cradle was designed to fit the hull using archaeological survey drawings, and was fitted with air bags to provide additional cushioning for the hull's delicate timber framework. The third and final stage was to lift the entire structure into the air, by which time the hull was also supported from below. Finally, on 11 October 1982, millions of people around the world held their breath as the timber skeleton of the Mary Rose was lifted clear of the water, ready to be returned home to Portsmouth.\
"""

TFNG_INSTRUCTION = (
    "Do the following statements agree with the information given in Reading Passage 1?\n"
    "In boxes 1-4 on your answer sheet, write\n"
    "TRUE if the statement agrees with the information\n"
    "FALSE if the statement contradicts the information\n"
    "NOT GIVEN if there is no information on this"
)

TFNG_QUESTIONS: list[dict] = [
    {
        "order": 1,
        "statement": "There is some doubt about what caused the Mary Rose to sink.",
        "correct": "True",
    },
    {
        "order": 2,
        "statement": (
            "The Mary Rose was the only ship to sink in the battle of 19 July 1545."
        ),
        "correct": "Not Given",
    },
    {
        "order": 3,
        "statement": (
            "Most of one side of the Mary Rose lay undamaged under the sea."
        ),
        "correct": "True",
    },
    {
        "order": 4,
        "statement": (
            "Alexander McKee knew that the wreck would contain many valuable "
            "historical objects."
        ),
        "correct": "False",
    },
]

MATCH_INSTRUCTION = (
    "Look at the following statements (Questions 5-8) and the list of dates below.\n"
    "Match each statement with the correct date, A-G.\n"
    "Write the correct letter, A-G, in boxes 5-8 on your answer sheet."
)

MATCH_OPTIONS = [
    "A. 1836",
    "B. 1840",
    "C. 1965",
    "D. 1967",
    "E. 1971",
    "F. 1979",
    "G. 1982",
]

MATCH_QUESTIONS: list[dict] = [
    {
        "order": 1,
        "question": "A search for the Mary Rose was launched.",
        "correct": "C",
    },
    {
        "order": 2,
        "question": "One person's exploration of the Mary Rose site stopped.",
        "correct": "B",
    },
    {
        "order": 3,
        "question": "It was agreed that the hull of the Mary Rose should be raised.",
        "correct": "G",
    },
    {
        "order": 4,
        "question": "The site of the Mary Rose was found by chance.",
        "correct": "A",
    },
]

DIAGRAM_TITLE = "Raising the hull of the Mary Rose: Stages one and two"

DIAGRAM_INSTRUCTION = (
    "Label the diagram below.\n"
    "Choose NO MORE THAN TWO WORDS from the passage for each answer.\n"
    "Write your answers in boxes 9-13 on your answer sheet."
)

DIAGRAM_STRUCTURE: dict = {
    "variant": "notes",
    "title": DIAGRAM_TITLE,
    "bullets": False,
    "instruction_words": "NO MORE THAN TWO WORDS",
    "max_words_per_gap": 2,
    # image_url left empty — upload Mary Rose diagram scan in admin wizard
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g1"},
                        {
                            "type": "text",
                            "value": " attached to hull by wires",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g2"},
                        {
                            "type": "text",
                            "value": " to prevent hull being sucked into mud",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "legs are placed into "},
                        {"type": "gap", "gap_id": "g3"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "hull is lowered into "},
                        {"type": "gap", "gap_id": "g4"},
                    ]
                },
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g5"},
                        {
                            "type": "text",
                            "value": " used as extra protection for the hull",
                        },
                    ]
                },
            ],
        },
    ],
}

DIAGRAM_ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["lifting frame", "frame"]),
    ("g2", ["hydraulic jacks"]),
    ("g3", ["stabbing guides"]),
    ("g4", ["lifting cradle", "cradle"]),
    ("g5", ["air bags", "airbags"]),
]


async def _wipe_section_groups(db: AsyncSession, section_id: uuid.UUID) -> int:
    """Remove every question group (and questions) on the passage."""
    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == section_id)
        )
    ).scalars().all()
    deleted = 0
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
        deleted += 1
    if deleted:
        await db.flush()
    return deleted


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(
            Section,
            PASSAGE1_ID,
            options=[
                selectinload(Section.question_groups).selectinload(
                    QuestionGroup.questions
                )
            ],
        )
        if section is None:
            raise SystemExit(f"Section {PASSAGE1_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title!r} ({section.id})")

        section.title = TITLE
        section.passage_subtitle = SUBTITLE
        section.passage = PASSAGE

        removed = await _wipe_section_groups(db, PASSAGE1_ID)
        if removed:
            print(f"Removed {removed} previous group row(s)")

        # Also clear any orphan compound leftovers in display range
        await delete_compound_groups(
            db,
            section_id=PASSAGE1_ID,
            question_types=("diagram_labeling", "note_completion"),
            order_range=(1, 13),
        )

        # --- Group 1: TFNG ---
        tfng_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE1_ID,
            order=await next_group_order(db, PASSAGE1_ID),
            question_type=QuestionType.TRUE_FALSE_NG.value,
            instruction=TFNG_INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(tfng_group)
        await db.flush()

        for item in TFNG_QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE1_ID,
                question_group_id=tfng_group.id,
                order=item["order"],
                question_type=QuestionType.TRUE_FALSE_NG,
                content={"statement": item["statement"]},
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{item['order']} TFNG -> {item['correct']}")

        # --- Group 2: matching dates ---
        match_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE1_ID,
            order=await next_group_order(db, PASSAGE1_ID),
            question_type=QuestionType.MATCHING_FEATURES.value,
            instruction=MATCH_INSTRUCTION,
            subtitle="List of Dates",
            options_shared={"options": MATCH_OPTIONS},
        )
        db.add(match_group)
        await db.flush()

        for item in MATCH_QUESTIONS:
            display = 4 + item["order"]
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE1_ID,
                question_group_id=match_group.id,
                order=item["order"],
                question_type=QuestionType.MATCHING_FEATURES,
                content={"question": item["question"]},
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{display} match -> {item['correct']}")

        # --- Group 3: diagram ---
        diagram_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE1_ID,
            order=await next_group_order(db, PASSAGE1_ID),
            question_type=QuestionType.DIAGRAM_LABELING.value,
            instruction=DIAGRAM_INSTRUCTION,
            subtitle=None,
            options_shared=DIAGRAM_STRUCTURE,
        )
        db.add(diagram_group)
        await db.flush()

        for i, (gap_id, variants) in enumerate(DIAGRAM_ANSWERS):
            order = i + 1
            display = 8 + order
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE1_ID,
                question_group_id=diagram_group.id,
                order=order,
                question_type=QuestionType.DIAGRAM_LABELING,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=2),
            )
            db.add(q)
            print(f"  Q{display} {gap_id} -> {variants}")

        await db.commit()
        print(
            f"\nDone. Passage 1 seeded: TFNG={tfng_group.id}, "
            f"match={match_group.id}, diagram={diagram_group.id}"
        )
        print("Upload the Mary Rose diagram image in the admin wizard.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
