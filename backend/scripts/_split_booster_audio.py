"""Cut a whole-test listening recording into the four parts the exam plays.

Each section closes with the half-minute pause the invigilator's script calls
"you will now have half a minute to check your answers", and nothing else in the
recording is that long. Cutting at the end of the first three such pauses gives
four parts that each open with their own "Section N" announcement.

Streams are copied rather than re-encoded, so the parts sound exactly like the
source.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Help Now 15 PTests")

SECTION_PAUSE = 27.0
SILENCE_FLOOR = "-35dB"
EXPECTED_PARTS = 4


def source_audio(test_no: int) -> Path:
    test_dirs = list(ROOT.glob(f"AcademicTestsSet*/TEST {test_no}"))
    if not test_dirs:
        raise SystemExit(f"test {test_no} not found")
    test_dir = test_dirs[0]

    hq = test_dir / "High quality listenings"
    if hq.is_dir():
        files = sorted(hq.glob("*.mp3"))
        if files:
            return files[0]
    files = [p for p in sorted(test_dir.glob("*.mp3")) if "speaking" not in p.name.lower()]
    if not files:
        raise SystemExit(f"no listening audio for test {test_no}")
    return files[0]


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def pause_ends(path: Path) -> list[float]:
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", f"silencedetect=noise={SILENCE_FLOOR}:d=2.5", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    ends: list[float] = []
    for line in out.splitlines():
        m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
        if m and float(m.group(2)) >= SECTION_PAUSE:
            ends.append(float(m.group(1)))
    return ends


def cut(src: Path, dest: Path, start: float, end: float) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
         "-c", "copy", str(dest)],
        check=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_no", type=int)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--prefix", default=None, help="defaults to practice_a_t<n>")
    args = ap.parse_args()

    src = source_audio(args.test_no)
    total = duration(src)
    ends = pause_ends(src)
    print(f"source: {src.name}  {total / 60:.1f} min  long pauses at "
          f"{', '.join(f'{e:.0f}s' for e in ends)}")

    # The fourth pause closes the last section, so only the first three split.
    if len(ends) < EXPECTED_PARTS - 1:
        raise SystemExit(f"found {len(ends)} long pauses, need at least 3 to split")
    marks = ends[: EXPECTED_PARTS - 1]
    bounds = [0.0, *marks, total]

    prefix = args.prefix or f"practice_a_t{args.test_no}"
    args.out.mkdir(parents=True, exist_ok=True)
    for part, (start, end) in enumerate(zip(bounds, bounds[1:]), start=1):
        dest = args.out / f"{prefix}_listening_p{part}.mp3"
        cut(src, dest, start, end)
        made = duration(dest)
        print(f"  part {part}: {start:7.1f}s -> {end:7.1f}s   {made / 60:4.1f} min   "
              f"{dest.stat().st_size / 1024 / 1024:.1f} MB  {dest.name}")

    if len(ends) > EXPECTED_PARTS:
        print(f"note: {len(ends)} long pauses found, expected {EXPECTED_PARTS}; "
              "listen to each part opening before publishing")


if __name__ == "__main__":
    main()
