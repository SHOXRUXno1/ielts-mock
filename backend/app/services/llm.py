"""LLM integration: Gemini for writing/speaking evaluation, Chirp then Whisper for transcription."""

import asyncio
import base64
import json
import logging
import mimetypes
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.rate_limiter import (
    KeyRotator,
    get_groq_stt_bucket,
    get_whisper_pool,
)
from app.services import google_stt, usage_meter
from app.services.scoring import compute_writing_band
from app.services.shared_http import get_http_client
from app.services.storage import resolve_local_path

logger = logging.getLogger(__name__)

_rotator: KeyRotator | None = None
# Groq STT is currently 403 from some VPS regions / revoked keys. Skip after
# the first hard reject so every speaking turn does not wait on a dead provider.
_groq_stt_blocked: bool = False
_EMPTY_STT_MARKERS = frozenset(
    {
        "",
        "empty",
        "(empty)",
        "[empty]",
        "no speech",
        "(no speech)",
        "no speech detected",
        "[no speech]",
    }
)

# Whisper never answers "nothing". Given audio without speech it invents a short
# stock phrase, and that invention was being stored as the candidate's answer:
# in one live sitting five of six Part 1 turns came back "Thank you.", and the
# intro reply became the student's name, so the examiner addressed her as
# "Thank" for the rest of the exam.
#
# Probed against the live Groq API (scripts/_probe_stt_silence.py): digital
# silence transcribes as "you", while microphone room tone and mains hum both
# transcribe as ".".
#
# The model's own confidence cannot catch this. For room tone Groq reports
# no_speech_prob 0.089 and avg_logprob -0.19 — figures that describe clean,
# confident speech. Only the text gives the game away, so the text is what we
# read. Every phrase here is a stock filler no candidate would offer as their
# whole answer; a genuinely brief reply such as "Call me Sasha" is untouched.
_SILENCE_HALLUCINATIONS = frozenset(
    {
        "you",
        "thank you",
        "thank you very much",
        "thanks",
        "thanks a lot",
        "thank you for watching",
        "thanks for watching",
        "thank you for listening",
        "please subscribe",
        "subscribe",
        "bye",
        "goodbye",
        "bye bye",
        "the end",
        "you you",
    }
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def reset_groq_stt_circuit() -> None:
    global _groq_stt_blocked
    _groq_stt_blocked = False


def _block_groq_stt(reason: str) -> None:
    global _groq_stt_blocked
    if not _groq_stt_blocked:
        logger.error("Disabling Groq STT for this process (%s)", reason)
    _groq_stt_blocked = True


def _strip_for_match(text: str) -> str:
    """Reduce a phrase to bare words for comparison against the stock list."""
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def _is_silence_hallucination(text: str) -> bool:
    """True when the transcript is Whisper talking to itself over silence.

    Sentences are de-duplicated first: fed a quiet microphone the model often
    repeats one filler, and "Thank you. Thank you." is no more an answer than a
    single "Thank you." is.
    """
    bare = _strip_for_match(text)
    if not bare:
        # Punctuation only — "." and "..." are what room tone returns.
        return True
    unique = {
        _strip_for_match(s)
        for s in _SENTENCE_SPLIT_RE.split(text.strip())
        if _strip_for_match(s)
    }
    return bool(unique) and unique <= _SILENCE_HALLUCINATIONS


def _normalize_stt_text(text: str) -> str:
    """Turn a provider's output into the candidate's words, or "" if there were none.

    Returning "" matters: the caller answers 400 and the candidate is asked to
    speak again, which is the honest outcome when nothing was recorded. Storing
    the model's invention instead marks a student on words they never said.
    """
    cleaned = text.strip().strip('"').strip()
    if cleaned.lower() in _EMPTY_STT_MARKERS:
        return ""
    if _is_silence_hallucination(cleaned):
        logger.info("Discarding silence hallucination from STT: %r", cleaned[:80])
        return ""
    return cleaned


def _gemini_url(model: str | None = None) -> str:
    return (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/{model or settings.gemini_model}:generateContent"
    )


def get_rotator() -> KeyRotator:
    global _rotator
    if _rotator is None:
        _rotator = KeyRotator(settings.gemini_key_list, settings.gemini_rpm_limit)
    return _rotator


def _key_prefix(key: str) -> str:
    return key[:10]


_KEY_IN_URL_RE = re.compile(r"([?&]key=)[^&\s'\"]+")


def redact_api_keys(text: str) -> str:
    """Strip API keys out of text bound for a log, the database or the admin UI.

    An httpx error quotes the request URL, and Gemini takes its key as a query
    parameter, so the raw message carries a live credential.
    """
    return _KEY_IN_URL_RE.sub(r"\1REDACTED", text)


def _redacted(exc: httpx.HTTPStatusError) -> httpx.HTTPStatusError:
    """Strip the key from a failure's message, in place.

    Rewriting the original rather than raising a replacement keeps the key out
    of the chained exception a replacement would carry behind it.
    """
    exc.args = tuple(
        redact_api_keys(arg) if isinstance(arg, str) else arg for arg in exc.args
    )
    return exc


def _retry_after_seconds(response: httpx.Response) -> float:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return 2.0
    try:
        return max(float(raw), 1.0)
    except ValueError:
        return 2.0


async def _gemini_request_with_rotation(
    call_fn: Callable[[str], Awaitable[httpx.Response]],
    *,
    max_retries: int | None = None,
) -> httpx.Response:
    """Execute a Gemini HTTP call, rotating keys on 429."""
    keys = settings.gemini_key_list
    if not keys:
        raise RuntimeError("No Gemini API keys configured")

    if max_retries is None:
        max_retries = max(len(keys) * 3, 6)

    rotator = get_rotator()
    last_exc: httpx.HTTPStatusError | None = None

    for attempt in range(max_retries):
        api_key = keys[attempt % len(keys)]
        await rotator.acquire_for(api_key)
        logger.debug(
            "Gemini request key %s..., attempt %d/%d",
            _key_prefix(api_key),
            attempt + 1,
            max_retries,
        )

        try:
            resp = await call_fn(api_key)
            resp.raise_for_status()
            usage_meter.record_gemini_call()
            return resp
        except httpx.HTTPStatusError as e:
            last_exc = e
            status = e.response.status_code
            has_more_attempts = attempt < max_retries - 1
            keys_left_in_cycle = len(keys) - ((attempt % len(keys)) + 1)

            if status == 429:
                usage_meter.record_gemini_rate_limited()

            if status == 429 and has_more_attempts:
                if keys_left_in_cycle > 0:
                    logger.warning(
                        "Gemini 429 on key %s..., trying next key (attempt %d/%d)",
                        _key_prefix(api_key),
                        attempt + 1,
                        max_retries,
                    )
                    continue
                wait = _retry_after_seconds(e.response)
                logger.warning(
                    "Gemini 429 on key %s..., attempt %d/%d, retry in %.1fs",
                    _key_prefix(api_key),
                    attempt + 1,
                    max_retries,
                    wait,
                )
                await asyncio.sleep(wait)
                continue
            if status >= 500 and has_more_attempts:
                if status == 503 and keys_left_in_cycle > 0:
                    logger.warning(
                        "Gemini 503 on key %s..., trying next key (attempt %d/%d)",
                        _key_prefix(api_key),
                        attempt + 1,
                        max_retries,
                    )
                    continue
                wait = min(2 ** attempt, 8)
                logger.warning(
                    "Gemini %s on key %s..., retrying in %ds (attempt %d/%d)",
                    status,
                    _key_prefix(api_key),
                    wait,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(wait)
                continue
            raise _redacted(e)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(
                    "Gemini network error on key %s..., retrying in %ds (attempt %d/%d)",
                    _key_prefix(api_key),
                    wait,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(wait)
                continue
            raise

    raise (_redacted(last_exc) if last_exc else RuntimeError("Gemini call failed"))


def _count_words(text: str) -> int:
    return len([w for w in text.strip().split() if w])


# ---------------------------------------------------------------------------
# Writing prompt — distinguishes Task 1 vs Task 2 with band descriptors
# ---------------------------------------------------------------------------

WRITING_PROMPT = """You are a certified IELTS examiner with 10+ years of experience.
Evaluate the following IELTS Writing **{task_label}** response.

### Task type
{task_type_description}

### Minimum word count
{min_words} words. If the response is significantly under the minimum, penalise
{task_criterion_name} accordingly (typically -1 band).

{image_instruction}
{essay_type_criteria}
### Task statement
{task_statement}

### Task question
{task_question}

### Instruction to the student
{task_instruction}

### Student's response
{text}

### Evaluation criteria — use official IELTS band descriptors for each band level
1. **{task_criterion_name}**
{task_criterion_descriptors}
2. **Coherence and Cohesion**
   - Band 9: Uses cohesion in such a way that it attracts no attention; paragraphing is well managed.
   - Band 8: Sequences information logically; manages cohesion well; uses paragraphing sufficiently.
   - Band 7: Logically organises information and ideas; clear overall progression; some over-/under-use of cohesive devices.
   - Band 6: Generally arranges information coherently; uses cohesive devices effectively, but mechanical use is noticeable.
   - Band 5: Organisation is evident but not wholly logical; limited use of cohesive devices; paragraphing may be inadequate.
3. **Lexical Resource**
   - Band 9: Wide range of vocabulary; very natural and sophisticated control; rare minor slips only.
   - Band 8: Wide resource; fluent and flexible use; minor errors in style or collocation.
   - Band 7: Sufficient range; some awareness of style and collocation; occasional errors in word choice or spelling.
   - Band 6: Adequate range; attempts to use less common vocabulary but with some inaccuracy; some errors in spelling or word formation.
   - Band 5: Limited range; noticeable errors in spelling or word formation; may cause some difficulty for the reader.
4. **Grammatical Range and Accuracy**
   - Band 9: Wide range of structures; full flexibility and accuracy; rare minor errors.
   - Band 8: Wide range of structures; majority of sentences error-free; only occasional errors or inappropriacies.
   - Band 7: Variety of complex structures; frequent error-free sentences; good control; few errors.
   - Band 6: Mix of simple and complex sentence forms; some errors; generally good control.
   - Band 5: Limited range of structures; attempts complex sentences but errors are frequent.

### Off-topic penalty
If the response is largely irrelevant to the prompt, cap {task_criterion_name} at 4.
Coherence and Cohesion, Lexical Resource and Grammatical Range are assessed ONLY
on the quality of the language itself. Never reduce, zero out or "nullify" them
because the content is off-topic, irrelevant or describes the wrong data — a
well-written off-topic response still scores highly on those three criteria.
Band 0 is reserved for a blank response; any response containing writing scores
at least Band 1 on every criterion.

### Key points extraction (Task 1 with chart/visual)
{key_points_instruction}

### Sentence-by-sentence analysis
Split the student's response into individual sentences. For EACH sentence provide:
- "sentence": the exact sentence text
- "category": one of "hit_key_point" | "linking_issue" | "grammatical_error" | "lexical_issue" | "off_topic"
- "comment": brief reason for the classification
- "reference": (optional) for hit_key_point — which key point or idea it covers

Use "hit_key_point" when the sentence correctly covers a relevant idea/data point.
Use "linking_issue" for cohesion/transition problems.
Use "grammatical_error" / "lexical_issue" when that is the dominant problem in the sentence.
Use "off_topic" when the sentence does not address the task.

### Inline errors
Identify up to 12 of the most significant errors or weaknesses in the student's text.
For each error, provide an EXACT substring that appears verbatim in the student's response
(so it can be highlighted client-side), the error category, a corrected version, and a brief explanation.
Focus on errors that most impact the band score.

### Overall review
Write 1–2 short paragraphs summarising the response's main strengths and weaknesses
and what the student should prioritise next.

### Optimized composition
Rewrite the student's response at Band 8–9 level while:
- Keeping the student's main points and overall structure
- Fixing grammatical and lexical errors
- Improving cohesion and precision
- Correcting any data inconsistencies (especially for Task 1)
- Keeping the rewrite at most 20% longer than the original

### Output format
Return ONLY valid JSON (no markdown, no code fences):
{{
  "task_achievement": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "coherence_cohesion": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "lexical_resource": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "grammatical_range": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "overall_band": <float, multiple of 0.5>,
  "strengths": ["<string>", ...],
  "improvements": ["<string>", ...],
  "errors": [
    {{
      "quote": "<exact verbatim substring from the student response>",
      "type": "grammar|lexical|spelling|cohesion|punctuation",
      "correction": "<corrected version of that phrase>",
      "explanation": "<short reason, max 15 words>"
    }}
  ],
  "key_points": [
    {{"point": "<key data point or idea>", "covered": <true|false>}}
  ],
  "sentence_analysis": [
    {{
      "sentence": "<exact sentence from student response>",
      "category": "hit_key_point|linking_issue|grammatical_error|lexical_issue|off_topic",
      "comment": "<brief reason>",
      "reference": "<optional key point reference>"
    }}
  ],
  "overall_review": "<1-2 paragraph summary>",
  "optimized_composition": "<full Band 8-9 rewrite>"
}}

Note: the JSON key is always "task_achievement" regardless of task number, for system compatibility.
For Task 2 (essay), set "key_points" to [] (or omit).
CRITICAL SCORING RULE:
Individual criteria scores (Task Achievement/Response, Coherence & Cohesion,
Lexical Resource, Grammatical Range & Accuracy) MUST be WHOLE NUMBERS ONLY
(0, 1, 2, 3, 4, 5, 6, 7, 8, 9).
Half bands like 6.5, 7.5, 8.5 are NOT allowed at the individual criterion level.
Only the final Task Band (overall_band, average of 4 criteria) may contain .5 values.
Return integer values for individual criteria in the JSON output.
overall_band = average of 4 criteria rounded to nearest 0.5.
Be strict but fair, calibrated to official Cambridge IELTS sample answers.
Every "quote" in errors MUST be an EXACT substring of the student's response — copy it character-for-character."""

_SENTENCE_CATEGORIES = frozenset({
    "hit_key_point",
    "linking_issue",
    "grammatical_error",
    "lexical_issue",
    "off_topic",
})

_KEY_POINTS_INSTRUCTION_WITH_CHART = """\
Step 1: Analyse the chart/visual and extract 5–8 key data points
(trends, peaks, troughs, specific numbers, comparisons, overview).
Step 2: Evaluate whether the student's response accurately covered each point.
Return them in "key_points" with covered=true/false."""

_KEY_POINTS_INSTRUCTION_TASK1_NO_CHART = """\
Extract 5–8 key points the Task 1 response should cover based on the prompt
(overview, main trends, comparisons, notable figures). Mark each as covered
or missed relative to the student's text. Return in "key_points"."""

_KEY_POINTS_INSTRUCTION_TASK2 = """\
This is Task 2 (essay). Do NOT extract chart data points.
Set "key_points" to an empty array []."""

# Per-task criterion name and band descriptors (official IELTS terminology)
_TASK1_CRITERION_NAME = "Task Achievement"
_TASK1_CRITERION_DESCRIPTORS = """\
   - Band 9: Fully covers the requirements of the task; accurately describes key features and presents a clear overview; data/information are appropriately selected and highlighted.
   - Band 8: Covers the requirements of the task; presents, highlights, and illustrates key features/bullet points clearly; may over-generalise or omit some features.
   - Band 7: Covers the requirements of the task; clearly presents and highlights key features but could be more fully extended.
   - Band 6: Addresses the requirements of the task; a relevant overview is attempted; some details may be inaccurate, irrelevant, or missing.
   - Band 5: Generally addresses the task but the format may be inappropriate; key features may be inadequately covered, inaccurate, or absent."""

_TASK2_CRITERION_NAME = "Task Response"
_TASK2_CRITERION_DESCRIPTORS = """\
   - Band 9: Fully addresses all parts of the task; position is fully developed with relevant, extended, and well-supported ideas.
   - Band 8: Sufficiently addresses all parts of the task; position is clear; main ideas are relevant, well extended, and supported.
   - Band 7: Addresses all parts of the task; clear position with relevant main ideas; some ideas may be insufficiently developed.
   - Band 6: Addresses the task, though some parts may be more fully covered; position is relevant but conclusions may be unclear.
   - Band 5: Addresses the task only partially; format may be inappropriate; position may not be consistent."""

_ESSAY_TYPE_CRITERIA: dict[str, str] = {
    "opinion": (
        "### Essay subtype: Opinion (Agree/Disagree)\n"
        "The student must take a clear side in the introduction and maintain that position "
        "consistently. Supporting reasons should include concrete examples. "
        "Penalise Task Response if the essay is balanced without a clear stance, "
        "or if the position shifts mid-essay."
    ),
    "discussion": (
        "### Essay subtype: Discussion (Both views + opinion)\n"
        "The student must cover both views fairly before giving a clear personal opinion "
        "with reasoning. Penalise Task Response if one side is missing or if the personal "
        "opinion is skipped or only vaguely stated."
    ),
    "problem_solution": (
        "### Essay subtype: Problem & Solution\n"
        "Problems must be clearly identified and solutions must directly address those "
        "problems with some feasibility. Penalise Task Response for imbalance "
        "(only problems, or only solutions) or for solutions that do not match the problems."
    ),
    "advantages_disadvantages": (
        "### Essay subtype: Advantages & Disadvantages\n"
        "Both advantages and disadvantages must be covered in a balanced way. "
        "If the prompt asks for a verdict or opinion, it must be present with reasoning. "
        "Penalise Task Response for one-sided coverage or a missing required verdict."
    ),
    "double_question": (
        "### Essay subtype: Double Question\n"
        "Both questions in the prompt must be answered directly with roughly equal depth. "
        "Penalise Task Response heavily if one question is skipped or answered only tangentially."
    ),
}

# ---------------------------------------------------------------------------
# Speaking prompt — with descriptors and question context
# ---------------------------------------------------------------------------

SPEAKING_PROMPT = """You are a certified IELTS examiner with 10+ years of experience.
Evaluate the following IELTS Speaking transcript.

### Questions / cue-card prompts given to the student
{questions}

### Transcript (auto-generated via speech-to-text, may contain minor transcription artifacts)
{transcript}

### Evaluation criteria (official IELTS band descriptors)
1. **Fluency and Coherence**
   - Band 9: Speaks fluently with only rare repetition or self-correction. Any hesitation is content-related. Topic developed coherently and appropriately.
   - Band 8: Speaks fluently with only occasional repetition or self-correction. Develops topics coherently and appropriately.
   - Band 7: Speaks at length without noticeable effort or loss of coherence. May demonstrate language-related hesitation at times. Uses a range of connectives and discourse markers with some flexibility.
   - Band 6: Is willing to speak at length though may lose coherence at times due to occasional repetition, self-correction or hesitation. Uses a range of connectives and discourse markers but not always appropriately.
   - Band 5: Usually maintains flow of speech but uses repetition, self-correction and/or slow speech to keep going. May over-use certain connectives and discourse markers.
   - Band 4: Cannot respond without noticeable pauses and may speak slowly. May self-correct and repeat. Links basic sentences but with repetitious use of simple connectives.
   - Band 3: Speaks with long pauses. Has limited ability to link simple sentences. Gives only simple responses and is frequently unable to convey basic message.
2. **Lexical Resource**
   - Band 9: Uses vocabulary with full flexibility and precision in all topics.
   - Band 8: Uses a wide vocabulary resource readily and flexibly. Uses less common and idiomatic vocabulary skilfully.
   - Band 7: Uses vocabulary resource flexibly to discuss a variety of topics. Uses some less common and idiomatic vocabulary.
   - Band 6: Has a wide enough vocabulary to discuss topics at length. Generally paraphrases successfully.
   - Band 5: Manages to talk about familiar and unfamiliar topics but uses vocabulary with limited flexibility. Attempts to use paraphrase but with mixed success.
   - Band 4: Is able to talk about familiar topics but can only convey basic meaning and may be unable to express less common ideas.
   - Band 3: Uses simple vocabulary to convey personal information. Has insufficient vocabulary for less familiar topics.
3. **Grammatical Range and Accuracy**
   - Band 9: Uses a full range of structures naturally and appropriately. Produces consistently accurate structures apart from slips.
   - Band 8: Uses a wide range of structures flexibly. Produces a majority of error-free sentences with only very occasional inappropriacies.
   - Band 7: Uses a range of complex structures with some flexibility. Frequently produces error-free sentences though some grammatical mistakes persist.
   - Band 6: Uses a mix of simple and complex structures but with limited flexibility. May make frequent mistakes with complex structures though these rarely cause comprehension problems.
   - Band 5: Produces basic sentence forms with reasonable accuracy. Uses a limited range of more complex structures but these usually contain errors.
   - Band 4: Produces basic sentence forms and some correct simple sentences but subordinate structures are rare. Errors are frequent and may lead to misunderstanding.
   - Band 3: Attempts basic sentence forms but with limited success. Errors are predominant.
4. **Pronunciation**
   - Band 9: Uses a full range of pronunciation features with precision and subtlety.
   - Band 8: Uses a wide range of pronunciation features. Sustained use of flexible features.
   - Band 7: Shows all positive features of Band 6 and some of Band 8. Generally easy to understand.
   - Band 6: Uses a range of pronunciation features with mixed control. Can generally be understood.
   - Band 5: Shows some effective use of features but this is not sustained. Mispronunciations are frequent and cause some difficulty for listener.
   - Band 4: Uses a limited range of pronunciation features. Mispronunciations are frequent and understanding requires some effort.
   - Band 3: Shows some simple features but unintelligible speech is more frequent.

   IMPORTANT for Pronunciation: you are reading a transcript, not listening to
   the candidate, so you hold no evidence about how they actually sound.
   Speech-to-text errors, odd word choices and broken fragments come from the
   microphone and the transcription model, not from the speaker's mouth, and a
   non-native accent that the model handles poorly is not a pronunciation fault.
   Never lower this criterion for any of them. With no audio to judge, award the
   band supported by the candidate's demonstrated command of spoken English,
   in line with the other three criteria, and say in the feedback that
   pronunciation could not be assessed directly from a recording.

### Relevance check
If the student's response does not address the given questions/cue card, cap Fluency and Coherence at 4.

### Output format
Return ONLY valid JSON (no markdown, no code fences):
{{
  "fluency_coherence": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "lexical_resource": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "grammatical_range": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "pronunciation": {{"band": <integer 0-9>, "feedback": "<string>"}},
  "overall_band": <float, multiple of 0.5>,
  "strengths": ["<string>", ...],
  "improvements": ["<string>", ...],
  "corrections": [
    {{"quote": "<exact words from student transcript>", "better": "<improved version>", "note": "<brief explanation>"}}
  ],
  "example_phrases": ["<useful phrase student could have used>", ...]
}}

Provide 3-5 corrections with real quotes from the transcript. Provide 3-5 example_phrases.
CRITICAL SCORING RULE:
Individual criteria scores (Fluency & Coherence, Lexical Resource,
Grammatical Range & Accuracy, Pronunciation) MUST be WHOLE NUMBERS ONLY
(0, 1, 2, 3, 4, 5, 6, 7, 8, 9).
Half bands like 4.5, 5.5, 6.5 are NOT allowed at the individual criterion level.
Only the final Speaking Band (overall_band, average of 4 criteria) may contain .5 values.
Return integer values for individual criteria in the JSON output.
overall_band = average of 4 criteria rounded to nearest 0.5.
Mark with the official best-fit approach a certified examiner uses: award the band
whose descriptors the performance actually meets, without inflating or deflating it.
Where a performance genuinely sits between two bands, award the higher one, as a
live examiner does. Judge what the candidate demonstrated, not what is missing from
a short exam answer.

IMPORTANT SCORING RULES:
- Band 0: No speech produced at all. Candidate did not attempt to speak.
- Band 1: Only isolated words. No connected speech. No sentences formed.
- Band 2: Extremely limited. Only very short, memorized phrases. Cannot form original sentences.
- Band 3: Very limited communication. Short responses, frequent long pauses, very basic vocabulary.
- Band 4+ requires: connected speech on multiple topics, some sentence formation, basic vocabulary range.
- Never give band 4 or above if total candidate speech is under 30 words.
- Never give band 5 or above if candidate answered fewer than half the questions."""


def _clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


async def _load_image_base64(image_url: str) -> tuple[str, str] | None:
    """Load an image and return (base64_data, mime_type), or None on failure."""
    local = resolve_local_path(image_url)
    if local is not None:
        data = local.read_bytes()
        mime = mimetypes.guess_type(str(local))[0] or "image/png"
    else:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                data = resp.content
                mime = resp.headers.get("content-type", "image/png").split(";")[0]
        except Exception:
            logger.warning("Could not load image: %s", image_url)
            return None
    return base64.b64encode(data).decode(), mime


async def _call_gemini(
    prompt: str,
    image_parts: list[dict] | None = None,
    *,
    max_output_tokens: int = 4096,
    max_json_attempts: int = 2,
) -> dict:
    parts: list[dict] = []
    if image_parts:
        parts.extend(image_parts)
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "responseMimeType": "application/json",
            "maxOutputTokens": max_output_tokens,
        },
    }

    async def _post(api_key: str) -> httpx.Response:
        client = get_http_client()
        return await client.post(
            _gemini_url(),
            json=payload,
            params={"key": api_key},
            timeout=60.0,
        )

    last_error: Exception | None = None
    for attempt in range(max(1, max_json_attempts)):
        try:
            resp = await _gemini_request_with_rotation(_post)
            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                raise ValueError("Gemini returned no candidates")
            text = candidates[0]["content"]["parts"][0]["text"]
            cleaned = _clean_json_response(text)
            return json.loads(cleaned)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
            last_error = exc
            logger.warning(
                "Gemini JSON parse failed (attempt %s/%s): %s",
                attempt + 1,
                max_json_attempts,
                exc,
            )
            if attempt + 1 >= max_json_attempts:
                break

    raise ValueError(f"Gemini returned invalid JSON after {max_json_attempts} attempts: {last_error}")


def _normalize_key_points(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        point = item.get("point")
        if not isinstance(point, str) or not point.strip():
            continue
        covered = item.get("covered")
        out.append({
            "point": point.strip(),
            "covered": bool(covered) if isinstance(covered, bool) else bool(covered),
        })
    return out


def _normalize_sentence_analysis(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        sentence = item.get("sentence")
        category = item.get("category")
        comment = item.get("comment")
        if not isinstance(sentence, str) or not sentence.strip():
            continue
        if not isinstance(category, str) or category not in _SENTENCE_CATEGORIES:
            continue
        if not isinstance(comment, str):
            comment = ""
        entry: dict = {
            "sentence": sentence.strip(),
            "category": category,
            "comment": comment.strip(),
        }
        reference = item.get("reference")
        if isinstance(reference, str) and reference.strip():
            entry["reference"] = reference.strip()
        out.append(entry)
    return out


def _normalize_optional_string(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text or None


_WRITING_CRITERION_KEYS = (
    "task_achievement",
    "task_response",
    "coherence_cohesion",
    "lexical_resource",
    "grammatical_range",
)


def _coerce_writing_criteria_to_int(result: dict) -> dict:
    """IELTS: individual criteria are whole bands only (0-9).

    Rounds any non-integer band to the nearest integer, clamps to 0-9,
    and logs a warning for monitoring. Mutates and returns *result*.
    """
    for key in _WRITING_CRITERION_KEYS:
        val = result.get(key)
        if not isinstance(val, dict) or val.get("band") is None:
            continue
        try:
            raw = float(val["band"])
        except (TypeError, ValueError):
            continue
        rounded = max(0, min(9, int(round(raw))))
        if rounded != raw:
            logger.warning(
                "Gemini returned non-integer Writing criterion %s=%s; "
                "rounded to %d",
                key,
                raw,
                rounded,
            )
        val["band"] = rounded
    return result


_LANGUAGE_CRITERION_KEYS = (
    "coherence_cohesion",
    "lexical_resource",
    "grammatical_range",
)

# Below this a near-zero score can be genuine, so don't force a retry.
_COLLAPSE_MIN_WORDS = 50


class WritingEvaluationError(RuntimeError):
    """Gemini returned a structurally invalid evaluation — safe to retry."""


def _validate_writing_criteria(result: dict, *, word_count: int) -> None:
    """Guard against the model nullifying language criteria for off-topic text.

    Coherence, Lexical Resource and Grammatical Range are scored on the language
    alone. When Gemini zeroes all three it has collapsed the whole evaluation
    onto task relevance, which silently costs the student over a band. Raising
    lets the worker retry instead of recording the bad score.
    """
    bands: list[int] = []
    for key in _LANGUAGE_CRITERION_KEYS:
        val = result.get(key)
        if isinstance(val, dict) and val.get("band") is not None:
            bands.append(int(val["band"]))
    if (
        word_count >= _COLLAPSE_MIN_WORDS
        and len(bands) == len(_LANGUAGE_CRITERION_KEYS)
        and all(b == 0 for b in bands)
    ):
        raise WritingEvaluationError(
            "Gemini zeroed every language criterion on a "
            f"{word_count}-word response; retrying evaluation"
        )

    # IELTS reserves band 0 for a blank script; anything written scores >= 1.
    for key in _WRITING_CRITERION_KEYS:
        val = result.get(key)
        if isinstance(val, dict) and val.get("band") == 0:
            logger.warning("Raising Writing criterion %s from 0 to 1", key)
            val["band"] = 1


def _enrich_writing_result(result: dict, *, is_task1: bool) -> dict:
    """Sanitize Jumpinto-level fields; omit empty optional sections."""
    key_points = _normalize_key_points(result.get("key_points"))
    if is_task1 and key_points:
        result["key_points"] = key_points
    else:
        result.pop("key_points", None)

    sentence_analysis = _normalize_sentence_analysis(result.get("sentence_analysis"))
    if sentence_analysis:
        result["sentence_analysis"] = sentence_analysis
    else:
        result.pop("sentence_analysis", None)

    overall_review = _normalize_optional_string(result.get("overall_review"))
    if overall_review:
        result["overall_review"] = overall_review
    else:
        result.pop("overall_review", None)

    optimized = _normalize_optional_string(result.get("optimized_composition"))
    if optimized:
        result["optimized_composition"] = optimized
    else:
        result.pop("optimized_composition", None)

    return result


async def evaluate_writing(
    answers: dict[str, str],
    prompts: dict[str, str],
    images: dict[str, str] | None = None,
    essay_types: dict[str, str] | None = None,
    task_descriptions: dict[str, str] | None = None,
    task_instructions: dict[str, str] | None = None,
    task_statements: dict[str, str] | None = None,
    task_questions: dict[str, str] | None = None,
) -> dict:
    """Evaluate writing tasks.

    answers/prompts keyed by 'task_1', 'task_2'.
    images optionally keyed by 'task_1' -> image_url for chart/diagram.
    essay_types optionally keyed by 'task_2' -> opinion|discussion|...
    task_descriptions / task_instructions override prompts when provided.
    task_statements / task_questions provide finer-grained Task 2 split.
    """
    images = images or {}
    essay_types = essay_types or {}
    task_descriptions = task_descriptions or {}
    task_instructions = task_instructions or {}
    task_statements = task_statements or {}
    task_questions = task_questions or {}

    async def _eval_one(task_key: str) -> tuple[str, dict] | None:
        text = answers.get(task_key, "")
        prompt = prompts.get(task_key, "")
        if not text.strip():
            return None

        is_task1 = "1" in task_key
        task_label = "Task 1" if is_task1 else "Task 2"
        task_type_description = (
            "Task 1: The candidate summarises, describes or explains visual information "
            "(graph, table, chart, diagram, map, process). A minimum of 150 words is required."
            if is_task1
            else "Task 2: The candidate writes an essay in response to a point of view, argument, "
            "or problem. A minimum of 250 words is required."
        )
        min_words = 150 if is_task1 else 250
        task_criterion_name = _TASK1_CRITERION_NAME if is_task1 else _TASK2_CRITERION_NAME
        task_criterion_descriptors = (
            _TASK1_CRITERION_DESCRIPTORS if is_task1 else _TASK2_CRITERION_DESCRIPTORS
        )

        essay_type = None if is_task1 else essay_types.get(task_key)
        essay_type_criteria = ""
        if essay_type and essay_type in _ESSAY_TYPE_CRITERIA:
            essay_type_criteria = _ESSAY_TYPE_CRITERIA[essay_type] + "\n\n"

        image_url = images.get(task_key)
        gemini_image_parts: list[dict] = []
        image_instruction = ""

        if image_url:
            loaded = await _load_image_base64(image_url)
            if loaded:
                b64, mime = loaded
                gemini_image_parts.append({
                    "inline_data": {"mime_type": mime, "data": b64}
                })
                image_instruction = (
                    "### Visual data\n"
                    "An image (chart/graph/diagram/map) is attached. "
                    "The student was asked to describe this visual. "
                    "Check whether the student accurately describes the data shown. "
                    "Inaccurate data descriptions should lower Task Achievement."
                )
            else:
                image_instruction = (
                    "### Note: A chart/image was provided but could not be loaded "
                    "for verification."
                )

        if is_task1:
            if gemini_image_parts:
                key_points_instruction = _KEY_POINTS_INSTRUCTION_WITH_CHART
            else:
                key_points_instruction = _KEY_POINTS_INSTRUCTION_TASK1_NO_CHART
        else:
            key_points_instruction = _KEY_POINTS_INSTRUCTION_TASK2

        desc = task_descriptions.get(task_key) or prompt
        instr = task_instructions.get(task_key) or ""
        stmt = task_statements.get(task_key) or desc
        q = task_questions.get(task_key) or ""

        full_prompt = WRITING_PROMPT.format(
            task_label=task_label,
            task_type_description=task_type_description,
            min_words=min_words,
            task_criterion_name=task_criterion_name,
            task_criterion_descriptors=task_criterion_descriptors,
            task_statement=stmt,
            task_question=q,
            task_instruction=instr,
            text=text,
            image_instruction=image_instruction,
            essay_type_criteria=essay_type_criteria,
            key_points_instruction=key_points_instruction,
        )

        result = await _call_gemini(
            full_prompt,
            image_parts=gemini_image_parts or None,
            max_output_tokens=8000,
        )
        # Gemini always emits task_achievement; for Task 2 rename to task_response
        if not is_task1 and "task_achievement" in result:
            result["task_response"] = result.pop("task_achievement")
        result = _enrich_writing_result(result, is_task1=is_task1)
        result = _coerce_writing_criteria_to_int(result)
        _validate_writing_criteria(result, word_count=_count_words(text))

        # Task Band is always recomputed from the (now integer) criteria —
        # do not trust Gemini's own overall_band.
        crit_bands: list[float] = []
        for key in _WRITING_CRITERION_KEYS:
            val = result.get(key)
            if isinstance(val, dict) and val.get("band") is not None:
                try:
                    crit_bands.append(float(val["band"]))
                except (TypeError, ValueError):
                    pass
        if crit_bands:
            result["overall_band"] = round(sum(crit_bands) / len(crit_bands) * 2) / 2
        result["text"] = text
        result["word_count"] = _count_words(text)
        return task_key, result

    task_keys = sorted(answers.keys())
    evaluated = await asyncio.gather(*[_eval_one(k) for k in task_keys])
    results: dict[str, dict] = {}
    for item in evaluated:
        if item is not None:
            task_key, task_result = item
            results[task_key] = task_result

    if not results:
        return {"overall_band": None, "error": "No writing submitted"}

    t1_band = results.get("task_1", {}).get("overall_band")
    t2_band = results.get("task_2", {}).get("overall_band")
    if "task_1" not in results:
        t1_band = None
    if "task_2" not in results:
        t2_band = None
    overall = compute_writing_band(
        float(t1_band) if t1_band is not None else None,
        float(t2_band) if t2_band is not None else None,
    )

    # None when either task is missing — never invent 0.0 as a writing overall
    return {
        "tasks": results,
        "overall_band": overall,
    }


class NonEnglishError(ValueError):
    """Raised when the spoken language is not English."""


async def transcribe_audio(audio_url: str) -> str:
    """Transcribe audio. Chirp first, then Groq Whisper, then Gemini."""
    local_path = resolve_local_path(audio_url)
    if local_path is not None:
        audio_bytes = local_path.read_bytes()
        content_type = "audio/webm"
    else:
        client = get_http_client()
        audio_resp = await client.get(audio_url, timeout=120.0)
        audio_resp.raise_for_status()
        audio_bytes = audio_resp.content
        content_type = audio_resp.headers.get("content-type") or "audio/webm"

    return await transcribe_audio_bytes(audio_bytes, content_type=content_type)


@dataclass(frozen=True)
class Transcription:
    """A transcript together with the engine that produced it.

    Which engine ran stops being an implementation detail once more than one
    of them serves the same exam. Chirp is the first ear; Groq Whisper and
    Gemini take the overflow, so one candidate's turns can be split between
    models with different failure habits — and a transcript can only be
    judged next to its source. Keeping that on the record is what turns
    "recognition is sometimes wrong" from an impression into something
    countable.
    """

    text: str
    provider: str
    reason: str | None = None
    latency_ms: int = 0
    audio_bytes: int = 0


async def transcribe_audio_bytes(
    audio_bytes: bytes,
    *,
    content_type: str | None = None,
    duration_seconds: float | None = None,
) -> str:
    """Transcribe raw audio, for callers that only need the words."""
    result = await transcribe_audio_bytes_detailed(
        audio_bytes,
        content_type=content_type,
        duration_seconds=duration_seconds,
    )
    return result.text


async def transcribe_audio_bytes_detailed(
    audio_bytes: bytes,
    *,
    content_type: str | None = None,
    duration_seconds: float | None = None,
) -> Transcription:
    """Transcribe raw audio. Chirp is the first ear when a service account
    is configured. Groq Whisper takes the rest of the live traffic within
    its minute budget; Gemini STT is the last resort. A candidate's turn
    must never fail just because one engine is busy.

    ``stt_google_only`` is a temporary probe: it leaves Chirp as the only
    ear so we can see the one-minute Recognize cliff on a real sitting.
    The Groq/Gemini helpers stay in this file; flip the flag to restore.

    Lenient: never raises NonEnglishError.
    """
    if len(audio_bytes) < 1024:
        raise ValueError(
            "Recording too short or empty — please speak for at least a few seconds"
        )

    google_only = settings.stt_google_only
    can_use_google = google_stt.is_configured() and not google_stt.is_blocked()
    can_use_gemini = (not google_only) and bool(settings.gemini_key_list)
    can_use_groq_fallback = (
        (not google_only) and bool(settings.groq_api_key) and not _groq_stt_blocked
    )
    groq_error: Exception | None = None
    google_error: Exception | None = None
    reason: str | None = None
    started = time.perf_counter()

    def done(text: str, provider: str) -> Transcription:
        record = Transcription(
            text=text,
            provider=provider,
            reason=reason,
            latency_ms=int((time.perf_counter() - started) * 1000),
            audio_bytes=len(audio_bytes),
        )
        logger.info(
            "STT provider=%s reason=%s latency_ms=%d audio_bytes=%d chars=%d empty=%s",
            record.provider,
            record.reason or "-",
            record.latency_ms,
            record.audio_bytes,
            len(record.text),
            not record.text.strip(),
        )
        return record

    if can_use_google:
        try:
            return done(
                await _transcribe_with_google(
                    audio_bytes, duration_seconds=duration_seconds
                ),
                "google",
            )
        except httpx.HTTPStatusError as exc:
            google_error = exc
            status = exc.response.status_code
            reason = f"google_http_{status}"
            if status in (401, 403):
                google_stt.block(f"HTTP {status}")
            elif not can_use_groq_fallback and not can_use_gemini:
                raise
            else:
                logger.warning("Google STT returned %s — falling back", status)
        except Exception as exc:
            google_error = exc
            reason = "google_error"
            if not can_use_groq_fallback and not can_use_gemini:
                raise
            logger.warning(
                "Google STT failed (%s) — falling back", type(exc).__name__
            )
    elif google_stt.is_configured() and google_stt.is_blocked():
        reason = "google_blocked"

    if google_only:
        if google_error is not None:
            raise google_error
        raise RuntimeError(
            "Google STT is not available — Chirp-only mode has no Whisper/Gemini fallback"
        )

    if settings.groq_api_key and not _groq_stt_blocked:
        # Skip Groq outright when its budget is spent, so we neither queue
        # behind the window nor spend a request we know will be refused.
        if can_use_gemini and not get_groq_stt_bucket().try_acquire():
            reason = reason or "groq_budget_spent"
            logger.info("Groq STT budget spent — routing this turn to Gemini")
        else:
            try:
                return done(
                    await _transcribe_with_groq(audio_bytes, content_type), "groq"
                )
            except httpx.HTTPStatusError as exc:
                groq_error = exc
                status = exc.response.status_code
                reason = f"groq_http_{status}"
                if status in (401, 403):
                    _block_groq_stt(f"HTTP {status}")
                elif not can_use_gemini:
                    raise
                else:
                    logger.warning("Groq STT returned %s — falling back", status)
    elif can_use_gemini and reason is None:
        reason = "groq_blocked" if _groq_stt_blocked else "groq_not_configured"

    if can_use_gemini:
        if groq_error is not None or google_error is not None:
            logger.warning("Transcribing via Gemini STT fallback")
        return done(
            await _transcribe_with_gemini(audio_bytes, content_type), "gemini"
        )

    if groq_error is not None:
        raise groq_error
    if google_error is not None:
        raise google_error
    raise RuntimeError("No speech-to-text provider configured")


async def _transcribe_with_google(
    audio_bytes: bytes,
    *,
    duration_seconds: float | None = None,
) -> str:
    return _normalize_stt_text(
        await google_stt.recognize(audio_bytes, duration_seconds=duration_seconds)
    )


async def _transcribe_with_groq(
    audio_bytes: bytes,
    content_type: str | None,
) -> str:
    filename, mime = _groq_upload_file(content_type)
    client = get_http_client()
    max_attempts = 3
    last_exc: httpx.HTTPStatusError | None = None

    async with get_whisper_pool().acquire():
        for attempt in range(max_attempts):
            resp = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                files={"file": (filename, audio_bytes, mime)},
                data={
                    "model": "whisper-large-v3",
                    "response_format": "json",
                    "language": "en",
                },
                timeout=120.0,
            )
            usage_meter.record_groq_headers(resp.headers, "stt")
            if resp.status_code >= 400:
                logger.error(
                    "Groq transcription failed (%s): %s",
                    resp.status_code,
                    resp.text[:500],
                )
            # 429 is deliberately absent: Groq's window is a whole minute, so
            # a few seconds of backoff cannot clear it. The caller spills that
            # case over to Gemini instead of stalling the candidate.
            if resp.status_code in (500, 502, 503, 504) and attempt < max_attempts - 1:
                wait = min(2 ** attempt, 8)
                logger.warning(
                    "Groq transcription %s — retry in %ds (attempt %d/%d)",
                    resp.status_code,
                    wait,
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(wait)
                continue
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                raise
            data = resp.json()
            logger.info(
                "Whisper (lenient) transcript length: %d chars",
                len(data.get("text", "")),
            )
            return _normalize_stt_text(data.get("text", ""))

    raise last_exc or RuntimeError("Groq transcription failed")


async def _transcribe_with_gemini(
    audio_bytes: bytes,
    content_type: str | None,
) -> str:
    _filename, mime = _groq_upload_file(content_type)
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime,
                            "data": base64.b64encode(audio_bytes).decode(),
                        }
                    },
                    {
                        "text": (
                            "Transcribe this spoken English recording verbatim. "
                            "Return only the transcript text, with no quotes or "
                            "commentary. If there is no intelligible speech, "
                            "return EMPTY."
                        )
                    },
                ]
            }
        ],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
    }

    async def _post(api_key: str) -> httpx.Response:
        client = get_http_client()
        return await client.post(
            _gemini_url(settings.gemini_stt_model),
            json=payload,
            params={"key": api_key},
            timeout=60.0,
        )

    resp = await _gemini_request_with_rotation(_post)
    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini STT returned no candidates")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = ""
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            text += part["text"]
    transcript = _normalize_stt_text(text)
    logger.info(
        "Gemini STT (%s) transcript length: %d chars",
        settings.gemini_stt_model,
        len(transcript),
    )
    return transcript


