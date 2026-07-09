"""Seed Cambridge IELTS 1 · Test 1 — Listening (S1-S4) + Reading (P1-P3).

Listening MP3s are copied from:
    backend/Ielts_tests/IELTS_1/Test 1/test 1, section {1..4}.mp3

Reading passage texts are loaded from (place these files yourself):
    backend/Ielts_tests/IELTS_1/Test 1/passage_1.txt
    backend/Ielts_tests/IELTS_1/Test 1/passage_2.txt
    backend/Ielts_tests/IELTS_1/Test 1/passage_3.txt

If a passage .txt file is missing, the section is created with an empty passage
and you can paste the text later via the admin UI (Section Edit → Passage field).

Idempotent: re-runs safely update existing rows in place.
Deterministic UUIDs: all IDs are stable across re-runs and environments.

Usage:
    cd backend
    venv\\Scripts\\python.exe -m scripts.seed_cambridge_1_test_1
"""

import asyncio
import logging
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.section import Section, SectionType
from app.models.test import Test

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
MEDIA_AUDIO_DIR = BACKEND_DIR / "media" / "audio"
MEDIA_IMAGES_DIR = BACKEND_DIR / "media" / "images"
IELTS1_DIR = BACKEND_DIR / "Ielts_tests" / "IELTS_1" / "Test 1"

# Writing Task 1 chart image
WRITING_IMAGE_SRC = IELTS1_DIR / "Writing_Task_1.jpg"
WRITING_IMAGE_FILENAME = "cambridge1_test1_writing_task1.jpg"
WRITING_IMAGE_URL = f"/media/images/{WRITING_IMAGE_FILENAME}"

# (source_filename, stable_dest_filename) keyed by section number
_AUDIO: dict[int, tuple[str, str]] = {
    1: ("test 1, section 1.mp3", "cambridge1_test1_listening_s1.mp3"),
    2: ("test 1, section 2.mp3", "cambridge1_test1_listening_s2.mp3"),
    3: ("test 1, section 3.mp3", "cambridge1_test1_listening_s3.mp3"),
    4: ("test 1, section 4.mp3", "cambridge1_test1_listening_s4.mp3"),
}


def _audio_url(section_num: int) -> str:
    return f"/media/audio/{_AUDIO[section_num][1]}"


def _copy_audio(section_num: int) -> None:
    """Copy section MP3 to media/audio/ with a stable filename."""
    src_name, dest_name = _AUDIO[section_num]
    src = IELTS1_DIR / src_name
    if not src.exists():
        raise FileNotFoundError(
            f"MP3 source not found: {src}\n"
            f"Place '{src_name}' in backend/Ielts_tests/IELTS_1/Test 1/"
        )
    MEDIA_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    dest = MEDIA_AUDIO_DIR / dest_name
    if dest.exists():
        log.info("  Audio S%d already exists — skipping copy (%s)", section_num, dest_name)
    else:
        shutil.copy2(src, dest)
        log.info("  Copied S%d audio  %d bytes → %s", section_num, dest.stat().st_size, dest_name)


def _copy_writing_image() -> None:
    """Copy Writing Task 1 chart to media/images/ with a stable filename."""
    if not WRITING_IMAGE_SRC.exists():
        log.warning(
            "  WARNING: %s not found. Task 1 will have no image.",
            WRITING_IMAGE_SRC.name,
        )
        return
    MEDIA_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    dest = MEDIA_IMAGES_DIR / WRITING_IMAGE_FILENAME
    if dest.exists():
        log.info("  Writing Task 1 image already exists — skipping copy (%s)", WRITING_IMAGE_FILENAME)
    else:
        shutil.copy2(WRITING_IMAGE_SRC, dest)
        log.info("  Copied Writing Task 1 image  %d bytes → %s", dest.stat().st_size, WRITING_IMAGE_FILENAME)


def _load_passage(passage_num: int) -> str | None:
    """Load passage text from .txt file. Returns None if file not found."""
    txt_path = IELTS1_DIR / f"passage_{passage_num}.txt"
    if not txt_path.exists():
        log.warning(
            "  WARNING: %s not found. Reading P%d will have empty passage. "
            "Add text via admin UI (Section Edit → Passage field) or create the file and re-run.",
            txt_path.name, passage_num,
        )
        return None
    text = txt_path.read_text(encoding="utf-8").strip()
    log.info("  Loaded passage_%d.txt  (%d chars)", passage_num, len(text))
    return text


# ── Deterministic IDs ─────────────────────────────────────────────────────────

_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # uuid.NAMESPACE_DNS
TEST_UUID = uuid.uuid5(_NS, "cambridge-ielts-1.test-1")

SECTION_UUID = {
    n: uuid.uuid5(TEST_UUID, f"listening-section-{n}") for n in range(1, 5)
}

READING_SECTION_UUID = {
    n: uuid.uuid5(TEST_UUID, f"reading-passage-{n}") for n in range(1, 4)
}

WRITING_SECTION_UUID = uuid.uuid5(TEST_UUID, "writing-section")

# ── Section durations (minutes) ───────────────────────────────────────────────
LISTENING_DURATION = {1: 10, 2: 8, 3: 10, 4: 10}
READING_DURATION = 20  # per passage

# ══════════════════════════════════════════════════════════════════════════════
# LISTENING SECTION DATA
# ══════════════════════════════════════════════════════════════════════════════

