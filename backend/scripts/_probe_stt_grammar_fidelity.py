#!/usr/bin/env python3
"""Does the transcriber repair the candidate's grammar before we mark it?

Grammatical range and accuracy is a scored IELTS criterion. If the engine that
turns speech into text quietly fixes "he go to school" into "he goes to school",
the examiner marks a sentence the candidate never produced, and the band goes up
for a mistake that was actually made. Nothing downstream can detect this: the
transcript looks like ordinary fluent English.

The risk is not symmetric between engines. Whisper is a dedicated recogniser.
Gemini is a general model performing recognition as a side task, and general
models are trained to produce well-formed text. Before making either one the
primary engine, we should know which of them hands back what was said.

Method: speak a sentence containing one deliberate learner error, then check
whether the transcript matches what was spoken or the corrected form. Both are
written out in advance, so the verdict is a string comparison rather than a
judgement call.

The audio is clean, native-accented text-to-speech — deliberately the easiest
case there is. An engine that rewrites grammar here will certainly rewrite it on
a nervous student with an accent, so a clean result is a floor, not a passing
grade.

    python scripts/_probe_stt_grammar_fidelity.py
    python scripts/_probe_stt_grammar_fidelity.py --models gemini-3.1-flash-lite,gemini-3.1-pro
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import re
import sys
from pathlib import Path

import edge_tts

from app.core.config import settings
from app.services import llm

# A British newsreader is the easiest audio an engine will ever get, which is
# what makes it the right control for the grammar question: anything rewritten
# here was rewritten by choice rather than out of uncertainty.
#
# The accented voices only approximate the harder case. Edge TTS refuses to read
# English in a Russian or Turkic voice, so nothing here sounds like an Uzbek
# candidate; these are second-language Englishes of a different family. They
# stress the recogniser, which is the point, but a difference measured on them
# is a hint about our students, not a measurement of them.
CLEAN_VOICE = "en-GB-SoniaNeural"
ACCENTED_VOICES = ("en-IN-NeerjaNeural", "en-NG-EzinneNeural")

AUDIO_ROOT = Path(__file__).parent / "_grammar_audio"

# (label, what the candidate says, what a "helpful" engine would turn it into)
# Every error here is one an IELTS examiner is paid to notice.
CASES: list[tuple[str, str, str]] = [
    (
        "subject-verb agreement",
        "My brother go to school every morning.",
        "My brother goes to school every morning.",
    ),
    (
        "missing article",
        "I want to be doctor in the future.",
        "I want to be a doctor in the future.",
    ),
    (
        "plural after many",
        "I have many friend in my city.",
        "I have many friends in my city.",
    ),
    (
        "past tense",
        "Yesterday I go to the market with my mother.",
        "Yesterday I went to the market with my mother.",
    ),
    (
        "double past marking",
        "She didn't went to the party last night.",
        "She didn't go to the party last night.",
    ),
    (
        "be plus agree",
        "I am agree with this opinion completely.",
        "I agree with this opinion completely.",
    ),
    (
        "uncountable noun",
        "There are many informations on the internet.",
        "There is a lot of information on the internet.",
    ),
    (
        "double comparative",
        "This one is more better than the other one.",
        "This one is better than the other one.",
    ),
    (
        "conditional",
        "If I would have money, I will travel to Japan.",
        "If I had money, I would travel to Japan.",
    ),
    (
        "question word order",
        "I don't know what is the answer of this question.",
        "I don't know what the answer to this question is.",
    ),
    # Controls: already correct. If these come back altered, the engine is
    # unreliable in a way that has nothing to do with grammar.
    (
        "control, correct",
        "I usually study in the library because it is quiet there.",
        "I usually study in the library because it is quiet there.",
    ),
    (
        "control, correct",
        "My hometown is famous for its old market and its food.",
        "My hometown is famous for its old market and its food.",
    ),
]


def words(text: str) -> list[str]:
    """Compare what was said, not how it was punctuated."""
    return re.sub(r"[^\w\s']", " ", text.lower()).split()


def error_rate(heard: str, spoken: str) -> tuple[int, int]:
    """Words the engine got wrong, over words actually spoken."""
    said, got = words(spoken), words(heard)
    matched = sum(
        block.size for block in difflib.SequenceMatcher(a=said, b=got).get_matching_blocks()
    )
    return max(len(said) - matched, 0), len(said)


async def render_all(voice: str) -> list[Path]:
    out = AUDIO_ROOT / voice
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, (_label, spoken, _fixed) in enumerate(CASES, start=1):
        path = out / f"case_{i:02d}.mp3"
        if not path.exists():
            await edge_tts.Communicate(spoken, voice).save(str(path))
        paths.append(path)
    return paths


# Some Gemini models answer 503 for minutes on end, and the client politely
# retries through all of it. A probe that stalls teaches nothing, so give up and
# record the failure — an engine we cannot reach is a finding in its own right.
CALL_TIMEOUT_S = 45


async def transcribe(engine: str, audio: bytes) -> str:
    if engine == "groq":
        return await asyncio.wait_for(
            llm._transcribe_with_groq(audio, "audio/mpeg"), CALL_TIMEOUT_S
        )
    original = settings.gemini_stt_model
    settings.gemini_stt_model = engine
    try:
        return await asyncio.wait_for(
            llm._transcribe_with_gemini(audio, "audio/mpeg"), CALL_TIMEOUT_S
        )
    finally:
        settings.gemini_stt_model = original


def verdict(heard: str, spoken: str, fixed: str) -> str:
    got = words(heard)
    if got == words(spoken):
        return "verbatim"
    if got == words(fixed):
        return "REPAIRED"
    return "misheard"


async def run(engines: list[str], voice: str, quiet: bool) -> int:
    print(f"Rendering {len(CASES)} sentences with {voice} ...")
    paths = await render_all(voice)

    tallies: dict[str, dict[str, int]] = {
        e: {"verbatim": 0, "REPAIRED": 0, "misheard": 0, "failed": 0} for e in engines
    }
    wrong: dict[str, int] = {e: 0 for e in engines}
    total: dict[str, int] = {e: 0 for e in engines}

    for i, ((label, spoken, fixed), path) in enumerate(zip(CASES, paths), start=1):
        audio = path.read_bytes()
        print(f"\n{i:2d}. {label}")
        print(f"    said:  {spoken}")
        for engine in engines:
            try:
                heard = await transcribe(engine, audio)
            except Exception as exc:  # a probe must survive one dead provider
                tallies[engine]["failed"] += 1
                print(f"    {engine:<26} FAILED  {type(exc).__name__}: {exc}"[:180])
                continue

            call = verdict(heard, spoken, fixed)
            tallies[engine][call] += 1
            bad, said = error_rate(heard, spoken)
            wrong[engine] += bad
            total[engine] += said
            if not quiet or call != "verbatim":
                print(f"    {engine:<26} {call:<9} {heard}")

    print("\n" + "=" * 78)
    print(f"voice: {voice}")
    print(
        f"{'engine':<26} {'verbatim':>9} {'REPAIRED':>9} {'misheard':>9} "
        f"{'failed':>7} {'word err':>9}"
    )
    for engine in engines:
        t = tallies[engine]
        rate = f"{100 * wrong[engine] / total[engine]:.1f}%" if total[engine] else "-"
        print(
            f"{engine:<26} {t['verbatim']:>9} {t['REPAIRED']:>9} "
            f"{t['misheard']:>9} {t['failed']:>7} {rate:>9}"
        )

    print(
        "\nREPAIRED is the one that matters: the candidate's error was silently\n"
        "corrected, so the examiner would mark a sentence that was never spoken.\n"
        "misheard and word err measure plain accuracy instead."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        default=f"groq,{settings.gemini_stt_model}",
        help="comma-separated: 'groq' plus any Gemini model names to try",
    )
    parser.add_argument(
        "--voice",
        default=CLEAN_VOICE,
        help=f"Edge TTS voice. Try {' or '.join(ACCENTED_VOICES)} for a harder case.",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="print only the transcripts that differ"
    )
    args = parser.parse_args()
    engines = [e.strip() for e in args.models.split(",") if e.strip()]
    if not engines:
        print("Nothing to test.")
        return 1
    return asyncio.run(run(engines, args.voice, args.quiet))


if __name__ == "__main__":
    sys.exit(main())
