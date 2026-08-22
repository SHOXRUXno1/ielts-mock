import { api } from '@/lib/axios'

export type ProviderStatus = 'ok' | 'warning' | 'error' | 'unknown'

/**
 * One provider tile. Every field past `status` is optional because each
 * provider exposes a different amount: ElevenLabs reports an exact character
 * balance, Groq only a last-seen rate window, Simli nothing at all.
 */
export type ProviderUsage = {
  name: string
  configured: boolean
  status: ProviderStatus
  detail?: string
  unit?: string

  used?: number | null
  limit?: number | null
  remaining?: number | null
  percent_left?: number | null

  /** True when the numbers are our own tally, not the provider's. */
  estimated?: boolean
  counting_since?: string

  tier?: string | null
  resets_at?: string | null

  model?: string
  stt_model?: string
  key_count?: number
  rpm_per_key?: number
  rate_limited_today?: number

  remaining_requests?: string | null
  limit_requests?: string | null
  remaining_audio_seconds?: string | null
  limit_audio_seconds?: string | null
  observed_at?: string | null
  stt_rpm_budget?: number

  month_to_date_usage?: string | null
  account_balance?: string | null
  month_to_date_balance?: string | null
  generated_at?: string | null

  max_concurrent?: number
}

export type UsageResponse = {
  generated_at: string
  providers: ProviderUsage[]
}

export async function fetchUsage(): Promise<UsageResponse> {
  const { data } = await api.get<UsageResponse>('/admin/usage')
  return data
}
