"""Seed IELTS 11 Test 2 Reading Passage 3 — Neuroaesthetics (Q27-40).

Groups:
  1. mcq Q27-30
  2. summary_completion Q31-33 (word bank A-H)
  3. yes_no_ng Q34-39
  4. mcq Q40
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
PASSAGE3_ID = uuid.UUID("a79f8088-2ba6-4de8-b707-65056fe52fb1")

TITLE = "Neuroaesthetics"

PASSAGE = """\
An emerging discipline called neuroaesthetics is seeking to bring scientific objectivity to the study of art, and has already given us a better understanding of many masterpieces. The blurred imagery of Impressionist paintings seems to stimulate the brain's amygdala, for instance. Since the amygdala plays a crucial role in our feelings, that finding might explain why many people find these pieces so moving.

Could the same approach also shed light on abstract twentieth-century pieces, from Mondrian's geometrical blocks of colour, to Pollock's seemingly haphazard arrangements of splashed paint on canvas? Sceptics believe that people claim to like such works simply because they are famous. We certainly do have an inclination to follow the crowd. When asked to make simple perceptual decisions such as matching a shape to its rotated image, for example, people often choose a definitively wrong answer if they see others doing the same. It is easy to imagine that this mentality would have even more impact on a fuzzy concept like art appreciation, where there is no right or wrong answer.

Angelina Hawley-Dolan, of Boston College, Massachusetts, responded to this debate by asking volunteers to view pairs of paintings – either the creations of famous abstract artists or the doodles of infants, chimps and elephants. They then had to judge which they preferred. A third of the paintings were given no captions, while many were labelled incorrectly – volunteers might think they were viewing a chimp's messy brushstrokes when they were actually seeing an acclaimed masterpiece. In each set of trials, volunteers generally preferred the work of renowned artists, even when they believed it was by an animal or a child. It seems that the viewer can sense the artist's vision in paintings, even if they can't explain why.

Robert Pepperell, an artist based at Cardiff University, creates ambiguous works that are neither entirely abstract nor clearly representational. In one study, Pepperell and his collaborators asked volunteers to decide how 'powerful' they considered an artwork to be, and whether they saw anything familiar in the piece. The longer they took to answer these questions, the more highly they rated the piece under scrutiny, and the greater their neural activity. It would seem that the brain sees these images as puzzles, and the harder it is to decipher the meaning, the more rewarding is the moment of recognition.

And what about artists such as Mondrian, whose paintings consist exclusively of horizontal and vertical lines encasing blocks of colour? Mondrian's works are deceptively simple, but eye-tracking studies confirm that they are meticulously composed, and that simply rotating a piece radically changes the way we view it. With the originals, volunteers' eyes tended to stay longer on certain places in the image, but with the altered versions they would flit across a piece more rapidly. As a result, the volunteers considered the altered versions less pleasurable when they later rated the work.

In a similar study, Oshin Vartanian of Toronto University asked volunteers to compare original paintings with ones which he had altered by moving objects around within the frame. He found that almost everyone preferred the original, whether it was a Van Gogh still life or an abstract by Miro. Vartanian also found that changing the composition of the paintings reduced activation in those brain areas linked with meaning and interpretation.

In another experiment, Alex Forsythe of the University of Liverpool analysed the visual intricacy of different pieces of art, and her results suggest that many artists use a key level of detail to please the brain. Too little and the work is boring, but too much results in a kind of 'perceptual overload', according to Forsythe. What's more, appealing pieces both abstract and representational, show signs of 'fractals' – repeated motifs recurring in different scales. Fractals are common throughout nature, for example in the shapes of mountain peaks or the branches of trees. It is possible that our visual system, which evolved in the great outdoors, finds it easier to process such patterns.

It is also intriguing that the brain appears to process movement when we see a handwritten letter, as if we are replaying the writer's moment of creation. This has led some to wonder whether Pollock's works feel so dynamic because the brain reconstructs the energetic actions the artist used as he painted. This may be down to our brain's 'mirror neurons', which are known to mimic others' actions. The hypothesis will need to be thoroughly tested, however. It might even be the case that we could use neuroaesthetic studies to understand the longevity of some pieces of artwork. While the fashions of the time might shape what is currently popular, works that are best adapted to our visual system may be the most likely to linger once the trends of previous generations have been forgotten.

