import { api, MEDIA_UPLOAD_TIMEOUT_MS } from '@/lib/axios'

export type AttemptMode = 'full_mock' | 'single_part' | 'single_section'

export type AttemptRead = {
  id: string
  test_id: string
  status: string
  mode: AttemptMode
  practice_section_id: string | null
  practice_part_number: number | null
  practice_section_type: string | null
  practice_correct: number | null
  practice_total: number | null
  started_at: string | null
  finished_at: string | null
  overall_band: number | null
  listening_band: number | null
  reading_band: number | null
  writing_band: number | null
  speaking_band: number | null
  listening_raw: number | null
  reading_raw: number | null
  /** @deprecated Legacy cumulative-deadline flag; no longer set on finish. */
  flagged_overtime: boolean
  /** Append-only proctoring log. Null until the first violation. */
  integrity_events: IntegrityEvent[] | null
  created_at: string
  updated_at: string
}

export type IntegrityEvent = {
  type: 'fullscreen_exit' | string
  at: string
}

export type SectionSnapshot = {
  id: string
  type: string
  order: number
}

export type QuestionSnapshot = {
  id: string
  section_id: string
  question_group_id?: string | null
  order: number
  question_type: string
  content: Record<string, unknown>
  answer_key: Record<string, unknown> | null
  /** Present for writing essays when the API includes it */
  task_number?: number | null
  computed_number?: number | null
  computed_number_end?: number | null
}

export type AnswerRead = {
  id: string
  question_id: string
  response: Record<string, unknown>
  is_correct: boolean | null
  score: number | null
  question: QuestionSnapshot | null
  section: SectionSnapshot | null
}

export type EvaluationJobRead = {
  id: string
  section_type: string
  status: string
  band_score: number | null
  result: Record<string, unknown> | null
  teacher_override_band: number | null
  processed_at: string | null
  error_message: string | null
  created_at?: string | null
  retry_count?: number
}

export type SpeakingSessionSummary = {
  id: string
  status: string
  overall_band: number | null
  score_json: Record<string, unknown> | null
  history_json: Array<{ role: string; text: string }> | null
}

export type AttemptDetailRead = AttemptRead & {
  answers: AnswerRead[]
  evaluation_jobs: EvaluationJobRead[]
  speaking_session?: SpeakingSessionSummary | null
  test_title?: string | null
}

export type AttemptListItem = AttemptRead & {
  test_title: string
  student_name: string | null
  student_id: string | null
}

export type StudentResultsResponse = {
  student: {
    id: string
    full_name: string
    login: string
    phone: string | null
    group_name: string | null
    is_active: boolean
    created_at: string
  }
  stats: {
    attempts_count: number
    best_band: number | null
    average_band: number | null
    last_attempt_at: string | null
  }
  band_progression: Array<{
    attempt_id: string
    band: number
    date: string
    test_name: string
  }>
  section_averages: {
    listening: number | null
    reading: number | null
    writing: number | null
    speaking: number | null
  }
  attempts: AttemptListItem[]
}

export async function startAttempt(testId: string): Promise<AttemptRead> {
  const { data } = await api.post<AttemptRead>(`/tests/${testId}/attempts`)
  return data
}

/** In-progress attempt for this test, or null when none exists (404). */
export async function getCurrentAttempt(
  testId: string,
): Promise<AttemptRead | null> {
  try {
    const { data } = await api.get<AttemptRead>(
      `/tests/${testId}/attempts/current`,
    )
    return data
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 404) return null
    throw err
  }
}

export async function submitAnswers(
  attemptId: string,
  answers: { question_id: string; response: Record<string, unknown> }[],
): Promise<void> {
  await api.post(`/attempts/${attemptId}/answers`, { answers })
}

export async function finishAttempt(attemptId: string): Promise<AttemptDetailRead> {
  const { data } = await api.post<AttemptDetailRead>(`/attempts/${attemptId}/finish`)
  return data
}

