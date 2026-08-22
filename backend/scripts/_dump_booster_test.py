"""Dump one practice-test paper to UTF-8 text, page by page.

The Windows console cannot print this book's typography, so the text goes to a
file. Page markers stay in, because the question numbering restarts per section
and the page boundary is often the only clue to where a section ends.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Help Now 15 PTests")


def find_paper(test_no: int, kind: str) -> Path:
    stem = {
        "paper": f"academic question paper test {test_no}.pdf",
        "script": f"listening script {test_no}.pdf",
    }[kind]
    matches = list(ROOT.glob(f"AcademicTestsSet*/TEST {test_no}/{stem}"))
    if not matches:
        raise SystemExit(f"not found: {stem}")
    return matches[0]


def find_answers(test_no: int, skill: str) -> Path:
    """Answer keys are filed per set of five tests, not per test."""
    set_no = (test_no - 1) // 5 + 1
    lo, hi = (set_no - 1) * 5 + 1, set_no * 5
    folder = ROOT / f"AcademicTestsSet{set_no}" / "ANSWERS"
    patterns = [
        f"academic {skill} answers - tests {lo} - {hi}.pdf",
        f"academic {skill} answers - tests {lo} _ {hi}.pdf",
        f"academic {skill} answers*{lo}*{hi}*.pdf",
    ]
    for pattern in patterns:
        matches = list(folder.glob(pattern))
        if matches:
            return matches[0]
    raise SystemExit(f"no {skill} answers for test {test_no} under {folder}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_no", type=int)
    ap.add_argument(
        "--kind",
        choices=("paper", "script", "answers-listening", "answers-reading"),
        default="paper",
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.kind.startswith("answers-"):
        src = find_answers(args.test_no, args.kind.split("-", 1)[1])
    else:
        src = find_paper(args.test_no, args.kind)
    chunks: list[str] = []
    with pdfplumber.open(src) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = (page.extract_text() or "").rstrip()
            note = f" [{len(page.images)} embedded image(s)]" if page.images else ""
            chunks.append(f"\n===== page {i}{note} =====\n{text}")

    args.out.write_text("\n".join(chunks), encoding="utf-8")
    print(f"{src.name} -> {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
