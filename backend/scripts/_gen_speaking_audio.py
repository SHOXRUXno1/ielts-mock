#!/usr/bin/env python3
"""Generate spoken candidate answers for the Speaking load test.

Uses Edge TTS (free) to render one MP3 per turn. Content matches the authored
Cambridge IELTS 16 Test 1 speaking plan (Part 1 "people you study/work with",
Part 2 "a tourist attraction you enjoyed visiting", Part 3 tourism) so the
examiner flow and the Gemini scoring both see coherent input.

  python scripts/_gen_speaking_audio.py

Writes to scripts/_speaking_audio/turn_NN.mp3
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

VOICE = "en-GB-SoniaNeural"
OUT_DIR = Path(__file__).parent / "_speaking_audio"

# One entry per candidate turn, in the order the examiner asks for them.
ANSWERS: list[str] = [
    # 1. Name
    "My name is Amina Karimova.",
    # 2. Nickname
    "Most people just call me Amina, so please use that.",
    # 3. Part 1 — who do you spend most time studying with
    "I spend most of my study time with two classmates from my university "
    "course. We meet in the library almost every afternoon because we are "
    "taking the same economics modules, and it is much easier to stay "
    "motivated when other people are working next to you.",
    # 4. Part 1 — what kinds of things do you work on together
    "We mostly work on problem sets and group presentations together. Our "
    "lecturers give us case studies that are quite complicated, so we split "
    "the reading between us and then explain the difficult parts to each "
    "other. I find that explaining something out loud helps me understand it "
    "far better than reading silently.",
    # 5. Part 1 — times when you prefer to study alone
    "Yes, definitely. When I need to memorise something or write an essay, I "
    "prefer to be completely alone, usually early in the morning before the "
    "flat gets noisy. Group work is useful for discussion, but for writing I "
    "need silence and no interruptions at all.",
    # 6. Part 1 — is it easy to make friends with people you study with
    "I would say it is fairly easy, because you already have something in "
    "common and you see each other every day. Having said that, some people "
    "keep a clear line between classmates and real friends, and I think that "
    "is perfectly reasonable.",
    # 7. Part 1 — do you prefer studying with older or younger people
    "I slightly prefer studying with people who are a bit older than me. They "
    "tend to be more organised and they have already made the mistakes I am "
    "about to make, so I can learn from their experience instead of my own.",
    # 8. Part 2 — the long monologue (cue card: a tourist attraction)
    "I would like to talk about Registan Square in Samarkand, which is "
    "probably the most impressive place I have ever visited. It is a large "
    "public square surrounded by three enormous madrasahs, and the whole "
    "complex is covered in blue and turquoise tilework that seems to change "
    "colour depending on the light. I went there two summers ago with my "
    "cousin, mainly because she had just finished her degree and we wanted a "
    "short holiday somewhere that did not require a long flight. We arrived "
    "quite early in the morning to avoid the heat, and that turned out to be "
    "an excellent decision, because the square was almost empty and we could "
    "take photographs without crowds of people in the background. We spent "
    "several hours simply walking around the courtyards and looking at the "
    "decoration in detail. Later a local guide explained the history of the "
    "buildings to us, including how they were used as a university hundreds "
    "of years ago, and in the evening we came back to see the whole square "
    "lit up. The reason I enjoyed it so much is that photographs really do "
    "not prepare you for the scale of it. Standing in the middle of that "
    "square, you get a very physical sense of how ambitious the people who "
    "built it were, and that feeling stayed with me long after the trip "
    "finished.",
    # 9. Rounding question after Part 2
    "Yes, I would happily go back, particularly in autumn when the weather is "
    "cooler and there are fewer tour groups.",
    # 10. Part 3 — most popular tourist attractions in your country
    "The most popular attractions in my country are definitely the historical "
    "cities along the old Silk Road, because they combine architecture and "
    "history in a way that is quite rare. Alongside those, the mountain areas "
    "near the capital attract a lot of domestic visitors at the weekend, "
    "since they are close enough for a day trip and cost almost nothing to "
    "enter.",
    # 11. Part 3 — how have the types of attraction changed
    "I think there has been a clear shift away from purely sightseeing towards "
    "experiences that visitors take part in. Twenty years ago people were "
    "satisfied with looking at a monument and taking a photograph, whereas now "
    "they want cooking classes, craft workshops or hiking routes. Social media "
    "has accelerated that change, because an unusual experience is far more "
    "shareable than a standard photograph of a famous building.",
    # 12. Part 3 — advantages and disadvantages of international tourism
    "The obvious advantage is economic, since tourism creates employment in "
    "regions that often have very few other industries, and it gives local "
    "authorities a financial reason to protect historical sites. The "
    "disadvantages are equally real, though. Popular places can become so "
    "crowded that residents are pushed out by rising prices, and the character "
    "of a neighbourhood can be reduced to whatever sells well to visitors.",
    # 13. Part 3 — should governments limit visitor numbers
    "On balance I believe they should, at least at the most fragile sites. "
    "Limiting numbers through timed tickets seems fairer than simply raising "
    "prices, because raising prices only excludes people who cannot afford "
    "them rather than reducing the overall damage. The revenue from those "
    "tickets could then be reinvested directly into conservation work.",
    # 14. Spare turn in case the plan runs longer than expected
    "That is an interesting question. I think the answer depends a great deal "
    "on the specific country, but broadly speaking I would say the benefits "
    "outweigh the drawbacks as long as the growth is managed carefully rather "
    "than left entirely to the market.",
]


async def render(index: int, text: str) -> None:
    path = OUT_DIR / f"turn_{index:02d}.mp3"
    await edge_tts.Communicate(text, VOICE).save(str(path))
    size_kb = path.stat().st_size / 1024
    print(f"  turn_{index:02d}.mp3  {size_kb:7.1f} KB  {len(text.split()):3d} words")


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendering {len(ANSWERS)} answers with {VOICE} -> {OUT_DIR}")
    # Sequential: Edge TTS throttles aggressive parallel use.
    for i, text in enumerate(ANSWERS, start=1):
        await render(i, text)
    total = sum(p.stat().st_size for p in OUT_DIR.glob("turn_*.mp3")) / 1024
    print(f"Done. {total:.0f} KB total.")


if __name__ == "__main__":
    asyncio.run(main())
