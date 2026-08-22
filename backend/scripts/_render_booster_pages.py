"""Render pages of a practice-test paper to PNG.

Forms, notes, tables and maps lose their layout when a PDF is read as a stream
of text: a gap number and the cell it belongs to end up on different lines. The
only reliable way to place a gap correctly is to look at the page.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Help Now 15 PTests")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_no", type=int)
    ap.add_argument("--pages", required=True, help="1-based, comma separated")
    ap.add_argument("--dpi", type=int, default=140)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    matches = list(ROOT.glob(f"AcademicTestsSet*/TEST {args.test_no}/academic question paper test {args.test_no}.pdf"))
    if not matches:
        raise SystemExit("paper not found")

    args.out.mkdir(parents=True, exist_ok=True)
    wanted = [int(p) for p in args.pages.split(",")]

    with pdfplumber.open(matches[0]) as pdf:
        for n in wanted:
            dest = args.out / f"test{args.test_no}_p{n:02d}.png"
            pdf.pages[n - 1].to_image(resolution=args.dpi).save(str(dest))
            print(f"page {n} -> {dest.name} ({dest.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
