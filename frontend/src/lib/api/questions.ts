import { api } from '@/lib/axios'
import type { Question } from '@/features/tests/data/schema'

export type QuestionCreatePayload = {
  order: number
  question_type: string
  content: Record<string, unknown>
  answer_key?: Record<string, unknown> | null
  task_number?: number | null
  min_words?: number | null
  image_url?: string | null
}

export type QuestionUpdatePayload = Partial<QuestionCreatePayload>

export async function fetchQuestions(sectionId: string): Promise<Question[]> {
  const { data } = await api.get<Question[]>(
    `/admin/sections/${sectionId}/questions/`
  )
  return data
}

export async function createQuestion(
  sectionId: string,
  payload: QuestionCreatePayload
): Promise<Question> {
  const { data } = await api.post<Question>(
    `/admin/sections/${sectionId}/questions/`,
    payload
  )
  return data
}

export async function updateQuestion(
  sectionId: string,
  questionId: string,
  payload: QuestionUpdatePayload
): Promise<Question> {
  const { data } = await api.patch<Question>(
    `/admin/sections/${sectionId}/questions/${questionId}`,
    payload
  )
  return data
}

export async function deleteQuestion(
  sectionId: string,
  questionId: string
): Promise<void> {
  await api.delete(`/admin/sections/${sectionId}/questions/${questionId}`)
}
