"""Seed Practice Set A Test 2 Listening, all 40 questions.

Part 1  hotel booking: 1-6 three-option MCQ, 7-10 short answer
Part 2  news broadcast: 11-15 two suspect descriptions, 16-20 sentence completion
Part 3  admissions interview: 21-26 tutor's notes, 27-30 the student's notes
Part 4  survey design lecture: 31-33 sentences, 34-37 a table, 38-40 notes

The suspect descriptions are printed as two side-by-side blocks, and the numbers
run down the first block before the second, so they are seeded as two note
blocks rather than one table: a table is walked row by row, which would number
them across the page instead of down it.

Idempotent: every part is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t2_listening.py
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
from seed_practice_a_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 2


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


def cell(*segments: dict) -> dict:
    return {"variant": "plain", "segments": list(segments)}


def bullets(*lines: list[dict]) -> dict:
    return {"variant": "bullets", "bullets": [{"segments": line} for line in lines]}


# ── Part 1 ───────────────────────────────────────────────────────────────────

PART1_MCQ: list[dict] = [
    {
        "question": "Mr. Griffin has been to the Sunrise Hotel...",
        "options": ["once previously.", "twice previously.", "three times previously."],
        "correct": "B",
    },
    {
        "question": "Mr. Griffin is from...",
        "options": ["Melbourne.", "Sydney.", "Perth."],
        "correct": "B",
    },
    {
        "question": "Mr. Griffin's passport number is...",
        "options": ["87647489.", "87637289.", "87637489."],
        "correct": "C",
    },
    {
        "question": "Mr. Griffin wants to book...",
        "options": [
            "a single room for 2 nights.",
            "a double room for 2 nights.",
            "a single room for 1 night.",
        ],
        "correct": "A",
    },
    {
        "question": "Mr. Griffin will arrive at the Sunrise Hotel by...",
        "options": ["9.15 pm.", "10.00 pm.", "9.35 pm."],
        "correct": "B",
    },
    {
        "question": (
            "When he gets to the Sunrise Hotel, the food Mr. Griffin will find "
            "in his room will be..."
        ),
        "options": ["a cheese sandwich with fries.", "a cheese sandwich.", "a burger."],
        "correct": "B",
    },
]

# The paper prints a "$" in front of the blank for the two money questions, so
# the answer is the figure alone; the version with the sign is accepted too
# rather than punishing a candidate who repeats it.
PART1_SHORT: list[dict] = [
    {
        "question": (
            "What number room will Mr. Griffin be in at the Sunrise Hotel?"
        ),
        "correct": ["34"],
        "max_words": 3,
    },
    {
        "question": (
            "How much will Mr. Griffin pay per night at the Sunrise Hotel? ($)"
        ),
        "correct": ["100", "$100"],
        "max_words": 3,
    },
    {
        "question": "Who will take Mr. Griffin's food to his room?",
        "correct": ["room service"],
        "max_words": 3,
    },
    {
        "question": "How much will Mr. Griffin pay for his food? ($)",
        "correct": ["9", "$9"],
        "max_words": 3,
    },
]

# ── Part 2 ───────────────────────────────────────────────────────────────────

DESCRIPTIONS_PREAMBLE = (
    "Below are descriptions that Police have released for the two men wanted "
    "in connection with the robbery at the local jewellery store, Nicholls.\n"
    "Complete the descriptions below.\n"
    "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer."
)

MAN1_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Man 1",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("Height  "), gap("d11")]},
                {"segments": [text("Build  Slight")]},
                {"segments": [text("Hair  Dark")]},
                {"segments": [text("Face  Small moustache")]},
                {"segments": [text("Age  Early 20s")]},
                {"segments": [text("Clothing  Blue jeans")]},
                {"segments": [text("White t-shirt")]},
                {"segments": [gap("d12")]},
                {"segments": [text("Motorbike helmet")]},
            ],
        }
    ],
}

MAN1_ANSWERS: list[tuple[str, list[str], int]] = [
    ("d11", ["about 6 foot", "6 foot", "about six foot", "six foot"], 3),
    (
        "d12",
        ["a black leather jacket", "black leather jacket"],
        3,
    ),
]

MAN2_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Man 2",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("Height  5 foot 8")]},
                {"segments": [text("Build  "), gap("d13")]},
                {"segments": [text("Hair  Red")]},
                {"segments": [text("Face  "), gap("d14")]},
                {"segments": [text("Age  "), gap("d15")]},
                {"segments": [text("Clothing  Dark blue sweater")]},
                {"segments": [text("Black jeans")]},
                {"segments": [text("Motorbike helmet")]},
            ],
        }
    ],
}

MAN2_ANSWERS: list[tuple[str, list[str], int]] = [
    ("d13", ["fat"], 3),
    ("d14", ["clean shaven", "clean-shaven"], 3),
    ("d15", ["early 20's", "early 20s", "early twenties"], 3),
]

PART2_SENTENCES: list[dict] = [
    {
        "prompt": (
            "CompTec blamed the job losses on reduced sales and ____."
        ),
        "correct": ["increased competition"],
    },
    {
        "prompt": (
            "The airport route expansion will result in a ____ of new jobs."
        ),
        "correct": ["significant number"],
    },
    {
        "prompt": (
            "The Oakley Woods development project was opposed by local residents "
            "and local ____."
        ),
        "correct": ["environmental groups"],
    },
    {
        "prompt": (
            "George Finchly, the Westley ____, gave the news to the media."
        ),
        "correct": ["mayor"],
    },
    {
        "prompt": (
            "East Moors CC will play their final on Sunday ____ August."
        ),
        "correct": ["30th", "30", "thirtieth"],
    },
]

# ── Part 3 ───────────────────────────────────────────────────────────────────

TUTOR_NOTES: dict = {
    "variant": "notes",
    "title": "Admission tutor's notes",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [text("Student's Name  Robert Johnson")]},
                {"segments": [text("Subject to study  "), gap("n21")]},
                {"segments": [text("Why this subject  Always interested")]},
                {"segments": [text("Father's field")]},
                {
                    "segments": [
                        text("At school, good at mathematics and "),
                        gap("n22"),
                    ]
                },
                {
                    "segments": [
                        text(
                            "Gap year  Worked and travelled in Australia and "
                            "New Zealand"
                        )
                    ]
                },
                {"segments": [text("Jobs during Gap Year  "), gap("n23")]},
                {"segments": [text("Pub work")]},
                {"segments": [gap("n24")]},
                {"segments": [text("Building site")]},
                {
                    "segments": [
                        text("Why Westley University  Department has "),
                        gap("n25"),
                    ]
                },
                {
                    "segments": [
                        text("Graduates from Westley get jobs in industry quickly")
                    ]
                },
                {"segments": [text("Near Snowdonia for "), gap("n26")]},
                {"segments": [text("Likes football - Westley has lots of teams")]},
            ],
        }
    ],
}

TUTOR_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n21", ["civil engineering"], 3),
    ("n22", ["physics"], 3),
    ("n23", ["delivered furniture", "furniture delivery"], 3),
    ("n24", ["hotel work"], 3),
    ("n25", ["a very good reputation", "good reputation", "a good reputation"], 3),
    ("n26", ["hiking", "mountaineering", "hiking/mountaineering"], 3),
]

ROBERT_NOTES: dict = {
    "variant": "notes",
    "title": "Robert Johnson's notes",
    "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        text("Type of Course  "),
                        gap("n27"),
                        text("  (3rd year in industry)"),
                    ]
                },
                {"segments": [text("Assessment  Year 1  5 exams")]},
                {"segments": [text("Year 2  "), gap("n28")]},
                {"segments": [text("Year 3  No assessment")]},
                {"segments": [text("Year 4  Dissertation of "), gap("n29")]},
                {"segments": [text("8 final exams during "), gap("n30")]},
            ],
        }
    ],
}

# The recording says "a minimum of 15 000 words", so the order the candidate
# writes it in is not something the question can fairly test.
ROBERT_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n27", ["sandwich", "sandwich course"], 3),
    ("n28", ["5 exams", "five exams"], 3),
    (
        "n29",
        [
            "15,000 words minimum",
            "15000 words minimum",
            "minimum 15,000 words",
            "minimum 15000 words",
            "15,000 words",
            "15000 words",
        ],
        3,
    ),
    ("n30", ["June"], 3),
]

# ── Part 4 ───────────────────────────────────────────────────────────────────

PART4_SENTENCES: list[dict] = [
    {
        "prompt": (
            "The lecture will be useful for any students who are writing ____."
        ),
        "correct": ["dissertations and theses"],
    },
    {
        "prompt": (
            "Modernised countries are described by the speaker as now being ____."
        ),
        "correct": ["information societies"],
    },
    {
        "prompt": "The size of a sample depends on the ____ required.",
        "correct": ["statistical quality"],
    },
]

SURVEY_TABLE: dict = {
    "variant": "table",
    "title": "Types of Survey",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "headers": ["", "Advantages", "Disadvantages"],
    "rows": [
        [
            cell(text("Mail")),
            bullets([gap("t34")], [text("Good for particular groups")]),
            cell(text("Not good for decent response rate")),
        ],
        [
            cell(text("Telephone")),
            cell(text("Good for when time and survey length are limited")),
            cell(gap("t35")),
        ],
        [
            cell(text("In-Person")),
            cell(text("Good for collecting complex information")),
            cell(text("Can mean lots of "), gap("t36")),
        ],
        [
            cell(text("Street Interview")),
            cell(gap("t37")),
            cell(text("Not scientific sampling")),
        ],
    ],
}

SURVEY_TABLE_ANSWERS: list[tuple[str, list[str], int]] = [
    ("t34", ["low in cost", "cheap"], 3),
    ("t35", ["expensive", "the cost", "cost"], 3),
    (
        "t36",
        ["travelling around", "travelling", "traveling around", "traveling", "travel"],
        3,
    ),
    ("t37", ["easy"], 3),
]

SURVEY_NOTES: dict = {
    "variant": "notes",
    "title": "Survey Content and Ethics",
    "instruction_words": "NO MORE THAN THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "Survey Content",
            "items": [
                {"segments": [text("Questions can ask about: opinions and attitudes")]},
                {"segments": [text("factual characteristics or behaviour")]},
                {"segments": [text("Questions can be open-ended or "), gap("n38")]},
                {"segments": [text("Questions can be from 5 mins long to 1 hour +")]},
                {
                    "segments": [
                        text("Survey can be "),
                        gap("n39"),
                        text(" - interviewees can be questioned on 2 or more occasions"),
                    ]
                },
            ],
        },
        {
            "heading": "Ethics",
            "items": [
                {"segments": [text("Results must not be used commercially")]},
                {"segments": [text("Individuals should not be mentioned")]},
                {
                    "segments": [
                        text("Results should be in "),
                        gap("n40"),
                        text("  ie: statistical tables or charts"),
                    ]
                },
            ],
        },
    ],
}

SURVEY_NOTES_ANSWERS: list[tuple[str, list[str], int]] = [
    ("n38", ["closed"], 3),
    ("n39", ["panel design", "panel"], 3),
    (
        "n40",
        ["completely anonymous summaries", "anonymous summaries"],
        3,
    ),
]


class ListeningWriter:
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

    async def mcq(self, items: list[dict], subtitle: str) -> None:
        for item in items:
            group = await self._group(
                QuestionType.MCQ,
                item["question"],
                subtitle=subtitle,
                options_shared={"options": item["options"]},
            )
            self._add(
                group,
                QuestionType.MCQ,
                {"question": item["question"]},
                {"correct": item["correct"]},
            )

    async def short_answer(self, items: list[dict], instruction: str) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                # The take screen reads a short answer's wording from
                # content.prompt; under any other key the line renders blank.
                {"prompt": item["question"], "max_words": item["max_words"]},
                gap_answer_key(item["correct"], max_words=item["max_words"]),
            )

    async def sentences(
        self, items: list[dict], instruction: str, *, max_words: int
    ) -> None:
        group = await self._group(QuestionType.SENTENCE_COMPLETION, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.SENTENCE_COMPLETION,
                {"prompt": item["prompt"], "max_words": max_words},
                gap_answer_key(item["correct"], max_words=max_words),
            )

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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    counts: list[int] = []

    section = await get_section(db, test.id, SectionType.LISTENING, 1)
    print(f"\nPart 1 ({section.id})  removed {await clear_section(db, section.id)} old row(s)")
    w = ListeningWriter(db, section)
    await w.mcq(PART1_MCQ, "Circle the correct letter A - C.")
    await w.short_answer(
        PART1_SHORT,
        "Answer the questions below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
    )
    counts.append(w.slots)
    print(f"  {w.slots} scoring slots")

    section = await get_section(db, test.id, SectionType.LISTENING, 2)
    print(f"\nPart 2 ({section.id})  removed {await clear_section(db, section.id)} old row(s)")
    w = ListeningWriter(db, section)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        DESCRIPTIONS_PREAMBLE,
        MAN1_STRUCTURE,
        MAN1_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION, "", MAN2_STRUCTURE, MAN2_ANSWERS
    )
    await w.sentences(
        PART2_SENTENCES,
        "Complete the sentences below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        max_words=3,
    )
    counts.append(w.slots)
    print(f"  {w.slots} scoring slots")

    section = await get_section(db, test.id, SectionType.LISTENING, 3)
    print(f"\nPart 3 ({section.id})  removed {await clear_section(db, section.id)} old row(s)")
    w = ListeningWriter(db, section)
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the admission tutor's notes below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        TUTOR_NOTES,
        TUTOR_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete Robert's notes below.\n"
        "Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
        ROBERT_NOTES,
        ROBERT_ANSWERS,
    )
    counts.append(w.slots)
    print(f"  {w.slots} scoring slots")

    section = await get_section(db, test.id, SectionType.LISTENING, 4)
    print(f"\nPart 4 ({section.id})  removed {await clear_section(db, section.id)} old row(s)")
    w = ListeningWriter(db, section)
    await w.sentences(
        PART4_SENTENCES,
        "Complete the sentences below.\n"
        "Write NO MORE THAN 3 WORDS for each answer.",
        max_words=3,
    )
    await w.compound(
        QuestionType.TABLE_COMPLETION,
        "Complete the notes below.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        SURVEY_TABLE,
        SURVEY_TABLE_ANSWERS,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION, "", SURVEY_NOTES, SURVEY_NOTES_ANSWERS
    )
    counts.append(w.slots)
    print(f"  {w.slots} scoring slots")

    await db.commit()
    print(f"\nDone. Listening seeded: {counts} = {sum(counts)} questions.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
