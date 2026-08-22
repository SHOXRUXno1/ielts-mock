"""Pull the three reading passages out of a practice-test paper as clean text.

Two things make a plain text extract unusable. The prose is wrapped at the page
width, so sentences arrive broken across lines. And the book marks a new
paragraph by indenting its first line rather than by leaving a blank line, so
that structure is invisible unless the extract keeps track of where each line
starts on the page.

Both are handled here by working from word positions: lines are rebuilt from
words, and a line that starts further right than the body margin opens a new
paragraph. Output is one paragraph per line, which is what the reading section
renderer expects.
"""

from __future__ import annotations

import argparse
import re
import statistics
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Help Now 15 PTests")

PASSAGE_HEAD_RE = re.compile(r"^READING PASSAGE\s+(\d+)\b")
QUESTIONS_RE = re.compile(r"^Questions?\s+\d+\s*[-–]", re.IGNORECASE)
SKILL_HEAD_RE = re.compile(r"^ACADEMIC (WRITING|SPEAKING|LISTENING|READING)")
FOOTER_RE = re.compile(
    r"^(Academic Test \d+; Page \d+|©\s*ieltshelpnow\.com|ieltshelpnow\.com.*"
    r"|IELTS-Blog\.com is an authorized distributor.*|Page \d+)$",
    re.IGNORECASE,
)
INTRO_RE = re.compile(r"^(You should spend about|Reading Passage \d+ (below|on the))")
PARA_MARKER_RE = re.compile(r"^[A-H]$")
# Indent is a couple of characters, so a small tolerance separates a genuine
# paragraph opening from ordinary jitter in glyph placement.
INDENT_TOLERANCE = 3.0


def page_lines(page) -> list[tuple[float, float, str]]:
    """(left edge, baseline, text) per visual line, in reading order."""
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    rows: dict[int, list[dict]] = {}
    for w in words:
        # Round the baseline so glyphs of one line group together despite
        # sub-pixel differences.
        rows.setdefault(round(w["top"] / 3), []).append(w)

    lines: list[tuple[float, float, str]] = []
    for key in sorted(rows):
        row = sorted(rows[key], key=lambda w: w["x0"])
        text = " ".join(w["text"] for w in row).strip()
        if text:
            lines.append((min(w["x0"] for w in row), min(w["top"] for w in row), text))
    return lines


def is_title(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(text) > 8 and bool(letters) and all(c.isupper() for c in letters)


def collect(pdf) -> tuple[dict[int, str], dict[int, list[tuple[float, float, str]]]]:
    titles: dict[int, str] = {}
    bodies: dict[int, list[tuple[float, float, str]]] = {}
    current: int | None = None
    state = "idle"  # idle -> await_title -> body

    for page in pdf.pages:
        previous_top: float | None = None
        for left, top, text in page_lines(page):
            if FOOTER_RE.match(text):
                continue
            if m := PASSAGE_HEAD_RE.match(text):
                current = int(m.group(1))
                bodies.setdefault(current, [])
                state = "await_title"
                continue
            if SKILL_HEAD_RE.match(text):
                state = "idle"
                continue
            if current is None or state == "idle":
                continue
            if INTRO_RE.match(text):
                continue
            if state == "await_title":
                if is_title(text):
                    titles[current] = text
                    state = "body"
                continue
            if QUESTIONS_RE.match(text):
                state = "idle"
                continue
            # Across a page break the distance is meaningless, and a paragraph
            # usually does run on, so report no gap.
            gap = 0.0 if previous_top is None else top - previous_top
            previous_top = top
            bodies[current].append((left, gap, text))

    return titles, bodies


def paragraphs(lines: list[tuple[float, float, str]]) -> list[str]:
    """Rebuild paragraphs from wrapped lines.

    The book uses two styles across passages: an indented first line, or extra
    space above. Both are checked, so one extractor handles either.
    """
    if not lines:
        return []

    margin = statistics.median(left for left, _, _ in lines)
    spacings = [gap for _, gap, _ in lines if gap > 0]
    line_height = statistics.median(spacings) if spacings else 0.0

    out: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            out.append(" ".join(buffer))
            buffer.clear()

    for left, gap, text in lines:
        if PARA_MARKER_RE.match(text):
            flush()
            out.append(f"[{text}]")
            continue
        if text.startswith("Source:"):
            flush()
            out.append(text)
            continue
        indented = left > margin + INDENT_TOLERANCE
        spaced = line_height > 0 and gap > line_height * 1.5
        if buffer and (indented or spaced):
            flush()
        buffer.append(text)
    flush()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_no", type=int)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    hits = list(
        ROOT.glob(
            f"AcademicTestsSet*/TEST {args.test_no}/academic question paper test {args.test_no}.pdf"
        )
    )
    if not hits:
        raise SystemExit("paper not found")

    args.out.mkdir(parents=True, exist_ok=True)
    with pdfplumber.open(hits[0]) as pdf:
        titles, bodies = collect(pdf)

    for number, lines in sorted(bodies.items()):
        paras = paragraphs(lines)
        dest = args.out / f"reading_p{number}.txt"
        title = titles.get(number, "")
        dest.write_text(f"{title}\n\n" + "\n".join(paras) + "\n", encoding="utf-8")
        words = sum(len(p.split()) for p in paras)
        print(f"passage {number}: {title[:46]!r}  {words} words, {len(paras)} paragraphs")


if __name__ == "__main__":
    main()
