"""Trim the publisher's spoken credit off the front of listening part 1.

The recording opens by naming the book and test number out loud, which would
tell a candidate exactly where to find the answer key. The generic exam preamble
that follows ("In the IELTS test you hear some recordings...") is what should be
heard first.

Finding the join by ear does not scale to fifteen tests, so candidate cut points
come from the short pauses between sentences, and each is checked by
transcribing what follows it.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\_trim_booster_branding.py <part1.mp3>
"""

from __future__ import annotations

import argparse
import asyncio
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from app.services.llm import transcribe_audio_bytes

# The credit is a sentence or two, so the join is always in this window.
SEARCH_WINDOW = (3.0, 25.0)
PROBE_SECONDS = 14
# The trimmed part must *open* on the generic preamble. Merely containing it
# still leaves words like "Test 1" spoken ahead of it.
WANTED_RE = re.compile(r"^\W*in the ielts test", re.IGNORECASE)


def sentence_pauses(src: Path) -> list[float]:
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(src),
         "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    ends = [
        float(m.group(1))
        for line in out.splitlines()
        if (m := re.search(r"silence_end: ([\d.]+)", line))
    ]
    lo, hi = SEARCH_WINDOW
    return [e for e in ends if lo <= e <= hi]


def clip_bytes(src: Path, start: float, seconds: int) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "probe.mp3"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-ss", f"{start:.3f}", "-t", str(seconds), "-i", str(src),
             "-c", "copy", str(clip)],
            check=True,
        )
        return clip.read_bytes()


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("part1", type=Path)
    ap.add_argument("--apply", action="store_true", help="rewrite the file in place")
    args = ap.parse_args()

    candidates = sentence_pauses(args.part1)
    if not candidates:
        print("no sentence pause found in the opening — trim by hand")
        return 1

    print(f"candidate cut points: {', '.join(f'{c:.2f}s' for c in candidates)}\n")

    chosen: float | None = None
    for start in candidates:
        text = (await transcribe_audio_bytes(
            clip_bytes(args.part1, start, PROBE_SECONDS), content_type="audio/mpeg"
        )).strip()
        clean = bool(WANTED_RE.match(text))
        print(f"  {start:5.2f}s  {'PICK ' if clean else '     '}{text[:90]!r}")
        if clean and chosen is None:
            chosen = start

    if chosen is None:
        print("\nno cut point removes the credit cleanly — trim by hand")
        return 1

    print(f"\ncut at {chosen:.2f}s removes the spoken credit")
    if not args.apply:
        print("re-run with --apply to rewrite the file")
        return 0

    trimmed = args.part1.with_suffix(".trimmed.mp3")
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-ss", f"{chosen:.3f}", "-i", str(args.part1), "-c", "copy", str(trimmed)],
        check=True,
    )
    trimmed.replace(args.part1)
    print(f"trimmed {args.part1.name} ({args.part1.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