def _groq_upload_file(content_type: str | None) -> tuple[str, str]:
    normalized = (content_type or "audio/webm").split(";", 1)[0].strip().lower()
    mapping = {
        "audio/webm": ("recording.webm", "audio/webm"),
        "audio/wav": ("recording.wav", "audio/wav"),
        "audio/x-wav": ("recording.wav", "audio/wav"),
        "audio/mp4": ("recording.mp4", "audio/mp4"),
        "audio/mpeg": ("recording.mp3", "audio/mpeg"),
        "audio/ogg": ("recording.ogg", "audio/ogg"),
    }
    return mapping.get(normalized, ("recording.webm", "audio/webm"))


def _gemini_contents_to_groq_messages(
    contents: list[dict],
    system_instruction: str,
) -> list[dict]:
    messages = [{"role": "system", "content": system_instruction}]
    for item in contents:
        role = "assistant" if item["role"] == "model" else "user"
        messages.append({"role": role, "content": item["parts"][0]["text"]})
    return messages


async def _call_groq_examiner_turn(contents: list[dict]) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("Groq API key not configured")

    messages = _gemini_contents_to_groq_messages(contents, EXAMINER_SYSTEM_PROMPT)
    client = get_http_client()
    resp = await client.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json={
            "model": settings.groq_examiner_model,
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        timeout=60.0,
    )
    usage_meter.record_groq_headers(resp.headers, "chat")
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Groq returned no choices")
    content = choices[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("Groq returned empty content")
    return content


async def evaluate_speaking(transcript: str, questions: list[str] | None = None) -> dict:
    """Evaluate a speaking transcript via Gemini, optionally with question context."""
    questions_text = "Not provided"
    if questions:
        questions_text = "\n".join(f"- {q}" for q in questions)

    full_prompt = SPEAKING_PROMPT.format(transcript=transcript, questions=questions_text)
    result = await _call_gemini(full_prompt)
    result["transcript"] = transcript
    _coerce_speaking_criteria_to_int(result)
    if all(
        isinstance(result.get(k), dict) and result[k].get("band") is not None
        for k in _SCORE_CRITERION_KEYS
    ):
        _recompute_overall_band(result)
    return result


# ---------------------------------------------------------------------------
# AI Examiner — conversational speaking test driven by Gemini
# ---------------------------------------------------------------------------

EXAMINER_SYSTEM_PROMPT = """\
You are James Harrison, an IELTS Speaking examiner.

Your role is LIMITED. The server tells you exactly what to do at each turn.

When given a specific question to ask, ask it EXACTLY as provided.
Do not rephrase or invent alternatives.

When asked to give a reaction, provide a brief natural response only:
'Thank you', 'I see', 'Alright', 'OK'. Nothing more.

When the server explicitly asks you to generate a cue card or a Part 3
question, generate it. Otherwise never invent content.

Never:
- Add greetings or introductions (server handles this)
- Invent questions not provided by the server
- Explain the test structure to the candidate
- Provide feedback or scores

Respond ONLY with what the examiner says aloud. When generating a cue card
or question for the server-driven flow, add the appropriate [PART:2] or
[PART:3] tag at the end."""


async def _call_gemini_text(
    contents: list[dict],
    max_retries: int | None = None,
    system_instruction: str | None = None,
) -> str:
    """Call Gemini with multi-turn contents and return plain text (no JSON parsing)."""
    payload: dict = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
        },
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    async def _post(api_key: str) -> httpx.Response:
        client = get_http_client()
        return await client.post(
            _gemini_url(),
            json=payload,
            params={"key": api_key},
            timeout=60.0,
        )

    resp = await _gemini_request_with_rotation(_post, max_retries=max_retries)
    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts") or []
    if not parts:
        raise RuntimeError("Gemini returned empty content")
    return parts[0]["text"]


