"""Seed Practice Set B Test 3 Reading, all three passages (Q1-40).

Source: IELTS Practice Tests Plus 2, Test 3. Keys from the printed
Answer Key (pp.176-178). Teaching strategy pages are omitted.

Passage 1  Q1-3   mcq                   song-in-head syndrome
           Q4-7   matching_features     theories → people A-F
           Q8-13  matching_information  paragraphs A-I
Passage 2  Q14-19 yes_no_ng             writer's claims
           Q20-25 summary_completion    Space for an increased population
           Q26-27 mcq
Passage 3  Q28-33 matching_features     sentence endings A-H
           Q34-38 flow_chart_completion Surveyor 3 / Apollo 12
           Q39-40 multi_select          writer's two main purposes

Passage text lives in scripts/data/practice_b_t3/ so the prose stays
proofreadable instead of buried in string literals.

Idempotent: each passage section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t3_reading.py
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
from seed_practice_b_common import (  # noqa: E402
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 3


def text(value: str) -> dict:
    return {"type": "text", "value": value}


def gap(gap_id: str) -> dict:
    return {"type": "gap", "gap_id": gap_id}


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "The writer says that 'song-in-head syndrome' may occur because the brain",
        [
            "confuses two different types of memory.",
            "cannot decide what information it needs to retain.",
            "has been damaged by harmful input.",
            "cannot hold onto all the information it processes.",
        ],
        "B",
    ),
    (
        "A tune is more likely to stay in your head if",
        [
            "it is simple and unoriginal.",
            "you have musical training.",
            "it is part of your culture.",
            "you have a good memory.",
        ],
        "A",
    ),
    (
        "Robert Zatorre found that a part of the auditory cortex was activated "
        "when volunteers",
        [
            "listened to certain types of music.",
            "learned to play a tune on an instrument.",
            "replayed a piece of music after several years.",
            "remembered a tune they had heard previously.",
        ],
        "D",
    ),
]

P1_PEOPLE = [
    "A. Roger Chaffin",
    "B. Susan Ball",
    "C. Steven Brown",
    "D. Caroline Palmer",
    "E. Sandra Calvert",
    "F. Leon James",
]

P1_THEORY_ITEMS: list[tuple[str, str]] = [
    (
        "The memorable nature of some tunes can help other learning processes.",
        "E",
    ),
    (
        "Music may not always be stored in the memory in the form of separate notes.",
        "D",
    ),
    (
        "People may have started to make music because of their need to remember things.",
        "F",
    ),
    (
        "Having a song going round your head may happen to you more often when "
        "one part of the brain is tired.",
        "B",
    ),
]

P1_PARAGRAPH_OPTIONS = [
    "A. Paragraph A",
    "B. Paragraph B",
    "C. Paragraph C",
    "D. Paragraph D",
    "E. Paragraph E",
    "F. Paragraph F",
    "G. Paragraph G",
    "H. Paragraph H",
    "I. Paragraph I",
]

P1_INFORMATION_ITEMS: list[tuple[str, str]] = [
    ("a claim that music strengthens social bonds", "I"),
    (
        "two reasons why some bits of music tend to stick in your mind more "
        "than others",
        "G",
    ),
    (
        "an example of how the brain may respond in opposition to your wishes",
        "E",
    ),
    (
        "the name of the part of the brain where song-in-head syndrome begins",
        "D",
    ),
    (
        "examples of two everyday events that can set off song-in-head syndrome",
        "A",
    ),
    (
        "a description of what one person does to prevent song-in-head syndrome",
        "F",
    ),
]


# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "Today's wealthy people ignore the fact that millions are living in poverty.",
        "Not Given",
    ),
    (
        "There are reasons why the future population of the world may not enjoy "
        "a comfortable lifestyle.",
        "Yes",
    ),
    (
        "The first thing to consider when planning for the future is "
        "environmental protection.",
        "No",
    ),
    (
        "As manufactured goods get cheaper, people will benefit more from them.",
        "Yes",
    ),
    (
        "It may be possible to find new types of raw materials for use in the "
        "production of machinery.",
        "Not Given",
    ),
    (
        "The rising prices of fossil fuels may bring some benefits.",
        "Yes",
    ),
]

P2_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "Space for an increased population",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                text("According to the writer, the use of land for "),
                gap("s20"),
                text(
                    " is the most serious threat to the environment. However, "
                    "in the US, there has already been an increase in the "
                    "amount of land used for "
                ),
                gap("s21"),
                text(
                    " and forests. Far less land would be required to feed the "
                    "world's population if the "
                ),
                gap("s22"),
                text(
                    " of the land could be improved worldwide. It has also been "
                    "claimed that the industrial production of animal foods "
                    "could allow greater access to animal "
                ),
                gap("s23"),
                text(
                    " by the entire world's population. Scientists could use "
                ),
                gap("s24"),
                text(
                    " from domesticated animals to help produce meat by tissue "
                    "cloning, and these species could then be allowed to die "
                    "out. In addition to this type of meat, "
                ),
                gap("s25"),
                text(" will also be widely available."),
            ]
        }
    ],
}

P2_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s20", ["agriculture", "farms", "farmland"]),
    ("s21", ["parks"]),
    ("s22", ["productivity"]),
    ("s23", ["protein"]),
    ("s24", ["DNA"]),
    ("s25", ["game"]),
]

P2_MCQ_ITEMS: list[tuple[str, list[str], str]] = [
    (
        "Greater mobility may be a feature of the future because of changes in",
        [
            "the location of housing.",
            "patterns of employment.",
            "centres of transport.",
            "the distribution of wealth.",
        ],
        "A",
    ),
    (
        "Air transport will be safe because of",
        [
            "new types of aircraft.",
            "better training methods.",
            "three-dimensional models.",
            "improved technology.",
        ],
        "D",
    ),
]


# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_ENDING_OPTIONS = [
    "A. activities of tourists and scientists have harmed the environment.",
    "B. some sites in space could be important in the history of space exploration.",
    "C. vehicles used for tourism have polluted the environment.",
    "D. it may be unclear who has responsibility for historic human footprints.",
    "E. past explorers used technology in order to find new places to live.",
    "F. man-made objects left in space are regarded as rubbish.",
    "G. astronauts may need to work more closely with archaeologists.",
    "H. important sites on the Moon may be under threat.",
]

P3_ENDING_ITEMS: list[tuple[str, str]] = [
    ("Ben Finney's main academic work investigates the way that", "E"),
    ("Ben Finney thought that in the long term", "B"),
    ("Commercial pressures mean that in the immediate future", "H"),
    (
        "Academics are concerned by the fact that in isolated regions on Earth,",
        "A",
    ),
    ("One problem with the 1967 UN treaty is that", "F"),
    (
        "The wording of legal agreements over ownership of land in space means that",
        "D",
    ),
]

P3_FLOW_STRUCTURE: dict = {
    "variant": "flow",
    "title": "",
    "instruction_words": "NO MORE THAN ONE WORD",
    "max_words_per_gap": 1,
    "steps": [
        {
            "segments": [
                text("During the assembly of the Surveyor 3 probe, someone "),
                gap("f34"),
                text(" on a TV camera."),
            ]
        },
        {
            "segments": [
                text("The TV camera was carried to the Moon on Surveyor 3.")
            ]
        },
        {
            "segments": [
                text("The TV camera remained on the Moon for over "),
                gap("f35"),
                text(" years."),
            ]
        },
        {
            "segments": [
                text("Apollo 12 astronauts "),
                gap("f36"),
                text(" the TV camera."),
            ]
        },
        {
            "segments": [
                text("The TV camera was returned to Earth for "),
                gap("f37"),
                text("."),
            ]
        },
        {
            "segments": [
                text("The Streptococcus mitis bacteria were found.")
            ]
        },
        {
            "segments": [
                text(
                    "The theory that this suggested there was "
                ),
                gap("f38"),
                text(" on the Moon was rejected."),
            ]
        },
        {
            "segments": [
                text(
                    "Scientists concluded that the bacteria can survive lunar "
                    "conditions."
                )
            ]
        },
    ],
}

P3_FLOW_ANSWERS: list[tuple[str, list[str]]] = [
    ("f34", ["sneezed"]),
    ("f35", ["two", "2"]),
    ("f36", ["removed"]),
    ("f37", ["analysis"]),
    ("f38", ["life"]),
]

P3_MULTI = {
    "question": "The TWO main purposes of the writer of this text are to explain",
    "options": [
        "the reasons why space archaeology is not possible.",
        "the dangers that could follow from contamination of objects from space.",
        "the need to set up careful controls over space tourism.",
        "the need to preserve historic sites and objects in space.",
        "the possible cultural effects of space travel.",
    ],
    "correct": ["C", "D"],
}


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
    slots: list[int] = []

    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage(TEST_NUMBER, "reading_p1.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "Some songs just won't leave you alone. But this may give us clues "
        "about how our brain works"
    )
    print(
        f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
        "Write your answers in boxes 1–3 on your answer sheet.",
        P1_MCQ_ITEMS,
    )
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Look at the following theories (Questions 4–7) and the list of people below.\n"
        "Match each theory with the person it is credited to.\n"
        "Write the correct letter A–F in boxes 4–7 on your answer sheet.",
        P1_PEOPLE,
        P1_THEORY_ITEMS,
        options_heading="List of People",
    )
    await w.lettered(
        QuestionType.MATCHING_INFORMATION,
        "Reading Passage 1 has nine paragraphs labelled A–I.\n"
        "Which paragraph contains the following information?\n"
        "Write the correct letter A–I in boxes 8–13 on your answer sheet.\n"
        "NB You may use any letter more than once.",
        P1_PARAGRAPH_OPTIONS,
        P1_INFORMATION_ITEMS,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage(TEST_NUMBER, "reading_p2.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "Can the future population of the world enjoy a comfortable lifestyle, "
        "with possessions, space and mobility, without crippling the environment?"
    )
    print(
        f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements reflect the claims of the writer in "
        "Reading Passage 2?\n"
        "In boxes 14–19 on your answer sheet write\n"
        "YES if the statement reflects the writer's claims\n"
        "NO if the statement contradicts the writer's claims\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P2_YNNG_ITEMS,
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose ONE WORD ONLY from the passage for each answer.\n"
        "Write your answers in boxes 20–25 on your answer sheet.",
        P2_SUMMARY_STRUCTURE,
        P2_SUMMARY_ANSWERS,
        max_words=1,
    )
    await w.mcq(
        "Choose the correct answer, A, B, C or D.\n"
        "Write your answers in boxes 26–27 on your answer sheet.",
        P2_MCQ_ITEMS,
    )
    counts.append(w.count)
    slots.append(w.slots)
    print(f"  {w.count} questions / {w.slots} slots")

    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title
    section.passage = body
    section.passage_subtitle = (
        "Space travel may still have a long way to go, but the notion of "
        "archaeological research and heritage management in space is already "
        "concerning scientists and environmentalists."
    )
    print(
        f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
        f" old row(s)  {len(body.split())} words"
    )
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Complete each sentence with the correct ending A–H from the box below.\n"
        "Write the correct letter A–H in boxes 28–33 on your answer sheet.",
        P3_ENDING_OPTIONS,
        P3_ENDING_ITEMS,
        options_heading="Endings",
    )
    await w.compound(
        QuestionType.FLOW_CHART_COMPLETION,
        "Complete the flow chart below.\n"
        "Choose NO MORE THAN ONE WORD from the passage for each answer.\n"
        "Write your answers in boxes 34–38 on your answer sheet.",
        P3_FLOW_STRUCTURE,
        P3_FLOW_ANSWERS,
        max_words=1,
    )
    await w.multi_select("Choose TWO letters A–E.", P3_MULTI)
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
        f"\nDone. Reading seeded: rows {counts} / slots {slots} = {total_slots}."
    )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
