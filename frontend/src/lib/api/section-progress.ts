import { api } from '@/lib/axios'
import type { SectionType } from '@/features/tests/data/schema'

export type SectionState = 'not_started' | 'active' | 'sealed'

export type SealReason = 'manual' | 'timeout' | 'submit' | 'advance'

export type SectionProgressRead = {
  section_type: SectionType | string
  state: SectionState | string
  started_at: string | null
  ends_at: string | null
  sealed_at: string | null
  sealed_reason: string | null
}

export type AttemptProgressRead = {
  server_now: string
  /** Seconds after ends_at during which the server still accepts answers. */
  grace_seconds?: number
  sections: SectionProgressRead[]
}

export type EnterSectionResponse = SectionProgressRead & {
  server_now: string
  grace_seconds?: number
}

export type SealSectionResponse = {
  sealed: SectionProgressRead
  next_section: string | null
  all_sealed: boolean
  server_now: string
}

export async function getAttemptProgress(
  attemptId: string,
): Promise<AttemptProgressRead> {
  const { data } = await api.get<AttemptProgressRead>(
    `/attempts/${attemptId}/progress`,
  )
  return data
}

export async function enterSection(
  attemptId: string,
  sectionType: string,
): Promise<EnterSectionResponse> {
  const { data } = await api.post<EnterSectionResponse>(
    `/attempts/${attemptId}/sections/${sectionType}/enter`,
  )
  return data
}

export async function sealSection(
  attemptId: string,
  sectionType: string,
  opts?: {
    answers?: Array<{ question_id: string; response: Record<string, unknown> }>
    reason?: SealReason
  },
): Promise<SealSectionResponse> {
  const { data } = await api.post<SealSectionResponse>(
    `/attempts/${attemptId}/sections/${sectionType}/seal`,
    {
      answers: opts?.answers ?? [],
      reason: opts?.reason ?? 'manual',
    },
  )
  return data
}
