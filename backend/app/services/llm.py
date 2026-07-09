"""LLM integration: Gemini for writing/speaking evaluation, Groq Whisper for transcription."""

import asyncio
import base64
import json
import logging
import mimetypes
from collections.abc import Awaitable, Callable

import httpx

from app.core.config import settings
from app.core.rate_limiter import KeyRotator
from app.services.shared_http import get_http_client
from app.services.storage import resolve_local_path

logger = logging.getLogger(__name__)

_rotator: KeyRotator | None = None


def _gemini_url() -> str:
    return (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/{settings.gemini_model}:generateContent"
    )


def get_rotator() -> KeyRotator:
    global _rotator
    if _rotator is None:
        _rotator = KeyRotator(settings.gemini_key_list, settings.gemini_rpm_limit)
    return _rotator


def _key_prefix(key: str) -> str:
    return key[:10]


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
            return resp
        except httpx.HTTPStatusError as e:
            last_exc = e
            status = e.response.status_code
            has_more_attempts = attempt < max_retries - 1
            keys_left_in_cycle = len(keys) - ((attempt % len(keys)) + 1)

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
            raise
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

    raise last_exc or RuntimeError("Gemini call failed")


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
{task_criterion_name} accordingly (typically -0.5 to -1.0 band).

{image_instruction}

### Task prompt given to the student
{prompt}

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
If the response is largely irrelevant to the prompt, cap {task_criterion_name} at 4.0.

### Inline errors
Identify up to 12 of the most significant errors or weaknesses in the student's text.
For each error, provide an EXACT substring that appears verbatim in the student's response
(so it can be highlighted client-side), the error category, a corrected version, and a brief explanation.
Focus on errors that most impact the band score.

### Output format
Return ONLY valid JSON (no markdown, no code fences):
{{
  "task_achievement": {{"band": <float>, "feedback": "<string>"}},
  "coherence_cohesion": {{"band": <float>, "feedback": "<string>"}},
  "lexical_resource": {{"band": <float>, "feedback": "<string>"}},
  "grammatical_range": {{"band": <float>, "feedback": "<string>"}},
  "overall_band": <float>,
  "strengths": ["<string>", ...],
  "improvements": ["<string>", ...],
  "errors": [
    {{
      "quote": "<exact verbatim substring from the student response>",
      "type": "grammar|lexical|spelling|cohesion|punctuation",
      "correction": "<corrected version of that phrase>",
      "explanation": "<short reason, max 15 words>"
    }}
  ]
}}

Note: the JSON key is always "task_achievement" regardless of task number, for system compatibility.
Band scores MUST be in 0.5 increments (e.g. 6.0, 6.5, 7.0).
overall_band = average of 4 criteria rounded to nearest 0.5.
Be strict but fair, calibrated to official Cambridge IELTS sample answers.
Every "quote" in errors MUST be an EXACT substring of the student's response — copy it character-for-character."""

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

   IMPORTANT for Pronunciation: Since we only have transcript (not audio), assess pronunciation INDIRECTLY through:
   - Whisper transcription errors suggest pronunciation issues
   - Natural collocations and phrasing suggest good pronunciation
   - Unusual word choices or fragments may indicate pronunciation difficulties
   - State in feedback that this is an approximate assessment from transcript

### Relevance check
If the student's response does not address the given questions/cue card, cap Fluency and Coherence at 4.0.

### Output format
Return ONLY valid JSON (no markdown, no code fences):
{{
  "fluency_coherence": {{"band": <float>, "feedback": "<string>"}},
  "lexical_resource": {{"band": <float>, "feedback": "<string>"}},
  "grammatical_range": {{"band": <float>, "feedback": "<string>"}},
  "pronunciation": {{"band": <float>, "feedback": "<string>"}},
  "overall_band": <float>,
  "strengths": ["<string>", ...],
  "improvements": ["<string>", ...],
  "corrections": [
    {{"quote": "<exact words from student transcript>", "better": "<improved version>", "note": "<brief explanation>"}}
  ],
  "example_phrases": ["<useful phrase student could have used>", ...]
}}

Provide 3-5 corrections with real quotes from the transcript. Provide 3-5 example_phrases.
Band scores MUST be in 0.5 increments.
overall_band = average of 4 criteria rounded to nearest 0.5.
Be strict but fair.

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


async def _call_gemini(prompt: str, image_parts: list[dict] | None = None) -> dict:
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

    resp = await _gemini_request_with_rotation(_post)
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    cleaned = _clean_json_response(text)
    return json.loads(cleaned)


