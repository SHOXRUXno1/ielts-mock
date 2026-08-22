"""Seed Practice Set A Test 2 Reading, all 40 questions.

Passage 1  Diabetes: 1-7 yes/no/not given, 8-11 sentence endings, 12-14 pick three
Passage 2  Contaminating the Arctic: 15-21 true/false/not given, 22-27 summary
Passage 3  The story of coffee: 28-33 headings, 34-36 bean diagram, 37-40 flow chart

The rubric printed above questions 15-21 tells the candidate to reread "the
passage about alternative farming methods in Oregon", which belongs to a
different test in this book. It is corrected here to name this passage, since a
candidate who followed it would look for a text that is not in front of them.

Idempotent: every passage is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t2_reading.py
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
from app.services.scoring import scoring_slots_for_question  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_a_common import (  # noqa: E402
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 2

# Only this test has a labelled diagram in its reading paper, so the name stays
# here rather than in the shared media constants.
BEAN_IMAGE_URL = "/media/images/practice_a_t2_reading_bean.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_YNNG: list[tuple[str, str]] = [
    ("Carbohydrate foods are the body's source of glucose.", "Yes"),
    ("Diabetics cannot produce insulin.", "No"),
    (
        "Some patients develop diabetes due to faults in their own immune systems.",
        "Yes",
    ),
    ("Hyperglycaemia leads to type 1 diabetes being diagnosed quite quickly.", "Yes"),
    (
        "Artificial insulin is the most effective treatment for those patients "
        "requiring insulin.",
        "Not Given",
    ),
    (
        "Frequent check ups at the doctor can drastically reduce the chances of "
        "suffering from problems related to diabetes.",
        "Not Given",
    ),
    ("The majority of diabetics develop heart problems or suffer strokes.", "Yes"),
]

P1_ENDING_OPTIONS = [
    "A. a healthy lifestyle.",
    "B. never suffer any ill effects.",
    "C. women.",
    "D. people also suffering strokes.",
    "E. body cells.",
    "F. the pancreas.",
    "G. do not realise the fact.",
    "H. injections.",
]

P1_ENDING_ITEMS: list[tuple[str, str]] = [
    ("Bizarre as it may seem, many people with diabetes…", "G"),
    ("Insulin is a hormone that allows glucose to be absorbed by…", "E"),
    ("Non severe type 2 diabetes can be solely treated by…", "A"),
    ("Increases in diabetes related heart problems are mainly seen in…", "C"),
]

P1_SYMPTOMS = {
    "question": "According to the text which of the following are symptoms of diabetes?",
    "options": [
        "hot flushes",
        "muscle pains",
        "nausea",
        "losing consciousness",
        "tiredness",
        "bleeding gums",
        "dilation of the eyes",
    ],
    "correct": ["B", "D", "E"],
}

# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_TFNG: list[tuple[str, str]] = [
    ("Industry in the Arctic has increased over the last 20 years.", "Not Given"),
    (
        "Arctic conditions mean that the break down of pollutants is much accelerated.",
        "False",
    ),
    ("Pollution absorbed by arctic algae can eventually affect humans.", "True"),
    (
        "The AEPS has set up scientific stations in the Arctic to monitor pollution.",
        "Not Given",
    ),
    ("Arctic pollution can sometimes resemble US urban pollution.", "True"),
    (
        "Evidence that this smog has only occurred in the 20th Century has been "
        "found in the ice on the polar ice cap.",
        "True",
    ),
    (
        "Research has shown that aerosol arctic pollutants remain in the air "
        "indefinitely.",
        "False",
    ),
]

P2_WORD_BANK = [
    "burning", "terrible", "ice cores", "valid", "certain",
    "originating", "sea", "destroying", "theories", "unknown",
    "agriculture", "decided", "bird life", "dissipating", "accepted",
    "gases", "darkness", "air density",
]

P2_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Arctic Haze",
    "instruction_words": "words from the box",
    "max_words_per_gap": 2,
    "options": P2_WORD_BANK,
    "paragraphs": [
        {
            "segments": [
                text(
                    "Theories that the origins of spring, arctic haze, first seen "
                    "over the ice cap in the 1950s, came from far away were at "
                    "first not "
                ),
                gap("s22"),
                text(
                    ". This haze is a smog formed in the dark, arctic winter by "
                    "pollution delivered to the Arctic by storms "
                ),
                gap("s23"),
                text(" in Europe and Asia. It is known to be a recent phenomenon "),
                text("as proof from "),
                gap("s24"),
                text(
                    " shows it only starting to occur in the 20th Century. The "
                    "smog consists of sulphates and carbon, the latter creating "
                    "the "
                ),
                gap("s25"),
                text(
                    " of the haze. Due to lack of research, the final destination "
                    "of the pollution is unknown but it probably ends up in the "
                ),
                gap("s26"),
                text(
                    " and therefore into the food chain. Scientists are presently "
                    "more worried about the "
                ),
                gap("s27"),
                text(" effect it has on climate change."),
            ]
        }
    ],
}

P2_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s22", ["accepted"]),
    ("s23", ["originating"]),
    ("s24", ["ice cores"]),
    ("s25", ["darkness"]),
    ("s26", ["sea"]),
    ("s27", ["unknown"]),
]

# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_HEADINGS = [
    "i. Growing Coffee",
    "ii. Problems with Manufacture",
    "iii. Processing the Bean",
    "iv. First Contact",
    "v. Arabian Coffee",
    "vi. Coffee Varieties",
    "vii. Modern Coffee",
    "viii. The Spread of Coffee",
    "ix. Consuming Coffee",
    "x. Climates for Coffee",
    "xi. The Coffee Plant",
]

# Paragraph A is given as the example (iv) and is not asked.
P3_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "viii"),
    ("Paragraph C", "ix"),
    ("Paragraph D", "vi"),
    ("Paragraph E", "xi"),
    ("Paragraph F", "i"),
    ("Paragraph G", "iii"),
]

# The printed numbers sit beside the artwork, so the crop keeps them and the
# three answers are typed under the picture in the same order.
BEAN_STRUCTURE: dict = {
    "variant": "notes",
    "title": "The layers of a coffee bean",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "image_url": BEAN_IMAGE_URL,
    "sections": [
        {
            "heading": "Write the word for each numbered label on the diagram above.",
            "items": [
                {"segments": [text("(34)  "), gap("b34")]},
                {"segments": [text("(35)  "), gap("b35")]},
                {"segments": [text("(36)  "), gap("b36")]},
            ],
        }
    ],
}

BEAN_ANSWERS: list[tuple[str, list[str], int]] = [
    ("b34", ["epicarp"], 1),
    ("b35", ["mesocarp"], 1),
    ("b36", ["endocarp"], 1),
]

FLOW_STRUCTURE: dict = {
    "variant": "flow",
    "title": "The Coffee Production Process",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "steps": [
        {
            "segments": [
                text("The coffee cherry is picked by hand and delivered to mills.")
            ]
        },
        {"segments": [text("The coffee cherry is pulped or "), gap("f37"), text(".")]},
        {
            "segments": [
                text("The pulped beans are left "),
                gap("f38"),
                text(" to ferment in pure water."),
            ]
        },
        {
            "segments": [
                text(
                    "The wet beans are sun dried for one or 2 weeks to make "
                    "parchment - they are "
                ),
                gap("f39"),
                text(" often to ensure an even drying procedure."),
            ]
        },
        {
            "segments": [
                text(
                    "The parchment is then bagged and taken to be milled to make "
                    "the green beans."
                )
            ]
        },
        {"segments": [text("The green beans are then roasted to "), gap("f40"), text(".")]},
        {"segments": [text("The roasted beans are cooled.")]},
        {"segments": [text("The finished product is packaged and mailed to the customer.")]},
    ],
}

FLOW_ANSWERS: list[tuple[str, list[str], int]] = [
    ("f37", ["wet milled", "wet-milled"], 3),
    ("f38", ["overnight"], 3),
    ("f39", ["raked"], 3),
    (
        "f40",
        [
            "the customers' specifications",
            "customers' specifications",
            "the customers specifications",
            "customers specifications",
        ],
        3,
    ),
]


class PassageWriter:
    def __init__(self, db: AsyncSession, section: Section) -> None:
        self.db = db
        self.section = section
        self.order = 1
        self.group_order = 1
        self.slots = 0

    async def _group(
        self,
        question_type: QuestionType,
        instruction: str,
        *,
        subtitle: str | None = None,
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
            subtitle=subtitle,
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
        self.slots += scoring_slots_for_question(question)

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

    async def multi_select(self, item: dict, instruction: str, subtitle: str) -> None:
        group = await self._group(
            QuestionType.MULTI_SELECT,
            instruction,
            subtitle=subtitle,
            options_shared={"options": item["options"]},
        )
        for correct in item["correct"]:
            self._add(
                group,
                QuestionType.MULTI_SELECT,
                {"statement": item["question"]},
                {"correct": correct},
            )

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str], int]],
    ) -> None:
        group = await self._group(question_type, instruction, options_shared=structure)
        for gap_id, variants, max_words in answers:
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

    section = await get_section(db, test.id, SectionType.READING, 10)
    _, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = "Diabetes"
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements reflect the views of the writer in "
        "Reading Passage 1?\n"
        "In boxes 1 - 7 on your answer sheet write\n"
        "YES if the statement agrees with the information\n"
        "NO if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this in the passage",
        P1_YNNG,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete the following statements (questions 8 - 11) with the best "
        "ending from the box below.\n"
        "Write the appropriate letters A - H in boxes 8 - 11 on your answer sheet.",
        P1_ENDING_OPTIONS,
        P1_ENDING_ITEMS,
        options_heading="Endings",
    )
    await w.multi_select(
        P1_SYMPTOMS,
        "According to the text which of the following are symptoms of diabetes?",
        "Choose THREE letters (A - G).",
    )
    counts.append(w.slots)
    print(f"  {w.slots} questions")

    section = await get_section(db, test.id, SectionType.READING, 11)
    _, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = "Contaminating the Arctic"
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Read the passage on Contaminating the Arctic again and look at the "
        "statements below.\n"
        "In boxes 15 - 21 on your answer sheet write\n"
        "TRUE if the statement is true\n"
        "FALSE if the statement is false\n"
        "NOT GIVEN if the information is not given in the passage",
        P2_TFNG,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary relating to Arctic Haze below.\n"
        "Choose your answers from the box below the summary and write them in "
        "boxes 22 - 27 on your answer sheet.\n"
        "NB There are more words than spaces, so you will not use them all.\n"
        "Example: the first gap is answered by 'Theories'.",
        P2_SUMMARY_STRUCTURE,
        [(gap_id, variants, 2) for gap_id, variants in P2_SUMMARY_ANSWERS],
    )
    counts.append(w.slots)
    print(f"  {w.slots} questions")

    section = await get_section(db, test.id, SectionType.READING, 12)
    _, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = "The Story of Coffee"
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "The reading passage on The Story of Coffee has 7 paragraphs A - G.\n"
        "From the list of headings below choose the most suitable headings for "
        "paragraphs B - G.\n"
        "Write the appropriate number (i - xi) in boxes 28 - 33 on your answer sheet.\n"
        "NB There are more headings than paragraphs, so you will not use them all.\n"
        "Example: Paragraph A — iv",
        P3_HEADINGS,
        P3_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.compound(
        QuestionType.DIAGRAM_LABELING,
        "Complete the labels on the diagram of a coffee bean below.\n"
        "Choose your answers from the text and write them in boxes 34 - 36 on "
        "your answer sheet.\n"
        "Write NO MORE THAN ONE WORD for each answer.",
        BEAN_STRUCTURE,
        BEAN_ANSWERS,
    )
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Using the information in the passage, complete the flow chart below.\n"
        "Write your answers in boxes 37 - 40 on your answer sheet.\n"
        "Use NO MORE THAN THREE WORDS from the passage for each answer.",
        FLOW_STRUCTURE,
        FLOW_ANSWERS,
    )
    counts.append(w.slots)
    print(f"  {w.slots} questions")

    await db.commit()
    print(f"\nDone. Reading seeded: {counts} = {sum(counts)} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