SECTION1_FORM = {
    "title": "PERSONAL DETAILS FORM",
    "instruction": "Complete the form. Write NO MORE THAN THREE WORDS for each answer.",
    "items": [
        [{"text": "Name:    Mary "}, {"gap": "6"}],
        [{"text": "Address: Flat 2, "}, {"gap": "7"}, {"text": ", "}, {"gap": "8"}, {"text": " Road, Canterbury"}],
        [{"text": "Telephone: "}, {"gap": "9"}],
        [{"text": "Estimated value of lost item:  £"}, {"gap": "10"}],
    ],
}

SECTION1_QUESTIONS: list[dict] = [
    {
        "order": 1,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 1,
            "section_title": "Lost property",
            "instruction": "Circle the appropriate letter.",
            "question": "What does her briefcase look like?",
            "options": [
                "A. Soft leather with two gold buckles at the front",
                "B. Hard leather with a combination lock at the top",
                "C. Soft leather with a zip fastening at the top",
                "D. Canvas bag with metal clasps at the front",
            ],
        },
        "answer_key": {"correct": "A. Soft leather with two gold buckles at the front"},
    },
    {
        "order": 2,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 1,
            "instruction": "Circle the appropriate letter.",
            "question": "Which option correctly shows the distinguishing features of the briefcase?",
            "options": [
                "A. Brand name top-right on back; no visible scratch",
                "B. Brand name bottom-left on back; no visible scratch",
                "C. Brand name bottom-left on back; scratch directly above it",
                "D. Scratch at the top; brand name in the centre of the back",
            ],
        },
        "answer_key": {"correct": "C. Brand name bottom-left on back; scratch directly above it"},
    },
    {
        "order": 3,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 1,
            "instruction": "Circle the appropriate letter.",
            "question": "What did she have inside her briefcase?",
            "options": [
                "A. wallet, pens and novel",
                "B. papers and wallet",
                "C. pens and novel",
                "D. papers, pens and novel",
            ],
        },
        "answer_key": {"correct": "D. papers, pens and novel"},
    },
    {
        "order": 4,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 1,
            "instruction": "Circle the appropriate letter.",
            "question": "Where was she standing when she lost her briefcase?",
            "options": [
                "A. At a bus stop",
                "B. Outside a taxi rank",
                "C. On a train platform",
                "D. On a tram platform",
            ],
        },
        "answer_key": {"correct": "D. On a tram platform"},
    },
    {
        "order": 5,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 1,
            "instruction": "Circle the appropriate letter.",
            "question": "What time was it when she lost her briefcase?",
            "options": ["A. 5.00", "B. 5.15", "C. 5.30", "D. 5.45"],
        },
        "answer_key": {"correct": "C. 5.30"},
    },
    {
        "order": 6,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 1, "notes_id": "s1_personal_details", "gap_key": "6", "notes": SECTION1_FORM,
                    "instruction": "Complete the form. Write NO MORE THAN THREE WORDS for each answer."},
        "answer_key": {"correct": "Prescott"},
    },
    {
        "order": 7,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 1, "notes_id": "s1_personal_details", "gap_key": "7", "notes": SECTION1_FORM},
        "answer_key": {"correct": "41"},
    },
    {
        "order": 8,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 1, "notes_id": "s1_personal_details", "gap_key": "8", "notes": SECTION1_FORM},
        "answer_key": {"correct": "Fountain"},
    },
    {
        "order": 9,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 1, "notes_id": "s1_personal_details", "gap_key": "9", "notes": SECTION1_FORM},
        "answer_key": {"correct": "752239"},
    },
    {
        "order": 10,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 1, "notes_id": "s1_personal_details", "gap_key": "10", "notes": SECTION1_FORM},
        "answer_key": {"correct": ["65", "65"]},
    },
]

SECTION2_HEADLINES_PAIR = {
    "pair_question": "Tick the THREE other items which are mentioned in the news headlines.",
    "options": [
        "A. Rivers flood in the north",
        "C. Nurses on strike in Melbourne",
        "D. Passengers rescued from ship",
        "E. Passengers rescued from plane",
        "F. Bus and train drivers national strike threat",
        "G. Teachers demand more pay",
        "H. New uniform for QANTAS staff",
        "I. National airports under new management",
    ],
    "instruction": "Choose THREE letters, A-I.",
}

SECTION2_NOTES = {
    "title": "News summary",
    "instruction": "Complete the notes below. Write NO MORE THAN THREE WORDS for each answer.",
    "items": [
        [{"text": "Government to give $"}, {"gap": "14"}, {"text": " to help farmers."}],
        [{"text": "Money was originally for Sydney's "}, {"gap": "15"}, {"text": " but has been re-allocated."}],
        [{"text": "Farmers say the money is "}, {"gap": "16"}, {"text": "."}],
        [{"text": "Aeroplane carried a group of "}, {"gap": "17"}, {"text": "."}],
        [{"text": "It had to land "}, {"gap": "18"}, {"text": " minutes after take-off."}],
        [{"text": "Passengers were rescued by "}, {"gap": "19"}, {"text": "."}],
        [{"text": "Passengers thanked the "}, {"gap": "20"}, {"text": " for saving their lives."}],
        [{"text": "They lost their "}, {"gap": "21"}, {"text": "."}],
    ],
}

