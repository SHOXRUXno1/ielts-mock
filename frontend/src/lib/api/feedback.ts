import { api } from '@/lib/axios'

export type WritingCriterion = {
  band: number
  feedback: string
}

export type WritingError = {
  quote: string
  type: 'grammar' | 'lexical' | 'spelling' | 'cohesion' | 'punctuation'
  correction: string
  explanation: string
}

export type WritingFeedbackResult = {
  overall_band: number
  task_achievement: WritingCriterion | null
  coherence_cohesion: WritingCriterion | null
  lexical_resource: WritingCriterion | null
  grammatical_range: WritingCriterion | null
  strengths: string[]
  improvements: string[]
  errors: WritingError[]
  word_count: number
}

export type WritingFeedbackRequest = {
  task: 1 | 2
  task_description?: string
  task_statement?: string
  task_question?: string
  task_instruction?: string
  prompt?: string
  text: string
  image_url?: string | null
  essay_type?: string | null
  attempt_id?: string | null
}

export async function requestWritingFeedback(
  payload: WritingFeedbackRequest,
): Promise<WritingFeedbackResult> {
  const res = await api.post<WritingFeedbackResult>(
    '/admin/feedback/writing',
    payload,
  )
  return res.data
}
