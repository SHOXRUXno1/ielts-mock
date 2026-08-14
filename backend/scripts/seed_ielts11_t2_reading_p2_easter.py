"""Seed IELTS 11 Test 2 Reading Passage 2 — Easter Island (Q14-26).

Groups:
  1. matching_headings Q14-20
  2. summary_completion Q21-24 (Jared Diamond's View)
  3. multi_select Q25-26 (choose TWO)
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
from app.services.seed_compound import gap_answer_key, next_group_order

TEST_ID = uuid.UUID("d82ada15-3d93-40f9-912f-5c1af6d2ce8b")  # Ielts 11 #2
PASSAGE2_ID = uuid.UUID("5c71b453-73f8-40a5-a603-3fad4a127900")

TITLE = "What destroyed the civilisation of Easter Island?"

PASSAGE = """\
A

Easter Island, or Rapu Nui as it is known locally, is home to several hundred ancient human statues – the moai. After this remote Pacific island was settled by the Polynesians, it remained isolated for centuries. All the energy and resources that went into the moai – some of which are ten metres tall and weigh over 7,000 kilos – came from the island itself. Yet when Dutch explorers landed in 1722, they met a Stone Age culture. The moai were carved with stone tools, then transported for many kilometres, without the use of animals or wheels, to massive stone platforms. The identity of the moai builders was in doubt until well into the twentieth century. Thor Heyerdahl, the Norwegian ethnographer and adventurer, thought the statues had been created by pre-Inca peoples from Peru. Bestselling Swiss author Erich von Daniken believed they were built by stranded extraterrestrials. Modern science – linguistic, archaeological and genetic evidence – has definitively proved the moai builders were Polynesians, but not how they moved their creations. Local folklore maintains that the statues walked, while researchers have tended to assume the ancestors dragged the statues somehow, using ropes and logs.

B

When the Europeans arrived, Rapa Nui was grassland, with only a few scrawny trees. In the 1970s and 1980s, though, researchers found pollen preserved in lake sediments, which proved the island had been covered in lush palm forests for thousands of years. Only after the Polynesians arrived did those forests disappear. US scientist Jared Diamond believes that the Rapanui people – descendants of Polynesian settlers – wrecked their own environment. They had unfortunately settled on an extremely fragile island – dry, cool, and too remote to be properly fertilised by windblown volcanic ash. When the islanders cleared the forests for firewood and farming, the forests didn't grow back. As trees became scarce and they could no longer construct wooden canoes for fishing, they ate birds. Soil erosion decreased their crop yields. Before Europeans arrived, the Rapanui had descended into civil war and cannibalism, he maintains. The collapse of their isolated civilisation, Diamond writes, is a 'worst-case scenario for what may lie ahead of us in our own future'.

C

The moai, he thinks, accelerated the self-destruction. Diamond interprets them as power displays by rival chieftains who, trapped on a remote little island, lacked other ways of asserting their dominance. They competed by building ever bigger figures. Diamond thinks they laid the moai on wooden sledges, hauled over log rails, but that required both a lot of wood and a lot of people. To feed the people, even more land had to be cleared. When the wood was gone and civil war began, the islanders began toppling the moai. By the nineteenth century none were standing.

D

Archaeologists Terry Hunt of the University of Hawaii and Carl Lipo of California State University agree that Easter Island lost its lush forests and that it was an 'ecological catastrophe' – but they believe the islanders themselves weren't to blame. And the moai certainly weren't. Archaeological excavations indicate that the Rapanui went to heroic efforts to protect the resources of their wind-lashed, infertile fields. They built thousands of circular stone windbreaks and gardened inside them, and used broken volcanic rocks to keep the soil moist. In short, Hunt and Lipo argue, the prehistoric Rapanui were pioneers of sustainable farming.

E

