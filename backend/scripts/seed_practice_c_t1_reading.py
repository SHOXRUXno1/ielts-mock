"""Seed Practice Set C Test 1 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 1. Keys from the printed
Answer Key (pp.173-175). Teaching strategy pages are omitted.

Passage 1  Q1-7   short_answer          Isle of Eigg
           Q8-13  true_false_ng
Passage 2  Q14-18 matching_information  paragraphs A-G
           Q19-23 matching_features     characteristics → periods A-C
           Q24-26 summary_completion    Businesses in the 21st century
Passage 3  Q27-31 mcq
           Q32-36 yes_no_ng
           Q37-40 summary_completion    letters A-I

Passage text lives in scripts/data/practice_c_t1/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t1_reading.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.services.compound import validate_compound_structure  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_c_common import (  # noqa: E402
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 1


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_SHORT_ITEMS: list[dict] = [
    {
        "prompt": "Approximately how many people live on Eigg?",
        "correct": ["100", "a hundred", "one hundred", "hundred"],
        "max_words": 2,
    },
    {
        "prompt": (
            "What proportion of a UK household's electricity consumption "
            "does an Eigg household consume?"
        ),
        "correct": [
            "50 percent",
            "fifty percent",
            "50%",
            "50 per cent",
            "fifty per cent",
        ],
        "max_words": 2,
    },
    {
        "prompt": (
            "Apart from wind and sun, where does most of Eigg's electricity "
            "come from?"
        ),
        "correct": ["water"],
        "max_words": 2,
    },
    {
        "prompt": (
            "What device measures the amount of electricity Eigg's "
            "households are using?"
        ),
        "correct": ["energy monitors", "energy monitor"],
        "max_words": 2,
    },
    {
        "prompt": (
            "When renewable energy supplies are insufficient, what backs "
            "them up?"
        ),
        "correct": ["diesel generators", "diesel generator"],
        "max_words": 2,
    },
    {
        "prompt": (
            "What has EHT provided free of charge in all the houses it owns?"
        ),
        "correct": ["insulation"],
        "max_words": 2,
    },
    {
        "prompt": (
            "Which gardening aid did some Eigg inhabitants claim grants for?"
        ),
        "correct": ["greenhouses", "greenhouse"],
        "max_words": 2,
    },
]

P1_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "Electricity was available for the first time on Eigg when a new "
        "grid was switched on.",
        "False",
    ),
    ("Eigg's carbon emissions are now much lower than before.", "True"),
    ("Wood will soon be the main source of heating on Eigg.", "Not Given"),
    (
        "Eigg is quieter as a result of having a new electricity supply.",
        "True",
    ),
    (
        "Well-off households pay higher prices for the use of extra "
        "electricity.",
        "False",
    ),
    (
        "The new electricity grid has created additional employment "
        "opportunities on Eigg.",
        "True",
    ),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_PARAGRAPH_OPTIONS = ["A", "B", "C", "D", "E", "F", "G"]

P2_INFORMATION_ITEMS: list[tuple[str, str]] = [
    (
        "some specific predictions about businesses and working practices",
        "F",
    ),
    (
        "reference to the way company employees were usually managed",
        "B",
    ),
    ("a warning for business leaders", "G"),
    ("the description of an era notable for the relative absence of change", "A"),
    ("a reason why customer satisfaction was not a high priority", "C"),
]

P2_PERIOD_OPTIONS = [
    "A. The agricultural age",
    "B. The industrial age",
    "C. The neo-industrial age",
]

P2_PERIOD_ITEMS: list[tuple[str, str]] = [
    ("a surplus of goods", "C"),
    ("an emphasis on production quantity", "B"),
    ("the proximity of consumers to workplaces", "A"),
    ("a focus on the quality of goods", "C"),
    ("new products and new ways of working", "B"),
]

P2_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Businesses in the 21st century",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                text(
                    "It is generally agreed that changes are taking place "
                    "more quickly now, and that organisations are being "
                    "transformed. One leading economist suggested that by "
                    "2020, up to a quarter of employees would be "
                ),
                gap("s24"),
                text(
                    ", and half of all employees would be based in the "
                ),
                gap("s25"),
                text(
                    ". Although predictions can be wrong, the speed of "
                    "change is not in doubt, and business leaders need to "
                    "understand the "
                ),
                gap("s26"),
                text(" that will be influential."),
            ]
        }
    ],
}

P2_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s24", ["temporary"]),
    ("s25", ["home"]),
    ("s26", ["factors"]),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "Experiments by Bernard Agranoff described in Reading Passage 3 involve",
        [
            "injecting goldfish at different stages of the experiments.",
            "training goldfish to do different types of task.",
            "using different types of treatment on goldfish.",
            "comparing the performance of different goldfish on certain tasks.",
        ],
        "A",
    ),
    (
        "Most findings from recent studies suggest that",
        [
            "drug treatments do not normally affect short-term memories.",
            "long-term memories build upon short-term memories.",
            "short and long-term memories are formed by separate processes.",
            "ECT treatment affects both short- and long-term memories.",
        ],
        "C",
    ),
    (
        "In the fifth paragraph, what does the writer want to show by the "
        "example of staircases?",
        [
            "Prompt memory formation underlies the performance of everyday "
            "tasks.",
            "Routine tasks can be carried out unconsciously.",
            "Physical accidents can impair the function of memory.",
            "Complex information such as regulations cannot be retained by "
            "the memory.",
        ],
        "A",
    ),
    (
        "Observations about memory by Kami and Sagi",
        [
            "cast doubt on existing hypotheses.",
            "related only to short-term memory.",
            "were based on tasks involving hearing.",
            "confirmed other experimental findings.",
        ],
        "D",
    ),
    (
        "What did the experiment by Shadmehr and Holcomb show?",
        [
            "Different areas of the brain were activated by different tasks.",
            "Activity in the brain gradually moved from one area to other "
            "areas.",
            "Subjects continued to get better at a task after training had "
            "finished.",
            "Treatment given to subjects improved their performance on a "
            "task.",
        ],
        "B",
    ),
]

P3_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "The training which Kami and Sagi's subjects were given was "
        "repeated over several days.",
        "Not Given",
    ),
    (
        "The rats in Weinberger's studies learned to associate a certain "
        "sound with a specific experience.",
        "Yes",
    ),
    (
        "The results of Weinberger's studies indicated that the strength of "
        "the rats' learned associations increases with time.",
        "Yes",
    ),
    (
        "It is easy to see the evolutionary advantage of the way lasting "
        "memories in humans are created.",
        "No",
    ),
    (
        "Long-term memories in humans are more stable than in many other "
        "species.",
        "Not Given",
    ),
]

P3_WORD_BANK = [
    "A. early",
    "B. easy",
    "C. large",
    "D. late",
    "E. lengthy",
    "F. new",
    "G. recently",
    "H. small",
    "I. quick",
]

P3_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Long-term memory",
    "instruction_words": "list of words A-I",
    "max_words_per_gap": 1,
    "options": P3_WORD_BANK,
    "paragraphs": [
        {
            "segments": [
                text(
                    "Various researchers have examined the way lasting "
                    "memories are formed. Laboratory experiments usually "
                    "involve teaching subjects to do something "
                ),
                gap("s37"),
                text(
                    ", and treating them with mild electric shocks or drugs. "
                    "Other studies monitor behaviour after a learning "
                    "experience, or use sophisticated equipment to observe "
                    "brain activity."
                ),
            ]
        },
        {
            "segments": [
                text(
                    "The results are generally consistent: they show that "
                    "lasting memories are the result of a "
                ),
                gap("s38"),
                text(
                    " and complex biological process. The fact that humans "
                    "share this trait with other species, including animals "
                    "with "
                ),
                gap("s39"),
                text(
                    " brains, suggests that it developed "
                ),
                gap("s40"),
                text(" in our evolutionary history."),
            ]
        },
    ],
}

P3_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s37", ["F", "new"]),
    ("s38", ["E", "lengthy"]),
    ("s39", ["H", "small"]),
    ("s40", ["A", "early"]),
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
            self._add(
                group, question_type, {"question": question}, {"correct": correct}
            )

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

    async def mcq(
        self, instruction: str, items: list[tuple[str, list[str], str]]
    ) -> None:
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
        group = await self._group(question_type, instruction)
        for item in items:
            self._add(
                group,
                question_type,
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
        max_words: int = 2,
    ) -> None:
        group = await self._group(
            question_type, instruction, options_shared=structure
        )
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

    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = f"Passage 1 — {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 1 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "Answer the questions below.\n"
        "Choose NO MORE THAN TWO WORDS AND/OR A NUMBER from the passage "
        "for each answer.",
        P1_SHORT_ITEMS,
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information given in "
        "Reading Passage 1?\n"
        "Write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P1_TFNG_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 — {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 2 has SEVEN paragraphs, A–G.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter, A–G.",
        P2_PARAGRAPH_OPTIONS,
        P2_INFORMATION_ITEMS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the following characteristics (Questions 19–23) and the "
        "list of periods below.\n"
        "Match each characteristic with the correct period, A, B or C.\n"
        "Write the correct letter, A, B or C.\n"
        "NB You may use any letter more than once.",
        P2_PERIOD_OPTIONS,
        P2_PERIOD_ITEMS,
        options_heading="List of periods",
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose ONE WORD ONLY from the passage for each answer.",
        P2_SUMMARY_STRUCTURE,
        P2_SUMMARY_ANSWERS,
        max_words=1,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = f"Passage 3 — {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 3 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P3_MCQ_ITEMS,
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer in "
        "Reading Passage 3?\n"
        "Write\n"
        "YES if the statement agrees with the views of the writer\n"
        "NO if the statement contradicts the views of the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P3_YNNG_ITEMS,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary using the list of words, A–I, below.\n"
        f"Write the correct letter, A–I.\n{SCREEN_LETTER_HINT}",
        P3_SUMMARY_STRUCTURE,
        P3_SUMMARY_ANSWERS,
        max_words=1,
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
