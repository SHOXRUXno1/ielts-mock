"""Which of the practice-test PDFs carry real text, and which are scans?

A text PDF can be parsed into questions and answer keys directly. A scan needs
OCR, which is slow and introduces mistakes into answer keys — the one place a
mistake is unacceptable. So this decides which books are worth seeding first.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters")

TARGETS = [
    "IELTS Help Now 15 PTests/AcademicTestsSet1/TEST 1/academic question paper test 1.pdf",
    "IELTS Help Now 15 PTests/AcademicTestsSet1/TEST 1/listening script 1.pdf",
    "IELTS Help Now 15 PTests/AcademicTestsSet1/ANSWERS/academic listening answers - tests 1 - 5.pdf",
    "IELTS Help Now 15 PTests/AcademicTestsSet1/ANSWERS/academic reading answers - tests 1 - 5.pdf",
    "IELTS Practice Test Plus 3/IELTS practice tests plus 3 .pdf",
    "IELTS Practice Tests Plus 2/IELTS Practice Tests Plus 2.pdf",
    "Ielts Reading Recent Actual Tests Vol 1(1).pdf",
    "BC Listening and Reading/Listening_practice_questions_121012.pdf",
    "BC Listening and Reading/Listening_practice_answers_121012.doc_.pdf",
    "BC Listening and Reading/Reading_Practice_1_IELTS_Academic_Questions.pdf",
    "Peter May Practice Tests/IELTS Practice Tests.pdf",
    "Thomson IELTS Practice Tests/Thomson IELTS Practice Tests.pdf",
    "6 IELTS practice tests/2017-02-13 (0) painted.pdf",
    "Actuals May - August/IELTS-Reading-Academic-May-August-fagnkp.pdf",
    "Actuals May - August/IELTS-Listening-Recent-test-May-August-2021-7w7hoy.pdf",
    "Listening Volume 3/BOOKS.pdf",
    "Actual test - Listening Vol4_/IELTS Recent Actual Listening Test Vol 4.pdf",
    "IELTS Listening Actual Test Vol 2/Ielts Listening Actual Test Vol 2/ielts-listening-recent-actual-test-volume-2.pdf",
    "LISTENING VOL.1/updated-IELTS Listening Recent Actual Tests.pdf",
]

# Enough pages to get past a cover, which is an image even in a text PDF.
SAMPLE_PAGES = 8


def verdict(chars_per_page: float) -> str:
    if chars_per_page > 800:
        return "TEXT      parse directly"
    if chars_per_page > 150:
        return "PART TEXT check by hand"
    return "SCAN      needs OCR"


def probe(path: Path) -> None:
    try:
        with pdfplumber.open(path) as pdf:
            pages = len(pdf.pages)
            sample = pdf.pages[2 : 2 + SAMPLE_PAGES] or pdf.pages[:SAMPLE_PAGES]
            total = sum(len((p.extract_text() or "").strip()) for p in sample)
            per_page = total / max(1, len(sample))
            print(f"  {pages:>4} pages  {per_page:>7.0f} chars/page  {verdict(per_page)}")
            first = (sample[0].extract_text() or "").strip().replace("\n", " ")
            if first:
                print(f"        sample: {first[:110]}")
    except Exception as exc:
        print(f"  FAILED to open: {type(exc).__name__}: {exc}")


def main() -> None:
    for rel in TARGETS:
        path = ROOT / rel
        print(f"\n{rel}")
        if not path.exists():
            print("  missing")
            continue
        probe(path)


if __name__ == "__main__":
    sys.exit(main())
