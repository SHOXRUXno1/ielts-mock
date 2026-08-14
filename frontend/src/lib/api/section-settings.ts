import { api } from '@/lib/axios'
import type {
  DurationMode,
  SectionSettings,
  SectionType,
} from '@/features/tests/data/schema'

export type SectionSettingsUpdatePayload = {
  duration_minutes?: number | null
  duration_mode?: DurationMode
}

export type SectionSettingsUpdateResult = {
  settings: SectionSettings
  /** Set when the value is allowed but differs from the IELTS recommendation. */
  warning: string | null
}

export async function updateSectionDuration(
  testId: string,
  sectionType: SectionType,
  payload: SectionSettingsUpdatePayload
): Promise<SectionSettingsUpdateResult> {
  const { data } = await api.patch<SectionSettingsUpdateResult>(
    `/admin/tests/${testId}/section-settings/${sectionType}`,
    payload
  )
  return data
}
