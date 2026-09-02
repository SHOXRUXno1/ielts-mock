"""Seed Practice Set D Test 5 Reading, all three passages (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 5.
Keys from the printed Answer Key (pp.230-233). Tip strips omitted.

Passage 1  Q1-3   short_answer          London birds questions (THREE WORDS)
           Q4     short_answer          TWO activities (building work + tree-felling)
           Q5-9   note_completion       Sparrow notes (THREE WORDS)
           Q10-13 matching_features     Bird classification A-F
Passage 2  Q14-20 matching_headings     Psychology paragraphs A-G → headings i-x
           Q21    note_completion       Choose THREE letters C/D/E (single gap)
           Q22-26 yes_no_ng             Personality assessment statements
Passage 3  Q27-29 mcq                   Gordon Moore / Intel A-D
           Q30-34 true_false_ng         Moore's Law statements
           Q35-40 summary_completion    Moore's Law word box

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t5_reading.py
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
from seed_practice_d_common import (  # noqa: E402
    SCREEN_LETTER_HINT,
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 5


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 — The birds of London ─────────────────────────────────────────

P1_SHORT_Q1_3: list[tuple[str, list[str]]] = [
    (
        "What kind of birds are the London pigeons descended from?",
        [
            "rockdoves", "rock doves", "rock-doves",
            "the rockdoves", "the rock doves",
        ],
    ),
    (
        "What were pigeons given to eat before attitudes towards "
        "them changed?",
        ["stale bread"],
    ),
    (
        "What are the routes taken by woodpigeons known as?",
        ["fly-lines", "fly lines", "flylines"],
    ),
]

P1_SHORT_Q4: list[tuple[str, list[str]]] = [
    (
        "What TWO activities have contributed to the drastic "
        "reduction in the number of rooks?",
        [
            "building work and tree-felling",
            "tree-felling and building work",
            "building work and tree felling",
            "tree felling and building work",
            "building work; tree-felling",
            "tree-felling; building work",
            "building work; tree felling",
            "tree felling; building work",
            "building work, tree-felling",
            "tree-felling, building work",
            "building work, tree felling",
            "tree felling, building work",
        ],
    ),
]

P1_NOTES_STRUCTURE: dict = {
    "variant": "notes",
    "title": "Sparrows",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [
                    text("A word meaning "),
                    gap("n5"),
                    text(" is derived from the bird\u2019s name"),
                ]},
                {"segments": [
                    text("Suited to atmosphere of London because of "
                         "tendency to rapidly "),
                    gap("n6"),
                ]},
                {"segments": [
                    text("Always likely to reproduce close to "),
                    gap("n7"),
                ]},
                {"segments": [
                    text("Characteristic noted: "),
                    gap("n8"),
                    text(" because of attitude of people in London"),
                ]},
                {"segments": [
                    text("Make a sound that seems to be a kind of "),
                    gap("n9"),
                ]},
            ],
        },
    ],
}

P1_NOTES_ANSWERS: list[tuple[str, list[str]]] = [
    ("n5", ["friend"]),
    ("n6", ["lose body heat"]),
    ("n7", ["an occupied building", "occupied building"]),
    ("n8", ["sociability"]),
    ("n9", ["interrogation"]),
]

BIRD_OPTIONS = [
    "A. pigeons",
    "B. woodpigeons",
    "C. sparrows",
    "D. chaffinches",
    "E. blackbirds",
    "F. rooks",
]

BIRD_ITEMS: list[tuple[str, str]] = [
    ("They are happier with people when they are in rural areas.", "D"),
    ("They rapidly became comfortable being with people.", "B"),
    ("They used to congregate particularly at old buildings.", "F"),
    ("They used to be attacked by people.", "A"),
]


# ── Passage 2 — Psychology and personality ───────────────────────────────────

HEADING_OPTIONS = [
    "i. The advantage of an intuitive approach to personality "
    "assessment",
    "ii. Overall theories of personality assessment rather than "
    "valuable guidance",
    "iii. The consequences of poor personality assessment",
    "iv. Differing views on the importance of personality "
    "assessment",
    "v. Success and failure in establishing an approach to "
    "personality assessment",
    "vi. Everyone makes personality assessments",
    "vii. Acknowledgement of the need for improvement in "
    "personality assessment",
    "viii. Little progress towards a widely applicable approach "
    "to personality assessment",
    "ix. The need for personality assessments to be well-judged",
    "x. The need for a different kind of research into "
    "personality assessment",
]

HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "vi"),
    ("Paragraph B", "ix"),
    ("Paragraph C", "iii"),
    ("Paragraph D", "vii"),
    ("Paragraph E", "ii"),
    ("Paragraph F", "viii"),
    ("Paragraph G", "v"),
]

Q21_STRUCTURE: dict = {
    "variant": "notes",
    "title": "",
    "instruction_words": "THREE LETTERS",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {"segments": [gap("q21")]},
            ],
        },
    ],
}

Q21_ANSWERS: list[tuple[str, list[str]]] = [
    ("q21", [
        "C, D, E", "C, E, D", "D, C, E", "D, E, C",
        "E, C, D", "E, D, C",
        "CDE", "CED", "DCE", "DEC", "ECD", "EDC",
        "C/D/E", "C/E/D", "D/C/E", "D/E/C", "E/C/D", "E/D/C",
        "C, D and E", "C, E and D",
    ]),
]

P2_YESNO: list[tuple[str, str]] = [
    (
        "People often feel that they have been wrongly assessed.",
        "Yes",
    ),
    (
        "Unscientific systems of personality assessment have been "
        "of some use.",
        "Not Given",
    ),
    (
        "People make false assumptions about the expertise of "
        "psychologists.",
        "Yes",
    ),
    (
        "It is likely that some psychologists are no better than "
        "anyone else at assessing personality.",
        "Yes",
    ),
    (
        "Research since 1940 has been based on acceptance of "
        "previous theories.",
        "No",
    ),
]


# ── Passage 3 — Titan of technology (Gordon Moore / Intel) ───────────────────

P3_MCQ: list[dict] = [
    {
        "question": (
            "What do we learn about Gordon Moore\u2019s personality "
            "in the first two paragraphs?"
        ),
        "options": [
            "A. It has changed noticeably as his career has "
            "developed.",
            "B. It was once considered unsuitable for the particular "
            "type of business he was in.",
            "C. It made him more suited to producing things than to "
            "selling them.",
            "D. It is less complicated than it may at first appear.",
        ],
        "correct": "C",
    },
    {
        "question": (
            "What do we learn about Intel when it was first "
            "established?"
        ),
        "options": [
            "A. It was unlike any other company in its field at "
            "the time.",
            "B. It combined a relaxed atmosphere with serious "
            "intent.",
            "C. It attracted attention because of the unconventional "
            "way in which it was run.",
            "D. It placed more emphasis on ingenuity than on any "
            "other aspect.",
        ],
        "correct": "B",
    },
    {
        "question": (
            "What is stated about the setting up of Intel in the "
            "third paragraph?"
        ),
        "options": [
            "A. It was primarily motivated by the existence of "
            "funds that made it possible.",
            "B. It involved keeping certain sensitive information "
            "secret.",
            "C. It resulted from the founders\u2019 desire to "
            "launch a particular product.",
            "D. It was caused by the founders\u2019 dissatisfaction "
            "with their employer\u2019s priorities.",
        ],
        "correct": "D",
    },
]

P3_TFNG: list[tuple[str, str]] = [
    (
        "Competitors soon came close to catching up with Intel\u2019s "
        "progress.",
        "False",
    ),
    (
        "Intel\u2019s Pentium 4 chip was more successful than Moore "
        "had anticipated.",
        "Not Given",
    ),
    (
        "Moore\u2019s prediction in 1975 was based on too little "
        "evidence.",
        "Not Given",
    ),
    (
        "Flashing trainers are an example of Moore\u2019s theory "
        "about the relationship between cost and applications.",
        "True",
    ),
    (
        "Moore has always been confident that problems concerning "
        "the size of components will be overcome.",
        "False",
    ),
]

P3_WORDBOX = [
    "sign", "use", "opinion", "invention",
    "cost-effectiveness", "failure", "sophistication", "proposition",
    "production", "influence", "understanding", "cost",
    "accuracy", "demand", "theory", "inter-dependence",
    "familiarity", "reception", "appearance", "reference",
]

P3_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Moore\u2019s Law",
    "instruction_words": "ONE WORD",
    "max_words_per_gap": 1,
    "word_box": P3_WORDBOX,
    "paragraphs": [
        {"segments": [
            text(
                "Gordon Moore\u2019s ability to foresee developments "
                "is well-known. In 1965, he referred to the increase "
                "in the "
            ),
            gap("w35"),
            text(
                " of integrated circuits and guessed that the number "
                "of transistors would go on rising for a decade. The "
            ),
            gap("w36"),
            text(
                " of his prediction surprised him. Previously, the "
            ),
            gap("w37"),
            text(
                " and main "
            ),
            gap("w38"),
            text(
                " of integrated circuits had been the major "
            ),
            gap("w39"),
            text(
                " with regard to their development. But Moore "
                "observed that the "
            ),
            gap("w40"),
            text(
                " of integrated circuits was going to improve "
                "dramatically. His resulting forecasts concerning "
                "chips led to the creation of the term "
                "\u2018Moore\u2019s Law\u2019."
            ),
        ]},
    ],
}

P3_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("w35", ["sophistication"]),
    ("w36", ["accuracy"]),
    ("w37", ["cost"]),
    ("w38", ["use"]),
    ("w39", ["influence"]),
    ("w40", ["cost-effectiveness", "cost effectiveness"]),
]


# ── writer helper ─────────────────────────────────────────────────────────────

class PassageWriter:
    def __init__(self, db: AsyncSession, section: Section) -> None:
        self.db = db
        self.section = section
        self.order = 1
        self.group_order = 1
        self.count = 0
        self.slots = 0

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
        self.count += 1
        self.slots += scoring_slots_for_question(question)
        return question

    async def compound(
        self,
        question_type: QuestionType,
        instruction: str,
        structure: dict,
        answers: list[tuple[str, list[str]]],
        *,
        max_words: int = 3,
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

    async def statements(
        self,
        question_type: QuestionType,
        instruction: str,
        items: list[tuple[str, str]],
    ) -> None:
        group = await self._group(question_type, instruction)
        for statement, correct in items:
            self._add(
                group,
                question_type,
                {"statement": statement},
                {"correct": correct},
            )

    async def short_answer(
        self,
        instruction: str,
        items: list[tuple[str, list[str]]],
        *,
        max_words: int = 3,
    ) -> None:
        group = await self._group(QuestionType.SHORT_ANSWER, instruction)
        for question, variants in items:
            self._add(
                group,
                QuestionType.SHORT_ANSWER,
                {"prompt": question, "max_words": max_words},
                gap_answer_key(variants, max_words=max_words),
            )

    async def mcq(
        self,
        instruction: str,
        items: list[dict],
    ) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {
                    "question": item["question"],
                    "options": item["options"],
                },
                {"correct": item["correct"]},
            )


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    counts: list[int] = []
    slots: list[int] = []

    # ── Passage 1 ──
    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = f"Passage 1 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 1 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.short_answer(
        "Answer the questions below using NO MORE THAN THREE WORDS "
        "for each answer.",
        P1_SHORT_Q1_3,
        max_words=3,
    )
    await w.short_answer(
        "Answer the question below.\n"
        "Write NO MORE THAN THREE WORDS for each activity.",
        P1_SHORT_Q4,
        max_words=6,
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Complete the notes below.\n"
        "Choose NO MORE THAN THREE WORDS from the passage for "
        "each answer.",
        P1_NOTES_STRUCTURE,
        P1_NOTES_ANSWERS,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Classify the following as being stated of\n"
        "Write the correct letter A\u2013F.\n"
        f"{SCREEN_LETTER_HINT}",
        BIRD_OPTIONS,
        BIRD_ITEMS,
        options_heading="Bird",
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # ── Passage 2 ──
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "Reading Passage 2 has seven paragraphs A\u2013G.\n"
        "Choose the correct heading for each paragraph from the "
        "list of headings below.\n"
        "Write the correct number i\u2013x.\n"
        f"{SCREEN_LETTER_HINT}",
        HEADING_OPTIONS,
        HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.compound(
        QuestionType.NOTE_COMPLETION,
        "Which THREE of the following are stated about "
        "psychologists involved in personality assessment?\n"
        "Choose THREE letters A\u2013F.\n\n"
        "A  \u2018Depth\u2019 psychologists are better at it than "
        "some other kinds of psychologist.\n"
        "B  Many of them accept that their conclusions are "
        "unreliable.\n"
        "C  They receive criticism from psychologists not involved "
        "in the field.\n"
        "D  They have made people realise how hard the subject is.\n"
        "E  They have told people what not to do, rather than what "
        "they should do.\n"
        "F  They keep changing their minds about what the best "
        "approaches are.",
        Q21_STRUCTURE,
        Q21_ANSWERS,
        max_words=3,
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the "
        "writer in Reading Passage 2?\n"
        "Write\n"
        "YES if the statement agrees with the views of the writer\n"
        "NO if the statement contradicts the views of the writer\n"
        "NOT GIVEN if it is impossible to say what the writer "
        "thinks about this",
        P2_YESNO,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # ── Passage 3 ──
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = f"Passage 3 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = None
    print(
        f"\nPassage 3 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P3_MCQ,
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information "
        "given in Reading Passage 3?\n"
        "Write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P3_TFNG,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below using words from the box.",
        P3_SUMMARY_STRUCTURE,
        P3_SUMMARY_ANSWERS,
        max_words=1,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    total_slots = sum(slots)
    if total_slots != 40:
        raise SystemExit(
            f"expected 40 reading scoring slots, got {total_slots} "
            f"(question rows {counts})"
        )

    await db.commit()
    print(
        f"\nDone. Reading seeded: rows {counts} / slots {slots} "
        f"= {total_slots}."
    )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
