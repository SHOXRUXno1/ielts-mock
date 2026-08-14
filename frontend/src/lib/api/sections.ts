import { api } from '@/lib/axios'
import type { Section } from '@/features/tests/data/schema'

export type SectionCreatePayload = {
  type: string
  audio_url?: string | null
  passage?: string | null
  audioscript?: string | null
}

export type SectionUpdatePayload = {
  audio_url?: string | null
  passage?: string | null
  audioscript?: string | null
  title?: string | null
  passage_subtitle?: string | null
}

export async function createSection(
  testId: string,
  payload: SectionCreatePayload
): Promise<Section> {
  const { data } = await api.post<Section>(`/admin/tests/${testId}/sections`, payload)
  return data
}

export async function updateSection(
  id: string,
  payload: SectionUpdatePayload
): Promise<Section> {
  const { data } = await api.patch<Section>(`/admin/sections/${id}`, payload)
  return data
}

export async function deleteSection(id: string): Promise<void> {
  await api.delete(`/admin/sections/${id}`)
}
