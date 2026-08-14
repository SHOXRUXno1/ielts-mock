import { api } from '@/lib/axios'
import type { SectionType } from '@/features/tests/data/schema'
import type { AttemptRead } from './attempts'

export type PracticeScope = 'part' | 'section'

export type PracticeUnitLastAttempt = {
  attempt_id: string
  status: string
  finished_at: string | null
  correct: number | null
  total: number | null
  band?: number | null
}

export type PracticeUnit = {
  section_type: SectionType
  part_number: number
  section_id: string
  label: string
  question_count: number
  duration_minutes: number | null
  duration_is_default: boolean
  is_enabled: boolean
  last_attempt: PracticeUnitLastAttempt | null
}

export type PracticeSectionUnit = {
  section_type: SectionType
  label: string
  part_count: number
  question_count: number
  duration_minutes: number | null
  is_enabled: boolean
  last_attempt: PracticeUnitLastAttempt | null
}

export type PracticeUnitsResponse = {
  test_id: string
  units: PracticeUnit[]
  sections: PracticeSectionUnit[]
}

export type PracticePartSetting = {
  section_type: SectionType
  part_number: number
  /** null when the row is absent — effective_duration_minutes is a proportional default. */
  duration_minutes: number | null
  is_enabled: boolean
  effective_duration_minutes: number | null
}

export type PracticePartSettingsUpdate = {
  duration_minutes?: number | null
  is_enabled?: boolean
}

export type PracticeResultRow = {
  id: string
  test_id: string
  test_title: string
  status: string
  mode?: string
  scope: PracticeScope
  section_type: SectionType | null
  part_number: number | null
  correct: number | null
  total: number | null
  band: number | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export async function fetchPracticeUnits(
  testId: string,
): Promise<PracticeUnitsResponse> {
  const { data } = await api.get<PracticeUnitsResponse>(
    `/tests/${testId}/practice-units`,
  )
  return data
}

export async function startPracticeAttempt(
  testId: string,
  payload: {
    section_type: SectionType
    scope?: PracticeScope
    part_number?: number
  },
): Promise<AttemptRead> {
  const { data } = await api.post<AttemptRead>(
    `/tests/${testId}/practice-attempts`,
    {
      section_type: payload.section_type,
      scope: payload.scope ?? 'part',
      part_number: payload.part_number,
    },
  )
  return data
}

export async function fetchAdminPracticeParts(
  testId: string,
): Promise<PracticePartSetting[]> {
  const { data } = await api.get<PracticePartSetting[]>(
    `/admin/tests/${testId}/practice-parts`,
  )
  return data
}

export async function updateAdminPracticePart(
  testId: string,
  sectionType: SectionType,
  partNumber: number,
  payload: PracticePartSettingsUpdate,
): Promise<PracticePartSetting> {
  const { data } = await api.patch<PracticePartSetting>(
    `/admin/tests/${testId}/practice-parts/${sectionType}/${partNumber}`,
    payload,
  )
  return data
}

export async function fetchPracticeResults(): Promise<PracticeResultRow[]> {
  const { data } = await api.get<PracticeResultRow[]>('/student/practice-results')
  return data
}
