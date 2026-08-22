"""Read the five-test answer sheets by column position, not by reading order.

The answer keys for five tests sit side by side in one table, and long answers
wrap. Flattened text puts a wrapped fragment next to whichever column happened
to be nearby, so "Semiconductor technolo-" / "gies" and its neighbours end up
attached to the wrong test. Reading each word's x position instead keeps every
fragment in the column it was printed in.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\_parse_booster_answers.py --skill listening
    .\\venv\\Scripts\\python scripts\\_parse_booster_answers.py --skill reading --test 2
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Help Now 15 PTests")

NUM_RE = re.compile(r"^(\d{1,2})\.$")
# The "any order" notes and the copyright line print below the table, inside the
# same columns, so they would otherwise be glued onto answer 40.
FOOTNOTE_RE = re.compile(r"^[*˚©]|^Answers for qu|^ieltshelpnow", re.IGNORECASE)


def answers_pdf(skill: str, set_no: int = 1) -> Path:
    lo, hi = (set_no - 1) * 5 + 1, set_no * 5
    folder = ROOT / f"AcademicTestsSet{set_no}" / "ANSWERS"
    for pattern in (
        f"academic {skill} answers - tests {lo} - {hi}.pdf",
        f"academic {skill} answers*{lo}*{hi}*.pdf",
    ):
        found = list(folder.glob(pattern))
        if found:
            return found[0]
    raise SystemExit(f"no {skill} answer sheet in {folder}")


def column_bounds(words: list[dict]) -> list[float]:
    """Left edge of each of the five test columns, taken from the '1.' markers.

    Every column starts its list with a "1." label, and those five labels are the
    only reliable landmark: the header row uses a different font size and the
    body rows wrap.
    """
    starts = sorted(w["x0"] for w in words if NUM_RE.match(w["text"]))
    if not starts:
        raise SystemExit("no numbered rows found")

    # Cluster the x positions of every row label; five clusters, one per column.
    clusters: list[list[float]] = [[starts[0]]]
    for x in starts[1:]:
        if x - clusters[-1][-1] <= 12:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    bounds = [min(c) for c in clusters]
    if len(bounds) != 5:
        raise SystemExit(f"expected 5 columns, found {len(bounds)}: {bounds}")
    return bounds


def column_of(x: float, bounds: list[float]) -> int:
    """Index of the column a word at *x* belongs to."""
    for i in range(len(bounds) - 1, -1, -1):
        if x >= bounds[i] - 6:
            return i
    return 0


def parse(skill: str, set_no: int = 1) -> dict[int, dict[int, str]]:
    """Return {test_number: {question_number: answer}}."""
    src = answers_pdf(skill, set_no)
    per_test: dict[int, dict[int, str]] = {}

    with pdfplumber.open(src) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=False)
            if not words:
                continue
            try:
                bounds = column_bounds(words)
            except SystemExit:
                continue

            # Group into printed lines, then split each line by column.
            lines: dict[float, list[dict]] = {}
            for w in words:
                key = round(w["top"] / 3)
                lines.setdefault(key, []).append(w)

            # current[col] = question number the column is still writing into
            current: dict[int, int] = {}
            for key in sorted(lines):
                row = sorted(lines[key], key=lambda w: w["x0"])
                by_col: dict[int, list[dict]] = {}
                for w in row:
                    by_col.setdefault(column_of(w["x0"], bounds), []).append(w)

                for col, cell in sorted(by_col.items()):
                    test_no = (set_no - 1) * 5 + col + 1
                    answers = per_test.setdefault(test_no, {})
                    tokens = [w["text"] for w in cell]

                    if NUM_RE.match(tokens[0]):
                        number = int(tokens[0][:-1])
                        if not 1 <= number <= 40:
                            continue
                        current[col] = number
                        answers[number] = " ".join(tokens[1:]).strip()
                    elif col in current:
                        # A wrapped continuation of this column's last answer.
                        number = current[col]
                        tail = " ".join(tokens).strip()
                        if not tail or FOOTNOTE_RE.match(tail):
                            # Footnotes sit below the table, in the same columns.
                            current.pop(col, None)
                            continue
                        head = answers.get(number, "")
                        if head.endswith("-"):
                            # A word split across lines: "specifica-" + "tions".
                            answers[number] = (head[:-1] + tail).strip()
                        else:
                            answers[number] = f"{head} {tail}".strip()

    return per_test


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", choices=("listening", "reading"), default="listening")
    ap.add_argument("--set", type=int, default=1)
    ap.add_argument("--test", type=int, help="show only this test")
    args = ap.parse_args()

    per_test = parse(args.skill, args.set)
    wanted = [args.test] if args.test else sorted(per_test)

    for test_no in wanted:
        answers = per_test.get(test_no, {})
        print(f"\n===== {args.skill} test {test_no}  ({len(answers)}/40 rows) =====")
        for n in range(1, 41):
            value = answers.get(n)
            print(f"{n:>3}. {value if value else '  <<< MISSING >>>'}")


if __name__ == "__main__":
    main()