It's still early days for the field of neuroaesthetics – and these studies are probably only a taste of what is to come. It would, however, be foolish to reduce art appreciation to a set of scientific laws. We shouldn't underestimate the importance of the style of a particular artist, their place in history and the artistic environment of their time. Abstract art offers both a challenge and the freedom to play with different interpretations. In some ways, it's not so different to science, where we are constantly looking for systems and decoding meaning so that we can view and appreciate the world in a new way.\
"""

MCQ_INSTRUCTION = (
    "Choose the correct letter, A, B, C or D.\n"
    "Write the correct letter in boxes 27-30 on your answer sheet."
)

MCQ_QUESTIONS: list[dict] = [
    {
        "order": 1,
        "question": (
            "In the second paragraph, the writer refers to a shape-matching "
            "test in order to illustrate"
        ),
        "options": [
            "the subjective nature of art appreciation.",
            "the reliance of modern art on abstract forms.",
            "our tendency to be influenced by the opinions of others.",
            "a common problem encountered when processing visual data.",
        ],
        "correct": "C",
    },
    {
        "order": 2,
        "question": "Angelina Hawley-Dolan's findings indicate that people",
        "options": [
            "mostly favour works of art which they know well.",
            "hold fixed ideas about what makes a good work of art.",
            "are often misled by their initial expectations of a work of art.",
            "have the ability to perceive the intention behind works of art.",
        ],
        "correct": "D",
    },
    {
        "order": 3,
        "question": (
            "Results of studies involving Robert Pepperell's pieces suggest "
            "that people"
        ),
        "options": [
            "can appreciate a painting without fully understanding it.",
            "find it satisfying to work out what a painting represents.",
            "vary widely in the time they spend looking at paintings.",
            "generally prefer representational art to abstract art.",
        ],
        "correct": "B",
    },
    {
        "order": 4,
        "question": (
            "What do the experiments described in the fifth paragraph suggest "
            "about the paintings of Mondrian?"
        ),
        "options": [
            "They are more carefully put together than they appear.",
            "They can be interpreted in a number of different ways.",
            "They challenge our assumptions about shape and colour.",
            "They are easier to appreciate than many other abstract works.",
        ],
        "correct": "A",
    },
]

SUMMARY_INSTRUCTION = (
    "Complete the summary using the list of words, A-H, below.\n"
    "Choose the correct letter, A-H, in boxes 31-33 on your answer sheet."
)

WORD_BANK = [
    "A. interpretation",
    "B. complexity",
    "C. emotions",
    "D. movements",
    "E. skill",
    "F. layout",
    "G. concern",
    "H. images",
]

SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Art and the Brain",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "options": WORD_BANK,
    "paragraphs": [
        {
            "segments": [
                {
                    "type": "text",
                    "value": (
                        "The discipline of neuroaesthetics aims to bring "
                        "scientific objectivity to the study of art. Neurological "
                        "studies of the brain, for example, demonstrate the impact "
                        "which Impressionist paintings have on our "
                    ),
                },
                {"type": "gap", "gap_id": "g1"},
                {
                    "type": "text",
                    "value": (
                        ". Alex Forsythe of the University of Liverpool believes "
                        "many artists give their works the precise degree of "
                    ),
                },
                {"type": "gap", "gap_id": "g2"},
                {
                    "type": "text",
                    "value": (
                        " which most appeals to the viewer's brain. She also "
                        "observes that pleasing works of art often contain certain "
                        "repeated "
                    ),
                },
                {"type": "gap", "gap_id": "g3"},
                {
                    "type": "text",
                    "value": " which occur frequently in the natural world.",
                },
            ]
        }
    ],
}

# Official keys are letters; also accept the bank words.
SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["C", "emotions"]),
    ("g2", ["B", "complexity"]),
    ("g3", ["H", "images"]),
]

YNNG_INSTRUCTION = (
    "Do the following statements agree with the claims of the writer in "
    "Reading Passage 3?\n"
    "In boxes 34-39 on your answer sheet, choose\n"
    "YES if the statement agrees with the claims of the writer\n"
    "NO if the statement contradicts the claims of the writer\n"
    "NOT GIVEN if it is impossible to say what the writer thinks about this"
)

