"""Can the one-file-per-test listening audio be cut into four parts reliably?

The platform plays one recording per listening part, but this book ships a
single file per test. Every IELTS recording ends each section with a half-minute
pause for checking answers, so those pauses are the cut points — if there are
exactly four of them, in the right places, in every test.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Help Now 15 PTests")

# The end-of-section pause is a nominal 30s; the mid-section "look at questions
# X to Y" pause is a nominal 20s. Sit the threshold between them.
SECTION_PAUSE = 27.0
SILENCE_FLOOR = "-35dB"


def probe(path: Path) -> tuple[float, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate",
         "-of", "csv=p=0:nk=1", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    duration, bitrate = out.split(",")
    return float(duration), int(bitrate) // 1000


def long_silences(path: Path) -> list[tuple[float, float]]:
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", f"silencedetect=noise={SILENCE_FLOOR}:d=2.5", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr

    found: list[tuple[float, float]] = []
    start: float | None = None
    for line in out.splitlines():
        if m := re.search(r"silence_start: ([\d.]+)", line):
            start = float(m.group(1))
        elif m := re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line):
            end, dur = float(m.group(1)), float(m.group(2))
            if dur >= SECTION_PAUSE and start is not None:
                found.append((end, dur))
            start = None
    return found


def pick_audio(test_dir: Path) -> Path | None:
    """Prefer the 128 kbps copy where the book ships one."""
    hq = test_dir / "High quality listenings"
    if hq.is_dir():
        files = sorted(hq.glob("*.mp3"))
        if files:
            return files[0]
    files = [p for p in sorted(test_dir.glob("*.mp3")) if "speaking" not in p.name.lower()]
    return files[0] if files else None


def main() -> None:
    tests: list[tuple[int, Path]] = []
    for set_dir in sorted(ROOT.glob("AcademicTestsSet*")):
        for test_dir in sorted(set_dir.glob("TEST *")):
            n = int(test_dir.name.split()[-1])
            audio = pick_audio(test_dir)
            if audio:
                tests.append((n, audio))
    tests.sort()

    print(f"{'test':>5}  {'mins':>5}  {'kbps':>5}  cuts  section lengths (minutes)")
    for n, audio in tests:
        duration, kbps = probe(audio)
        cuts = long_silences(audio)
        marks = [c[0] for c in cuts]
        # Four pauses means the last one trails the end of section 4.
        bounds = [0.0, *marks[:3], duration]
        lengths = " ".join(f"{(b - a) / 60:.1f}" for a, b in zip(bounds, bounds[1:]))
        flag = "" if len(cuts) == 4 else f"  <-- {len(cuts)} pauses, check by hand"
        print(f"{n:>5}  {duration / 60:>5.1f}  {kbps:>5}  {len(cuts):>4}  {lengths}{flag}")


if __name__ == "__main__":
    main()