async def evaluate_writing(
    answers: dict[str, str],
    prompts: dict[str, str],
    images: dict[str, str] | None = None,
) -> dict:
    """Evaluate writing tasks.

    answers/prompts keyed by 'task_1', 'task_2'.
    images optionally keyed by 'task_1' -> image_url for chart/diagram.
    """
    images = images or {}
    results = {}

    for task_key in sorted(answers.keys()):
        text = answers.get(task_key, "")
        prompt = prompts.get(task_key, "")
        if not text.strip():
            continue

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
        task_criterion_descriptors = _TASK1_CRITERION_DESCRIPTORS if is_task1 else _TASK2_CRITERION_DESCRIPTORS

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
                image_instruction = "### Note: A chart/image was provided but could not be loaded for verification."
        else:
            image_instruction = ""

        full_prompt = WRITING_PROMPT.format(
            task_label=task_label,
            task_type_description=task_type_description,
            min_words=min_words,
            task_criterion_name=task_criterion_name,
            task_criterion_descriptors=task_criterion_descriptors,
            prompt=prompt,
            text=text,
            image_instruction=image_instruction,
        )

        result = await _call_gemini(full_prompt, image_parts=gemini_image_parts or None)
        # Gemini always emits task_achievement; for Task 2 rename to task_response
        if not is_task1 and "task_achievement" in result:
            result["task_response"] = result.pop("task_achievement")
        result["text"] = text
        result["word_count"] = _count_words(text)
        results[task_key] = result

    if not results:
        return {"overall_band": 0, "error": "No writing submitted"}

    all_bands = [r.get("overall_band", 0) for r in results.values()]
    overall = round(sum(all_bands) / len(all_bands) * 2) / 2

    return {
        "tasks": results,
        "overall_band": overall,
    }


class NonEnglishError(ValueError):
    """Raised when the spoken language is not English."""


async def transcribe_audio(audio_url: str) -> str:
    """Transcribe audio using Groq Whisper API. Supports local files and remote URLs."""
    if not settings.groq_api_key:
        raise RuntimeError("Groq API key not configured")

    local_path = resolve_local_path(audio_url)
    if local_path is not None:
        audio_bytes = local_path.read_bytes()
    else:
        async with httpx.AsyncClient(timeout=120.0) as client:
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()
            audio_bytes = audio_resp.content

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": ("audio.webm", audio_bytes, "audio/webm")},
            data={"model": "whisper-large-v3", "response_format": "verbose_json"},
        )
        resp.raise_for_status()

    data = resp.json()
    detected_lang = data.get("language", "english").lower()
    transcript_text = data.get("text", "").strip()

    logger.info("Whisper detected language: %s", detected_lang)

    if detected_lang != "english":
        raise NonEnglishError(
            f"Please record your response in English. "
            f"Detected language: {detected_lang}."
        )

    return transcript_text


async def transcribe_audio_bytes(
    audio_bytes: bytes,
    *,
    content_type: str | None = None,
) -> str:
    """Transcribe raw audio bytes via Groq Whisper. Lenient: never raises NonEnglishError."""
    if not settings.groq_api_key:
        raise RuntimeError("Groq API key not configured")

    if len(audio_bytes) < 1024:
        raise ValueError(
            "Recording too short or empty — please speak for at least a few seconds"
        )

    filename, mime = _groq_upload_file(content_type)
    client = get_http_client()
    max_attempts = 3
    last_exc: httpx.HTTPStatusError | None = None

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
        if resp.status_code >= 400:
            logger.error(
                "Groq transcription failed (%s): %s",
                resp.status_code,
                resp.text[:500],
            )
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_attempts - 1:
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
        return data.get("text", "").strip()

    raise last_exc or RuntimeError("Groq transcription failed")


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
    return result


# ---------------------------------------------------------------------------
# AI Examiner — conversational speaking test driven by Gemini
# ---------------------------------------------------------------------------

EXAMINER_SYSTEM_PROMPT = """\
You are James Harrison, a professional IELTS Speaking examiner.

STRUCTURE — follow this exactly:

PART 1 (Introduction, 4-5 questions):
Ask simple personal questions one at a time. Topics: hometown, work/study, hobbies, daily routine, food preferences.
After each answer, give a brief natural reaction ('Thank you', 'I see', 'Interesting') then ask the next question.

PART 2 (Long Turn):
Give exactly ONE cue card topic in this format:
Describe [specific topic]. You should say:
- [point 1]
- [point 2]
- [point 3]
and explain [final point].

Do NOT say 'you have 1 minute to prepare' or 'please begin speaking' — the system handles timing.
After the candidate finishes speaking, say 'Thank you' and move to Part 3.

PART 3 (Discussion, 3-4 questions):
Ask abstract questions related to the Part 2 topic. These should require opinion and analysis.

END:
After Part 3, say exactly: 'That is the end of the speaking test. Thank you very much.'
Then add the tag [END_OF_TEST] at the very end.

RULES:
- ONE question at a time, never multiple
- Brief natural reactions between questions
- Never give feedback or scores during the test
- Add [PART:1], [PART:2], or [PART:3] tag at the end of each response
- Respond ONLY with what the examiner says aloud, plus the tag"""


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
                    "Begin the IELTS Speaking test now. Greet the candidate "
                    "and ask the first Part 1 question."
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


_SCORE_CRITERION_KEYS = (
    "fluency_coherence",
    "lexical_resource",
    "grammatical_range",
    "pronunciation",
)


def _round_band(band: float) -> float:
    return round(band * 2) / 2


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
    return _recompute_overall_band(result)