SECTION2_QUESTIONS: list[dict] = [
    {
        "order": 11,
        "question_type": QuestionType.MULTI_SELECT,
        "content": {"part": 2, "pair_id": "s2_headlines", **SECTION2_HEADLINES_PAIR},
        "answer_key": {"correct": "E. Passengers rescued from plane"},
    },
    {
        "order": 12,
        "question_type": QuestionType.MULTI_SELECT,
        "content": {"part": 2, "pair_id": "s2_headlines", **SECTION2_HEADLINES_PAIR},
        "answer_key": {"correct": "F. Bus and train drivers national strike threat"},
    },
    {
        "order": 13,
        "question_type": QuestionType.MULTI_SELECT,
        "content": {"part": 2, "pair_id": "s2_headlines", **SECTION2_HEADLINES_PAIR},
        "answer_key": {"correct": "H. New uniform for QANTAS staff"},
    },
    {
        "order": 14,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "14", "notes": SECTION2_NOTES,
                    "instruction": "Complete the notes below. Write NO MORE THAN THREE WORDS for each answer."},
        "answer_key": {"correct": ["250 million", "$250 million", "250,000,000"]},
    },
    {
        "order": 15,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "15", "notes": SECTION2_NOTES},
        "answer_key": {"correct": ["roads", "road system"]},
    },
    {
        "order": 16,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "16", "notes": SECTION2_NOTES},
        "answer_key": {"correct": "too late"},
    },
    {
        "order": 17,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "17", "notes": SECTION2_NOTES},
        "answer_key": {"correct": ["school children", "boys", "schoolchildren"]},
    },
    {
        "order": 18,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "18", "notes": SECTION2_NOTES},
        "answer_key": {"correct": ["3", "three"]},
    },
    {
        "order": 19,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "19", "notes": SECTION2_NOTES},
        "answer_key": {"correct": ["boats", "pleasure craft", "boats and pleasure craft"]},
    },
    {
        "order": 20,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "20", "notes": SECTION2_NOTES},
        "answer_key": {"correct": "pilot"},
    },
    {
        "order": 21,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 2, "notes_id": "s2_news", "gap_key": "21", "notes": SECTION2_NOTES},
        "answer_key": {"correct": ["instruments", "musical instruments"]},
    },
]

SECTION3_NOTES = {
    "title": "Course requirements",
    "instruction": "Complete the notes below using NO MORE THAN THREE WORDS.",
    "items": [
        {"heading": "Tutorial paper"},
        [{"text": "A piece of work on a given topic. Students must:"}],
        [{"text": "  \u2022 "}, {"gap": "26"}, {"text": " for 25 minutes"}],
        [{"text": "  \u2022 "}, {"gap": "27"}],
        [{"text": "  \u2022 give to lecturer for marking"}],
        {"heading": "Essay topic"},
        [{"text": "Usually "}, {"gap": "28"}],
        {"heading": "Type of exam"},
        [{"gap": "29"}],
        {"heading": "Library"},
        [{"text": "Important books are in "}, {"gap": "30"}, {"text": "."}],
        {"heading": "Focus of course"},
        [{"text": "Focus on "}, {"gap": "31"}, {"text": "."}],
    ],
}

SECTION3_QUESTIONS: list[dict] = [
    {
        "order": 22,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 3, "section_title": "Economics course information",
            "instruction": "Circle the appropriate letter.",
            "question": "The orientation meeting",
            "options": ["A. took place recently.", "B. took place last term.", "C. will take place tomorrow.", "D. will take place next week."],
        },
        "answer_key": {"correct": "A. took place recently."},
    },
    {
        "order": 23,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 3, "instruction": "Circle the appropriate letter.",
            "question": "Attendance at lectures is",
            "options": ["A. optional after 4 pm.", "B. closely monitored.", "C. difficult to enforce.", "D. sometimes unnecessary."],
        },
        "answer_key": {"correct": "B. closely monitored."},
    },
    {
        "order": 24,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 3, "instruction": "Circle the appropriate letter.",
            "question": "Tutorials take place",
            "options": ["A. every morning.", "B. twice a week.", "C. three mornings a week.", "D. three afternoons a week."],
        },
        "answer_key": {"correct": "C. three mornings a week."},
    },
    {
        "order": 25,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 3, "instruction": "Circle the appropriate letter.",
            "question": "The lecturer's name is",
            "options": ["A. Roberts.", "B. Rawson.", "C. Rogers.", "D. Robertson."],
        },
        "answer_key": {"correct": "A. Roberts."},
    },
    {
        "order": 26,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 3, "notes_id": "s3_course", "gap_key": "26", "notes": SECTION3_NOTES,
                    "instruction": "Complete the notes below using NO MORE THAN THREE WORDS."},
        "answer_key": {"correct": ["talk", "give a talk"]},
    },
    {
        "order": 27,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 3, "notes_id": "s3_course", "gap_key": "27", "notes": SECTION3_NOTES},
        "answer_key": {"correct": "write up work"},
    },
    {
        "order": 28,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 3, "notes_id": "s3_course", "gap_key": "28", "notes": SECTION3_NOTES},
        "answer_key": {"correct": "can choose"},
    },
    {
        "order": 29,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 3, "notes_id": "s3_course", "gap_key": "29", "notes": SECTION3_NOTES},
        "answer_key": {"correct": "open book"},
    },
    {
        "order": 30,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 3, "notes_id": "s3_course", "gap_key": "30", "notes": SECTION3_NOTES},
        "answer_key": {"correct": "closed reserve"},
    },
    {
        "order": 31,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 3, "notes_id": "s3_course", "gap_key": "31", "notes": SECTION3_NOTES},
        "answer_key": {"correct": ["vocational subjects", "vocational", "work", "employment"]},
    },
]

