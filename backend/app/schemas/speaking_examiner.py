import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: Literal["examiner", "candidate"]
    text: str


class RespondRequest(BaseModel):
    candidate_text: str
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    session_id: uuid.UUID | None = None


class ScoreRequest(BaseModel):
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    session_id: uuid.UUID | None = None


class SaveSessionRequest(BaseModel):
    session_id: uuid.UUID | None = None
    started_at: str | None = None
    finished_at: str | None = None
    overall_band: float
    score_json: dict
    history_json: list[ConversationTurn]


class PerformanceTimings(BaseModel):
    whisper_ms: int | None = None
    gemini_ms: int | None = None
    tts_ms: int | None = None
    db_ms: int | None = None
    history_turns: int | None = None
    tts_cache_hit: bool | None = None


class ExaminerTurnResponse(BaseModel):
    text: str
    audio_base64: str
    part: int
    is_end: bool
    question_number: int
    questions_total: int | None = None
    cue_card: str | None = None
    session_id: str | None = None
    tts_error: str | None = None
    timings: PerformanceTimings | None = None


class TranscribeResponse(BaseModel):
    transcript: str


class TranscribeAndRespondResponse(ExaminerTurnResponse):
    transcript: str


class SynthesizeTurnRequest(BaseModel):
    text: str
    part: int
    cue_card: str | None = None


class SynthesizeTurnResponse(BaseModel):
    audio_base64: str
    tts_error: str | None = None
    timings: PerformanceTimings | None = None


class PhraseResponse(BaseModel):
    text: str
    audio_base64: str
    tts_error: str | None = None


class SessionIdResponse(BaseModel):
    id: str


NO_SPEECH_TRANSCRIPT = "(no speech detected)"


class CriterionScore(BaseModel):
    band: float
    feedback: str


class ScoreCorrection(BaseModel):
    quote: str
    better: str
    note: str | None = None


class ExaminerScore(BaseModel):
    fluency_coherence: CriterionScore
    lexical_resource: CriterionScore
    grammatical_range: CriterionScore
    pronunciation: CriterionScore
    overall_band: float
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    transcript: str
    corrections: list[ScoreCorrection] = Field(default_factory=list)
    example_phrases: list[str] = Field(default_factory=list)
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
