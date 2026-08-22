"""Confirm each split listening part opens with its own section announcement.

A cut in the wrong pause would put the start of one section at the end of
another, and a candidate would only discover it mid-exam. Transcribing the
opening seconds of each part settles it: part N must announce section N.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\_verify_booster_audio_cuts.py scripts\\_booster_text\\audio
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

OPENING_SECONDS = 25

WORD_FOR_NUMBER = {
    1: ("one", "1"),
    2: ("two", "2"),
    3: ("three", "3"),
    4: ("four", "4"),
}


def opening_clip(src: Path) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "clip.mp3"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(src), "-t", str(OPENING_SECONDS), "-c", "copy", str(clip)],
            check=True,
        )
        return clip.read_bytes()


def announces(text: str, part: int) -> bool:
    lowered = text.lower()
    if "section" not in lowered and "part" not in lowered:
        return False
    return any(
        re.search(rf"(section|part)\s+{token}\b", lowered)
        for token in WORD_FOR_NUMBER[part]
    )


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--prefix", default="practice_a_t1_listening_p")
    args = ap.parse_args()

    problems = 0
    for part in (1, 2, 3, 4):
        src = args.folder / f"{args.prefix}{part}.mp3"
        if not src.exists():
            print(f"part {part}: MISSING {src.name}")
            problems += 1
            continue
        clip = opening_clip(src)
        text = (await transcribe_audio_bytes(clip, content_type="audio/mpeg")).strip()
        ok = announces(text, part)
        print(f"part {part}: {'ok  ' if ok else 'CHECK'} {text[:120]!r}")
        if not ok:
            problems += 1

    print("\nall four parts open correctly" if not problems
          else f"\n{problems} part(s) need a listen")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
