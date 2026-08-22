"""Seed Practice Set A Test 5 Listening, all four parts (Q1-40).

Part 1  Q1-5   form_completion      bus pass application
        Q6-10  note_completion      Adelaide day trips
Part 2  Q11-16 sentence_completion  building the Sydney Harbour Bridge
        Q17-20 multi_select         what is no longer true of the bridge
Part 3  Q21-27 sentence_completion  planning a street survey
        Q28-30 multi_select         where the survey will be run
Part 4  Q31-34 matching_features    who did what in the coelacanth story
        Q35-40 mcq

Every answer here was checked against the recording's own transcript, not just
copied off the answer sheet.

Two places where the paper is not usable as printed:

  * The form on page 1 numbers both DATE OF BIRTH and TEL NUMBER "(4)", but
    prints the date of birth in full. Only the phone number is really asked, so
    the date of birth is given as a filled-in row.
  * Question 9 asks when the Huron Gold Mine bus leaves for the return trip,
    which the recording never says outright: it gives the 2.00pm arrival and a
    half-hour journey. The printed Pearl Bay row is the same subtraction
    already worked out, so the key's 1.30pm stands and the arrival time is not
    accepted in a "leaves" row.

Idempotent: each part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t5_listening.py
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
)

TEST_NUMBER = 5

# Both completion groups in Part 1 print the same limit, and Parts 2 and 3 print
# the same one again, so the ceiling is the paper's rather than a per-gap guess.
PART1_WORDS = "NO MORE THAN THREE WORDS AND/OR SOME NUMBERS"
PART1_MAX = 3
SENTENCE_MAX = 3


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Part 1 ───────────────────────────────────────────────────────────────────

FORM_STRUCTURE: dict = {
    "variant": "form",
    "form_title": "BUS PASS APPLICATION FORM",
    "instruction_words": PART1_WORDS,
    "max_words_per_gap": PART1_MAX,
    "fields": [
        {"label": "PASS APPLIED FOR", "type": "static", "value": "1 month (example)"},
        {
            "label": "NAME",
            "type": "gap_line",
            "segments": [text("Nathalie "), gap("g1")],
        },
        {
            "label": "ADDRESS",
            "type": "gap_line",
            "segments": [text("45 "), gap("g2"), text(", Newlands, Adelaide")],
        },
        {"label": "POSTCODE", "type": "gap_line", "segments": [gap("g3")]},
        {"label": "DATE OF BIRTH", "type": "static", "value": "13th May 1982"},
        {"label": "TEL NUMBER", "type": "gap_line", "segments": [gap("g4")]},
        {"label": "UNIVERSITY CARD SHOWN", "type": "static", "value": "Yes"},
        {"label": "ZONES REQUIRED", "type": "gap_line", "segments": [gap("g5")]},
    ],
}

# (gap_id, accepted answers, max words)
FORM_ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["Jameson"], PART1_MAX),
    ("g2", ["Forest Avenue", "Forest Ave", "Forest Ave."], PART1_MAX),
    ("g3", ["8490"], PART1_MAX),
    ("g4", ["6249 7152", "62497152"], PART1_MAX),
    (
        "g5",
        ["1 - 5", "1-5", "1 – 5", "1 to 5", "Zones 1 - 5", "Zones 1-5", "zone 1 - 5"],
        PART1_MAX,
    ),
]

TRIPS_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Adelaide Day Trips on the Bus",
    "instruction_words": PART1_WORDS,
    "max_words_per_gap": PART1_MAX,
    "sections": [
        {
            "heading": "1  The MacDonald Nature Park",
            "items": [
                {"segments": [text("Outward Journey Leaves: 8.00am")]},
                {"segments": [text("Length of Journey: 2 hours")]},
                {"segments": [text("Return Journey Leaves: "), gap("n6")]},
                {
                    "segments": [
                        text("Things to do/see: Walk nature trails + MacDonald River")
                    ]
                },
                {"segments": [text("Bring: A camera")]},
            ],
        },
        {
            "heading": "2  Pearl Bay",
            "items": [
                {"segments": [text("Outward Journey Leaves: 9.00am")]},
                {"segments": [text("Length of Journey: "), gap("n7")]},
                {"segments": [text("Return Journey Leaves: 4.00pm")]},
                {
                    "segments": [
                        text("Things to do/see: Walk along "),
                        gap("n8"),
                        text(" + see view"),
                    ]
                },
                {"segments": [text("Lie on the beach + swim")]},
                {"segments": [text("Bring: Swimming gear + a towel")]},
            ],
        },
        {
            "heading": "3  The Huron Gold Mine",
            "items": [
                {"segments": [text("Outward Journey Leaves: 9.30am")]},
                {"segments": [text("Length of Journey: Half an hour")]},
                {"segments": [text("Return Journey Leaves: "), gap("n9")]},
                {
                    "segments": [
                        text("Things to do/see: Go round the museum and tunnels")
                    ]
                },
                {"segments": [text("Find some gold!!")]},
                {"segments": [text("Bring: "), gap("n10")]},
            ],
        },
    ],
}

TRIPS_ANSWERS: list[tuple[str, list[str], int]] = [
    (
        "n6",
        ["4.30pm", "4.30 pm", "4:30pm", "4:30 pm", "4.30", "16.30", "16:30"],
        PART1_MAX,
    ),
    ("n7", ["1 hour", "one hour", "an hour"], PART1_MAX),
    ("n8", ["the cliffs", "cliffs"], PART1_MAX),
    # Only the 2.00pm arrival is spoken; the departure has to be worked back
    # from the half-hour journey, as the printed Pearl Bay row already does.
    ("n9", ["1.30pm", "1.30 pm", "1:30pm", "1:30 pm", "1.30", "13.30", "13:30"], PART1_MAX),
    ("n10", ["a sweater", "sweater", "A sweater"], PART1_MAX),
]

# ── Part 2 ───────────────────────────────────────────────────────────────────

BRIDGE_SENTENCES: list[dict] = [
    {
        "prompt": "The highest point of the bridge is 134m above ______.",
        "correct": ["mean sea level", "sea level"],
    },
    {
        "prompt": "The two pairs of pylons are made of ______.",
        "correct": ["concrete and granite", "granite and concrete"],
    },
    {
        "prompt": "______% of the steel for making the bridge came from the UK.",
        "correct": ["79", "about 79", "About 79", "79%", "about 79%"],
    },
    {
        "prompt": (
            "800 families from ______ homes were moved without compensation to "
            "accommodate the construction of the approaches to the bridge."
        ),
        "correct": ["438"],
    },
    {
        "prompt": (
            "People ______ was the main cause of death of workers while "
            "constructing the bridge."
        ),
        "correct": ["falling", "falling off", "falling off the bridge"],
    },
    {
        "prompt": (
            "Three ______ were made to mark the opening of the bridge. One is "
            "worth several hundred dollars today."
        ),
        "correct": ["postage stamps", "stamps"],
    },
]

BRIDGE_TODAY_ITEM = {
    "question": (
        "Which FOUR of the following facts are NOT true about the Sydney "
        "Harbour Bridge today?"
    ),
    "options": [
        "There are no more trams crossing the bridge.",
        "There are eight traffic lanes on the bridge.",
        "Trains still cross the bridge.",
        "People are allowed to walk across the bridge.",
        "Buses are allowed to cross the bridge.",
        "The Harbour Tunnel has not helped traffic congestion on the bridge.",
        "More than 182 000 vehicles cross the bridge daily.",
        "Horses can no longer cross the bridge.",
        "Bicycles are not allowed to cross the bridge.",
        "To go back and forward across the bridge costs $6.",
    ],
    "correct": ["D", "F", "G", "J"],
}

# ── Part 3 ───────────────────────────────────────────────────────────────────

SURVEY_SENTENCES: list[dict] = [
    {
        "prompt": "While waiting for Phil, Mel and Laura were ______.",
        "correct": ["chatting", "talking", "just chatting", "just talking"],
    },
    {
        "prompt": "A telephone survey was rejected because it would be ______.",
        "correct": ["too expensive"],
    },
    {
        "prompt": "A mail survey was rejected because it would ______.",
        "correct": ["take too long"],
    },
    {
        "prompt": "The best number of people to survey would be ______.",
        "correct": ["1000", "1,000", "about 1000", "about 1,000"],
    },
    {
        "prompt": (
            "If their survey only included 100 people, it would not be ______."
        ),
        "correct": ["statistically significant"],
    },
    {
        "prompt": (
            "The number of people that Laura, Phil and Mel agree to survey "
            "was ______."
        ),
        "correct": ["500"],
    },
    {
        "prompt": "The number of questions in the survey was agreed to be ______.",
        "correct": ["5", "five"],
    },
]

SURVEY_PLACES_ITEM = {
    "question": (
        "What are the three locations that Laura, Phil and Mel chose for "
        "their survey?"
    ),
    "options": [
        "The town square",
        "The train station",
        "The university cafeteria",
        "Dobbins department store",
        "The corner of the High Street and College Road",
        "The bus station",
        "The corner of the High Street and Wilkins Road",
    ],
    "correct": ["A", "D", "E"],
}

# ── Part 4 ───────────────────────────────────────────────────────────────────

ROLE_OPTIONS = [
    "A. Paid fishermen for unidentified finds.",
    "B. Caught a strange looking fish.",
    "C. Contacted scientists in Indonesia.",
    "D. Photographed a coelacanth seen by accident.",
    "E. First recognised the coelacanth for what it was.",
    "F. Bought a specimen of a coelacanth in a market.",
]

ROLE_ITEMS: list[tuple[str, str]] = [
    ("Dr. J.L.B. Smith", "E"),
    ("Marjorie Courtney-Latimer", "A"),
    ("Dr. Mark Erdmann", "D"),
    ("Captain Goosen", "B"),
]

PART4_MCQ: list[dict] = [
    {
        "question": "The coelacanth was...",
        "options": [
            "well known to Indonesian fishermen.",
            "unknown to Indonesian fishermen.",
            "a first in the market.",
        ],
        "correct": "A",
    },
    {
        "question": (
            "The only difference between the Comoros coelacanth and the "
            "Sulawesi coelacanth is..."
        ),
        "options": ["their intercranial joint.", "their paired fins.", "their colour."],
        "correct": "C",
    },
    {
        "question": "Coelacanths seemed to have their greatest population...",
        "options": [
            "360 million years ago.",
            "240 million years ago.",
            "80 million years ago.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "Modern coelacanths probably left no fossilised remains over the "
            "past 80 million years because..."
        ),
        "options": [
            "of too much clay sediment.",
            "conditions where they lived were not favourable for fossilisation.",
            "volcanoes are needed for fossilisation.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "Scientists had a better understanding of the coelacanth after "
            "1991 because..."
        ),
        "options": [
            "the French government had previously limited study on the "
            "Comoros coelacanth.",
            "the Comoros were far away and difficult to reach.",
            "the Comoros opened an airport.",
        ],
        "correct": "A",
    },
    {
        "question": "On the 1991 expedition, scientists studied the coelacanth...",
        "options": [
            "only from fishermen's specimens.",
            "through the windows of their submarine.",
            "from diving down.",
        ],
        "correct": "B",
    },
]


# ── writing helpers ──────────────────────────────────────────────────────────


class SectionWriter:
    """Accumulates groups and questions for one listening part."""

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
    ) -> Question:
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
            self._add(group, question_type, {"question": question}, {"correct": correct})


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    totals: list[int] = []

    # Part 1
    part = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.compound(
        QuestionType.FORM_COMPLETION,
        "Complete the form below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR SOME NUMBERS for each answer.",
        FORM_STRUCTURE,
        FORM_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR SOME NUMBERS for each answer.",
        TRIPS_STRUCTURE,
        TRIPS_ANSWERS,
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 2
    part = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.sentences(
        "Complete the sentences below.\n"
        "Write NO MORE THAN 3 WORDS AND/OR A NUMBER for each answer.",
        BRIDGE_SENTENCES,
        max_words=SENTENCE_MAX,
    )
    await w.multi_select(
        "Choose FOUR letters, A-J.", BRIDGE_TODAY_ITEM
    )
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 3
    part = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.sentences(
        "Complete the sentences below.\n"
        "Write NO MORE THAN 3 WORDS AND/OR A NUMBER for each answer.",
        SURVEY_SENTENCES,
        max_words=SENTENCE_MAX,
    )
    await w.multi_select("Choose THREE letters, A-G.", SURVEY_PLACES_ITEM)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    # Part 4
    part = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({part.id})  removed {await clear_section(db, part.id)} old row(s)")
    w = SectionWriter(db, part)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Match each individual with their role in the lecture on the coelacanth.\n"
        "Write the appropriate letter (A-F) for each answer.\n"
        "NB There are more roles than individuals so you will not need to use "
        "them all.",
        ROLE_OPTIONS,
        ROLE_ITEMS,
        options_heading="ROLES",
    )
    await w.mcq("Choose the correct letter, A, B or C.", PART4_MCQ)
    totals.append(w.slots)
    print(f"  {w.slots} scoring slots")

    total = sum(totals)
    if total != 40:
        raise SystemExit(f"expected 40 scoring slots across the four parts, got {total}")

    await db.commit()
    print(f"\nDone. Listening seeded: {totals} = {total} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
