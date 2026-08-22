import axios from 'axios'
import { api } from '@/lib/axios'

export const SPEAKING_REQUEST_TIMEOUT_MS = 90_000
export const NO_SPEECH_TRANSCRIPT = '(no speech detected)'

export type ConversationTurn = {
  role: 'examiner' | 'candidate'
  text: string
}

export type ExaminerTurnResponse = {
  text: string
  audio_base64: string
  part: number
  is_end: boolean
  question_number: number
  cue_card?: string | null
  session_id?: string
  tts_error?: string | null
  timings?: PerformanceTimings | null
}

export type PerformanceTimings = {
  whisper_ms?: number | null
  gemini_ms?: number | null
  tts_ms?: number | null
  db_ms?: number | null
  history_turns?: number | null
  tts_cache_hit?: boolean | null
}

export type TranscribeAndRespondResponse = ExaminerTurnResponse & {
  transcript: string
}

export type SynthesizeTurnResponse = {
  audio_base64: string
  tts_error?: string | null
  timings?: PerformanceTimings | null
}

export type ScoreCorrection = {
  quote: string
  better: string
  note?: string
}

export type ExaminerScore = {
  fluency_coherence: { band: number; feedback: string }
  lexical_resource: { band: number; feedback: string }
  grammatical_range: { band: number; feedback: string }
  pronunciation: { band: number; feedback: string }
  overall_band: number
  strengths: string[]
  improvements: string[]
  transcript: string
  corrections?: ScoreCorrection[]
  example_phrases?: string[]
  conversation_history?: ConversationTurn[]
}

export type TranscribeResponse = {
  transcript: string
}

export type SpeakingSessionSummary = {
  id: string
  started_at: string | null
  finished_at: string | null
  overall_band: number | null
  created_at: string
}

export type SpeakingSessionDetail = SpeakingSessionSummary & {
  score_json: ExaminerScore
  history_json: ConversationTurn[]
}

export type SimliTokenReason =
  | 'not_configured'
  | 'simli_credits_exhausted'
  | 'simli_api_error'
  | 'capacity'
  | 'network_error'
  | 'unauthorized'

export type SimliTokenResponse = {
  enabled: boolean
  session_token?: string
  face_id?: string
  ice_servers?: RTCIceServer[] | null
  reason?: SimliTokenReason | string
  detail?: string
  /** @deprecated use reason/detail */
  error?: string
}

function speakingRequestConfig(signal?: AbortSignal) {
  return {
    timeout: SPEAKING_REQUEST_TIMEOUT_MS,
    ...(signal ? { signal } : {}),
  }
}

export type PhraseResponse = {
  text: string
  audio_base64: string
  tts_error?: string | null
}

export async function getPart2BeginPhrase(): Promise<PhraseResponse> {
  const { data } = await api.get<PhraseResponse>(
    '/admin/speaking-examiner/part2-begin-phrase',
    speakingRequestConfig(),
  )
  return data
}

/** Warm the examiner intro-greeting TTS from the readiness gate. */
export async function getIntroGreetingPhrase(
  signal?: AbortSignal,
): Promise<PhraseResponse> {
  const { data } = await api.get<PhraseResponse>(
    '/admin/speaking-examiner/intro-greeting-phrase',
    speakingRequestConfig(signal),
  )
  return data
}

export async function startExaminer(
  attemptId?: string | null,
  signal?: AbortSignal,
): Promise<ExaminerTurnResponse> {
  const body = attemptId ? { attempt_id: attemptId } : {}
  const { data } = await api.post<ExaminerTurnResponse>(
    '/admin/speaking-examiner/start',
    body,
    speakingRequestConfig(signal),
  )
  return data
}

export async function transcribeAndRespondExaminer(
  blob: Blob,
  sessionId?: string | null,
  signal?: AbortSignal,
): Promise<TranscribeAndRespondResponse> {
  const formData = new FormData()
  const mimeType = blob.type.split(';')[0] || 'audio/webm'
  formData.append(
    'file',
    new File([blob], 'recording.webm', { type: mimeType }),
  )
  const params = sessionId ? { session_id: sessionId } : undefined
  const { data } = await api.post<TranscribeAndRespondResponse>(
    '/admin/speaking-examiner/transcribe-and-respond',
    formData,
    { ...speakingRequestConfig(signal), params },
  )
  return data
}

export async function synthesizeExaminerTurn(
  payload: { text: string; part: number; cue_card?: string | null },
  signal?: AbortSignal,
): Promise<SynthesizeTurnResponse> {
  const { data } = await api.post<SynthesizeTurnResponse>(
    '/admin/speaking-examiner/synthesize-turn',
    payload,
    speakingRequestConfig(signal),
  )
  return data
}

export async function transcribeExaminer(
  blob: Blob,
  signal?: AbortSignal,
): Promise<TranscribeResponse> {
  const formData = new FormData()
  const mimeType = blob.type.split(';')[0] || 'audio/webm'
  formData.append(
    'file',
    new File([blob], 'recording.webm', { type: mimeType }),
  )
  const { data } = await api.post<TranscribeResponse>(
    '/admin/speaking-examiner/transcribe',
    formData,
    speakingRequestConfig(signal),
  )
  return data
}

export async function respondExaminer(
  candidateText: string,
  conversationHistory: ConversationTurn[],
  sessionId?: string | null,
  signal?: AbortSignal,
): Promise<ExaminerTurnResponse> {
  const { data } = await api.post<ExaminerTurnResponse>(
    '/admin/speaking-examiner/respond',
    {
      candidate_text: candidateText,
      conversation_history: sessionId ? [] : conversationHistory,
      session_id: sessionId ?? undefined,
    },
    speakingRequestConfig(signal),
  )
  return data
}

