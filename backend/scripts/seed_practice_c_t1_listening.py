"""Seed Practice Set C Test 1 Listening, all four parts (Q1-40).

Source: IELTS Practice Tests Plus 3, Test 1. Every key is taken from the
printed Answer Key (p.173). Alternative spellings listed there (slash or
bracket) are accepted; nothing else is invented.

Part 1  Q1-10  form_completion      Health club customer research
Part 2  Q11-16 flow_chart_completion Making a steam pit (letters A-G)
        Q17-18 multi_select         bamboo oven (TWO of A-E)
        Q19-20 multi_select         wild fungi advice (TWO of A-E)
Part 3  Q21-25 mcq                  research project on attitudes
        Q26-30 matching_features    research techniques → difficulties A-G
Part 4  Q31-40 sentence_completion  Saving the juniper plant

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t1_listening.py
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
from app.services.scoring import scoring_slots_for_question  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_c_common import (  # noqa: E402
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 1


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 ───────────────────────────────────────────────────────────────────

FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "Health club customer research",
    "instruction_words": "NO MORE THAN TWO WORDS OR A NUMBER",
    "max_words_per_gap": 2,
    "fields": [
        {"label": "Example Name", "type": "static", "value": "Selina Thompson"},
        {
            "label": "Occupation",
            "type": "gap_line",
            "segments": [gap("g1")],
        },
        {
            "label": "Age group",
            "type": "gap_line",
            "segments": [gap("g2")],
        },
        {
            "label": "Type of membership",
            "type": "gap_line",
            "segments": [gap("g3")],
        },
        {
            "label": "Length of membership",
            "type": "gap_line",
            "segments": [gap("g4"), text(" years")],
        },
        {
            "label": "Why joined",
            "type": "gap_line",
            "segments": [text("Recommended by a "), gap("g5")],
        },
        {
            "label": "Visits to club per month",
            "type": "static",
            "value": "Eight (on an average)",
        },
        {
            "label": "Facility used most",
            "type": "gap_line",
            "segments": [gap("g6")],
        },
        {
            "label": "Facility not used (if any)",
            "type": "gap_line",
            "segments": [
                text("Tennis courts (because reluctant to "),
                gap("g7"),
                text(")"),
            ],
        },
        {
            "label": "Suggestions for improvements",
            "type": "gap_line",
            "segments": [text("Have more "), gap("g8")],
        },
        {
            "label": "",
            "type": "gap_line",
            "segments": [text("Install "), gap("g9"), text(" in the gym.")],
        },
        {
            "label": "",
            "type": "gap_line",
            "segments": [text("Open "), gap("g10"), text(" later at weekends.")],
        },
    ],
}

FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["an accountant", "accountant"], 2),
    ("g2", ["over 50", "over fifty"], 2),
    ("g3", ["family membership", "family", "a family membership"], 2),
    ("g4", ["nine", "9"], 1),
    ("g5", ["doctor"], 1),
    ("g6", ["swimming pool", "pool", "the swimming pool", "the pool"], 2),
    ("g7", ["pay extra", "pay"], 2),
    ("g8", ["social events"], 2),
    ("g9", ["air conditioning"], 2),
    ("g10", ["the restaurant", "restaurant"], 2),
]


# ── Part 2 ───────────────────────────────────────────────────────────────────

STEAM_OPTIONS = [
    "A. air",
    "B. ash",
    "C. earth",
    "D. grass",
    "E. sticks",
    "F. stones",
    "G. water",
]

FLOW2_STRUCTURE: dict = {
    "variant": "flow",
    "title": "Making a steam pit",
    "instruction_words": "letter A–G",
    "max_words_per_gap": 1,
    "options": STEAM_OPTIONS,
    "steps": [
        {"segments": [text("Dig a pit.")]},
        {
            "segments": [
                text("Arrange a row of "),
                gap("f11"),
                text(" over the pit."),
            ]
        },
        {"segments": [text("Place "), gap("f12"), text(" on top.")]},
        {"segments": [text("Light the wood and let it burn out.")]},
        {"segments": [text("Remove "), gap("f13"), text(".")]},
        {"segments": [text("Insert a stick.")]},
        {"segments": [text("Cover the pit with "), gap("f14"), text(".")]},
        {
            "segments": [
                text("Place wrapped food on top, and cover it with "),
                gap("f15"),
                text("."),
            ]
        },
        {
            "segments": [
                text("Remove the stick and put "),
                gap("f16"),
                text(" into the hole."),
            ]
        },
    ],
}

FLOW2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("f11", ["E", "sticks"], 1),
    ("f12", ["F", "stones"], 1),
    ("f13", ["B", "ash"], 1),
    ("f14", ["D", "grass"], 1),
    ("f15", ["C", "earth"], 1),
    ("f16", ["G", "water"], 1),
]

PART2_MULTI_17 = {
    "question": "Which TWO characteristics apply to the bamboo oven?",
    "options": [
        "It's suitable for windy weather.",
        "The fire is lit below the bottom end of the bamboo.",
        "The bamboo is cut into equal lengths.",
        "The oven hangs from a stick.",
        "It cooks food by steaming it.",
    ],
    "correct": ["B", "E"],
}

PART2_MULTI_19 = {
    "question": (
        "Which TWO pieces of advice does the speaker give about eating "
        "wild fungi?"
    ),
    "options": [
        "Cooking doesn't make poisonous fungi edible.",
        "Edible wild fungi can be eaten without cooking.",
        "Wild fungi are highly nutritious.",
        "Some edible fungi look very similar to poisonous varieties.",
        "Fungi which cannot be identified should only be eaten in small "
        "quantities.",
    ],
    "correct": ["A", "D"],
}


# ── Part 3 ───────────────────────────────────────────────────────────────────

PART3_MCQ: list[dict] = [
    {
        "question": "Phoebe's main reason for choosing her topic was that",
        "options": [
            "her classmates had been very interested in it.",
            "it would help prepare her for her first teaching post.",
            "she had been inspired by a particular book.",
        ],
        "correct": "C",
    },
    {
        "question": "Phoebe's main research question related to",
        "options": [
            "the effect of teacher discipline.",
            "the variety of learning activities.",
            "levels of pupil confidence.",
        ],
        "correct": "A",
    },
    {
        "question": "Phoebe was most surprised by her finding that",
        "options": [
            "gender did not influence behaviour significantly.",
            "girls were more negative about school than boys.",
            "boys were more talkative than girls in class.",
        ],
        "correct": "B",
    },
    {
        "question": "Regarding teaching, Phoebe says she has learned that",
        "options": [
            "teachers should be flexible in their lesson planning.",
            "brighter children learn from supporting weaker ones.",
            "children vary from each other in unpredictable ways.",
        ],
        "correct": "A",
    },
    {
        "question": "Tony is particularly impressed by Phoebe's ability to",
        "options": [
            "recognise the limitations of such small-scale research.",
            "reflect on her own research experience in an interesting way.",
            "design her research in such a way as to minimise difficulties.",
        ],
        "correct": "B",
    },
]

DIFFICULTY_OPTIONS = [
    "A. Obtaining permission",
    "B. Deciding on a suitable focus",
    "C. Concentrating while gathering data",
    "D. Working collaboratively",
    "E. Processing data she had gathered",
    "F. Finding a suitable time to conduct the research",
    "G. Getting hold of suitable equipment",
]

DIFFICULTY_ITEMS: list[tuple[str, str]] = [
    ("Observing lessons", "E"),
    ("Interviewing teachers", "G"),
    ("Interviewing pupils", "A"),
    ("Using questionnaires", "D"),
    ("Taking photographs", "B"),
]


# ── Part 4 ───────────────────────────────────────────────────────────────────

PART4_SENTENCES: list[dict] = [
    {
        "prompt": (
            "Juniper was one of the first plants to colonise Britain after "
            "the last ______."
        ),
        "correct": ["ice age"],
    },
    {
        "prompt": (
            "Its smoke is virtually ______, so juniper wood was used as fuel "
            "in illegal activities."
        ),
        "correct": ["invisible"],
    },
    {
        "prompt": (
            "Oils from the plant were used to prevent ______ spreading."
        ),
        "correct": ["infection", "infections"],
    },
    {
        "prompt": (
            "Nowadays, its berries are widely used to ______ food and drink."
        ),
        "correct": ["flavour", "flavor"],
    },
    {
        "prompt": (
            "Juniper plants also support several species of insects and ______."
        ),
        "correct": ["fungus", "fungi"],
    },
    {
        "prompt": (
            "In current juniper populations, ratios of the ______ are poor."
        ),
        "correct": ["sexes"],
    },
    {
        "prompt": (
            "Many of the bushes in each group are of the same age so ______ "
            "of whole populations is rapid."
        ),
        "correct": ["extinction"],
    },
    {
        "prompt": (
            "Plantlife is trialling novel techniques across ______ areas of "
            "England."
        ),
        "correct": ["lowland"],
    },
    {
        "prompt": "One measure is to introduce ______ for seedlings.",
        "correct": ["shelter", "shelters"],
    },
    {
        "prompt": "A further step is to plant ______ from healthy bushes.",
        "correct": ["cuttings"],
    },
]


# ── writing helpers ──────────────────────────────────────────────────────────


class SectionWriter:
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
        options_shared: dict | None = None,
        subtitle: str | None = None,
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
        *,
        image_url: str | None = None,
    ) -> Question:
        question = Question(
            id=uuid.uuid4(),
            section_id=self.section.id,
            question_group_id=group.id,
            order=self.order,
            question_type=question_type,
            content=content,
            answer_key=answer_key,
            image_url=image_url,
        )
        self.db.add(question)
        self.order += 1
        self.slots += scoring_slots_for_question(question)
        return question

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str], int]],
    ) -> None:
        group = await self._group(
            question_type, instruction, options_shared=structure
        )
        for gap_id, variants, max_words in answers:
            self._add(
                group,
                question_type,
                {"gap_id": gap_id},
                gap_answer_key(variants, max_words=max_words),
            )

    async def sentences(
        self, instruction: str, items: list[dict], *, max_words: int
    ) -> None:
        group = await self._group(QuestionType.SENTENCE_COMPLETION, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.SENTENCE_COMPLETION,
                {"prompt": item["prompt"], "max_words": max_words},
                gap_answer_key(item["correct"], max_words=max_words),
            )

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": item["question"], "options": item["options"]},
                {"correct": item["correct"]},
            )

    async def multi_select(self, instruction: str, item: dict) -> None:
        group = await self._group(QuestionType.MULTI_SELECT, instruction)
        self._add(
            group,
            QuestionType.MULTI_SELECT,
            {
                "choose_n": len(item["correct"]),
                "question": item["question"],
                "options": item["options"],
            },
            {"correct": item["correct"]},
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
            self._add(
                group, question_type, {"question": question}, {"correct": correct}
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.FORM_COMPLETION,
        "Complete the form below.\n"
        "Write NO MORE THAN TWO WORDS OR A NUMBER for each answer.",
        FORM_STRUCTURE,
        FORM_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Choose SIX answers from the box and write the correct letter, A–G, "
        f"next to questions 11–16.\n{SCREEN_LETTER_HINT}",
        FLOW2_STRUCTURE,
        FLOW2_ANSWERS,
    )
    await w.multi_select("Choose TWO letters, A–E.", PART2_MULTI_17)
    await w.multi_select("Choose TWO letters, A–E.", PART2_MULTI_19)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.mcq("Choose the correct letter, A, B or C.", PART3_MCQ)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What did Phoebe find difficult about the different research "
        "techniques she used?\n"
        "Choose FIVE answers from the box and write the correct letter A–G "
        f"next to questions 26–30.\n{SCREEN_LETTER_HINT}",
        DIFFICULTY_OPTIONS,
        DIFFICULTY_ITEMS,
        options_heading="Difficulties",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.sentences(
        "Complete the sentences below.\n"
        "Write NO MORE THAN TWO WORDS for each answer.",
        PART4_SENTENCES,
        max_words=2,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    total = sum(totals)
    if total != 40:
        raise SystemExit(
            f"expected 40 scoring slots across the four parts, got {total}"
        )

    await db.commit()
    print(f"\nDone. Listening seeded: {totals} = {total} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
