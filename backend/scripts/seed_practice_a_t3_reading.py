"""Seed Practice Set A Test 3 Reading, all three passages (Q1-40).

Passage 1  Q1-6   matching_features     which agency did which clean-up job
           Q7-14  yes_no_ng
Passage 2  Q15-21 yes_no_ng
           Q22-26 short_answer
           Q27    mcq                   best title for the passage
Passage 3  Q28-32 matching_headings     paragraphs A-E
           Q33-37 true_false_ng
           Q38-40 sentence_completion

Passage text lives in scripts/data/practice_a_t3/ so the prose stays
proofreadable instead of buried in string literals.

Idempotent: each passage section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t3_reading.py
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
from seed_practice_a_common import (  # noqa: E402
    clear_section,
    get_section,
    get_test,
    read_passage,
)

TEST_NUMBER = 3


# ── Passage 1 ────────────────────────────────────────────────────────────────

P1_ACTION_OPTIONS = [
    "A. Operating the Rubbish Muncher",
    "B. Creating Community Strategies",
    "C. Monitoring the Cleanliness of the River Thames",
    "D. Monitoring Fish Levels",
    "E. Collecting Solid Waste from the Tideway",
    "F. Creating Enlarged Sewage Works",
    "G. Controlling the River Thames' Traffic",
]

P1_ACTION_ITEMS: list[tuple[str, str]] = [
    ("The Environment Agency", "C"),
    ("Transport for London", "G"),
    ("The Greater London Council", "F"),
    ("Thames Water", "A"),
    ("Port of London", "E"),
    ("Local Boroughs", "B"),
]

P1_YNNG_ITEMS: list[tuple[str, str]] = [
    ("The Thames is now cleaner than it was in 1900.", "Yes"),
    ("Swimming in the Thames now poses no health hazards.", "Not Given"),
    (
        "It is now mainly the responsibility of those who pollute the Thames to "
        "clean their waste up.",
        "Not Given",
    ),
    (
        "All local London boroughs are now partly responsible for keeping the "
        "Thames clean.",
        "Yes",
    ),
    (
        "Transport for London now employs a type of River Police to enforce "
        "control of their regulations.",
        "Yes",
    ),
    ("Rubbish Munchers are now situated at various locations on the Thames.", "No"),
    (
        "Previously no one department had overall responsibility or control for "
        "monitoring the cleanliness of the Thames.",
        "Yes",
    ),
    ("British Waterways will no longer have any part in keeping the Thames clean.", "No"),
]

# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "Although nicotine is probably the well-known chemical in cigarettes, it "
        "is not necessarily the one that changes the psyche of the smoker when "
        "cigarettes are smoked.",
        "No",
    ),
    (
        "In spite of the difficulties, according to the text more than thirty-five "
        "million people a year give up smoking.",
        "No",
    ),
    (
        "It has been shown that nicotine in cigarettes can improve people's "
        "abilities to perform some actions more quickly.",
        "Yes",
    ),
    ("Added ammonia in cigarettes allows smokers to inhale more nicotine.", "Yes"),
    ("Snorted substances reach the brain faster than injected substances.", "Not Given"),
    ("Nicotine dilates the blood vessels that carry it around the body.", "Not Given"),
    (
        "Nicotine molecules allow greater electrical charges to pass between "
        "neurones.",
        "Yes",
    ),
]

P2_SHORT_ANSWER: list[dict] = [
    {
        "prompt": "What is the natural colour of nicotine?",
        # The passage gives the colour inside the phrase "a clear liquid", so a
        # candidate who lifts the whole phrase has still read it correctly.
        "correct": ["Clear", "Clear liquid", "A clear liquid"],
        "max_words": 3,
    },
    {
        "prompt": (
            "By how much would cigarette companies have to cut the nicotine "
            "content in cigarettes to prevent them from being addictive?"
        ),
        "correct": ["95%", "95 percent", "95", "By 95%"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Name ONE of 2 things that first take nicotine into a smoker's body."
        ),
        "correct": [
            "Skin",
            "The skin",
            "Mouth lining",
            "The mouth lining",
            "Lining of the mouth",
            "The lining of the mouth",
            "Mouth",
            "The mouth",
        ],
        "max_words": 3,
    },
    {
        "prompt": (
            "According to the passage, by how many beats a minute can a cigarette "
            "raise a smoker's heart rate?"
        ),
        "correct": ["10 - 20", "10-20", "10 to 20", "Between 10 and 20", "10 to 20 beats"],
        "max_words": 3,
    },
    {
        "prompt": "What surrounds neurones?",
        "correct": ["Spaces", "The spaces", "Space"],
        "max_words": 3,
    },
]

P2_TITLE_MCQ: list[dict] = [
    {
        "question": "From the list below choose the most suitable title for Reading Passage 2.",
        "options": [
            "How to Quit Smoking",
            "The Dangers of Smoking",
            "Cell Biology",
            "Why Smoking is Addictive",
            "Nicotine is a Poison",
        ],
        "correct": "D",
    },
]

# ── Passage 3 ────────────────────────────────────────────────────────────────

P3_HEADINGS = [
    "i. Industry Structures",
    "ii. Disease Affects Production",
    "iii. Trends in Production",
    "iv. Government Assistance",
    "v. How Deer Came to Australia",
    "vi. Research and Development",
    "vii. Asian Competition",
    "viii. Industry Development",
]

P3_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph A", "v"),
    ("Paragraph B", "viii"),
    ("Paragraph C", "i"),
    ("Paragraph D", "iii"),
    ("Paragraph E", "vi"),
]

P3_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "Until 1985 only 2 species of the originally released Australian deer were "
        "not used for farming.",
        "True",
    ),
    (
        "Since 1985 many imported deer have been interbred with the established "
        "herds.",
        "Not Given",
    ),
    (
        "The drop in deer numbers since 1997 led to an increase in the price of "
        "venison.",
        "False",
    ),
    (
        "Only a small amount of Australian venison production is consumed "
        "domestically.",
        "True",
    ),
    (
        "Current economic conditions in Asian countries have had positive effect "
        "on the Australian deer industry.",
        "Not Given",
    ),
]

P3_SENTENCES: list[dict] = [
    {
        "prompt": (
            "A stringent __________ allows the Australian deer industry to "
            "maintain their excellence of product."
        ),
        "correct": ["Quality assurance program", "Quality assurance programme"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Herd stock expansion was made difficult by the killing of __________ "
            "to continue product supply."
        ),
        "correct": ["Breeding females", "Young breeding females"],
        "max_words": 3,
    },
    {
        "prompt": (
            "Foreign and home markets for Australian venison increased due to the "
            "__________."
        ),
        "correct": ["Venison Market Project", "Venison Market Project 1992 to 1996"],
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

    async def mcq(self, instruction: str, items: list[dict]) -> None:
        group = await self._group(QuestionType.MCQ, instruction)
        for item in items:
            self._add(
                group,
                QuestionType.MCQ,
                {"question": item["question"], "options": item["options"]},
                {"correct": item["correct"]},
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
                {"prompt": item["prompt"], "max_words": item["max_words"]},
                {
                    "correct": item["correct"],
                    "max_words": item["max_words"],
                    "case_sensitive": False,
                },
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
        QuestionType.MATCHING_FEATURES,
        "Some of the actions taken to clean up the River Thames are listed below.\n"
        "The writer gives these actions as examples of things that have been done "
        "by various agencies connected with the River Thames.\n"
        "Match each action with the agency responsible for doing it.\n"
        "Write the appropriate letters (A-G) in boxes 1-6 on your answer sheet.\n"
        "Example: The Fisheries Department — D",
        P1_ACTION_OPTIONS,
        P1_ACTION_ITEMS,
        options_heading="Actions to Clean up the River Thames",
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer of the "
        "reading passage on Cleaning up the Thames?\n"
        "In boxes 7-14 write\n"
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
    # The paper prints this passage untitled because Q27 asks for its title, so
    # the section header names the subject rather than the answer.
    section.title = title.title()
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer of "
        "Reading Passage 2?\n"
        "In boxes 15-21 write\n"
        "YES if the statement agrees with the writer\n"
        "NO if the statement doesn't agree with the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P2_YNNG_ITEMS,
    )
    await w.free_text(
        QuestionType.SHORT_ANSWER,
        "Using NO MORE THAN THREE WORDS AND/OR A NUMBER from Reading Passage 2, "
        "answer the following questions.\n"
        "Write your answers in boxes 22-26 on your answer sheet.",
        P2_SHORT_ANSWER,
    )
    await w.mcq(
        "Choose the correct letter, A, B, C, D or E.",
        P2_TITLE_MCQ,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    # Passage 3
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage(TEST_NUMBER, "reading_p3.txt")
    section.title = title.title()
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "The reading passage on Deer Farming In Australia has 5 paragraphs (A-E).\n"
        "From the list of headings below choose the most suitable headings for "
        "paragraphs A-E.\n"
        "Write the appropriate number (i-viii) in boxes 28-32 on your answer sheet.\n"
        "NB There are more headings than paragraphs, so you will not use them all.",
        P3_HEADINGS,
        P3_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Read the passage about Deer Farming in Australia again and look at the "
        "statements below.\n"
        "In boxes 33-37 on your answer sheet write\n"
        "TRUE if the statement is true\n"
        "FALSE if the statement is false\n"
        "NOT GIVEN if the information is not given in Reading Passage 3",
        P3_TFNG_ITEMS,
    )
    await w.free_text(
        QuestionType.SENTENCE_COMPLETION,
        "Complete each of the following statements (Questions 38-40) with words "
        "taken from Reading Passage 3.\n"
        "Write NO MORE THAN THREE WORDS for each answer.\n"
        "Write your answers in boxes 38-40 on your answer sheet.",
        P3_SENTENCES,
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