function isRetryableSpeakingError(err: unknown): boolean {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status
    return status === 429 || status === 502 || status === 503
  }
  return false
}

async function withSpeakingRetry<T>(
  fn: () => Promise<T>,
  signal?: AbortSignal,
): Promise<T> {
  let lastError: unknown
  for (let attempt = 0; attempt < 2; attempt++) {
    if (signal?.aborted) {
      throw new DOMException('Aborted', 'AbortError')
    }
    if (attempt > 0) {
      await new Promise((resolve) => setTimeout(resolve, 2000))
      if (signal?.aborted) {
        throw new DOMException('Aborted', 'AbortError')
      }
    }
    try {
      return await fn()
    } catch (err) {
      lastError = err
      if (signal?.aborted || axios.isCancel(err)) break
      if (!isRetryableSpeakingError(err) || attempt === 1) break
    }
  }
  throw lastError
}

export async function startExaminerWithRetry(
  attemptId?: string | null,
  signal?: AbortSignal,
): Promise<ExaminerTurnResponse> {
  return withSpeakingRetry(() => startExaminer(attemptId, signal), signal)
}

export async function transcribeAndRespondWithRetry(
  blob: Blob,
  sessionId?: string | null,
  signal?: AbortSignal,
): Promise<TranscribeAndRespondResponse> {
  return withSpeakingRetry(
    () => transcribeAndRespondExaminer(blob, sessionId, signal),
    signal,
  )
}

export async function respondExaminerWithRetry(
  candidateText: string,
  conversationHistory: ConversationTurn[],
  sessionId?: string | null,
  signal?: AbortSignal,
): Promise<ExaminerTurnResponse> {
  return withSpeakingRetry(
    () => respondExaminer(candidateText, conversationHistory, sessionId, signal),
    signal,
  )
}

export async function scoreExaminer(
  conversationHistory: ConversationTurn[],
  sessionId?: string | null,
  signal?: AbortSignal,
): Promise<ExaminerScore> {
  const { data } = await api.post<ExaminerScore>(
    '/admin/speaking-examiner/score',
    {
      conversation_history: conversationHistory,
      session_id: sessionId ?? undefined,
    },
    speakingRequestConfig(signal),
  )
  return data
}

export async function scoreExaminerWithRetry(
  conversationHistory: ConversationTurn[],
  sessionId?: string | null,
  signal?: AbortSignal,
): Promise<ExaminerScore> {
  return withSpeakingRetry(
    () => scoreExaminer(conversationHistory, sessionId, signal),
    signal,
  )
}

export async function getSimliToken(): Promise<SimliTokenResponse> {
  const { data } = await api.get<SimliTokenResponse>(
    '/admin/speaking-examiner/simli-token',
    { timeout: 20_000 },
  )
  return data
}

export async function saveSpeakingSession(payload: {
  session_id?: string | null
  started_at: string | null
  finished_at: string
  overall_band: number
  score_json: ExaminerScore
  history_json: ConversationTurn[]
}): Promise<{ id: string }> {
  const { data } = await api.post<{ id: string }>(
    '/admin/speaking-examiner/sessions',
    payload,
    speakingRequestConfig(),
  )
  return data
}

export async function listSpeakingSessions(): Promise<SpeakingSessionSummary[]> {
  const { data } = await api.get<SpeakingSessionSummary[]>(
    '/admin/speaking-examiner/sessions',
    speakingRequestConfig(),
  )
  return data
}

export async function getSpeakingSession(
  id: string,
): Promise<SpeakingSessionDetail> {
  const { data } = await api.get<SpeakingSessionDetail>(
    `/admin/speaking-examiner/sessions/${id}`,
    speakingRequestConfig(),
  )
  return data
}

export function isSpeakingAbortError(err: unknown): boolean {
  if (axios.isCancel(err)) return true
  if (err instanceof DOMException && err.name === 'AbortError') return true
  return false
}

export function getSpeakingApiErrorDetail(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.code === 'ECONNABORTED') {
      return 'Request timed out — try again'
    }
    if (err.response?.status === 401) {
      return 'Session expired — please sign in again'
    }
    if (!err.response) {
      return 'Cannot reach server — check that the backend is running'
    }
    const detail = err.response.data
    if (detail && typeof detail === 'object' && 'detail' in detail) {
      return String(detail.detail)
    }
    if (err.response.status >= 500) {
      return 'Speaking service had an error — try Start again'
    }
  }
  return err instanceof Error ? err.message : 'Unknown error'
}

export function formatSimliUnavailable(resp: SimliTokenResponse): string | null {
  if (resp.enabled) return null
  if (resp.reason === 'not_configured') return null

  if (resp.reason === 'simli_credits_exhausted') {
    const detail =
      resp.detail ??
      'Simli free credits are used up — upgrade at https://app.simli.com'
    return `${detail} Audio-only mode is active — you can still start the test.`
  }

  if (resp.reason === 'capacity') {
    const detail =
      resp.detail ??
      'Video avatar slots are full right now'
    return `${detail} Audio-only mode is active — you can still start the test.`
  }

  const detail =
    resp.detail ??
    resp.error ??
    (resp.reason === 'simli_api_error'
      ? 'Video avatar service unavailable'
      : null)

  if (!detail) return 'Video avatar unavailable — using audio fallback'

  return `${detail}. Audio-only mode is active — you can still start the test.`
}

export function getSimliFetchErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.response?.status === 401) {
      return 'Session expired — please sign in again'
    }
    if (!err.response) {
      return 'Cannot reach server — video avatar disabled, audio fallback active'
    }
  }
  return 'Video avatar unavailable — using audio fallback'
}