Hunt and Lipo contend that moai-building was an activity that helped keep the peace between islanders. They also believe that moving the moai required few people and no wood, because they were walked upright. On that issue, Hunt and Lipo say, archaeological evidence backs up Rapanui folklore. Recent experiments indicate that as few as 18 people could, with three strong ropes and a bit of practice, easily manoeuvre a 1,000 kg moai replica a few hundred metres. The figures' fat bellies tilted them forward, and a D-shaped base allowed handlers to roll and rock them side to side.

F

Moreover, Hunt and Lipo are convinced that the settlers were not wholly responsible for the loss of the island's trees. Archaeological finds of nuts from the extinct Easter Island palm show tiny grooves, made by the teeth of Polynesian rats. The rats arrived along with the settlers, and in just a few years, Hunt and Lipo calculate, they would have overrun the island. They would have prevented the reseeding of the slow-growing palm trees and thereby doomed Rapa Nui's forest, even without the settlers' campaign of deforestation. No doubt the rats ate birds' eggs too. Hunt and Lipo also see no evidence that Rapanui civilisation collapsed when the palm forest did. They think its population grew rapidly and then remained more or less stable until the arrival of the Europeans, who introduced deadly diseases to which islanders had no immunity. Then in the nineteenth century slave traders decimated the population, which shrivelled to 111 people by 1877.

G

Hunt and Lipo's vision, therefore, is one of an island populated by peaceful and ingenious moai builders and careful stewards of the land, rather than by reckless destroyers ruining their own environment and society. 'Rather than a case of abject failure, Rapu Nui is an unlikely story of success', they claim. Whichever is the case, there are surely some valuable lessons which the world at large can learn from the story of Rapa Nui.\
"""

HEADINGS_INSTRUCTION = (
    "Reading Passage 2 has seven paragraphs, A-G.\n"
    "Choose the correct heading for each paragraph from the list of headings below.\n"
    "Write the correct number, i-ix, in boxes 14-20 on your answer sheet."
)

HEADINGS = [
    "i. Evidence of innovative environment management practices",
    "ii. An undisputed answer to a question about the moai",
    "iii. The future of the moai statues",
    "iv. A theory which supports a local belief",
    "v. The future of Easter Island",
    "vi. Two opposing views about the Rapanui people",
    "vii. Destruction outside the inhabitants' control",
    "viii. How the statues made a situation worse",
    "ix. Diminishing food resources",
]

# Cambridge IELTS 11 Reading Test 2 Passage 2 — bare roman prefixes
HEADING_ANSWERS: list[tuple[str, str]] = [
    ("Paragraph A", "ii"),
    ("Paragraph B", "ix"),
    ("Paragraph C", "viii"),
    ("Paragraph D", "i"),
    ("Paragraph E", "iv"),
    ("Paragraph F", "vii"),
    ("Paragraph G", "vi"),
]

SUMMARY_INSTRUCTION = (
    "Complete the summary below.\n"
    "Choose ONE WORD ONLY from the passage for each answer.\n"
    "Write your answers in boxes 21-24 on your answer sheet."
)

SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Jared Diamond's View",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                {
                    "type": "text",
                    "value": (
                        "Diamond believes that the Polynesian settlers on Rapa Nui "
                        "destroyed its forests, cutting down its trees for fuel and "
                        "clearing land for "
                    ),
                },
                {"type": "gap", "gap_id": "g1"},
                {
                    "type": "text",
                    "value": (
                        ". Twentieth-century discoveries of pollen prove that "
                        "Rapa Nui had once been covered in palm forests, which had "
                        "turned into grassland by the time the Europeans arrived on "
                        "the island. When the islanders were no longer able to build "
                        "the "
                    ),
                },
                {"type": "gap", "gap_id": "g2"},
                {
                    "type": "text",
                    "value": (
                        " they needed to go fishing, they began using the island's "
                    ),
                },
                {"type": "gap", "gap_id": "g3"},
                {
                    "type": "text",
                    "value": (
                        " as a food source, according to Diamond. Diamond also claims "
                        "that the moai were built to show the power of the island's "
                        "chieftains, and that the methods of transporting the statues "
                        "needed not only a great number of people, but also a great "
                        "deal of "
                    ),
                },
                {"type": "gap", "gap_id": "g4"},
                {"type": "text", "value": "."},
            ]
        }
    ],
}

SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["farming"]),
    ("g2", ["canoes"]),
    ("g3", ["birds"]),
    ("g4", ["wood"]),
]

MULTI_INSTRUCTION = "Choose TWO letters, A-E."

MULTI_ITEM = {
    "question": "On what points do Hunt and Lipo disagree with Diamond?",
    "options": [
        "the period when the moai were created",
        "how the moai were transported",
        "the impact of the moai on Rapanui society",
        "how the moai were carved",
        "the origins of the people who made the moai",
    ],
    "correct": ["B", "C"],
}


async def _wipe_section_groups(db: AsyncSession, section_id: uuid.UUID) -> int:
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
    leftovers = (
        await db.execute(select(Question).where(Question.section_id == section_id))
    ).scalars().all()
    for q in leftovers:
        await db.delete(q)
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

        section = await db.get(Section, PASSAGE2_ID)
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Passage 2 {PASSAGE2_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title!r} ({section.id})")

        section.title = TITLE
        section.passage_subtitle = None
        section.passage = PASSAGE

        removed = await _wipe_section_groups(db, PASSAGE2_ID)
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

        # --- matching headings ---
        headings_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE2_ID,
            order=await next_group_order(db, PASSAGE2_ID),
            question_type=QuestionType.MATCHING_HEADINGS.value,
            instruction=HEADINGS_INSTRUCTION,
            subtitle=None,
            options_shared={"options": HEADINGS},
        )
        db.add(headings_group)
        await db.flush()

        for i, (label, correct) in enumerate(HEADING_ANSWERS, start=1):
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE2_ID,
                question_group_id=headings_group.id,
                order=i,
                question_type=QuestionType.MATCHING_HEADINGS,
                content={"question": label},
                answer_key={"correct": correct},
            )
            db.add(q)
            print(f"  Q{13 + i} {label} -> {correct}")

        # --- summary ---
        summary_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE2_ID,
            order=await next_group_order(db, PASSAGE2_ID),
            question_type=QuestionType.SUMMARY_COMPLETION.value,
            instruction=SUMMARY_INSTRUCTION,
            subtitle=None,
            options_shared=SUMMARY_STRUCTURE,
        )
        db.add(summary_group)
        await db.flush()

        for i, (gap_id, variants) in enumerate(SUMMARY_ANSWERS, start=1):
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE2_ID,
                question_group_id=summary_group.id,
                order=i,
                question_type=QuestionType.SUMMARY_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
            db.add(q)
            print(f"  Q{20 + i} {gap_id} -> {variants}")

        # --- multi select (2 slots) ---
        multi_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE2_ID,
            order=await next_group_order(db, PASSAGE2_ID),
            question_type=QuestionType.MULTI_SELECT.value,
            instruction=MULTI_INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(multi_group)
        await db.flush()

        multi_q = Question(
            id=uuid.uuid4(),
            section_id=PASSAGE2_ID,
            question_group_id=multi_group.id,
            order=1,
            question_type=QuestionType.MULTI_SELECT,
            content={
                "choose_n": 2,
                "question": MULTI_ITEM["question"],
                "options": MULTI_ITEM["options"],
            },
            answer_key={"correct": MULTI_ITEM["correct"]},
        )
        db.add(multi_q)
        print(f"  Q25-26 multi_select -> {MULTI_ITEM['correct']}")

        await db.commit()
        print(
            f"\nDone. Passage 2 seeded: headings={headings_group.id}, "
            f"summary={summary_group.id}, multi={multi_group.id}"
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
