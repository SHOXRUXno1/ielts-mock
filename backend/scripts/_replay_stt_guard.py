"""Replay every candidate turn ever recorded through the new silence guard.

Unit tests prove the rules; this proves the rules against reality. It prints
each turn the guard would have discarded so a human can confirm none of them
was a real answer, and each turn whose decoder loop would have been collapsed.

Run from backend/:  py scripts/_replay_stt_guard.py ../.git/turns.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.services.llm import _normalize_stt_text


def load(path: Path) -> list[dict]:
    data = path.read_bytes()
    encoding = "utf-16" if data[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    raw = data.decode(encoding).strip()
    return json.loads(raw[raw.index("[") : raw.rindex("]") + 1])


def main() -> None:
    turns = load(Path(sys.argv[1]))
    dropped: list[dict] = []
    collapsed: list[tuple[dict, str]] = []

    for turn in turns:
        text = turn.get("text") or ""
        out = _normalize_stt_text(text)
        if not out.strip():
            dropped.append(turn)
        elif out != text.strip().strip('"').strip():
            collapsed.append((turn, out))

    print(f"total candidate turns : {len(turns)}")
    print(f"would be discarded    : {len(dropped)}")
    print(f"loops collapsed       : {len(collapsed)}\n")

    print("=== DISCARDED (each must be something nobody actually said) ===")
    for t in dropped:
        print(f"  [{t.get('who')}/{t.get('phase')}] {t.get('text')!r}")

    print("\n=== LOOPS COLLAPSED ===")
    for t, out in collapsed:
        print(f"  [{t.get('who')}/{t.get('phase')}]")
        print(f"    before: {t.get('text')!r}")
        print(f"    after : {out!r}")

    print("\n=== SURVIVORS SHORTER THAN 5 WORDS (watch for false rejections) ===")
    for t in turns:
        text = (t.get("text") or "").strip()
        out = _normalize_stt_text(text)
        if out.strip() and len(out.split()) < 5:
            print(f"  [{t.get('who')}/{t.get('phase')}] {out!r}")


if __name__ == "__main__":
    main()
