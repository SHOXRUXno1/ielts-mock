import { api } from '@/lib/axios'
import type { Question, QuestionGroup } from '@/features/tests/data/schema'

export type QuestionGroupCreatePayload = {
  order?: number
  question_type: string
  instruction?: string
  options_shared?: Record<string, unknown> | null
}

export type QuestionGroupUpdatePayload = Partial<QuestionGroupCreatePayload>

export type QuestionInGroupPayload = {
  order: number
  question_type?: string  // omit to inherit from group
  content: Record<string, unknown>
  answer_key?: Record<string, unknown> | null
}

export async function fetchQuestionGroups(sectionId: string): Promise<QuestionGroup[]> {
  const { data } = await api.get<QuestionGroup[]>(
    `/admin/sections/${sectionId}/question-groups`
  )
  return data
}

export async function createQuestionGroup(
  sectionId: string,
  payload: QuestionGroupCreatePayload
): Promise<QuestionGroup> {
  const { data } = await api.post<QuestionGroup>(
    `/admin/sections/${sectionId}/question-groups`,
    payload
  )
  return data
}

export async function updateQuestionGroup(
  groupId: string,
  payload: QuestionGroupUpdatePayload
): Promise<QuestionGroup> {
  const { data } = await api.patch<QuestionGroup>(
    `/admin/question-groups/${groupId}`,
    payload
  )
  return data
}

export async function deleteQuestionGroup(groupId: string): Promise<void> {
  await api.delete(`/admin/question-groups/${groupId}`)
}

export async function createQuestionInGroup(
  groupId: string,
  payload: QuestionInGroupPayload
): Promise<Question> {
  const { data } = await api.post<Question>(
    `/admin/question-groups/${groupId}/questions`,
    payload
  )
  return data
}