SECTION4_NOTES = {
    "title": "Course details — Arts and Social Sciences",
    "instruction": "Complete the notes. Write NO MORE THAN THREE WORDS for each answer.",
    "items": [
        [{"text": "First semester subjects: psychology, sociology, "}, {"gap": "34"}, {"text": "."}],
        [{"text": "Students may have problems with "}, {"gap": "35"}, {"text": " and "}, {"gap": "36"}, {"text": "."}],
    ],
}

SECTION4_QUESTIONS: list[dict] = [
    {
        "order": 32,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 4, "section_title": "University orientation lecture",
            "instruction": "Circle the appropriate letter.",
            "question": "The speaker works within the Faculty of",
            "options": ["A. Science and Technology.", "B. Arts and Social Sciences.", "C. Architecture.", "D. Law."],
        },
        "answer_key": {"correct": "B. Arts and Social Sciences."},
    },
    {
        "order": 33,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 4, "instruction": "Circle the appropriate letter.",
            "question": "The Faculty consists firstly of",
            "options": ["A. subjects.", "B. degrees.", "C. divisions.", "D. departments."],
        },
        "answer_key": {"correct": "C. divisions."},
    },
    {
        "order": 34,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 4, "notes_id": "s4_course", "gap_key": "34", "notes": SECTION4_NOTES,
                    "instruction": "Complete the notes. Write NO MORE THAN THREE WORDS for each answer."},
        "answer_key": {"correct": "history and economics"},
    },
    {
        "order": 35,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 4, "notes_id": "s4_course", "gap_key": "35", "notes": SECTION4_NOTES},
        "answer_key": {"correct": ["deadlines", "meeting deadlines", "deadlines for essays"]},
    },
    {
        "order": 36,
        "question_type": QuestionType.GAP_FILL,
        "content": {"part": 4, "notes_id": "s4_course", "gap_key": "36", "notes": SECTION4_NOTES},
        "answer_key": {"correct": "attendance"},
    },
    {
        "order": 37,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 4, "instruction": "Circle the appropriate letter.",
            "question": "The speaker says students can visit her",
            "options": ["A. every morning.", "B. some mornings.", "C. mornings only.", "D. Friday morning."],
        },
        "answer_key": {"correct": "B. some mornings."},
    },
    {
        "order": 38,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 4, "instruction": "Circle the appropriate letter.",
            "question": "According to the speaker, a tutorial",
            "options": ["A. is a type of lecture.", "B. is less important than a lecture.", "C. provides a chance to share views.", "D. provides an alternative to groupwork."],
        },
        "answer_key": {"correct": "C. provides a chance to share views."},
    },
    {
        "order": 39,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 4, "instruction": "Circle the appropriate letter.",
            "question": "When writing essays, the speaker advises the students to",
            "options": ["A. research their work well.", "B. name the books they have read.", "C. share work with their friends.", "D. avoid using other writers' ideas."],
        },
        "answer_key": {"correct": "B. name the books they have read."},
    },
    {
        "order": 40,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 4, "instruction": "Circle the appropriate letter.",
            "question": "The speaker thinks that plagiarism is",
            "options": ["A. a common problem.", "B. an acceptable risk.", "C. a minor concern.", "D. a serious offence."],
        },
        "answer_key": {"correct": "D. a serious offence."},
    },
    {
        "order": 41,
        "question_type": QuestionType.MCQ,
        "content": {
            "part": 4, "instruction": "Circle the appropriate letter.",
            "question": "The speaker's aims are to",
            "options": [
                "A. introduce students to university expectations.",
                "B. introduce students to the members of staff.",
                "C. warn students about the difficulties of studying.",
                "D. guide students round the university.",
            ],
        },
        "answer_key": {"correct": "A. introduce students to university expectations."},
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# READING PASSAGE 1 DATA
# Source: Cambridge IELTS 1, Test 1, Reading Passage 1
# "A spark, a flint: How fire leapt to life"
# Answer keys (PDF p.131): Q1-8 word-bank summary; Q9-15 match types
# ══════════════════════════════════════════════════════════════════════════════

# Q1-8: Summary completion using a word bank
# The summary "EARLY FIRE-LIGHTING METHODS" is a compound notes_card.
# Word bank (20 words, use each at most once):
#   Mexicans, random, rotating, despite, preserve, realising, sunlight, lacking,
#   heavenly, percussion, chance, friction, unaware, without, make, heating, Eskimos,
#   surprised, until, smoke
PASSAGE1_SUMMARY = {
    "title": "EARLY FIRE-LIGHTING METHODS",
    "instruction": (
        "Complete the summary below. Choose your answers from the word box and write them in the spaces. "
        "There are more words than spaces so you will not use them all.\n"
        "Word box: Mexicans | rotating | despite | preserve | realising | sunlight | lacking | "
        "percussion | chance | friction | unaware | without | make | heating | Eskimos | until | smoke"
    ),
    "items": [
        [{"text": "Primitive societies saw fire as a divine gift. They tried to "}, {"gap": "1"}, {"text": " burning logs or charcoal,"}],
        [{"gap": "2"}, {"text": " that they could create fire themselves."}],
        [{"text": "It is suspected that the first man-made flames were produced by "}],
        [{"gap": "3"}, {"text": "."}],
        [{"text": "The very first fire-lighting methods involved the creation of "}],
        [{"gap": "4"}, {"text": " by, for example, rapidly "}],
        [{"gap": "5"}, {"text": " a wooden stick in a round hole."}],
        [{"text": "The use of "}, {"gap": "6"}, {"text": " or persistent chipping was also widespread in Europe and among other peoples such as the Chinese and "}],
        [{"gap": "7"}, {"text": ". European practice of this method continued until the 1850s "}],
        [{"gap": "8"}, {"text": " the discovery of phosphorus some years earlier."}],
    ],
}

# Q9-15: Match description to type of match (one compound MATCHING question)
# Answer keys: Q9=F, Q10=D, Q11=E, Q12=C, Q13=G, Q14=A, Q15=C
PASSAGE1_QUESTIONS: list[dict] = [
    # Q1-Q8 — summary completion (word bank)
    {
        "order": 1,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "1", "notes": PASSAGE1_SUMMARY,
                    "instruction": "Complete the summary. Choose from the word box."},
        "answer_key": {"correct": "preserve"},
    },
    {
        "order": 2,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "2", "notes": PASSAGE1_SUMMARY},
        "answer_key": {"correct": "unaware"},
    },
    {
        "order": 3,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "3", "notes": PASSAGE1_SUMMARY},
        "answer_key": {"correct": "chance"},
    },
    {
        "order": 4,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "4", "notes": PASSAGE1_SUMMARY},
        "answer_key": {"correct": "friction"},
    },
    {
        "order": 5,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "5", "notes": PASSAGE1_SUMMARY},
        "answer_key": {"correct": "rotating"},
    },
    {
        "order": 6,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "6", "notes": PASSAGE1_SUMMARY},
        "answer_key": {"correct": "percussion"},
    },
    {
        "order": 7,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "7", "notes": PASSAGE1_SUMMARY},
        "answer_key": {"correct": "Eskimos"},
    },
    {
        "order": 8,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p1_summary", "gap_key": "8", "notes": PASSAGE1_SUMMARY},
        "answer_key": {"correct": "despite"},
    },
    # Q9-15 — match description to type of match (compound MATCHING, order=9)
    {
        "order": 9,
        "question_type": QuestionType.MATCHING,
        "content": {
            "instruction": (
                "Questions 9-15. Look at the following notes about the matches described in Reading Passage 1. "
                "Decide which type of match (A-H) corresponds with each description. "
                "NB There are more matches than descriptions so you will not use them all. "
                "You may use any match more than once."
            ),
            "left": [
                "9. made using a less poisonous type of phosphorus",
                "10. identical to a previous type of match",
                "11. caused a deadly illness",
                "12. first to look like modern matches",
                "13. first matches used for advertising",
                "14. relied on an airtight glass container",
                "15. made with the help of an army design",
            ],
            "right": [
                "A. the Ethereal Match",
                "B. the Instantaneous Lightbox",
                "C. Congreves",
                "D. Lucifers",
                "E. the first strike-anywhere match",
                "F. Lundstrom's safety match",
                "G. book matches",
                "H. waterproof matches",
            ],
        },
        "answer_key": {
            "correct": {
                "9. made using a less poisonous type of phosphorus": "F. Lundstrom's safety match",
                "10. identical to a previous type of match": "D. Lucifers",
                "11. caused a deadly illness": "E. the first strike-anywhere match",
                "12. first to look like modern matches": "C. Congreves",
                "13. first matches used for advertising": "G. book matches",
                "14. relied on an airtight glass container": "A. the Ethereal Match",
                "15. made with the help of an army design": "C. Congreves",
            }
        },
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# READING PASSAGE 2 DATA
# Source: Cambridge IELTS 1, Test 1, Reading Passage 2
# "Zoo conservation programmes"
# Answer keys (PDF p.132): Q16-22 YES/NO/NG; Q23-25 MCQ; Q26-28 choose 3 factors
# ══════════════════════════════════════════════════════════════════════════════

_YES_NO_NG_INSTRUCTION = (
    "Do the following statements agree with the views of the writer in Reading Passage 2? "
    "Choose YES if the statement agrees with the writer, "
    "NO if the statement contradicts the writer, "
    "NOT GIVEN if it is impossible to say what the writer thinks about this."
)

ZOO_FACTORS_PAIR = {
    "pair_question": (
        "The writer mentions a number of factors which lead him to doubt the value of the WZCS document. "
        "Which THREE of the following factors are mentioned?"
    ),
    "options": [
        "A. the number of unregistered zoos in the world",
        "B. the lack of money in developing countries",
        "C. the actions of the Isle of Wight local council",
        "D. the failure of the WZCS to examine the standards of the 'core zoos'",
        "E. the unrealistic aim of the WZCS in view of the number of species 'saved' to date",
        "F. the policies of WZCS zoo managers",
    ],
    "instruction": "Choose THREE letters, A-F.",
}

PASSAGE2_QUESTIONS: list[dict] = [
    # Q16-22 — YES / NO / NOT GIVEN (writer's views)
    {
        "order": 16,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": _YES_NO_NG_INSTRUCTION,
            "question": "London Zoo's advertisements are dishonest.",
            "options": ["YES", "NO", "NOT GIVEN"],
        },
        "answer_key": {"correct": "YES"},
    },
    {
        "order": 17,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": _YES_NO_NG_INSTRUCTION,
            "question": "Zoos made an insignificant contribution to conservation up until 30 years ago.",
            "options": ["YES", "NO", "NOT GIVEN"],
        },
        "answer_key": {"correct": "YES"},
    },
    {
        "order": 18,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": _YES_NO_NG_INSTRUCTION,
            "question": "The WZCS document is not known in Eastern Europe.",
            "options": ["YES", "NO", "NOT GIVEN"],
        },
        "answer_key": {"correct": "NOT GIVEN"},
    },
    {
        "order": 19,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": _YES_NO_NG_INSTRUCTION,
            "question": "Zoos in the WZCS select list were carefully inspected.",
            "options": ["YES", "NO", "NOT GIVEN"],
        },
        "answer_key": {"correct": "NO"},
    },
    {
        "order": 20,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": _YES_NO_NG_INSTRUCTION,
            "question": "No-one knew how the animals were being treated at Robin Hill Adventure Park.",
            "options": ["YES", "NO", "NOT GIVEN"],
        },
        "answer_key": {"correct": "NO"},
    },
    {
        "order": 21,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": _YES_NO_NG_INSTRUCTION,
            "question": "Colin Tudge was dissatisfied with the treatment of animals at London Zoo.",
            "options": ["YES", "NO", "NOT GIVEN"],
        },
        "answer_key": {"correct": "NOT GIVEN"},
    },
    {
        "order": 22,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": _YES_NO_NG_INSTRUCTION,
            "question": "The number of successful zoo conservation programmes is unsatisfactory.",
            "options": ["YES", "NO", "NOT GIVEN"],
        },
        "answer_key": {"correct": "YES"},
    },
    # Q23-25 — MCQ
    {
        "order": 23,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": "Choose the appropriate letters A-D.",
            "question": "What were the objectives of the WZCS document?",
            "options": [
                "A. to improve the calibre of zoos world-wide",
                "B. to identify zoos suitable for conservation practice",
                "C. to provide funds for zoos in underdeveloped countries",
                "D. to list the endangered species of the world",
            ],
        },
        "answer_key": {"correct": "B. to identify zoos suitable for conservation practice"},
    },
    {
        "order": 24,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": "Choose the appropriate letters A-D.",
            "question": "Why does the writer refer to Robin Hill Adventure Park?",
            "options": [
                "A. to support the Isle of Wight local council",
                "B. to criticise the 1981 Zoo Licensing Act",
                "C. to illustrate a weakness in the WZCS document",
                "D. to exemplify the standards in AAZPA zoos",
            ],
        },
        "answer_key": {"correct": "C. to illustrate a weakness in the WZCS document"},
    },
    {
        "order": 25,
        "question_type": QuestionType.MCQ,
        "content": {
            "instruction": "Choose the appropriate letters A-D.",
            "question": "What word best describes the writer's response to Colin Tudge's prediction on captive breeding programmes?",
            "options": ["A. disbelieving", "B. impartial", "C. prejudiced", "D. accepting"],
        },
        "answer_key": {"correct": "A. disbelieving"},
    },
    # Q26-28 — choose THREE factors (MULTI_SELECT)
    {
        "order": 26,
        "question_type": QuestionType.MULTI_SELECT,
        "content": {"pair_id": "p2_factors", **ZOO_FACTORS_PAIR},
        "answer_key": {"correct": "A. the number of unregistered zoos in the world"},
    },
    {
        "order": 27,
        "question_type": QuestionType.MULTI_SELECT,
        "content": {"pair_id": "p2_factors", **ZOO_FACTORS_PAIR},
        "answer_key": {"correct": "D. the failure of the WZCS to examine the standards of the 'core zoos'"},
    },
    {
        "order": 28,
        "question_type": QuestionType.MULTI_SELECT,
        "content": {"pair_id": "p2_factors", **ZOO_FACTORS_PAIR},
        "answer_key": {"correct": "E. the unrealistic aim of the WZCS in view of the number of species 'saved' to date"},
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# READING PASSAGE 3 DATA
# Source: Cambridge IELTS 1, Test 1, Reading Passage 3
# "Architecture — Reaching for the Sky"
# Answer keys (PDF p.132-133): Q29-35 table completion; Q36-40 match causes/effects
# ══════════════════════════════════════════════════════════════════════════════

PASSAGE3_TABLE = {
    "title": "Architectural periods (Reading Passage 3)",
    "instruction": "Complete the table below. Write NO MORE THAN THREE WORDS for each answer.",
    "items": [
        {"heading": "Period | Style | Materials | Characteristics"},
        [{"text": "Before 18th century | traditional | "}, {"gap": "29"}, {"text": " | traditional techniques"}],
        [{"text": "1920s | introduction of "}, {"gap": "30"}, {"text": " | steel, glass & concrete | exploration of latest technology"}],
        [{"text": "1930s\u20131950s | "}, {"gap": "31"}, {"text": " | new materials | geometric forms"}],
        [{"text": "1960s | decline of Modernism | pre-fabricated sections | "}, {"gap": "32"}],
        [{"text": "1970s | end of Modernist era | traditional materials | "}, {"gap": "33"}, {"text": " of historic buildings"}],
        [{"text": "1970s | beginning of "}, {"gap": "34"}, {"text": " era | metal and glass | sophisticated techniques paraded"}],
        [{"text": "1980s | Post-Modernism | mixed | "}, {"gap": "35"}],
    ],
}

PASSAGE3_QUESTIONS: list[dict] = [
    # Q29-35 — table completion
    {
        "order": 29,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p3_table", "gap_key": "29", "notes": PASSAGE3_TABLE,
                    "instruction": "Complete the table. Write NO MORE THAN THREE WORDS for each answer."},
        "answer_key": {"correct": ["timber and stone", "stone and timber"]},
    },
    {
        "order": 30,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p3_table", "gap_key": "30", "notes": PASSAGE3_TABLE},
        "answer_key": {"correct": "Modernism"},
    },
    {
        "order": 31,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p3_table", "gap_key": "31", "notes": PASSAGE3_TABLE},
        "answer_key": {"correct": ["International style", "international style"]},
    },
    {
        "order": 32,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p3_table", "gap_key": "32", "notes": PASSAGE3_TABLE},
        "answer_key": {
            "correct": [
                "badly designed buildings",
                "multi-storey housing",
                "mass-produced, low-cost high-rises",
                "mass produced low cost high rises",
            ]
        },
    },
    {
        "order": 33,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p3_table", "gap_key": "33", "notes": PASSAGE3_TABLE},
        "answer_key": {"correct": ["preservation", "preserving"]},
    },
    {
        "order": 34,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p3_table", "gap_key": "34", "notes": PASSAGE3_TABLE},
        "answer_key": {"correct": "High-Tech"},
    },
    {
        "order": 35,
        "question_type": QuestionType.GAP_FILL,
        "content": {"notes_id": "p3_table", "gap_key": "35", "notes": PASSAGE3_TABLE},
        "answer_key": {
            "correct": [
                "co-existence of styles",
                "different styles together",
                "styles mixed",
                "coexistence of styles",
            ]
        },
    },
    # Q36-40 — matching causes to effects (compound MATCHING, order=36)
    # Causes list (left); Effects list A-H (right)
    # Answers: Q36=G, Q37=F, Q38=H, Q39=C, Q40=D
    {
        "order": 36,
        "question_type": QuestionType.MATCHING,
        "content": {
            "instruction": (
                "Questions 36-40. Reading Passage 3 describes cause and effect relationships. "
                "Match each Cause (36-40) in List A with its Effect (A-H) in List B. "
                "NB There are more effects than causes, so you will not use all of them."
            ),
            "left": [
                "36. A rapid movement of people from rural areas to cities is triggered by technological advance.",
                "37. Buildings become simple and functional.",
                "38. An economic depression and the second world war hit Europe.",
                "39. Multi-storey housing estates are built according to contemporary ideas on town planning.",
                "40. Less land must be used for building.",
            ],
            "right": [
                "A. The quality of life is improved.",
                "B. Architecture reflects the age.",
                "C. A number of these have been knocked down.",
                "D. Light steel frames and lifts are developed.",
                "E. Historical buildings are preserved.",
                "F. All decoration is removed.",
                "G. Parts of cities become slums.",
                "H. Modernist ideas cannot be put into practice until the second half of the 20th century.",
            ],
        },
        "answer_key": {
            "correct": {
                "36. A rapid movement of people from rural areas to cities is triggered by technological advance.": "G. Parts of cities become slums.",
                "37. Buildings become simple and functional.": "F. All decoration is removed.",
                "38. An economic depression and the second world war hit Europe.": "H. Modernist ideas cannot be put into practice until the second half of the 20th century.",
                "39. Multi-storey housing estates are built according to contemporary ideas on town planning.": "C. A number of these have been knocked down.",
                "40. Less land must be used for building.": "D. Light steel frames and lifts are developed.",
            }
        },
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# WRITING DATA
# Source: Cambridge IELTS 1, Test 1, Writing Tasks (PDF p.31-32)
# Task 1: bar chart + pie chart on adult education (image: Writing_Task_1.jpg)
# Task 2: discursive essay on music
# Scoring: automatic via EvaluationJob → Gemini (worker.py); answer_key = None
# ══════════════════════════════════════════════════════════════════════════════

WRITING_QUESTIONS: list[dict] = [
    {
        "order": 1,
        "question_type": QuestionType.ESSAY,
        "content": {
            "task_type": "task_1",
            "prompt": (
                "The charts below show the results of a survey of adult education. "
                "The first chart shows the reasons why adults decide to study. "
                "The pie chart shows how people think the costs of adult education should be shared.\n\n"
                "Write a report for a university lecturer, describing the information shown below."
            ),
            "instruction": "You should spend about 20 minutes on this task. Write at least 150 words.",
            "min_words": 150,
            "image_url": WRITING_IMAGE_URL,
        },
        "answer_key": None,
    },
    {
        "order": 2,
        "question_type": QuestionType.ESSAY,
        "content": {
            "task_type": "task_2",
            "prompt": (
                "Present a written argument or case to an educated reader with no specialist "
                "knowledge of the following topic:\n\n"
                "There are many different types of music in the world today. Why do we need music? "
                "Is the traditional music of a country more important than the international music "
                "that is heard everywhere nowadays?\n\n"
                "Use your own ideas, knowledge and experience and support your arguments with "
                "examples and relevant evidence."
            ),
            "instruction": "You should spend about 40 minutes on this task. Write at least 250 words.",
            "min_words": 250,
        },
        "answer_key": None,
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED SECTIONS REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def _build_sections() -> dict[int, dict]:
    """Build the full sections registry (called once at module load)."""
    return {
        # ── Listening S1-S4 ───────────────────────────────────────────────────
        1: {
            "id": SECTION_UUID[1], "label": "Listening S1",
            "type": SectionType.LISTENING, "order": 1,
            "duration": LISTENING_DURATION[1],
            "audio_url": _audio_url(1), "passage": None,
            "questions": SECTION1_QUESTIONS,
        },
        2: {
            "id": SECTION_UUID[2], "label": "Listening S2",
            "type": SectionType.LISTENING, "order": 2,
            "duration": LISTENING_DURATION[2],
            "audio_url": _audio_url(2), "passage": None,
            "questions": SECTION2_QUESTIONS,
        },
        3: {
            "id": SECTION_UUID[3], "label": "Listening S3",
            "type": SectionType.LISTENING, "order": 3,
            "duration": LISTENING_DURATION[3],
            "audio_url": _audio_url(3), "passage": None,
            "questions": SECTION3_QUESTIONS,
        },
        4: {
            "id": SECTION_UUID[4], "label": "Listening S4",
            "type": SectionType.LISTENING, "order": 4,
            "duration": LISTENING_DURATION[4],
            "audio_url": _audio_url(4), "passage": None,
            "questions": SECTION4_QUESTIONS,
        },
        # ── Reading P1-P3 ─────────────────────────────────────────────────────
        5: {
            "id": READING_SECTION_UUID[1], "label": "Reading P1",
            "type": SectionType.READING, "order": 5,
            "duration": READING_DURATION,
            "audio_url": None, "passage": _load_passage(1),
            "questions": PASSAGE1_QUESTIONS,
        },
        6: {
            "id": READING_SECTION_UUID[2], "label": "Reading P2",
            "type": SectionType.READING, "order": 6,
            "duration": READING_DURATION,
            "audio_url": None, "passage": _load_passage(2),
            "questions": PASSAGE2_QUESTIONS,
        },
        7: {
            "id": READING_SECTION_UUID[3], "label": "Reading P3",
            "type": SectionType.READING, "order": 7,
            "duration": READING_DURATION,
            "audio_url": None, "passage": _load_passage(3),
            "questions": PASSAGE3_QUESTIONS,
        },
        # ── Writing ───────────────────────────────────────────────────────────
        8: {
            "id": WRITING_SECTION_UUID, "label": "Writing",
            "type": SectionType.WRITING, "order": 8,
            "duration": 60,
            "audio_url": None, "passage": None,
            "questions": WRITING_QUESTIONS,
        },
    }


SECTIONS = _build_sections()

# ── DB helpers ────────────────────────────────────────────────────────────────

async def _upsert_section(
    db: AsyncSession,
    section_id: "uuid.UUID",
    section_type: SectionType,
    label: str,
    order: int,
    duration: int,
    audio_url: str | None,
    passage: str | None,
    questions: list[dict],
) -> None:
    section = await db.get(Section, section_id)
    if section is None:
        section = Section(
            id=section_id,
            test_id=TEST_UUID,
            type=section_type,
            order=order,
            duration_minutes=duration,
            audio_url=audio_url,
            passage=passage,
        )
        db.add(section)
        await db.flush()
        log.info("  Created section %s (%s)", label, section_id)
    else:
        section.type = section_type
        section.order = order
        section.duration_minutes = duration
        section.audio_url = audio_url
        if passage is not None:
            section.passage = passage
        log.info("  Updated section %s (%s)", label, section_id)

    await db.execute(delete(Question).where(Question.section_id == section_id))
    await db.flush()

    for q in questions:
        db.add(
            Question(
                section_id=section_id,
                order=q["order"],
                question_type=q["question_type"],
                content=q["content"],
                answer_key=q["answer_key"],
            )
        )

    await db.commit()
    log.info("  Seeded %d questions for %s", len(questions), label)


# ── Main seed ─────────────────────────────────────────────────────────────────

async def seed(db: AsyncSession) -> None:
    # Test (upsert)
    test = await db.get(Test, TEST_UUID)
    if test is None:
        test = Test(
            id=TEST_UUID,
            title="Test 1",
            description="Cambridge IELTS 1 — Academic Practice Test 1",
            type="academic",
            book_name="Cambridge IELTS 1",
            is_published=False,
        )
        db.add(test)
        await db.flush()
        log.info("Created test '%s' (%s)", test.title, test.id)
    else:
        test.title = "Test 1"
        test.book_name = "Cambridge IELTS 1"
        test.type = "academic"
        log.info("Updated test '%s' (%s)", test.title, test.id)

    # All sections (Listening + Reading)
    for cfg in SECTIONS.values():
        log.info("--- %s ---", cfg["label"])
        await _upsert_section(
            db,
            section_id=cfg["id"],
            section_type=cfg["type"],
            label=cfg["label"],
            order=cfg["order"],
            duration=cfg["duration"],
            audio_url=cfg["audio_url"],
            passage=cfg["passage"],
            questions=cfg["questions"],
        )


# ── Entrypoint ────────────────────────────────────────────────────────────────

async def main() -> None:
    # Copy Listening MP3s
    for num in range(1, 5):
        _copy_audio(num)
    # Copy Writing Task 1 chart image
    _copy_writing_image()

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        await seed(db)

    await engine.dispose()
    log.info(
        "Done. %d sections seeded (%d Listening, %d Reading, %d Writing).",
        len(SECTIONS),
        sum(1 for c in SECTIONS.values() if c["type"] == SectionType.LISTENING),
        sum(1 for c in SECTIONS.values() if c["type"] == SectionType.READING),
        sum(1 for c in SECTIONS.values() if c["type"] == SectionType.WRITING),
    )


if __name__ == "__main__":
    asyncio.run(main())
