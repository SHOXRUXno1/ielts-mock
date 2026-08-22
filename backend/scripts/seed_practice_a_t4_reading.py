"""Seed Practice Set A Test 4 Reading, all three passages (Q1-40).

Passage 1  Q1-6   matching_headings     paragraphs B-G
           Q7     mcq
           Q8     diagram_labeling      pick the graph that fits the catches
           Q9-10  mcq
           Q11-14 yes_no_ng
Passage 2  Q15-21 matching_features     who said what, by initials
           Q22-27 matching_information  which paragraph covers what
Passage 3  Q28-32 true_false_ng
           Q33-36 sentence_completion
           Q37-40 short_answer

Q8 prints four line graphs and asks which one matches the passage. An mcq here
cannot carry an image, so the four graphs are shown as one figure and the letter
is typed — which is what the paper asks for anyway ("write them in boxes").

Passage text lives in scripts/data/practice_a_t4/ so the prose stays
proofreadable instead of buried in string literals.

Idempotent: each passage section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t4_reading.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.services.compound import validate_compound_structure  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_a_common import (  # noqa: E402
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 4

GRAPH_IMAGE_URL = "/media/images/practice_a_t4_reading_cod_graphs.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_HEADINGS = [
    "i. Factory Closures",
    "ii. The Human Cost",
    "iii. The Tragedy of State Mismanagement",
    "iv. A Warning to the World",
    "v. European Techniques",
    "vi. Destructive Trawling Technology",
    "vii. Lessons to be Learned",
    "viii. The Demise of the Northern Cod",
    "ix. Canadian Fishing Limits",
    "x. The Breaking of Agreements",
    "xi. Foreign Over-fishing",
]

# Paragraph A is given as the example (iv) and is not asked.
P1_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "viii"),
    ("Paragraph C", "vi"),
    ("Paragraph D", "xi"),
    ("Paragraph E", "iii"),
    ("Paragraph F", "ii"),
    ("Paragraph G", "vii"),
]

P1_MCQ_7: list[tuple[str, list[str], str]] = [
    (
        "The Canadian government didn't want to reduce cod catches pre 1992 "
        "because they were worried about…",
        [
            "possible rising unemployment",
            "the ecological effects",
            "the marine ecosystem",
            "drastic measures",
        ],
        "A",
    ),
]

P1_GRAPH_STRUCTURE: dict = {
    "variant": "notes",
    "title": "",
    "instruction_words": "ONE LETTER",
    "max_words_per_gap": 2,
    "image_url": GRAPH_IMAGE_URL,
    "sections": [
        {
            "heading": (
                "Which graph most accurately describes Canadian cod catches "
                "from 1950 to 1992?"
            ),
            "items": [{"segments": [gap("g8")]}],
        }
    ],
}

P1_GRAPH_ANSWERS: list[tuple[str, list[str]]] = [("g8", ["B", "Graph B"])]

P1_MCQ_9_10: list[tuple[str, list[str], str]] = [
    (
        "According to Reading Passage 1, which of the following is now true "
        "about the Newfoundland fisheries?",
        [
            "Catches of 1700 tons a year only are permitted.",
            "Normal fishing could start again in 2007.",
            "No cod fishing is allowed but some other species can be caught.",
            "Fishing with draggers will be allowed again in 2007.",
        ],
        "B",
    ),
    (
        "Who does the writer blame for the collapse of the Newfoundland cod "
        "fishery?",
        [
            "The Canadian fishing industry.",
            "The foreign fishing industry.",
            "The Canadian government.",
            "The US fishing industry.",
        ],
        "C",
    ),
]

P1_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "Disruption of cod breeding was a major factor in the Newfoundland cod "
        "disaster.",
        "Yes",
    ),
    ("Foreign trawlers frequently broke the catch allowances.", "Yes"),
    (
        "There was often conflict between the foreign fishermen and the Canadian "
        "authorities.",
        "Not Given",
    ),
    ("Europe does not face the seriousness of the Canadian disaster.", "No"),
]

# ── Passage 2 ────────────────────────────────────────────────────────────────

# The paper identifies speakers by their initials rather than by letter, so the
# options carry those initials as the prefix the dropdown offers.
P2_FEATURE_OPTIONS = [
    "PK. Peter Killeen",
    "JC. Joe Cranston",
    "LM. Linda McCaig",
    "MB. Michael Blum",
    "BM. Barbara Murray",
]

P2_FEATURE_ITEMS: list[tuple[str, str]] = [
    ("Antibiotics are sometimes used to only prevent infections.", "LM"),
    ("Choosing the correct antibiotic for particular infections is important.", "PK"),
    (
        "Today there are some bacterial infections for which we have no "
        "effective antibiotic.",
        "MB",
    ),
    ("Untested drugs can be used on terminal patients as a last resort.", "MB"),
    ("Resistance develops every time an antibiotic is used.", "JC"),
    ("Merely washing hands can have a positive effect.", "BM"),
    ("Antibiotics are often impotently used against viruses.", "LM"),
]

P2_PARAGRAPH_OPTIONS = [
    "A. Paragraph A",
    "B. Paragraph B",
    "C. Paragraph C",
    "D. Paragraph D",
    "E. Paragraph E",
    "F. Paragraph F",
]

P2_INFORMATION_ITEMS: list[tuple[str, str]] = [
    ("How antibiotic resistance happens.", "D"),
    ("The survival of the fittest bacteria.", "C"),
    (
        "Factors to consider in solving the antibiotic-resistant bacteria problem.",
        "F",
    ),
    ("The impact of the discovery of the first antibiotic.", "A"),
    ("The misuse and overuse of antibiotics.", "E"),
    ("The cessation of research into combating bacterial infections.", "B"),
]

# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_TFNG_ITEMS: list[tuple[str, str]] = [
    ("Canada uses the most hydroelectric power in the world today.", "Not Given"),
    ("An early use of hydroelectric power was in the timber industry.", "True"),
    (
        "The first hydroelectric power stations were more effective than those "
        "using competing energy sources.",
        "True",
    ),
    (
        "People have been drowned by the flooding of their traditional territory "
        "when reservoirs are created.",
        "Not Given",
    ),
    (
        "Nowadays, agriculture below hydroelectric dams is not affected by the "
        "change in water flow.",
        "False",
    ),
]

P3_SENTENCE_ITEMS: list[dict] = [
    {
        "prompt": (
            "The origin of hydroelectric power is the ____ produced when water "
            "obeys the laws of gravity."
        ),
        "correct": ["Kinetic energy", "the kinetic energy"],
        "max_words": 3,
    },
    {
        "prompt": (
            "How far water drops to the turbines in a power station is known "
            "as ____."
        ),
        "correct": ["The head", "head"],
        "max_words": 3,
    },
    {
        "prompt": (
            "A drawback to low head hydroelectric power stations is that they "
            "depend on ____."
        ),
        "correct": ["Seasonal water flow", "the seasonal water flow"],
        "max_words": 3,
    },
    {
        "prompt": "Derelict hydroelectric power stations could be ____ in the future.",
        "correct": ["Renovated"],
        "max_words": 3,
    },
]

P3_SHORT_ANSWER_ITEMS: list[dict] = [
    {
        "prompt": (
            "What proportion of the world's electricity supply is provided by "
            "hydroelectric power?"
        ),
        "correct": ["15%", "about 15%", "15 per cent", "about 15 per cent"],
        "max_words": 3,
    },
    {
        "prompt": (
            "How is the flow rate of a hydroelectric power station quantified?"
        ),
        "correct": ["Volume over time", "as volume over time"],
        "max_words": 3,
    },
    {
        "prompt": (
            "When do high head power plants usually use surplus electricity to "
            "transfer water to a second reservoir?"
        ),
        "correct": ["At night", "night"],
        "max_words": 3,
    },
    {
        "prompt": (
            "What underwater action can lead to the production of pollution "
            "similar to that produced by fossil fuel power stations?"
        ),
        "correct": ["Decomposing flooded vegetation", "decomposing, flooded vegetation"],
        "max_words": 3,
    },
]


# ── writing helpers ──────────────────────────────────────────────────────────


class PassageWriter:
    def __init__(self, db: AsyncSession, section: Section) -> None:
        self.db = db
        self.section = section
        self.order = 1
        self.group_order = 1
        self.count = 0

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
    ) -> None:
        self.db.add(
            Question(
                id=uuid.uuid4(),
                section_id=self.section.id,
                question_group_id=group.id,
                order=self.order,
                question_type=question_type,
                content=content,
                answer_key=answer_key,
            )
        )
        self.order += 1
        self.count += 1

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
        group = await self._group(question_type, instruction, options_shared=shared)
        for question, correct in items:
            self._add(group, question_type, {"question": question}, {"correct": correct})

    async def statements(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[tuple[str, str]],
    ) -> None:
        group = await self._group(question_type, instruction)
        for statement, correct in items:
            self._add(
                group, question_type, {"statement": statement}, {"correct": correct}
            )

    async def mcq(self, instruction: str, items: list[tuple[str, list[str], str]]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for question, options, correct in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": question, "options": options},
                {"correct": correct},
            )

    async def free_text(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[dict],
    ) -> None:
        """Short-answer and sentence-completion rows, which share a shape."""
        group = await self._group(question_type, instruction)
        for item in items:
            self._add(
                group,
                question_type,
                # The take UI reads content.prompt; content.question keeps the
                # admin previews in step with the rest of the book.
                {
                    "prompt": item["prompt"],
                    "question": item["prompt"],
                    "max_words": item["max_words"],
                },
                {
                    "correct": item["correct"],
                    "max_words": item["max_words"],
                    "case_sensitive": False,
                },
            )

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str]]],
        *,
        max_words: int,
    ) -> None:
        group = await self._group(question_type, instruction, options_shared=structure)
        for gap_id, variants in answers:
            self._add(
                group,
                question_type,
                {"gap_id": gap_id},
                gap_answer_key(variants, max_words=max_words),
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    counts: list[int] = []

    # Passage 1
    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = title.title()
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 1 has 7 paragraphs (A – G).\n"
        "From the list of headings below choose the most suitable headings for "
        "paragraphs B – G.\n"
        "Write the appropriate number (i – xi) in boxes 1 – 6 on your answer sheet.\n"
        "NB There are more headings than paragraphs, so you will not use them all.\n"
        "Example: Paragraph A — iv",
        P1_HEADINGS,
        P1_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.mcq(
        "Choose the appropriate letter A – D and write it in box 7 on your "
        "answer sheet.",
        P1_MCQ_7,
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Look at the four graphs below.\n"
        "Write the letter of the graph you choose (A, B, C or D) in box 8 on "
        "your answer sheet.",
        P1_GRAPH_STRUCTURE,
        P1_GRAPH_ANSWERS,
        max_words=2,
    )
    await w.mcq(
        "Choose the appropriate letters A – D and write them in boxes 9 – 10 on "
        "your answer sheet.",
        P1_MCQ_9_10,
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer of the "
        "reading passage on Cod in Trouble?\n"
        "In boxes 11 - 14 write\n"
        "YES if the statement agrees with the writer\n"
        "NO if the statement doesn't agree with the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P1_YNNG_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    # Passage 2
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Match the views (15 – 21) with the people listed below.\n"
        "Write the appropriate initials in boxes 15 - 21 on your answer sheet.",
        P2_FEATURE_OPTIONS,
        P2_FEATURE_ITEMS,
        options_heading="List of People",
    )
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 2 has 6 paragraphs (A - F). Which paragraphs "
        "concentrate on the following information?\n"
        "Write the appropriate letters (A - F) in boxes 22 - 27 on your answer "
        "sheet.",
        P2_PARAGRAPH_OPTIONS,
        P2_INFORMATION_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    # Passage 3
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Read the passage about Hydroelectric Power again and look at the "
        "statements below.\n"
        "In boxes 28 - 32 on your answer sheet write\n"
        "TRUE if the statement is true\n"
        "FALSE if the statement is false\n"
        "NOT GIVEN if the information is not given in the passage",
        P3_TFNG_ITEMS,
    )
    await w.free_text(
        QuestionType.SENTENCE_COMPLETION,
        "Complete each of the following statements (Questions 33 - 36) with "
        "words taken from Reading Passage 3.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        P3_SENTENCE_ITEMS,
    )
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "Using NO MORE THAN THREE WORDS AND/OR A NUMBER from Reading Passage 3, "
        "answer the following questions.",
        P3_SHORT_ANSWER_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    total = sum(counts)
    if total != 40:
        raise SystemExit(f"expected 40 reading questions, got {total}")

    await db.commit()
    print(f"\nDone. Reading seeded: {counts} = {total} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
