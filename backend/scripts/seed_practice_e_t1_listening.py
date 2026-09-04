"""Seed Practice Set E Test 1 Listening, all four parts (Q1-40).

Source: Peter May Oxford IELTS Practice Tests, Test 1.
Every key is taken from the printed Explanatory Answer Key (pp.118-125).

Part 1  Q1-7   note_completion       Clark's Bicycle Hire (THREE WORDS AND/OR A NUMBER)
        Q8-10  map_labeling          Map of area around Clark's (A-E)
Part 2  Q11-17 table_completion      Clubs and societies table (THREE WORDS)
        Q18-20 mcq                   Clubs funding / choice / action (A-C)
Part 3  Q21-25 flow_chart_completion Lectures and note taking (THREE WORDS)
        Q26-29 short_answer          Lecture attendance tips (THREE WORDS)
        Q30    mcq                   Summing-up points diagram (A-D)
Part 4  Q31-36 summary_completion    Coober Pedy mining town (THREE WORDS)
        Q37-40 matching_features     Coober Pedy locations A/B/C

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t1_listening.py
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
from seed_practice_e_common import (  # noqa: E402
    AUDIO_URL,
    MAP_IMAGE_URL,
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 1
MAP_URL = MAP_IMAGE_URL.format(test=TEST_NUMBER)
Q30_IMAGE_URL = f"/media/images/practice_e_t{TEST_NUMBER}_listening_q30.png"


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 — Clark's Bicycle Hire ────────────────────────────────────────────

# Wording follows the printed notes on p.10 (not paraphrased).
NOTES1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Notes \u2013 Clark\u2019s Bicycle Hire",
    "instruction_words": "THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("Example  Type: touring bike")]},
                {
                    "segments": [
                        text("Rental: \u00a350 a week, or \u00a3"),
                        gap("n1"),
                        text(" a day"),
                    ]
                },
                {
                    "segments": [
                        text("Late return fee: \u00a3"),
                        gap("n2"),
                        text(" per extra hour"),
                    ]
                },
                {
                    "segments": [
                        text("Deposit: \u00a3"),
                        gap("n3"),
                        text(" returnable"),
                    ]
                },
                {
                    "segments": [
                        text("Accessories: \u00a35 for "),
                        gap("n4"),
                        text(": pannier or handlebar type"),
                    ]
                },
                {"segments": [text("free: pump")]},
                {"segments": [text("repair kit")]},
                {
                    "segments": [
                        text("strong "),
                        gap("n5"),
                    ]
                },
                {
                    "segments": [
                        text("Insurance: included, but must pay first \u00a3"),
                        gap("n6"),
                        text(" of claim"),
                    ]
                },
                {
                    "segments": [
                        text("Pay: by "),
                        gap("n7"),
                        text(" only"),
                    ]
                },
            ],
        },
    ],
}

NOTES1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n1", ["14", "\u00a314"], 3),
    ("n2", ["1.25", "\u00a31.25"], 3),
    ("n3", ["60", "\u00a360"], 3),
    ("n4", ["(lightweight) bags", "bags"], 3),
    ("n5", ["lock"], 3),
    ("n6", ["100", "\u00a3100"], 3),
    ("n7", ["credit card"], 3),
]

MAP1_OPTIONS = [
    "A. health centre",
    "B. Maple Leaf pub",
    "C. Clark\u2019s Cycle Hire",
    "D. supermarket",
    "E. garage",
]

MAP1_ITEMS: list[tuple[str, str]] = [
    ("8", "E"),
    ("9", "A"),
    ("10", "C"),
]


# ── Part 2 — Clubs and Societies ─────────────────────────────────────────────

TABLE2_STRUCTURE: dict = {
    "variant": "table",
    "title": "Clubs and Societies",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "headers": ["Type of club or society", "Examples"],
    "rows": [
        [
            {"variant": "plain", "segments": [text("Sports")]},
            {"variant": "plain", "segments": [text("rugby, tennis")]},
        ],
        [
            {"variant": "plain", "segments": [text("Hobby/Interest")]},
            {"variant": "plain", "segments": [
                text("landscape photography, "),
                gap("t11"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [gap("t12")]},
            {"variant": "plain", "segments": [text("dancing, speed-dating")]},
        ],
        [
            {"variant": "plain", "segments": [text("Religious")]},
            {"variant": "plain", "segments": [text("")]},
        ],
        [
            {"variant": "plain", "segments": [text("International/Cultural")]},
            {"variant": "plain", "segments": [
                gap("t13"),
                text(", Afro-Caribbean"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [gap("t14")]},
            {"variant": "plain", "segments": [
                text("human rights, environmental"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [gap("t15")]},
            {"variant": "plain", "segments": [
                text("Republicans, "),
                gap("t16"),
            ]},
        ],
        [
            {"variant": "plain", "segments": [text("Performing Arts")]},
            {"variant": "plain", "segments": [
                gap("t17"),
                text(", amateur theatre"),
            ]},
        ],
    ],
}

TABLE2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t11", ["stamp collecting"], 3),
    ("t12", ["social"], 3),
    ("t13", ["China"], 3),
    ("t14", ["charities"], 3),
    ("t15", ["political"], 3),
    ("t16", ["Liberal Democrats"], 3),
    ("t17", ["light opera"], 3),
]

MCQ2_ITEMS: list[dict] = [
    {
        "question": (
            "In this city, clubs and societies are mainly paid for by"
        ),
        "options": [
            "embassies of other countries.",
            "individual members.",
            "the city council.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "Finding the right club might influence your choice of"
        ),
        "options": [
            "city.",
            "district.",
            "friends.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "What should you do if the right club does not exist?"
        ),
        "options": [
            "set one up yourself",
            "find one on the Internet",
            "join one in another town",
        ],
        "correct": "A",
    },
]


# ── Part 3 — Lectures and Note Taking ────────────────────────────────────────

FLOW3_STRUCTURE: dict = {
    "variant": "flow",
    "title": "LECTURES AND NOTE TAKING",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "steps": [
        {
            "segments": [
                text("Complete all "),
                gap("f21"),
                text(" before lecture"),
            ]
        },
        {
            "segments": [
                text("Think about likely "),
                gap("f22"),
                text(" of lecture"),
            ]
        },
        {
            "segments": [
                text("Take notes during lecture"),
            ]
        },
        {
            "segments": [
                gap("f23"),
                text(" immediately after lecture"),
            ]
        },
        {
            "fork": [
                {
                    "segments": [
                        text("Revise before "),
                        gap("f24"),
                    ]
                },
                {
                    "segments": [
                        text("Revise every "),
                        gap("f25"),
                    ]
                },
            ]
        },
    ],
}

FLOW3_ANSWERS: list[tuple[str, list[str], int]] = [
    ("f21", ["(background) reading", "background reading", "reading"], 3),
    ("f22", ["content"], 3),
    ("f23", ["edit (notes)", "edit notes", "edit them", "edit"], 3),
    ("f24", ["next lecture", "the next lecture"], 3),
    ("f25", ["week"], 3),
]

P3_SHORT: list[tuple[str, list[str]]] = [
    (
        "Where should you sit when you attend a lecture?",
        ["at the front", "the front", "front"],
    ),
    (
        "What should you do if you miss an important point?",
        ["leave a space", "leave space"],
    ),
    (
        "Why must your notes be easy to read?",
        ["it saves time", "(it) saves time", "saves time",
         "(because) it saves time"],
    ),
    (
        "What do we call expressions which indicate what is coming next?",
        ["signpost words"],
    ),
]

MCQ3_ITEM: dict = {
    "question": (
        "Where does Carlos write summing-up points on his notes?"
    ),
    "options": [
        "A",
        "B",
        "C",
        "D",
    ],
    "correct": "B",
    "image_url": Q30_IMAGE_URL,
}


# ── Part 4 — Coober Pedy ─────────────────────────────────────────────────────

SUMMARY4_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Coober Pedy",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "paragraphs": [
        {
            "segments": [
                text(
                    "The Australian mining town of Coober Pedy is about "
                ),
                gap("s31"),
                text(
                    " kilometres south of Alice Springs. Opals were "
                    "first found in the area in "
                ),
                gap("s32"),
                text(
                    " and people began to settle there after the "
                ),
                gap("s33"),
                text(
                    ". In the late 1940s, new opal fields and mass "
                    "immigration from "
                ),
                gap("s34"),
                text(
                    " created a boom, despite the extreme climate "
                    "which forced about "
                ),
                gap("s35"),
                text(
                    " of the population to live underground, where "
                    "they built hotels, churches, and the world\u2019s "
                    "only underground "
                ),
                gap("s36"),
                text("."),
            ]
        },
    ],
}

SUMMARY4_ANSWERS: list[tuple[str, list[str], int]] = [
    ("s31", ["690"], 3),
    ("s32", ["1915"], 3),
    ("s33", ["First World War"], 3),
    ("s34", ["Europe"], 3),
    ("s35", ["70%", "seventy per cent", "70 per cent", "70 percent"], 3),
    ("s36", ["shopping centre", "shopping center"], 3),
]

LOCATION_OPTIONS = [
    "A. in the town of Coober Pedy",
    "B. near Coober Pedy",
    "C. far from Coober Pedy",
]

LOCATION_ITEMS: list[tuple[str, str]] = [
    ("the town of Woomera", "C"),
    ("the opal museum", "A"),
    ("the Dingo Fence", "B"),
    ("the sets of films", "B"),
]


# ── writer helpers ───────────────────────────────────────────────────────────


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

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            content = {
                "question": item["question"],
                "options": item["options"],
            }
            if item.get("image_url"):
                content["image_url"] = item["image_url"]
            self._add(
                group,
                QuestionType.MCQ,
                content,
                {"correct": item["correct"]},
                image_url=item.get("image_url"),
            )

    async def short_answer(
        self,
        instruction: str,
        items: list[tuple[str, list[str]]],
        *,
        max_words: int = 3,
    ) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for prompt, variants in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                {"prompt": prompt, "max_words": max_words},
                gap_answer_key(variants, max_words=max_words),
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
        group = await self._group(
            question_type, instruction, options_shared=shared
        )
        for question, correct in items:
            self._add(
                group,
                question_type,
                {"question": question},
                {"correct": correct},
            )

    async def map_labeling(
        self,
        instruction: str,
        options: list[str],
        items: list[tuple[str, str]],
        *,
        image_url: str,
        subtitle: str | None = None,
    ) -> None:
        group = await self._group(
            QuestionType.MAP_LABELING,
            instruction,
            options_shared={"options": options, "image_url": image_url},
            subtitle=subtitle,
        )
        for location, letter in items:
            self._add(
                group,
                QuestionType.MAP_LABELING,
                {"location": location},
                {"correct": letter},
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    # -- Part 1 --
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(
        f"\nPart 1 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        NOTES1_STRUCTURE,
        NOTES1_ANSWERS,
    )
    await w.map_labeling(
        "Label the map below.\n"
        "Choose your answers from the box and write the correct "
        "letter, A\u2013E, next to questions 8\u201310.",
        MAP1_OPTIONS,
        MAP1_ITEMS,
        image_url=MAP_URL,
        subtitle="Which places are at the following locations?",
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 2 --
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(
        f"\nPart 2 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the table below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        TABLE2_STRUCTURE,
        TABLE2_ANSWERS,
    )
    await w.mcq(
        "Choose the correct letter, A, B or C.",
        MCQ2_ITEMS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 3 --
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(
        f"\nPart 3 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Label the flow chart.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        FLOW3_STRUCTURE,
        FLOW3_ANSWERS,
    )
    await w.short_answer(
        "Write NO MORE THAN THREE WORDS for each answer.",
        P3_SHORT,
        max_words=3,
    )
    await w.mcq(
        "Circle the correct letter A, B, C or D.",
        [MCQ3_ITEM],
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # -- Part 4 --
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(
        f"\nPart 4 ({part.id})  removed "
        f"{await clear_section(db, part.id)} old row(s)"
    )
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        SUMMARY4_STRUCTURE,
        SUMMARY4_ANSWERS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "What are the locations of the following places?\n"
        "Write the correct letter, A, B or C, next to questions "
        "37\u201340.\n"
        f"{SCREEN_LETTER_HINT}",
        LOCATION_OPTIONS,
        LOCATION_ITEMS,
        options_heading="Location",
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
