"""Structured speaking test plan for the server-driven examiner.

Canonical speaking content (one speaking_part question per Part section):
  Part 1/3: { "part": 1|3, "questions": ["...", ...] }
  Part 2:   { "part": 2, "cue_card": { "topic", "bullets": [...], "follow_up"? } }

Legacy shapes are also accepted for backward compatibility.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import QuestionType
from app.models.section import Section, SectionType
from app.models.test import Test

DEFAULT_PART1: list[str] = [
    "Do you work or are you a student?",
    "What do you enjoy most about your work or studies?",
    "Let's talk about your hometown. Where are you from?",
    "What do you like most about your hometown?",
    "Do you enjoy spending time outdoors?",
]

DEFAULT_PART3_TARGET = 4

# Admin-only prompts like "[Why?]" / "[Why/Why not?]" cue the examiner to
# probe further; they must never be read aloud.
_ADMIN_HINT_RE = re.compile(r"\s*\[[^\]]*\]")


def sanitize_question(text: str) -> str:
    """Strip admin hints and collapse whitespace for spoken examiner text."""
    cleaned = _ADMIN_HINT_RE.sub("", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


@dataclass(frozen=True)
class SpeakingCueCard:
    topic: str
    bullets: list[str]
    follow_up: str | None = None


@dataclass(frozen=True)
class SpeakingPlan:
    part1: list[str]
    cue_card: SpeakingCueCard | None
    part3: list[str]
    part1_authored: bool
    part3_authored: bool
    cue_card_authored: bool

    @property
    def part1_target(self) -> int:
        return len(self.part1)

    @property
    def part3_target(self) -> int:
        if self.part3_authored:
            return len(self.part3)
        return DEFAULT_PART3_TARGET


def parse_part1_or_3(content: dict) -> list[str]:
    questions = content.get("questions")
    if isinstance(questions, list):
        cleaned = [sanitize_question(str(q)) for q in questions]
        return [q for q in cleaned if q]
    prompt = content.get("prompt")
    if isinstance(prompt, str):
        cleaned_prompt = sanitize_question(prompt)
        if cleaned_prompt:
            return [cleaned_prompt]
    return []


def parse_part2_cue(content: dict) -> SpeakingCueCard | None:
    cue = content.get("cue_card")
    if isinstance(cue, dict):
        topic = sanitize_question(str(cue.get("topic") or ""))
        bullets_raw = cue.get("bullets") or []
        bullets = (
            [b for b in (sanitize_question(str(x)) for x in bullets_raw) if b]
            if isinstance(bullets_raw, list)
            else []
        )
        follow_up = cue.get("follow_up")
        follow = sanitize_question(follow_up) if isinstance(follow_up, str) else ""
        if not topic:
            return None
        return SpeakingCueCard(topic=topic, bullets=bullets, follow_up=follow or None)
    if isinstance(cue, str):
        cleaned_cue = sanitize_question(cue)
        if cleaned_cue:
            return SpeakingCueCard(topic=cleaned_cue, bullets=[], follow_up=None)
    topic = sanitize_question(str(content.get("topic") or ""))
    if not topic:
        return None
    bullets_raw = content.get("bullets") or []
    bullets = (
        [b for b in (sanitize_question(str(x)) for x in bullets_raw) if b]
        if isinstance(bullets_raw, list)
        else []
    )
    return SpeakingCueCard(topic=topic, bullets=bullets, follow_up=None)


def format_cue_card(cue: SpeakingCueCard) -> str:
    lines = [f"Describe {cue.topic}. You should say:"]
    for bullet in cue.bullets:
        lines.append(f"- {bullet}")
    if cue.follow_up:
        lines.append(f"and explain {cue.follow_up}.")
    return "\n".join(lines)


def plan_from_sections(speaking_sections: list[Section]) -> SpeakingPlan:
    """Build a SpeakingPlan from ordered speaking sections (no DB I/O)."""
    part1_qs: list[str] = []
    part3_qs: list[str] = []
    cue: SpeakingCueCard | None = None

    if speaking_sections:
        sorted_secs = sorted(speaking_sections, key=lambda s: s.order)
        for idx, section in enumerate(sorted_secs[:3]):
            part_num = idx + 1
            questions = sorted(section.questions or [], key=lambda q: q.order)
            speaking_qs = [
                q
                for q in questions
                if (
                    q.question_type.value
                    if hasattr(q.question_type, "value")
                    else q.question_type
                )
                == QuestionType.SPEAKING_PART.value
                or str(q.question_type) == "speaking_part"
            ]
            if not speaking_qs:
                continue
            content = (
                speaking_qs[0].content
                if isinstance(speaking_qs[0].content, dict)
                else {}
            )
            explicit_part = content.get("part")
            if isinstance(explicit_part, int) and explicit_part in (1, 2, 3):
                part_num = explicit_part

            if part_num in (1, 3):
                parsed = parse_part1_or_3(content)
                if part_num == 1:
                    part1_qs = parsed
                else:
                    part3_qs = parsed
            elif part_num == 2:
                cue = parse_part2_cue(content)

    part1_authored = bool(part1_qs)
    part3_authored = bool(part3_qs)
    cue_authored = cue is not None

    return SpeakingPlan(
        part1=list(part1_qs) if part1_authored else list(DEFAULT_PART1),
        cue_card=cue,
        part3=list(part3_qs),
        part1_authored=part1_authored,
        part3_authored=part3_authored,
        cue_card_authored=cue_authored,
    )


def default_speaking_plan() -> SpeakingPlan:
    return SpeakingPlan(
        part1=list(DEFAULT_PART1),
        cue_card=None,
        part3=[],
        part1_authored=False,
        part3_authored=False,
        cue_card_authored=False,
    )


async def load_speaking_plan(
    test_id: uuid.UUID | None,
    db: AsyncSession,
) -> SpeakingPlan:
    """Load authored speaking content for a test, or return defaults."""
    if test_id is None:
        return default_speaking_plan()

    result = await db.execute(
        select(Test)
        .options(selectinload(Test.sections).selectinload(Section.questions))
        .where(Test.id == test_id)
    )
    test = result.scalar_one_or_none()
    if test is None:
        return default_speaking_plan()

    speaking = [
        s
        for s in (test.sections or [])
        if (s.type.value if hasattr(s.type, "value") else s.type)
        == SectionType.SPEAKING.value
        or str(s.type) == "speaking"
    ]
    return plan_from_sections(speaking)


def format_plan_as_context(plan: SpeakingPlan) -> str | None:
    """Legacy string form used by the session-less Gemini path."""
    if not plan.part1_authored and not plan.cue_card_authored and not plan.part3_authored:
        return None

    lines: list[str] = [
        "TEST-SPECIFIC QUESTIONS — use these instead of inventing topics:",
        "",
    ]
    if plan.part1_authored:
        lines.append("PART 1 QUESTIONS (ask these one at a time, in order):")
        for q in plan.part1:
            lines.append(f"- {q}")
        lines.append("")
    if plan.cue_card is not None:
        lines.append("PART 2 CUE CARD (use this exact topic):")
        lines.append(format_cue_card(plan.cue_card))
        lines.append("")
    if plan.part3_authored:
        lines.append("PART 3 QUESTIONS (ask these one at a time, in order):")
        for q in plan.part3:
            lines.append(f"- {q}")
        lines.append("")

    lines.append(
        "Follow the STRUCTURE and RULES from your system prompt, but prefer "
        "the questions/cue card above over inventing new ones."
    )
    return "\n".join(lines).strip()
