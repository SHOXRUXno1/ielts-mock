import { api } from '@/lib/axios'

export type AttemptRead = {
  id: string
  test_id: string
  status: string
  started_at: string | null
  finished_at: string | null
  overall_band: number | null
  listening_band: number | null
  reading_band: number | null
  writing_band: number | null
  speaking_band: number | null
  listening_raw: number | null
  reading_raw: number | null
  flagged_overtime: boolean
  created_at: string
  updated_at: string
}

export type SectionSnapshot = {
  id: string
  type: string
  order: number
}

export type QuestionSnapshot = {
  id: string
  section_id: string
  order: number
  question_type: string
  content: Record<string, unknown>
  answer_key: Record<string, unknown> | null
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
}

export type AttemptDetailRead = AttemptRead & {
  answers: AnswerRead[]
  evaluation_jobs: EvaluationJobRead[]
}

export type AttemptListItem = AttemptRead & {
  test_title: string
}

export async function startAttempt(testId: string): Promise<AttemptRead> {
  const { data } = await api.post<AttemptRead>(
    `/tests/${testId}/attempts`
  )
  return data
}

export async function submitAnswers(
  attemptId: string,
  answers: { question_id: string; response: Record<string, unknown> }[]
): Promise<void> {
  await api.post(`/attempts/${attemptId}/answers`, { answers })
}

export async function finishAttempt(
  attemptId: string
): Promise<AttemptDetailRead> {
  const { data } = await api.post<AttemptDetailRead>(
    `/attempts/${attemptId}/finish`
  )
  return data
}

export async function getAttempt(
  attemptId: string
): Promise<AttemptDetailRead> {
  const { data } = await api.get<AttemptDetailRead>(
    `/attempts/${attemptId}`
  )
  return data
}

export async function fetchResults(): Promise<AttemptListItem[]> {
  const { data } = await api.get<AttemptListItem[]>('/results/')
  return data
}

export async function fetchResultDetail(
  attemptId: string
): Promise<AttemptDetailRead> {
  const { data } = await api.get<AttemptDetailRead>(
    `/results/${attemptId}`
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
    formData
  )
  return data.url
}

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<{ url: string }>(
    '/admin/upload/image',
    formData
  )
  return data.url
}

export async function submitSpeakingScore(
  attemptId: string,
  payload: { speaking_band: number; score_json?: Record<string, unknown> | null }
): Promise<AttemptRead> {
  const { data } = await api.post<AttemptRead>(
    `/attempts/${attemptId}/speaking-score`,
    payload
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