def _merge_gemini_contents(contents: list[dict]) -> list[dict]:
    """Merge consecutive same-role turns — Gemini rejects back-to-back user/model."""
    merged: list[dict] = []
    for item in contents:
        text = item["parts"][0]["text"]
        if merged and merged[-1]["role"] == item["role"]:
            merged[-1]["parts"][0]["text"] += f"\n\n{text}"
        else:
            merged.append({"role": item["role"], "parts": [{"text": text}]})
    return merged


def _build_examiner_gemini_contents(
    conversation_history: list[dict],
    candidate_text: str | None,
    extra_instructions: str,
) -> list[dict]:
    """Build valid multi-turn Gemini contents for the examiner dialog."""
    trimmed_history = _trim_examiner_history(conversation_history)
    history_for_turn = trimmed_history
    if (
        candidate_text is not None
        and trimmed_history
        and trimmed_history[-1]["role"] == "candidate"
        and trimmed_history[-1]["text"].strip() == candidate_text.strip()
    ):
        history_for_turn = trimmed_history[:-1]

    contents: list[dict] = []

    if not history_for_turn:
        contents.append({
            "role": "user",
            "parts": [{
                "text": (
                    "Continue the IELTS Speaking test. The candidate has just "
                    "answered your last question. Ask the next appropriate "
                    "question according to the current part of the test."
                ),
            }],
        })
    else:
        for turn in history_for_turn:
            role = "model" if turn["role"] == "examiner" else "user"
            contents.append({"role": role, "parts": [{"text": turn["text"]}]})

        if candidate_text is not None:
            contents.append({"role": "user", "parts": [{"text": candidate_text}]})

    if extra_instructions.strip():
        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"][0]["text"] += "\n\n" + extra_instructions.strip()
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": extra_instructions.strip()}],
            })

    contents = _merge_gemini_contents(contents)

    if contents and contents[0]["role"] == "model":
        contents.insert(0, {
            "role": "user",
            "parts": [{"text": "(The speaking test has already started.)"}],
        })

    return contents


