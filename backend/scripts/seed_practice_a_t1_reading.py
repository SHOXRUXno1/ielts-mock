"""Seed Practice Set A Test 1 Reading, all three passages (Q1-40).

Passage 1  Q1-8   matching_features    cheetahs / leopards / both / neither
           Q9-13  summary_completion   with a word box
Passage 2  Q14-19 matching_headings    paragraphs B-G
           Q20-27 yes_no_ng
Passage 3  Q28-35 matching_features    who said what, by initials
           Q36-40 true_false_ng

Passage text lives in scripts/data/practice_a_t1/ so the prose stays
proofreadable instead of buried in string literals.

Idempotent: each passage section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t1_reading.py
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
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_a_common import (  # noqa: E402
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

P1_FEATURE_OPTIONS = [
    "A. if the statement refers to cheetahs at the Breeding Centre.",
    "B. if the statement refers to leopards at the Breeding Centre.",
    "C. if the statement refers to both cheetahs and leopards at the Breeding Centre.",
    "D. if the statement refers to neither cheetahs nor leopards at the Breeding Centre.",
]

P1_FEATURE_ITEMS: list[tuple[str, str]] = [
    ("These animals were smuggled into the UAE.", "A"),
    ("At first these animals did not adapt to life at the Sharjah Breeding Centre.", "D"),
    ("These animals are regarded as the most important animal at the Centre.", "B"),
    ("Half of these animals were born at the Breeding centre.", "D"),
    ("These animals can be dangerous to one another.", "B"),
    ("The role of the keeper is vital in the breeding programme of these animals.", "C"),
    ("The first of these animals at the Breeding Centre were relatively young.", "A"),
    ("It is normally difficult for humans to approach these animals.", "B"),
]

# More words than gaps, as printed — the surplus are the distractors.
P1_WORD_BANK = [
    "reptiles", "variety", "behaviour", "success", "creating",
    "expanding", "difficulty", "diversity", "action", "habitat",
    "season", "fish", "change", "working", "programme",
]

P1_SUMMARY_STRUCTURE: dict = {
    "variant": "summary",
    "title": "The Sharjah Breeding Centre",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "options": P1_WORD_BANK,
    "paragraphs": [
        {
            "segments": [
                text(
                    "The Sharjah Breeding Centre now has a variety of animals "
                    "including birds, mammals and "
                ),
                gap("s9"),
                text(
                    ". As its name suggests, the Centre is primarily involved "
                    "in breeding and "
                ),
                gap("s10"),
                text(
                    " the numbers of the species housed there whilst still "
                    "maintaining the "
                ),
                gap("s11"),
                text(
                    " of bloodlines in order to retain genetic health. In spite "
                    "of problems involving the complex "
                ),
                gap("s12"),
                text(" of the animals, a fair amount of "),
                gap("s13"),
                text(
                    " has been achieved with North African cheetahs and "
                    "Arabian leopards."
                ),
            ]
        }
    ],
}

P1_SUMMARY_ANSWERS: list[tuple[str, list[str]]] = [
    ("s9", ["reptiles"]),
    ("s10", ["expanding"]),
    ("s11", ["diversity"]),
    ("s12", ["behaviour", "behavior"]),
    ("s13", ["success"]),
]

# ── Passage 2 ────────────────────────────────────────────────────────────────

P2_HEADINGS = [
    "i. The Role of Sleep",
    "ii. Insomnia Medication",
    "iii. Habits to Promote a Good Night's Sleep",
    "iv. What is Insomnia",
    "v. Complications for Insomniacs",
    "vi. Government Action",
    "vii. Available Treatment for Insomnia",
    "viii. The Causes of Insomnia",
    "ix. Therapy Solutions",
    "x. Types of Insomnia",
    "xi. Current Research",
]

# Paragraph A is given as the example (iv) and is not asked.
P2_HEADING_ITEMS: list[tuple[str, str]] = [
    ("Paragraph B", "viii"),
    ("Paragraph C", "i"),
    ("Paragraph D", "x"),
    ("Paragraph E", "vii"),
    ("Paragraph F", "v"),
    ("Paragraph G", "iii"),
]

P2_YNNG_ITEMS: list[tuple[str, str]] = [
    (
        "Someone who only gets four hours of sleep a night must be suffering "
        "from insomnia.",
        "No",
    ),
    ("Travelling can cause insomnia.", "Yes"),
    ("REM sleep is felt to be the most important for the body's rest.", "No"),
    ("Secondary insomnia is far more common than primary insomnia.", "Not Given"),
    ("Sufferers of insomnia can attend specialist sleep clinics.", "Not Given"),
    (
        "Many people suffering from insomnia don't realise that they suffer from it.",
        "Not Given",
    ),
    ("There is no actual correlation linking insomnia and depression.", "No"),
    ("Sleeping during the day can make insomnia worse.", "Yes"),
]

# ── Passage 3 ────────────────────────────────────────────────────────────────

# The paper identifies speakers by their initials rather than by letter, so the
# options carry those initials as the prefix the dropdown offers.
P3_FEATURE_OPTIONS = [
    "TB. Tony Brown",
    "PL. Patrick Leahy",
    "BB. Bill Bowler",
    "PJ. Paul Jepson",
    "AP. Art Pimms",
    "SB. Steve Black",
    "RH. Rick Hilton",
]

P3_FEATURE_ITEMS: list[tuple[str, str]] = [
    ("There is a double advantage to the new techniques.", "AP"),
    ("Expectations of end users of agricultural products affect the products.", "RH"),
    ("The work on developing these alternative techniques is not finished.", "PJ"),
    (
        "Eating food that has had chemicals used in its production is dangerous "
        "to our health.",
        "BB",
    ),
    ("Changing current farming methods is not a cheap process.", "TB"),
    ("Results have exceeded anticipations.", "SB"),
    ("The research done should be translated into practical projects.", "PJ"),
    ("The U.S. produces the best food in the world.", "PL"),
]

P3_TFNG_ITEMS: list[tuple[str, str]] = [
    (
        "Integrated Pest Management has generally been regarded as a success "
        "in the US.",
        "False",
    ),
    (
        "Oregon farmers of apples and pears have been promoted as successful "
        "examples of Integrated Pest Management.",
        "True",
    ),
    ("The IPPC uses scientists from different organisations.", "True"),
    ("Straw mulch experiments produced unplanned benefits.", "True"),
    ("The apple industry is now facing a lot of competition from abroad.", "Not Given"),
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

    # Passage 1
    section = await get_section(db, test.id, SectionType.READING, 10)
    title, body = read_passage("reading_p1.txt")
    section.title = title.title()
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 1 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Use the information in the text to match the statements (1-8) with "
        "the animals (A-D).\n"
        "Write the appropriate letter (A-D) in boxes 1-8 on your answer sheet.\n"
        "Example: These animals are endangered — C",
        P1_FEATURE_OPTIONS,
        P1_FEATURE_ITEMS,
        options_heading="Write",
    )
    await w.compound(
        QuestionType.SUMMARY_COMPLETION,
        "Complete the summary below.\n"
        "Choose your answers from the box below the summary and write them in "
        "boxes 9-13 on your answer sheet.\n"
        "NB There are more words than spaces, so you will not use them all.",
        P1_SUMMARY_STRUCTURE,
        P1_SUMMARY_ANSWERS,
        max_words=1,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    # Passage 2
    section = await get_section(db, test.id, SectionType.READING, 11)
    title, body = read_passage("reading_p2.txt")
    section.title = "Insomnia — The Enemy of Sleep"
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 2 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_HEADINGS,
        "The reading passage on Insomnia has 7 paragraphs (A-G).\n"
        "From the list of headings below choose the most suitable headings for "
        "paragraphs B-G.\n"
        "Write the appropriate number (i-xi) in boxes 14-19 on your answer sheet.\n"
        "NB There are more headings than paragraphs, so you will not use them all.\n"
        "Example: Paragraph A — iv",
        P2_HEADINGS,
        P2_HEADING_ITEMS,
        options_heading="List of Headings",
    )
    await w.statements(
        QuestionType.YES_NO_NG,
        "Do the following statements agree with the views of the writer of the "
        "reading passage on Insomnia?\n"
        "In boxes 20-27 write\n"
        "YES if the statement agrees with the writer\n"
        "NO if the statement doesn't agree with the writer\n"
        "NOT GIVEN if it is impossible to say what the writer thinks about this",
        P2_YNNG_ITEMS,
    )
    counts.append(w.count)
    print(f"  {w.count} questions")

    # Passage 3
    section = await get_section(db, test.id, SectionType.READING, 12)
    title, body = read_passage("reading_p3.txt")
    section.title = "Alternative Farming Methods In Oregon"
    section.passage = body
    section.passage_subtitle = None
    print(f"\nPassage 3 ({section.id})  removed {await clear_section(db, section.id)}"
          f" old row(s)  {len(body.split())} words")
    w = PassageWriter(db, section)
    await w.lettered(
        QuestionType.MATCHING_FEATURES,
        "Match the views (28-35) with the people listed below.\n"
        "Write the appropriate initials in boxes 28-35 on your answer sheet.",
        P3_FEATURE_OPTIONS,
        P3_FEATURE_ITEMS,
        options_heading="List of People",
    )
    await w.statements(
        QuestionType.TRUE_FALSE_NG,
        "Read the passage about alternative farming methods in Oregon again and "
        "look at the statements below.\n"
        "In boxes 36-40 on your answer sheet write\n"
        "TRUE if the statement is true\n"
        "FALSE if the statement is false\n"
        "NOT GIVEN if the information is not given in the text",
        P3_TFNG_ITEMS,
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