export async function finalizeAttempt(attemptId: string): Promise<AttemptRead> {
  const { data } = await api.post<AttemptRead>(`/attempts/${attemptId}/finalize`)
  return data
}

export async function getAttempt(attemptId: string): Promise<AttemptDetailRead> {
  const { data } = await api.get<AttemptDetailRead>(`/attempts/${attemptId}`)
  return data
}

export type IntegrityEventType = 'fullscreen_exit'

export type IntegrityEventResponse = {
  recorded: boolean
  terminated: boolean
  events_count: number
}

export async function reportIntegrityEvent(
  attemptId: string,
  type: IntegrityEventType,
  terminal: boolean,
): Promise<IntegrityEventResponse> {
  const { data } = await api.post<IntegrityEventResponse>(
    `/attempts/${attemptId}/integrity-event`,
    { type, terminal },
  )
  return data
}

export interface PaginatedResults {
  items: AttemptListItem[]
  total: number
  limit: number
  offset: number
}

export async function fetchResults(params?: {
  limit?: number
  offset?: number
}): Promise<AttemptListItem[]> {
  const { data } = await api.get<PaginatedResults>('/results/', {
    params: { limit: params?.limit ?? 500, offset: params?.offset ?? 0 },
  })
  return data.items
}

export async function fetchResultDetail(
  attemptId: string
): Promise<AttemptDetailRead> {
  const { data } = await api.get<AttemptDetailRead>(
    `/results/${attemptId}`
  )
  return data
}

const PDF_TIMEOUT_MS = 60_000

function filenameFromDisposition(
  header: string | undefined,
  fallback: string,
): string {
  if (!header) return fallback
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(header)
  if (utf8?.[1]) {
    try {
      return decodeURIComponent(utf8[1])
    } catch {
      // fall through to the quoted filename
    }
  }
  const ascii = /filename="([^"]+)"/i.exec(header)
  return ascii?.[1] ?? fallback
}

export async function downloadResultPdf(attemptId: string): Promise<void> {
  const response = await api.get(`/results/${attemptId}/pdf`, {
    responseType: 'blob',
    timeout: PDF_TIMEOUT_MS,
  })
  const header = response.headers['content-disposition'] as string | undefined
  const filename = filenameFromDisposition(header, 'ielts-result.pdf')
  const url = URL.createObjectURL(response.data as Blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export async function deleteAttempt(attemptId: string): Promise<void> {
  await api.delete(`/results/${attemptId}`)
}

export async function fetchStudentResults(
  studentId: string,
): Promise<StudentResultsResponse> {
  const { data } = await api.get<StudentResultsResponse>(
    `/results/students/${studentId}`,
  )
  return data
}

export async function overrideBand(
  jobId: string,
  band: number
): Promise<EvaluationJobRead> {
  const { data } = await api.patch<EvaluationJobRead>(
    `/results/jobs/${jobId}/override`,
    { band }
  )
  return data
}

export async function uploadAudio(file: Blob): Promise<string> {
  const formData = new FormData()
  formData.append('file', file, 'recording.webm')
  const { data } = await api.post<{ url: string }>(
    '/admin/upload/audio',
    formData,
    { timeout: MEDIA_UPLOAD_TIMEOUT_MS },
  )
  return data.url
}

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<{ url: string }>(
    '/admin/upload/image',
    formData,
    { timeout: MEDIA_UPLOAD_TIMEOUT_MS },
  )
  return data.url
}

export async function submitSpeakingScore(
  attemptId: string,
  payload: {
    speaking_band: number
    score_json?: Record<string, unknown> | null
    session_id?: string | null
  },
): Promise<AttemptRead> {
  const { data } = await api.post<AttemptRead>(
    `/attempts/${attemptId}/speaking-score`,
    payload,
  )
  return data
}

/** Build an absolute URL from a relative /media/... path. */
export function mediaUrl(url: string): string {
  if (url.startsWith('http')) return url
  const base = (import.meta.env.VITE_API_URL as string) || ''
  return base + url
}

/** @deprecated Use mediaUrl instead */
export const audioPlaybackUrl = mediaUrl