_EXAMINER_HISTORY_WINDOW = 12


def _trim_examiner_history(conversation_history: list[dict]) -> list[dict]:
    """Keep recent turns for Gemini; summarize older context to cap latency."""
    if len(conversation_history) <= _EXAMINER_HISTORY_WINDOW:
        return conversation_history

    skipped = conversation_history[:-_EXAMINER_HISTORY_WINDOW]
    recent = conversation_history[-_EXAMINER_HISTORY_WINDOW:]
    summary_lines: list[str] = []
    for turn in skipped:
        label = "Examiner" if turn["role"] == "examiner" else "Candidate"
        text = turn["text"].replace("\n", " ").strip()
        if len(text) > 100:
            text = text[:100] + "…"
        summary_lines.append(f"{label}: {text}")

    summary_turn = {
        "role": "user",
        "text": (
            "[Earlier in this test — summary only, do not repeat these questions]\n"
            + "\n".join(summary_lines)
        ),
    }
    return [summary_turn, *recent]


async def generate_examiner_turn(
    conversation_history: list[dict],
    candidate_text: str | None = None,
    extra_instructions: str = "",
) -> str:
    """Generate the next examiner turn given conversation history.

    Returns raw Gemini output (still contains [PART:n] / [END_OF_TEST] tags).
    The caller is responsible for parsing and stripping those tags.
    """
    contents = _build_examiner_gemini_contents(
        conversation_history,
        candidate_text,
        extra_instructions,
    )
    try:
        return await _call_gemini_text(
            contents,
            system_instruction=EXAMINER_SYSTEM_PROMPT,
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in (429, 503) and settings.groq_api_key:
            logger.warning(
                "Gemini %s for examiner turn — falling back to Groq LLM",
                status,
            )
            return await _call_groq_examiner_turn(contents)
        raise


async def generate_cue_card(topic_hint: str = "") -> str:
    """Fallback: ask Gemini for a Part 2 cue card when none is authored."""
    hint = topic_hint.strip() or "an everyday personal experience"
    prompt = (
        "Generate exactly ONE IELTS Speaking Part 2 cue card about "
        f"{hint}. Use this format exactly:\n"
        "Describe [specific topic]. You should say:\n"
        "- [point 1]\n"
        "- [point 2]\n"
        "- [point 3]\n"
        "and explain [final point].\n"
        "Add [PART:2] tag at the end. Respond ONLY with the cue card text and tag."
    )
    contents = [{"role": "user", "parts": [{"text": prompt}]}]
    try:
        return await _call_gemini_text(
            contents,
            system_instruction=EXAMINER_SYSTEM_PROMPT,
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in (429, 503) and settings.groq_api_key:
            logger.warning(
                "Gemini %s for cue card — falling back to Groq LLM",
                status,
            )
            return await _call_groq_examiner_turn(contents)
        raise


async def generate_part3_question(
    conversation_history: list[dict],
    *,
    cue_topic: str = "",
    question_index: int = 0,
) -> str:
    """Fallback: ask Gemini for one Part 3 discussion question."""
    topic = cue_topic.strip() or "the Part 2 topic"
    prompt = (
        f"Ask Part 3 discussion question number {question_index + 1} "
        f"related to: {topic}. "
        "Require opinion and analysis. ONE question only. "
        "Add [PART:3] tag at the end. Respond ONLY with the question and tag."
    )
    return await generate_examiner_turn(
        conversation_history,
        None,
        prompt,
    )


_SCORE_CRITERION_KEYS = (
    "fluency_coherence",
    "lexical_resource",
    "grammatical_range",
    "pronunciation",
)


def _round_band(band: float) -> float:
    return round(band * 2) / 2


def _coerce_speaking_criteria_to_int(result: dict) -> dict:
    """IELTS: individual Speaking criteria are whole bands only (0-9).

    Rounds any non-integer band to the nearest integer, clamps to 0-9,
    and logs a warning for monitoring. Mutates and returns *result*.
    """
    for key in _SCORE_CRITERION_KEYS:
        val = result.get(key)
        if not isinstance(val, dict) or val.get("band") is None:
            continue
        try:
            raw = float(val["band"])
        except (TypeError, ValueError):
            continue
        rounded = max(0, min(9, int(round(raw))))
        if rounded != raw:
            logger.warning(
                "Gemini returned non-integer Speaking criterion %s=%s; "
                "rounded to %d",
                key,
                raw,
                rounded,
            )
        val["band"] = rounded
    return result


def _recompute_overall_band(result: dict) -> dict:
    avg = sum(result[key]["band"] for key in _SCORE_CRITERION_KEYS) / 4
    result["overall_band"] = _round_band(avg)
    return result


async def evaluate_speaking_dialog(conversation_history: list[dict]) -> dict:
    """Score a full examiner dialog using the standard SPEAKING_PROMPT."""
    examiner_lines = []
    candidate_lines = []
    for turn in conversation_history:
        if turn["role"] == "examiner":
            examiner_lines.append(turn["text"])
        else:
            candidate_lines.append(turn["text"])

    questions_text = "\n".join(f"- {q}" for q in examiner_lines) if examiner_lines else "Not provided"
    transcript = "\n\n".join(candidate_lines) if candidate_lines else "(empty)"

    full_prompt = SPEAKING_PROMPT.format(questions=questions_text, transcript=transcript)
    result = await _call_gemini(full_prompt)
    result["transcript"] = transcript
    _coerce_speaking_criteria_to_int(result)
    return _recompute_overall_band(result)
