"""Data-driven Collins Practice Tests 3/4 seeder for Practice Set D.

The book title is intentionally kept out of student-facing records.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

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
from app.services.writing_presets import get_default_instruction  # noqa: E402
from seed_practice_d_common import (  # noqa: E402
    AUDIO_URL,
    CHART_IMAGE_URL,
    clear_section,
    get_section,
    get_test,
    read_passage,
)


def txt(value: str) -> dict[str, str]:
    return {"type": "text", "value": value}


def gap(value: str) -> dict[str, str]:
    return {"type": "gap", "gap_id": value}


def structure(variant: str, title: str, words: int, items: list[list[dict[str, str]]]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "variant": variant,
        "title": title,
        "instruction_words": f"{words} WORD" + ("S" if words != 1 else ""),
        "max_words_per_gap": words,
    }
    if variant == "summary":
        result["paragraphs"] = [{"segments": row} for row in items]
    elif variant == "flow":
        result["steps"] = [{"segments": row} for row in items]
    else:
        result["sections"] = [{"heading": "", "items": [{"segments": row} for row in items]}]
    return result


async def put_group(
    db: AsyncSession,
    section: Section,
    group_order: int,
    question_type: QuestionType,
    instruction: str,
    entries: list[tuple[dict[str, Any], dict[str, Any] | None]],
    *,
    shared: dict[str, Any] | None = None,
) -> tuple[int, int]:
    if shared and "variant" in shared:
        validate_compound_structure(question_type.value, shared)
    group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=group_order,
        question_type=question_type.value,
        instruction=instruction,
        options_shared=shared,
    )
    db.add(group)
    await db.flush()
    slots = 0
    for order, (content, answer_key) in enumerate(entries, start=1):
        question = Question(
            id=uuid.uuid4(),
            section_id=section.id,
            question_group_id=group.id,
            order=order,
            question_type=question_type,
            content=content,
            answer_key=answer_key,
        )
        db.add(question)
        slots += scoring_slots_for_question(question)
    return group_order + 1, slots


def choices(values: list[str]) -> dict[str, Any]:
    return {"options": values}


def lettered_entries(items: list[tuple[str, str]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [({"question": prompt}, {"correct": answer}) for prompt, answer in items]


def statement_entries(items: list[tuple[str, str]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [({"statement": prompt}, {"correct": answer}) for prompt, answer in items]


def gap_entries(items: list[tuple[str, list[str], int]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [({"gap_id": gap_id}, gap_answer_key(answers, max_words=limit)) for gap_id, answers, limit in items]


async def seed_reading(db: AsyncSession, number: int) -> None:
    test = await get_test(db, number)
    totals: list[int] = []

    async def passage(order: int, label: str, groups: list[dict[str, Any]]) -> None:
        section = await get_section(db, test.id, SectionType.READING, order)
        title, body = read_passage(number, f"reading_p{order - 9}.txt")
        section.title = f"Passage {order - 9} — {title}"
        section.passage = body
        section.passage_subtitle = None
        await clear_section(db, section.id)
        gorder = 1
        points = 0
        for group in groups:
            gorder, count = await put_group(
                db,
                section,
                gorder,
                group["type"],
                group["instruction"],
                group["entries"],
                shared=group.get("shared"),
            )
            points += count
        totals.append(points)
        print(f"  {label}: {points} scoring slots; passage {len(body.split())} words")

    if number == 3:
        stages = ["A. Stage 1", "B. Stage 2", "C. Stage 3", "D. Stage 4"]
        p1multi = {
            "question": "Which TWO statements are mentioned in paragraphs 5–7?",
            "options": [
                "A. During stage 3, company productivity increases as people adapt.",
                "B. Staff training is not worthwhile during organisational change.",
                "C. Some people accept change because they have no alternative.",
                "D. Change is harder to process when people receive no support.",
                "E. Communication can prevent all stress during change.",
            ],
        }
        p1 = [
            {"type": QuestionType.MATCHING_FEATURES, "instruction": "Match each description to the stage in which it occurs. You may use any letter more than once.", "shared": choices(stages), "entries": lettered_entries([
                ("Common feelings include anger, resentment or fear.", "B"),
                ("Training and practical support help people adapt.", "C"),
                ("People refuse to accept the facts of the change.", "A"),
                ("People acknowledge and work with the new reality.", "C"),
                ("Colleagues' relationships become difficult and work is disrupted.", "B"),
                ("People should be told about change and included in the process.", "A"),
                ("Success and the difficulties experienced should be acknowledged.", "D"),
                ("People begin making plans and seeing new opportunities.", "D"),
            ])},
            {"type": QuestionType.TRUE_FALSE_NG, "instruction": "Do the following statements agree with the information given in Reading Passage 1? Write TRUE, FALSE or NOT GIVEN.", "entries": statement_entries([
                ("The Change Curve explains why organisations decide to change.", "FALSE"),
                ("The model was based on counselling ideas for people facing death.", "TRUE"),
                ("The model explains how people adapt to significant national events.", "NOT GIVEN"),
                ("Organisations use a more complex version of Kübler-Ross's stages.", "FALSE"),
            ])},
            {"type": QuestionType.MULTI_SELECT, "instruction": "Choose TWO letters, A–E.", "entries": [({"question": p1multi["question"], "options": p1multi["options"]}, {"correct": ["C", "D"]})]},
        ]
        endings = ["A. can be found mostly in the same orbit area as the ISS", "B. produce more debris that can travel long distances", "C. are above Siberia", "D. are no longer active", "E. can be tracked from the ground", "F. are among the 5,000 satellites still circling Earth", "G. burn up as they fall back to Earth", "H. circle the planet in medium Earth orbit"]
        p2summary = structure("summary", "Solutions to the Kessler syndrome", 3, [
            [txt("Laws could require satellites to "), gap("q24"), txt(" the Earth's atmosphere at the end of their life and impose "), gap("q25"), txt(" on countries that fail to comply.")],
            [txt("The situation needs to "), gap("q26"), txt(" by removing larger objects from orbit. Their "), gap("q27"), txt(" makes this difficult; proposed methods include "), gap("q28"), txt(" or a "), gap("q29"), txt(".")],
        ])
        p2 = [
            {"type": QuestionType.MATCHING_FEATURES, "instruction": "Complete each sentence with the correct ending, A–H.", "shared": choices(endings), "entries": lettered_entries([
                ("Many satellites orbiting Earth", "D"), ("Debris larger than 10 centimetres", "E"),
                ("Debris fragments created by collisions", "A"), ("Some objects in low Earth orbit", "G"),
                ("High-speed collisions", "B"),
            ])},
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B, C or D.", "entries": [
                ({"question": "How did the ISS avoid the debris in 2014?", "options": ["A. A window was damaged.", "B. A docked supply vehicle moved it out of the path.", "C. Scientists destroyed the Russian satellite.", "D. The station was designed for high-speed debris." ]}, {"correct": "B"}),
                ({"question": "What is true about satellites and debris in low Earth orbit?", "options": ["A. Satellites can withstand any impact.", "B. Collisions are a constant risk.", "C. Debris paths can always be predicted accurately.", "D. The ISS is moved frequently." ]}, {"correct": "C"}),
                ({"question": "The amount of space junk will NOT lead to", "options": ["A. more expensive launches.", "B. a cloud of debris around Earth.", "C. easier tracking of fragments.", "D. a chain reaction of collisions." ]}, {"correct": "C"}),
                ({"question": "What is making the space-junk problem worse?", "options": ["A. Deliberately destroying old satellites.", "B. A high concentration of debris.", "C. Inactive satellites remaining in orbit.", "D. Lack of awareness of the problem." ]}, {"correct": "A"}),
            ]},
            {"type": QuestionType.SUMMARY_COMPLETION, "instruction": "Complete the summary. Choose NO MORE THAN THREE WORDS from the passage for each answer.", "shared": p2summary, "entries": gap_entries([
                ("q24", ["re-enter", "reenter"], 3), ("q25", ["penalties"], 3), ("q26", ["stabilise", "stabilize"], 3), ("q27", ["size"], 3), ("q28", ["harpoons or nets", "nets or harpoons"], 3), ("q29", ["satellite service station"], 3),
            ])},
        ]
        p3table = {
            "variant": "table",
            "title": "",
            "instruction_words": "NO MORE THAN TWO WORDS",
            "max_words_per_gap": 2,
            "headers": ["Age (years)", "Phase", "Height", "Feature"],
            "rows": [
                [
                    {"variant": "plain", "segments": [txt("10–15")]},
                    {"variant": "plain", "segments": [txt("sapling")]},
                    {"variant": "plain", "segments": [txt("3–6 metres")]},
                    {"variant": "plain", "segments": [txt("—")]},
                ],
                [
                    {"variant": "plain", "segments": [txt("60–70")]},
                    {"variant": "plain", "segments": [gap("q33")]},
                    {"variant": "plain", "segments": [txt("5–15 metres")]},
                    {"variant": "plain", "segments": [txt("the tree's "), gap("q34"), txt(" is the quickest")]},
                ],
                [
                    {"variant": "plain", "segments": [txt("70–300")]},
                    {"variant": "plain", "segments": [txt("bottle")]},
                    {"variant": "plain", "segments": [txt("10–20 metres")]},
                    {"variant": "plain", "segments": [txt("the trunk "), gap("q35"), txt(" and takes on the familiar baobab shape")]},
                ],
                [
                    {"variant": "plain", "segments": [txt("300–800")]},
                    {"variant": "plain", "segments": [txt("old age")]},
                    {"variant": "plain", "segments": [txt("—")]},
                    {"variant": "plain", "segments": [txt("the tree trunk becomes hollow and expands")]},
                ],
            ],
        }
        p3 = [
            {"type": QuestionType.SHORT_ANSWER, "instruction": "Complete the sentences. Choose ONE WORD ONLY from the passage.", "entries": [
                ({"prompt": "The baobab's branches stick up into the air like tree ...", "max_words": 1}, gap_answer_key(["branches"], max_words=1)),
                ({"prompt": "The hollow trunk provides ... for animals and people.", "max_words": 1}, gap_answer_key(["shelter"], max_words=1)),
                ({"prompt": "At the end of its life, the tree ... quickly.", "max_words": 1}, gap_answer_key(["disintegrates"], max_words=1)),
            ]},
            {"type": QuestionType.TABLE_COMPLETION, "instruction": "Complete the table. Choose NO MORE THAN TWO WORDS from the passage for each answer.", "shared": p3table, "entries": gap_entries([("q33", ["cone"], 2), ("q34", ["growth"], 2), ("q35", ["broadens out", "broadens"], 2)])},
            {"type": QuestionType.MATCHING_INFORMATION, "instruction": "Which paragraph, A–E, contains the information?", "shared": choices(["A", "B", "C", "D", "E"]), "entries": lettered_entries([
                ("How the baobab reproduces", "D"), ("The end of the baobab's life", "E"),
                ("How the baobab survives in dry conditions", "C"), ("The climate and regions where it grows", "A"),
                ("How scientists determine the trees' ages", "B"),
            ])},
        ]
        await passage(10, "Passage 1", p1)
        await passage(11, "Passage 2", p2)
        await passage(12, "Passage 3", p3)
    else:
        p1summary = structure("summary", "Coastal erosion", 1, [
            [txt("Erosion creates different types of "), gap("q1"), txt(" with varied "), gap("q2"), txt("; growing "), gap("q3"), txt(" of coastal homes and businesses makes management a "), gap("q4"), txt(". Failure may harm the "), gap("q5"), txt(".")],
        ])
        p1flow = structure("flow", "Engineered coastal defences", 1, [
            [txt("Vertical sea walls: foundations can be "), gap("q9"), txt(" by the sea.")],
            [txt("Curved sea walls: prevent water from "), gap("q10"), txt(" over the wall.")],
            [txt("Mound walls: capable of "), gap("q11"), txt(" wave energy.")],
            [txt("Groynes: have a short "), gap("q12"), txt(".")],
        ])
        p1 = [
            {"type": QuestionType.MATCHING_FEATURES, "instruction": "Complete the summary using the words A–I.", "shared": choices(["A. crisis", "B. priority", "C. landscape", "D. management", "E. economy", "F. roles", "G. society", "H. resources", "I. development"]), "entries": lettered_entries([
                ("Coastal features formed by erosion", "C"), ("Their functions", "F"), ("Increasing presence of homes and businesses", "I"), ("Managing erosion is", "B"), ("Severe effects on", "G"),
            ])},
            {"type": QuestionType.SHORT_ANSWER, "instruction": "Complete the sentences. Choose ONE WORD ONLY from the passage.", "entries": [
                ({"prompt": "The sea wears down coastal features by its ...", "max_words": 1}, gap_answer_key(["action"], max_words=1)),
                ({"prompt": "Waves move sediment when they hit the beach at an ...", "max_words": 1}, gap_answer_key(["angle"], max_words=1)),
                ({"prompt": "A beach may ... further down the coast.", "max_words": 1}, gap_answer_key(["re-form", "reform"], max_words=1)),
            ]},
            {"type": QuestionType.FLOW_CHART_COMPLETION, "instruction": "Complete the flow chart. Choose ONE WORD from the passage for each answer.", "shared": p1flow, "entries": gap_entries([("q9", ["undermined"], 1), ("q10", ["crashing"], 1), ("q11", ["absorbing"], 1), ("q12", ["lifespan"], 1)])},
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B, C or D.", "entries": [
                ({"question": "Which statement is NOT TRUE about beach nourishment?", "options": ["A. Sea walls are not needed.", "B. Materials must be replaced often.", "C. More material is carried down the coast.", "D. Roads are built to bring material to the coast."]}, {"correct": "D"}),
                ({"question": "Which statement is TRUE about managed retreat?", "options": ["A. It usually creates cliffs.", "B. It is used in areas with little commercial value.", "C. Little land is lost to the sea.", "D. It is expensive."]}, {"correct": "B"}),
            ]},
        ]
        table = {
            "variant": "table",
            "title": "",
            "instruction_words": "ONE WORD ONLY",
            "max_words_per_gap": 1,
            "headers": ["Stage", "Behaviours"],
            "rows": [
                [{"variant": "plain", "segments": [txt("Forming")]}, {"variant": "plain", "segments": [txt("People become acquainted and learn where they fit into the group's "), gap("q15")] }],
                [{"variant": "plain", "segments": [txt("Storming")]}, {"variant": "plain", "segments": [txt("Differences "), gap("q16"), txt(" in the team about the task and how to do it")] }],
                [{"variant": "plain", "segments": [txt("Norming")]}, {"variant": "plain", "segments": [txt("Team "), gap("q17"), txt(" improves as people learn to work together")] }],
                [{"variant": "plain", "segments": [txt("Performing")]}, {"variant": "plain", "segments": [txt("The team follows agreed "), gap("q18")] }],
                [{"variant": "plain", "segments": [txt("Adjourning")]}, {"variant": "plain", "segments": [txt("The team reflects on its "), gap("q19"), txt(" and successes")] }],
            ],
        }
        p2 = [
            {"type": QuestionType.TABLE_COMPLETION, "instruction": "Complete the table. Choose ONE WORD ONLY from the passage.", "shared": table, "entries": gap_entries([
                ("q15", ["hierarchy"], 1), ("q16", ["emerge"], 1), ("q17", ["cooperation"], 1), ("q18", ["norms"], 1), ("q19", ["performance"], 1),
            ])},
            {"type": QuestionType.MULTI_SELECT, "instruction": "Choose TWO letters, A–E.", "entries": [({"question": "Which TWO features of Tuckman's model are mentioned?", "options": ["A. It depends on good managers.", "B. It helps managers support staff forming teams.", "C. It helps managers monitor team performance.", "D. It is based on Tuckman's workplace observations.", "E. It allows teams to return to an earlier stage."]}, {"correct": ["B", "E"]})]},
            {"type": QuestionType.MULTI_SELECT, "instruction": "Choose TWO letters, A–E.", "entries": [({"question": "Which TWO shortcomings of the model are mentioned?", "options": ["A. It only applies to postgraduate schools.", "B. It predicts teams become unstable.", "C. It does not predict how long teams stay together.", "D. It excludes external factors affecting progress.", "E. It did not match what was observed in practice."]}, {"correct": ["D", "E"]})]},
            {"type": QuestionType.TRUE_FALSE_NG, "instruction": "Do the following statements agree with the information in Reading Passage 2? Write TRUE, FALSE or NOT GIVEN.", "entries": statement_entries([
                ("Modern technology companies do not keep teams together for more than six months.", "NOT GIVEN"),
                ("Technology companies use reteaming to break up teams and create new ones.", "TRUE"),
                ("Reteaming prevents companies from responding quickly to market changes.", "FALSE"),
                ("Technology companies routinely recruit new team members from outside the company.", "NOT GIVEN"),
                ("Some teams are allowed to grow until they can be divided in two.", "TRUE"),
                ("Volunteers may form a temporary team to solve one problem.", "TRUE"),
            ])},
        ]
        p3summary = structure("summary", "Artificial curation", 1, [
            [txt("Too much data creates "), gap("q30"), txt(". AI curation finds and displays "), gap("q31"), txt(" in data. Technology can gather and "), gap("q32"), txt(" digital information.")],
        ])
        flow = structure("flow", "How a news company combines human and AI curation", 1, [
            [txt("Readers' selected stories form the "), gap("q37"), txt(" for algorithms.")],
            [txt("A human editor "), gap("q38"), txt(" the stories gathered by the algorithm.")],
            [txt("The editor "), gap("q39"), txt(" unsuitable content.")],
            [txt("The combined approach improves the quality of "), gap("q40"), txt(".")],
        ])
        p3 = [
            {"type": QuestionType.SUMMARY_COMPLETION, "instruction": "Complete the sentences. Choose ONE WORD ONLY from the passage.", "shared": p3summary, "entries": gap_entries([("q30", ["confusion"], 1), ("q31", ["patterns"], 1), ("q32", ["interpret"], 1)])},
            {"type": QuestionType.MULTI_SELECT, "instruction": "Choose TWO letters, A–E.", "entries": [({"question": "Which TWO things does an algorithm do?", "options": ["A. It uses past internet activity to gather data.", "B. It helps users build relationships with preferred websites.", "C. It uses questionnaire responses to create adverts.", "D. It collects information from other algorithms.", "E. It presents information users do not want."]}, {"correct": ["A", "B"]})]},
            {"type": QuestionType.MULTI_SELECT, "instruction": "Choose TWO letters, A–E.", "entries": [({"question": "Which TWO things can't an AI algorithm do?", "options": ["A. Present certain information directly.", "B. Distinguish reliable stories from fabricated ones.", "C. Recommend items appropriate for the user.", "D. Find sources quickly and efficiently.", "E. Find stories about famous people."]}, {"correct": ["B", "C"]})]},
            {"type": QuestionType.FLOW_CHART_COMPLETION, "instruction": "Complete the flow chart. Choose ONE WORD ONLY from the passage.", "shared": flow, "entries": gap_entries([("q37", ["basis"], 1), ("q38", ["fine-tunes", "fine tunes"], 1), ("q39", ["deletes"], 1), ("q40", ["curation"], 1)])},
        ]
        await passage(10, "Passage 1", p1)
        await passage(11, "Passage 2", p2)
        await passage(12, "Passage 3", p3)

    if sum(totals) != 40:
        raise SystemExit(f"expected 40 reading scoring slots, got {sum(totals)}")
    await db.commit()
    print(f"Reading Test {number}: 40 scoring slots in {totals}")


async def seed_listening(db: AsyncSession, number: int) -> None:
    """Seed listening content from the supplied Collins audio script and key."""
    test = await get_test(db, number)
    total_slots = 0

    async def part(order: int, groups: list[dict[str, Any]]) -> None:
        nonlocal total_slots
        section = await get_section(db, test.id, SectionType.LISTENING, order)
        await clear_section(db, section.id)
        group_order = 1
        part_slots = 0
        for item in groups:
            group_order, count = await put_group(
                db,
                section,
                group_order,
                item["type"],
                item["instruction"],
                item["entries"],
                shared=item.get("shared"),
            )
            part_slots += count
        total_slots += part_slots
        print(f"  Listening part {order}: {part_slots} scoring slots")

    def short(items: list[tuple[str, list[str], int]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        return [
            ({"prompt": prompt, "max_words": limit}, gap_answer_key(answers, max_words=limit))
            for prompt, answers, limit in items
        ]

    def mcqs(items: list[tuple[str, list[str], str]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        return [({"question": question, "options": options}, {"correct": answer}) for question, options, answer in items]

    def multi(question: str, options: list[str], answers: list[str]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        return [({"question": question, "options": options}, {"correct": answers})]

    if number == 3:
        form = {
            "variant": "form", "form_title": "Jamieson's Ltd — Job Application",
            "instruction_words": "NO MORE THAN THREE WORDS AND/OR A NUMBER", "max_words_per_gap": 3,
            "fields": [
                {"label": "Applicant's name", "type": "static", "value": "Tessa Murphy"},
                {"label": "Placement of job advertisement", "type": "gap_line", "segments": [gap("l1")]},
                {"label": "Post", "type": "gap_line", "segments": [gap("l2")]},
                {"label": "Degree in", "type": "gap_line", "segments": [gap("l3")]},
                {"label": "January–May — Role", "type": "gap_line", "segments": [gap("l4")]},
                {"label": "Responsibilities", "type": "gap_line", "segments": [txt("served customers and helped arrange "), gap("l5")]},
                {"label": "Period", "type": "gap_line", "segments": [gap("l6"), txt(": Summer school — social organiser")]},
                {"label": "Responsibilities", "type": "gap_line", "segments": [gap("l7"), txt(" and evening events")]},
                {"label": "Hobbies and interests", "type": "gap_line", "segments": [txt("Reading; going to "), gap("l8")]},
                {"label": "Possible starting date", "type": "gap_line", "segments": [gap("l9")]},
                {"label": "Unavailable on", "type": "gap_line", "segments": [gap("l10")]},
            ],
        }
        await part(1, [{"type": QuestionType.FORM_COMPLETION, "instruction": "Complete the form. Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.", "shared": form, "entries": gap_entries([
            ("l1", ["website"], 1), ("l2", ["retail assistant"], 2), ("l3", ["English and French"], 3), ("l4", ["sales assistant"], 2), ("l5", ["window displays"], 2), ("l6", ["June to August", "June-August"], 3), ("l7", ["planned trips"], 2), ("l8", ["dance classes"], 2), ("l9", ["7th June", "7 June"], 2), ("l10", ["Tuesdays"], 1),
        ])}])
        plan = {"variant": "notes", "title": "Marston Country Farm", "instruction_words": "NO MORE THAN TWO WORDS", "max_words_per_gap": 2,
            "sections": [{"heading": "", "items": [{"segments": [txt(f"{label}: "), gap(f"m{n}")]} for n, label in enumerate(["Toilets", "Goat shed", "Donkey rides", "Rabbit house", "Insect house", "Picnic area", "Gift shop"], 11)]}]}
        await part(2, [
                {"type": QuestionType.DIAGRAM_LABELING, "instruction": "Label the plan below. Write NO MORE THAN TWO WORDS for each answer.", "shared": {**plan, "image_url": "/media/images/practice_d_t3_listening_map.png?v=3"}, "entries": gap_entries([(f"m{n}", [answer], 2) for n, answer in zip(range(11,18), ["toilets", "goat shed", "donkey rides", "rabbit house", "insect house", "picnic area", "gift shop"])])},
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B or C.", "entries": mcqs([
                ("The duck pond", ["is quite shallow.", "often has people falling in.", "is closed to visitors due to heavy rain."], "A"),
                ("Visitors to the farm", ["should not handle animals before eating.", "often forget to wash their hands.", "should try to keep hand-wash stations clean."], "C"),
                ("Visitors needing first aid should", ["phone for help.", "speak to someone at the main desk.", "go to the first aiders near the farm."], "B"),
            ])},
        ])
        await part(3, [
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B or C.", "entries": mcqs([
                ("Work experience", ["is usually organised by the student.", "is a necessary part of the degree.", "sometimes takes place at the university."], "B"),
                ("Students will be paid if", ["they take time off in the summer.", "they are on placement for a year.", "they show they are responsible."], "B"),
                ("Companies offering work-experience placements", ["sometimes hold competitions.", "expect database and spreadsheet skills.", "often have more than one student applying."], "C"),
                ("Students attending an interview", ["should expect it to be formal.", "should prepare for it.", "should chat with the Careers Service first."], "B"),
            ])},
            {"type": QuestionType.MULTI_SELECT, "instruction": "Choose TWO letters, A–E.", "entries": multi("Which TWO things does the Careers Service help with?", ["A. identifying your strengths", "B. dealing with problems at the company", "C. supporting work-based assessments", "D. keeping a record of your experiences", "E. helping with academic work"], ["B", "D"])},
            {"type": QuestionType.SENTENCE_COMPLETION, "instruction": "Complete the summary. Write ONE WORD ONLY for each answer.", "entries": short([
                ("Your year in industry will confirm your choice of ...", ["career"], 1), ("It gives you a chance to ... the work you are interested in.", ["reconsider"], 1), ("A positive ... may lead to a job offer.", ["impression"], 1), ("You may make useful ... in the industry.", ["contacts"], 1),
            ])},
        ])
        methods = ["A. cows' cells", "B. goats' milk", "C. silkworms", "D. synthetic silk"]
        await part(4, [
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B or C.", "entries": mcqs([
                ("The substance that makes up spider silk", ["changes its form when it leaves the spider's body.", "consists of five different proteins.", "is commonly found in garden plants."], "A"),
                ("Spider silk", ["is similar in strength to steel.", "can stretch 30 times its length.", "is not affected by freezing temperatures."], "C"),
            ])},
            {"type": QuestionType.SHORT_ANSWER, "instruction": "Complete the sentences. Write NO MORE THAN TWO WORDS for each answer.", "entries": short([
                ("The ... used spider silk to treat people who were bleeding.", ["ancient Greeks"], 2), ("Indigenous Australians used it as ...", ["fishing lines"], 2), ("Scientists used it to grow human skin to treat ...", ["burn victims"], 2), ("Silk in car airbags may reduce the ... on the body.", ["impact"], 1),
            ])},
            {"type": QuestionType.MATCHING_FEATURES, "instruction": "Which method of producing silk matches each statement? Choose A–D.", "shared": choices(methods), "entries": lettered_entries([
                ("It could be used to help wounds heal.", "D"), ("It is stronger than a particular man-made material.", "A"), ("It needs no further work after the silk is spun.", "C"), ("It could produce large quantities of silk protein.", "B"),
            ])},
        ])
    else:
        form = {"variant": "form", "form_title": "Training day catering order", "instruction_words": "NO MORE THAN TWO WORDS AND/OR A NUMBER", "max_words_per_gap": 2, "fields": [
            {"label": "Event date", "type": "gap_line", "segments": [gap("t1")]}, {"label": "Food delivery time", "type": "gap_line", "segments": [gap("t2")]}, {"label": "Number of people", "type": "gap_line", "segments": [gap("t3")]}, {"label": "Buffet cost per person", "type": "gap_line", "segments": [gap("t4")]}, {"label": "Special dietary requirement", "type": "gap_line", "segments": [gap("t5")]}, {"label": "Contact person", "type": "gap_line", "segments": [gap("t6")]}, {"label": "Telephone extension", "type": "gap_line", "segments": [gap("t7")]},
        ]}
        await part(1, [
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B or C.", "entries": mcqs([
                ("Where will the food be served?", ["in the training room", "in the office", "in the main meeting room"], "C"), ("Why was breakfast not chosen?", ["staff prefer lunch", "the kitchen is unavailable", "the budget is insufficient"], "C"), ("Who needs to be included in the catering order?", ["the manager", "a visiting speaker", "the trainer"], "C"),
            ])},
            {"type": QuestionType.FORM_COMPLETION, "instruction": "Complete the form. Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.", "shared": form, "entries": gap_entries([
                ("t1", ["13th November", "13 November"], 2), ("t2", ["8.00", "8 am", "8 a.m."], 2), ("t3", ["15", "fifteen"], 1), ("t4", ["£3.25", "3.25"], 1), ("t5", ["dairy-free", "dairy free"], 2), ("t6", ["Beecham"], 1), ("t7", ["523"], 1),
            ])},
        ])
        await part(2, [{"type": QuestionType.NOTE_COMPLETION, "instruction": "Complete the leaflet. Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.", "shared": structure("notes", "Stay Safe During a Heatwave", 3, [
            [txt("Limit the amount of "), gap("h11"), txt(" entering rooms.")], [txt("Monitor your "), gap("h12")], [txt("Take a "), gap("h13")], [txt("The wrists and back of the neck are the body's "), gap("h14")], [txt("Replace nutrients lost through "), gap("h15")], [txt("Stay inside between "), gap("h16")], [txt("Use an "), gap("h17")], [txt("Wear clothes made from "), gap("h18")], [txt("Reduce effort during "), gap("h19")], [txt("Check on neighbours with "), gap("h20")],
        ]), "entries": gap_entries([( "h11", ["direct sunlight"], 2), ("h12", ["energy usage"], 2), ("h13", ["cool shower"], 2), ("h14", ["cooling points"], 2), ("h15", ["sweating"], 1), ("h16", ["11 to 3", "11 am to 3 pm", "11 a.m. to 3 p.m."], 5), ("h17", ["umbrella"], 1), ("h18", ["cotton or linen"], 3), ("h19", ["physical exercise"], 2), ("h20", ["health issues"], 2)])}])
        await part(3, [
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B or C.", "entries": mcqs([
                ("The student did not speak with Professor Collins because", ["she did not have time.", "she could not get an appointment.", "he is not around at the moment."], "C"), ("When doing assignments, many students", ["are surprised by how difficult they are to write.", "often fail to get the required grades.", "do not provide a full answer."], "C"), ("Words such as 'analyse', 'discuss' and 'evaluate'", ["each require a completely different response.", "often have the same meaning.", "can be difficult to understand."], "B"), ("The danger of some internet sources is that", ["the assignment may receive a lower grade.", "they are full of promotions and adverts.", "they are sometimes written by politicians."], "A"), ("Books on a reading list", ["express fewer opinions than the internet.", "are more critical of other authors.", "have been assessed by other experts."], "C"),
            ])},
            {"type": QuestionType.SENTENCE_COMPLETION, "instruction": "Complete the checklist. Write NO MORE THAN TWO WORDS for each answer.", "entries": short([
                ("Paragraphs should be ... and logically ordered.", ["well constructed", "well-constructed"], 2), ("Points should be ...", ["relevant"], 1), ("Check for ... and spelling.", ["typing mistakes"], 2), ("Check your ... are grammatically correct.", ["sentence structures"], 2), ("Check your ...", ["punctuation"], 1),
            ])},
        ])
        await part(4, [
            {"type": QuestionType.MULTI_SELECT, "instruction": "Choose TWO letters, A–E.", "entries": multi("Which TWO things can result from a lack of strength training?", ["A. No benefit from natural activities", "B. A person may not perform as well in their sport as they could", "C. An athlete can no longer practise", "D. A person cannot visit a gym", "E. Injuries will get worse"], ["B", "C"])},
            {"type": QuestionType.MCQ, "instruction": "Choose the correct letter, A, B or C.", "entries": mcqs([
                ("An injury caused by a fall", ["tends to be unexpected.", "needs to be dealt with urgently.", "is often caused by weak muscles."], "A"), ("Athletes who do more than one sport", ["place too much pressure on their bodies.", "are in particular need of strength training.", "avoid overworking one part of the body."], "C"), ("Injuries can be avoided", ["if an athlete makes fewer repetitive movements.", "if less-used muscles are exercised.", "if an athlete learns to keep their balance."], "B"), ("A strength-training programme", ["should also help you move more freely.", "will reduce daily aches and pains.", "is only suitable for particular sports."], "A"), ("What problem do older athletes face?", ["They eat a poorer diet.", "They cannot continue their chosen sport.", "They lose muscle mass."], "C"),
            ])},
            {"type": QuestionType.SENTENCE_COMPLETION, "instruction": "Complete the sentences. Write NO MORE THAN TWO WORDS for each answer.", "entries": short([
                ("Athletes may be less able to practise during the ...", ["winter months"], 2), ("Seeing improvements can help athletes develop a ...", ["positive attitude"], 2), ("Strength training can help athletes remain ... when sport is restricted.", ["motivated"], 1),
            ])},
        ])

    if total_slots != 40:
        raise SystemExit(f"expected 40 listening scoring slots, got {total_slots}")
    for order in range(1, 5):
        section = await get_section(db, test.id, SectionType.LISTENING, order)
        section.audio_url = AUDIO_URL.format(test=number, part=order)
    await db.commit()
    print(f"Listening Test {number}: 40 scoring slots")


async def seed_writing(db: AsyncSession, number: int) -> None:
    test = await get_test(db, number)
    section = await get_section(db, test.id, SectionType.WRITING, 20)
    await clear_section(db, section.id)
    group = QuestionGroup(id=uuid.uuid4(), section_id=section.id, order=1, question_type=QuestionType.ESSAY.value, instruction="")
    db.add(group)
    await db.flush()

    if number == 3:
        task1 = "The line graph below shows demographic trends in Scotland.\n\nSummarise the information by selecting and reporting the main features."
        task2_statement = "Given the increase in the consumption of fast food amongst young people, the school curriculum should place far more emphasis on teaching the principles of good nutrition and the skills necessary to maintain a healthy diet."
        task2_question = "To what extent do you agree or disagree with this opinion?"
        task2_type = "opinion"
    else:
        task1 = "The diagram below shows a recommended recruitment process for new staff.\n\nSummarise the information by selecting and reporting the main features."
        task2_statement = "Popular social media bloggers and vloggers have become a significant influence for those who follow them."
        task2_question = "How do social media influencers impact on an audience's purchasing decisions? Is this a positive or negative development?"
        task2_type = "double_question"

    task1_instruction = get_default_instruction(1)
    db.add(Question(
        id=uuid.uuid4(), section_id=section.id, question_group_id=group.id, order=1,
        question_type=QuestionType.ESSAY, content={"task_description": task1, "task_instruction": task1_instruction, "prompt": f"{task1}\n\n{task1_instruction}"},
        answer_key=None, task_number=1, min_words=150,
        image_url=f"{CHART_IMAGE_URL.format(test=number)}?v=3", essay_type=None,
    ))
    task2_instruction = get_default_instruction(2, task2_type)
    task2_description = f"{task2_statement}\n\n{task2_question}"
    db.add(Question(
        id=uuid.uuid4(), section_id=section.id, question_group_id=group.id, order=2,
        question_type=QuestionType.ESSAY,
        content={"task_statement": task2_statement, "task_question": task2_question, "use_custom_question": True, "task_description": task2_description, "task_instruction": task2_instruction, "prompt": f"{task2_description}\n\n{task2_instruction}"},
        answer_key=None, task_number=2, min_words=250, image_url=None, essay_type=task2_type,
    ))
    await db.commit()
    print(f"Writing Test {number}: two tasks")


async def seed_speaking(db: AsyncSession, number: int) -> None:
    test = await get_test(db, number)
    if number == 3:
        parts = [
            (30, {"part": 1, "topic": "Friends and the future", "questions": ["How often do you see your friends?", "What do you like to do when you meet up with friends?", "Do you still have friends from when you were young?", "What qualities do you think make a good friend?", "Do you think you will always live in the same town or city you live in now?", "Do you think your local area will change much over the next few years?", "How do you think your life might be different in 10 years' time?", "Are you optimistic that we will solve the environmental problems we face today?"]}),
            (31, {"part": 2, "cue_card": {"topic": "a building you have seen that made a big impression on you", "bullets": ["what the building was", "when you went there", "why you went there"], "follow_up": "and say what it is about the building that you liked"}}),
            (32, {"part": 3, "topics": ["Buildings"], "questions": ["Do you think it's important to save old historic buildings?", "Are modern buildings as impressive as those built in the past?", "What kind of buildings are most memorable?", "To what extent do the buildings in a city give it its character?", "Why do tourists tend to spend so much time visiting important buildings?", "What makes a house a home?"]}),
        ]
    else:
        parts = [
            (30, {"part": 1, "topic": "Books, films and travelling", "questions": ["What kind of books or films do you like?", "Do you prefer reading digital or traditional books?", "How often do you go to the cinema?", "Would you prefer to spend an evening reading a book or going to the cinema?", "What form of transport do you use most often?", "Is there any type of transport that you don't like?", "What's the public transport system like in your country?", "Is there anything about travelling around your local area that you would change?"]}),
            (31, {"part": 2, "cue_card": {"topic": "a present you were given that you particularly liked", "bullets": ["what the present was", "why you received it", "who gave it to you"], "follow_up": "and say what it is about the present that you liked"}}),
            (32, {"part": 3, "topics": ["Presents"], "questions": ["Do you think it's better to give rather than receive?", "What type of gifts are particularly special for the person receiving them?", "Is giving someone money for a birthday present more thoughtful than buying a gift?", "Is it important how much we spend on a gift?", "Are certain ages easier to buy presents for than others?", "Why might it be good for a company to give a customer a free gift?"]}),
        ]
    for order, content in parts:
        section = await get_section(db, test.id, SectionType.SPEAKING, order)
        section.title = f"Part {order - 29}"
        await clear_section(db, section.id)
        group = QuestionGroup(id=uuid.uuid4(), section_id=section.id, order=1, question_type=QuestionType.SPEAKING_PART.value, instruction="")
        db.add(group)
        await db.flush()
        db.add(Question(id=uuid.uuid4(), section_id=section.id, question_group_id=group.id, order=1, question_type=QuestionType.SPEAKING_PART, content=content, answer_key=None))
    await db.commit()
    print(f"Speaking Test {number}: three parts")


async def main(number: int, skill: str) -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        if skill == "reading":
            await seed_reading(db, number)
        elif skill == "listening":
            await seed_listening(db, number)
        elif skill == "writing":
            await seed_writing(db, number)
        elif skill == "speaking":
            await seed_speaking(db, number)
        else:
            raise SystemExit(f"skill not authored yet: {skill}")
    await engine.dispose()


if __name__ == "__main__":
    raise SystemExit("Use seed_practice_d_tN_reading.py / _listening.py wrappers")
