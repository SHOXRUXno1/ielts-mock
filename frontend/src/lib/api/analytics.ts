import { api } from '@/lib/axios'

export type AnalyticsSummary = {
  total_attempts: number
  completed_attempts: number
  completion_rate: number | null
  avg_band: number | null
  active_students: number
}

export type BandTrendPoint = {
  bucket: string
  count: number
  overall: number | null
  listening: number | null
  reading: number | null
  writing: number | null
  speaking: number | null
}

export type AnalyticsSectionAverage = {
  section: string
  avg_band: number | null
  count: number
}

export type TestDifficulty = {
  test_id: string
  title: string
  attempts_count: number
  avg_band: number | null
  completion_rate: number | null
}

export type GroupComparison = {
  group_name: string
  students: number
  attempts_count: number
  avg_band: number | null
}

export type CompletionBreakdown = {
  completed: number
  abandoned: number
  in_progress: number
}

export type AnalyticsResponse = {
  period_days: number
  summary: AnalyticsSummary
  band_trend: BandTrendPoint[]
  section_averages: AnalyticsSectionAverage[]
  test_difficulty: TestDifficulty[]
  group_comparison: GroupComparison[]
  completion: CompletionBreakdown
}

export async function getAnalytics(
  days: number,
): Promise<AnalyticsResponse> {
  const { data } = await api.get<AnalyticsResponse>('/admin/analytics', {
    params: { days },
  })
  return data
}