YNNG_QUESTIONS: list[dict] = [
    {
        "order": 1,
        "statement": (
            "Forsythe's findings contradicted previous beliefs on the function "
            "of 'fractals' in art."
        ),
        "correct": "Not Given",
    },
    {
        "order": 2,
        "statement": (
            "Certain ideas regarding the link between 'mirror neurons' and art "
            "appreciation require further verification."
        ),
        "correct": "Yes",
    },
    {
        "order": 3,
        "statement": (
            "People's taste in paintings depends entirely on the current "
            "artistic trends of the period."
        ),
        "correct": "No",
    },
    {
        "order": 4,
        "statement": (
            "Scientists should seek to define the precise rules which govern "
            "people's reactions to works of art."
        ),
        "correct": "No",
    },
    {
        "order": 5,
        "statement": (
            "Art appreciation should always involve taking into consideration "
            "the cultural context in which an artist worked."
        ),
        "correct": "Yes",
    },
    {
        "order": 6,
        "statement": (
            "It is easier to find meaning in the field of science than in that "
            "of art."
        ),
        "correct": "Not Given",
    },
]

MCQ40_INSTRUCTION = (
    "Choose the correct letter, A, B, C or D.\n"
    "Write the correct letter in box 40 on your answer sheet."
)

MCQ40 = {
    "question": "What would be the most appropriate subtitle for the article?",
    "options": [
        "Some scientific insights into how the brain responds to abstract art",
        "Recent studies focusing on the neural activity of abstract artists",
        (
            "A comparison of the neurological bases of abstract and "
            "representational art"
        ),
        "How brain research has altered public opinion about abstract art",
    ],
    "correct": "A",
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

        section = await db.get(Section, PASSAGE3_ID)
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Passage 3 {PASSAGE3_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title!r} ({section.id})")

        section.title = TITLE
        section.passage_subtitle = None
        section.passage = PASSAGE

        removed = await _wipe_section_groups(db, PASSAGE3_ID)
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

        # --- MCQ 27-30 ---
        mcq_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE3_ID,
            order=await next_group_order(db, PASSAGE3_ID),
            question_type=QuestionType.MCQ.value,
            instruction=MCQ_INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(mcq_group)
        await db.flush()

        for item in MCQ_QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE3_ID,
                question_group_id=mcq_group.id,
                order=item["order"],
                question_type=QuestionType.MCQ,
                content={
                    "question": item["question"],
                    "options": item["options"],
                },
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{26 + item['order']} MCQ -> {item['correct']}")

        # --- summary word bank 31-33 ---
        summary_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE3_ID,
            order=await next_group_order(db, PASSAGE3_ID),
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
                section_id=PASSAGE3_ID,
                question_group_id=summary_group.id,
                order=i,
                question_type=QuestionType.SUMMARY_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
            db.add(q)
            print(f"  Q{30 + i} {gap_id} -> {variants}")

        # --- Y/N/NG 34-39 ---
        ynng_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE3_ID,
            order=await next_group_order(db, PASSAGE3_ID),
            question_type=QuestionType.YES_NO_NG.value,
            instruction=YNNG_INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(ynng_group)
        await db.flush()

        for item in YNNG_QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE3_ID,
                question_group_id=ynng_group.id,
                order=item["order"],
                question_type=QuestionType.YES_NO_NG,
                content={"statement": item["statement"]},
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{33 + item['order']} YNNG -> {item['correct']}")

        # --- MCQ 40 ---
        mcq40_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE3_ID,
            order=await next_group_order(db, PASSAGE3_ID),
            question_type=QuestionType.MCQ.value,
            instruction=MCQ40_INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(mcq40_group)
        await db.flush()

        q40 = Question(
            id=uuid.uuid4(),
            section_id=PASSAGE3_ID,
            question_group_id=mcq40_group.id,
            order=1,
            question_type=QuestionType.MCQ,
            content={
                "question": MCQ40["question"],
                "options": MCQ40["options"],
            },
            answer_key={"correct": MCQ40["correct"]},
        )
        db.add(q40)
        print(f"  Q40 MCQ -> {MCQ40['correct']}")

        await db.commit()
        print(
            f"\nDone. Passage 3 seeded: mcq={mcq_group.id}, "
            f"summary={summary_group.id}, ynng={ynng_group.id}, "
            f"mcq40={mcq40_group.id}"
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
