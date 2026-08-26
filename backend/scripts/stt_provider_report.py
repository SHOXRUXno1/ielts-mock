"""Report which engine transcribed each Speaking turn, and how they compare.

Chirp is the first ear when a Google service account is configured. Groq
Whisper and Gemini take the overflow. Until the label existed nobody could
tell which one had heard a given answer, so "recognition is sometimes
wrong" had no denominator — there was no way to say whether the misses
cluster on one engine, on the intro, or on nothing in particular.

Turns now carry the engine that produced them. This counts them, and reports
sittings split between both engines separately, because a candidate whose answers
were shared between two models is the case most likely to feel arbitrary.

Sittings recorded before that label existed are reported apart rather than folded
in: an unlabelled turn is not a Groq turn, and counting it as one would invent
the very number we are trying to measure.

    python scripts/stt_provider_report.py             # last 30 days
    python scripts/stt_provider_report.py --days 7
    python scripts/stt_provider_report.py --show-turns
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any

from sqlalchemy import select

from app.core.database import async_session
from app.models.speaking_session import SpeakingSession
from app.schemas.speaking_examiner import NO_SPEECH_TRANSCRIPT

# An answer this short is not an answer. It is either a candidate who said
# nothing or an engine that heard nothing, and both are worth looking at.
SHORT_ANSWER_WORDS = 3


def heard_nothing(text: str) -> bool:
    return not text.strip() or text.strip() == NO_SPEECH_TRANSCRIPT


def barely_heard(text: str) -> bool:
    return not heard_nothing(text) and len(text.split()) <= SHORT_ANSWER_WORDS


@dataclass
class Tally:
    turns: int = 0
    empty: int = 0
    short: int = 0
    latencies: list[int] = field(default_factory=list)

    def add(self, text: str, latency_ms: int) -> None:
        self.turns += 1
        if heard_nothing(text):
            self.empty += 1
        elif barely_heard(text):
            self.short += 1
        if latency_ms:
            self.latencies.append(latency_ms)

    @property
    def median_latency_ms(self) -> int | None:
        return round(median(self.latencies)) if self.latencies else None


@dataclass
class SplitSitting:
    session_id: str
    band: float | None
    counts: dict[str, int]


@dataclass
class QuietTurn:
    session_id: str
    phase: str
    provider: str
    text: str


@dataclass
class Report:
    sittings: int = 0
    by_provider: dict[str, Tally] = field(default_factory=dict)
    reasons: Counter = field(default_factory=Counter)
    labelled_sittings: int = 0
    unlabelled_sittings: int = 0
    unlabelled_turns: int = 0
    split: list[SplitSitting] = field(default_factory=list)
    quiet: list[QuietTurn] = field(default_factory=list)

    @property
    def labelled_turns(self) -> int:
        return sum(t.turns for t in self.by_provider.values())


def collect(sessions: Iterable[Any]) -> Report:
    """Walk sittings and count candidate turns by the engine that heard them."""
    report = Report()
    by_provider: dict[str, Tally] = defaultdict(Tally)

    for session in sessions:
        report.sittings += 1
        here: Counter[str] = Counter()
        unlabelled = 0

        for turn in session.history_json or []:
            if not isinstance(turn, dict) or turn.get("role") != "candidate":
                continue
            text = str(turn.get("text") or "")
            stt = turn.get("stt")
            if not isinstance(stt, dict):
                unlabelled += 1
                continue

            provider = str(stt.get("provider") or "unknown")
            here[provider] += 1
            by_provider[provider].add(text, int(stt.get("latency_ms") or 0))
            if stt.get("reason"):
                report.reasons[str(stt["reason"])] += 1

            if heard_nothing(text) or barely_heard(text):
                report.quiet.append(
                    QuietTurn(
                        session_id=str(session.id),
                        phase=str(turn.get("phase") or "-"),
                        provider=provider,
                        text=text.strip(),
                    )
                )

        report.unlabelled_turns += unlabelled
        if here:
            report.labelled_sittings += 1
            if len(here) > 1:
                report.split.append(
                    SplitSitting(
                        session_id=str(session.id),
                        band=session.overall_band,
                        counts=dict(here),
                    )
                )
        elif unlabelled:
            report.unlabelled_sittings += 1

    report.by_provider = dict(by_provider)
    return report


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "-"


def render(report: Report, days: int, show_turns: bool) -> list[str]:
    out = [f"Speaking sittings in the last {days} day(s): {report.sittings}", ""]

    total = report.labelled_turns
    if not total:
        out += [
            "No turn carries an engine label yet. The label is written as sittings",
            "are taken, so this fills in from the next exam onward.",
        ]
        if report.unlabelled_turns:
            out += [
                "",
                f"{report.unlabelled_turns} turn(s) across "
                f"{report.unlabelled_sittings} sitting(s) predate the record.",
            ]
        return out

    out.append(f"Candidate turns with a known engine: {total}")
    for name in sorted(report.by_provider):
        tally = report.by_provider[name]
        lat = tally.median_latency_ms
        out.append(
            f"  {name:<10} {tally.turns:>5} turns ({pct(tally.turns, total):>4})   "
            f"nothing heard: {tally.empty:>3}   very short: {tally.short:>3}   "
            f"median: {f'{lat}ms' if lat is not None else '-'}"
        )

    if report.reasons:
        out += ["", "Why the fallback engine was used:"]
        for reason, count in report.reasons.most_common():
            out.append(f"  {reason:<22} {count:>5}  ({pct(count, total)} of all turns)")
    else:
        out += ["", "The fallback never ran: every turn stayed on one engine."]

    out += [
        "",
        f"Sittings split between engines: {len(report.split)} of "
        f"{report.labelled_sittings} "
        f"({pct(len(report.split), report.labelled_sittings)})",
    ]
    for sitting in report.split:
        counts = ", ".join(f"{n} {c}" for n, c in sorted(sitting.counts.items()))
        band = sitting.band if sitting.band is not None else "-"
        out.append(f"    {sitting.session_id}  band {str(band):<4}  {counts}")

    if report.unlabelled_turns:
        out += [
            "",
            f"Left out: {report.unlabelled_turns} turn(s) across "
            f"{report.unlabelled_sittings} sitting(s) taken before the engine "
            "was recorded.",
        ]

    if show_turns:
        if report.quiet:
            out += ["", f"Turns where little or nothing was heard ({len(report.quiet)}):"]
            for turn in report.quiet:
                out.append(
                    f"    {turn.session_id}  {turn.phase:<6} "
                    f"{turn.provider:<7} {turn.text[:60]!r}"
                )
        else:
            out += ["", "Every labelled turn came back with a real answer."]

    return out


async def run(days: int, show_turns: bool) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    async with async_session() as db:
        sessions = (
            (
                await db.execute(
                    select(SpeakingSession)
                    .where(SpeakingSession.created_at >= cutoff)
                    .order_by(SpeakingSession.created_at)
                )
            )
            .scalars()
            .all()
        )

    if not sessions:
        print(f"No Speaking sittings in the last {days} day(s).")
        return 0

    for line in render(collect(sessions), days, show_turns):
        print(line)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument(
        "--show-turns",
        action="store_true",
        help="list the individual turns that came back empty or near-empty",
    )
    args = parser.parse_args()
    return asyncio.run(run(args.days, args.show_turns))


if __name__ == "__main__":
    raise SystemExit(main())
