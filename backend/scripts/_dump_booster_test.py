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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_no", type=int)
    ap.add_argument("--kind", choices=("paper", "script"), default="paper")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

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
