"""Cut the map and the chart out of a practice-test paper as PNGs.

Cropping by eye drifts between tests, so the bounds come from the page itself:
the union of the vector rectangles that make up the map, and the union of the
embedded images that make up the chart. Text is excluded so the instruction
lines above the figure do not end up baked into it.

Some figures cannot be found that way. A labelled diagram carries its question
numbers as ordinary page text beside the artwork, and a data table drawn in text
has no artwork at all; in both cases the crop has to include the surrounding
text, so `--top`/`--bottom` take an explicit vertical band instead.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Help Now 15 PTests")
PAD = 6


def paper(test_no: int) -> Path:
    hits = list(
        ROOT.glob(f"AcademicTestsSet*/TEST {test_no}/academic question paper test {test_no}.pdf")
    )
    if not hits:
        raise SystemExit(f"paper for test {test_no} not found")
    return hits[0]


def union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def figure_bbox(
    page,
    source: str,
    min_side: float,
    top: float | None = None,
    bottom: float | None = None,
) -> tuple[float, float, float, float]:
    """Bounds of the drawing on the page.

    `min_side` drops the hairlines and specks that vector art leaves behind,
    which would otherwise stretch the crop to the whole page.
    """
    if source == "band":
        if top is None or bottom is None:
            raise SystemExit("band mode needs --top and --bottom")
        return (0.0, top, page.width, bottom)
    if source == "images":
        shapes = [(im["x0"], im["top"], im["x1"], im["bottom"]) for im in page.images]
    else:
        shapes = [
            (r["x0"], r["top"], r["x1"], r["bottom"])
            for r in page.rects
            if (r["x1"] - r["x0"]) >= min_side and (r["bottom"] - r["top"]) >= min_side
        ]
    if not shapes:
        raise SystemExit(f"no {source} found on this page")
    return union(shapes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_no", type=int)
    ap.add_argument("--page", type=int, required=True, help="1-based")
    ap.add_argument("--source", choices=("rects", "images", "band"), required=True)
    ap.add_argument("--min-side", type=float, default=12.0)
    ap.add_argument("--top", type=float, help="band mode: top edge in points")
    ap.add_argument("--bottom", type=float, help="band mode: bottom edge in points")
    # The page footer sits just under the artwork and would otherwise be baked
    # into the figure, naming the book to whoever sits the exam.
    ap.add_argument("--cut-bottom", type=float, default=0.0, help="points to drop")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    with pdfplumber.open(paper(args.test_no)) as pdf:
        page = pdf.pages[args.page - 1]
        x0, top, x1, bottom = figure_bbox(
            page, args.source, args.min_side, args.top, args.bottom
        )
        box = (
            max(0, x0 - PAD),
            max(0, top - PAD),
            min(page.width, x1 + PAD),
            min(page.height, bottom + PAD - args.cut_bottom),
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        page.within_bbox(box).to_image(resolution=args.dpi).save(str(args.out))

    print(
        f"page {args.page} {args.source} -> {args.out.name}  "
        f"bbox={tuple(round(v) for v in box)}  {args.out.stat().st_size / 1024:.0f} KB"
    )


if __name__ == "__main__":
    main()
