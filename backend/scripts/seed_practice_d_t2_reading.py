"""Seed Practice Set D Test 2 Reading, all three passages (Q1-40).

Source: Thomson Exam Essentials IELTS Practice Tests, Test 2.
Keys from the printed Answer Key (pp.214-220).

Passage 1  Q1     mcq                 Emigration to the US (A-D)
           Q2-9   summary_completion  sentence completion from passage (THREE WORDS)
           Q10-13 matching_features   sentence endings (A-H)
Passage 2  Q14-20 matching_features   spacecraft (A-E)
           Q21-26 summary_completion  Beagle 2 assembly diagram labels (THREE WORDS)
Passage 3  Q27-34 summary_completion  TV news summary (word box)
           Q35-40 true_false_ng

Passage text lives in scripts/data/practice_d_t2/.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t2_reading.py
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

TEST_NUMBER = 2


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_MCQ: list[dict] = [
    {
        "question": (
            "Which of the following does the writer state in the "
            "first paragraph?"
        ),
        "options": [
            "The extent of emigration in the nineteenth century is "
            "unlikely to be repeated.",
            "Doubts may be cast on how much emigration there really "
            "was in the nineteenth century.",
            "It is possible that emigration from Europe may be "
            "exceeded by emigration from outside Europe.",
            "Emigration can prove to be a better experience for "
            "some nationalities than for others.",
        ],
        "correct": "C",
    },
]

P1_SENTENCE_STRUCTURE: dict = {
    "variant": "summary",
    "title": "General Causes of Emigration to the US",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "paragraphs": [
        {"segments": [
            text("Population increases made it impossible for some to "
                 "live from agriculture. In Europe, countries kept "),
            gap("s2"),
            text(" that were both big, and this resulted in increases "
                 "in "),
            gap("s3"),
            text(" and in "),
            gap("s4"),
            text(", which a lot of people wanted to escape."),
        ]},
        {"segments": [
            text("It became impossible for "),
            gap("s5"),
            text(" in Europe to earn a living because of developments "
                 "in other countries and the introduction of "),
            gap("s6"),
            text("."),
        ]},
        {"segments": [
            text("People knew more about the world beyond their own "
                 "countries because there was greater "),
            gap("s7"),
            text("."),
        ]},
        {"segments": [
            gap("s8"),
            text(" had been formed because of major historical events."),
        ]},
        {"segments": [
            text("The creation of "),
            gap("s9"),
            text(" caused changes in demand."),
        ]},
    ],
}

P1_SENTENCE_ANSWERS: list[tuple[str, list[str]]] = [
    ("s2", ["armies and navies"]),
    ("s3", ["taxes"]),
    ("s4", ["mass conscription"]),
    ("s5", ["peasants"]),
    ("s6", ["free trade"]),
    ("s7", ["literacy"]),
    ("s8", ["New states"]),
    ("s9", ["new industries"]),
]

P1_ENDING_OPTIONS = [
    "A. made people reluctant to move elsewhere.",
    "B. resulted in a need for more agricultural workers.",
    "C. provided evidence of the advantages of emigration.",
    "D. created a false impression of the advantages of moving elsewhere.",
    "E. did little to improve the position of much of the population.",
    "F. took a long time to have any real effect.",
    "G. failed to satisfy employment requirements.",
    "H. created a surplus of people who had emigrated.",
]

P1_ENDING_ITEMS: list[tuple[str, str]] = [
    ("The end of the potato famine in Ireland", "E"),
    ("People who had emigrated from Ireland", "C"),
    ("Movement off the land in the US", "G"),
    ("The arrival of railroad companies in the West of the US", "B"),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_SPACECRAFT_OPTIONS = [
    "A. Apollo craft",
    "B. Surveyor probe",
    "C. Galileo probe",
    "D. Beagle 2",
    "E. Mars Express",
]

P2_SPACECRAFT_ITEMS: list[tuple[str, str]] = [
    ("provided transport from Earth for bacteria", "B"),
    ("led to realisation of how tenacious bacteria are", "A"),
    (
        "was created so that there could be no bacteria on the "
        "outer structure",
        "D",
    ),
    (
        "was capable of changing direction in the event of a problem",
        "E",
    ),
    (
        "brought material which was kept in more than one kind "
        "of container",
        "A",
    ),
    (
        "required action because of the possibility of the "
        "introduction of harmful bacteria",
        "C",
    ),
    (
        "resulted in disagreement as to the relative value of "
        "what was found",
        "A",
    ),
]

P2_BEAGLE_STRUCTURE: dict = {
    "variant": "summary",
    "title": "The Assembly of Beagle 2",
    "instruction_words": "THREE WORDS",
    "max_words_per_gap": 3,
    "paragraphs": [
        {"segments": [
            text("Spacecraft built in newly created "),
            gap("d21"),
        ]},
        {"segments": [
            text("Information given through a "),
            gap("d22"),
        ]},
        {"segments": [
            text("Bacteria on "),
            gap("d23"),
            text(" destroyed at low temperatures"),
        ]},
        {"segments": [
            text("Parachutes and gas bags treated with "),
            gap("d24"),
        ]},
        {"segments": [
            text("People not allowed to have "),
            gap("d25"),
        ]},
        {"segments": [
            text("Large number of "),
            gap("d26"),
            text(" circulated and filtered the air"),
        ]},
    ],
}

P2_BEAGLE_ANSWERS: list[tuple[str, list[str]]] = [
    ("d21", ["clean room", "a clean room"]),
    ("d22", ["glass wall", "a glass wall"]),
    ("d23", ["electronic equipment"]),
    ("d24", ["gamma radiation"]),
    ("d25", ["beards", "facial hair", "beards/facial hair"]),
    ("d26", ["fans"]),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

WORD_BOX = (
    "upsetting / creative / secondary / controversial / fast-moving / "
    "contrary / opinionated / routine / step-by-step / informal / "
    "crucial / story-telling / repetitive / informative / traditional / "
    "overwhelming / mysterious / related / confusing / diverse"
)

P3_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "The structure of television news",
    "instruction_words": "ONE WORD",
    "max_words_per_gap": 1,
    "paragraphs": [
        {"segments": [
            text("Justin Lewis says that television news does not have "
                 "the "),
            gap("w27"),
            text(" feature that other types of programme have. As a "
                 "result, many viewers do not find it interesting and "
                 "may find it "),
            gap("w28"),
            text(". This is because the "),
            gap("w29"),
            text(" information comes first and after that "),
            gap("w30"),
            text(" matters are covered. In television news, there is "
                 "no "),
            gap("w31"),
            text(" progress towards a conclusion and nothing "),
            gap("w32"),
            text(" to find out about. In fact, he believes that "
                 "television news is an example of how the "),
            gap("w33"),
            text(" process in the field of television could result in "
                 "something that is "),
            gap("w34"),
            text(" to what constitutes an interesting programme."),
        ]},
    ],
}

P3_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("w27", ["story-telling"]),
    ("w28", ["confusing"]),
    ("w29", ["crucial"]),
    ("w30", ["secondary"]),
    ("w31", ["step-by-step"]),
    ("w32", ["mysterious"]),
    ("w33", ["creative"]),
    ("w34", ["contrary"]),
]

P3_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "Lewis concentrates more on the structure of programmes "
        "than on what is actually in them.",
        "True",
    ),
    (
        "Lewis regrets viewers\u2019 preference for soap operas over "
        "television news.",
        "Not Given",
    ),
    (
        "Lewis suggests that viewers sometimes find that television "
        "news contradicts their knowledge of the world.",
        "False",
    ),
    (
        "Lewis believes that viewers have an inconsistent attitude "
        "towards the reliability of television news.",
        "True",
    ),
    (
        "Parkin states that many working-class people see themselves "
        "as exceptions to general beliefs.",
        "True",
    ),
    (
        "The writer of the text believes that viewers should have a "
        "less passive attitude towards what they are told by the media.",
        "Not Given",
    ),
]


# ── writing helpers ──────────────────────────────────────────────────────────

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
        self.count += 1
        self.slots += scoring_slots_for_question(question)

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": item["question"], "options": item["options"]},
                {"correct": item["correct"]},
            )

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


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")
    counts: list[int] = []
    slots: list[int] = []

    # -- Passage 1 --
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
    await w.mcq(
        "Choose the correct letter, A, B, C or D.",
        P1_MCQ,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the sentences below with words taken from "
        "Reading Passage 1.\n"
        "Write NO MORE THAN THREE WORDS for each answer.",
        P1_SENTENCE_STRUCTURE,
        P1_SENTENCE_ANSWERS,
        max_words=3,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending A\u2013H "
        "from the box below.\n"
        f"Write the correct letter, A\u2013H.\n{SCREEN_LETTER_HINT}",
        P1_ENDING_OPTIONS,
        P1_ENDING_ITEMS,
        options_heading="Ending",
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 2 --
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = f"Passage 2 \u2014 {title}"
    section.passage = body
    section.passage_subtitle = (
        "Mankind\u2019s search for alien life could be jeopardised by "
        "ultra-resilient bacteria from Earth. David Derbyshire reports"
    )
    print(
        f"\nPassage 2 ({section.id})  removed "
        f"{await clear_section(db, section.id)} old row(s)  "
        f"{len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the statements (Questions 14\u201320) and the list of "
        "spacecraft below.\n"
        "Match each statement with the spacecraft it applies to.\n"
        "Write the correct letter, A\u2013E.\n"
        f"NB You may use any letter more than once.\n{SCREEN_LETTER_HINT}",
        P2_SPACECRAFT_OPTIONS,
        P2_SPACECRAFT_ITEMS,
        options_heading="Spacecraft",
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Label the diagram below.\n"
        "Choose NO MORE THAN THREE WORDS from the reading passage "
        "for each answer.",
        P2_BEAGLE_STRUCTURE,
        P2_BEAGLE_ANSWERS,
        max_words=3,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    # -- Passage 3 --
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
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below using words from the box.\n\n"
        f"[{WORD_BOX}]",
        P3_SUMMARY_STRUCTURE,
        P3_SUMMARY_ANSWERS,
        max_words=1,
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Do the following statements agree with the information "
        "given in Reading Passage 3?\n"
        "Write\n"
        "TRUE if the statement agrees with the information\n"
        "FALSE if the statement contradicts the information\n"
        "NOT GIVEN if there is no information on this",
        P3_TFNG_ITEMS,
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
