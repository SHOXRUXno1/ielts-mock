import { api } from '@/lib/axios'
import type { AttemptRead } from '@/lib/api/attempts'

export type DashboardAttempt = {
  id: string
  test_id: string
  test_title: string
  overall_band: number | null
  status: string
  finished_at: string | null
  created_at: string
}

export type BandTrendPoint = {
  attempt_id: string
  band: number
  date: string
}

export type SectionBands = {
  listening: number | null
  reading: number | null
  writing: number | null
  speaking: number | null
}

export type InProgressAttempt = {
  id: string
  test_id: string
  test_title: string
  answered: number
  total: number
  updated_at: string
}

export type DashboardResponse = {
  tests_taken: number
  avg_band: number | null
  best_band: number | null
  section_bands: SectionBands
  band_trend: BandTrendPoint[]
  in_progress: InProgressAttempt | null
  recent: DashboardAttempt[]
}

export type SectionProgress = {
  score: number | null
  completed: boolean
}

export type CatalogTest = {
  id: string
  title: string
  book_name: string | null
  test_type: string
  duration_minutes: number
  section_count: number
  sections: {
    listening: SectionProgress
    reading: SectionProgress
    writing: SectionProgress
    speaking: SectionProgress
  }
  overall_score: number | null
  status: 'new' | 'in_progress' | 'completed'
  in_progress_attempt_id: string | null
  last_attempt_at: string | null
}

export type TestGroup = {
  name: string
  tests: CatalogTest[]
}

export type CatalogResponse = {
  groups: TestGroup[]
}

export type StudentResult = {
  id: string
  test_id: string
  test_title: string
  status: string
  overall_band: number | null
  listening_band: number | null
  reading_band: number | null
  writing_band: number | null
  speaking_band: number | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export async function getDashboard(): Promise<DashboardResponse> {
  const { data } = await api.get<DashboardResponse>('/student/dashboard')
  return data
}

export async function getTestCatalog(): Promise<CatalogResponse> {
  const { data } = await api.get<CatalogResponse>('/student/tests')
  if (!data || !Array.isArray(data.groups)) {
    throw new Error('Invalid catalog response')
  }
  return data
}

export type FullMockStatus = {
  remaining: number
  total_published: number
  in_progress_attempt_id: string | null
  in_progress_test_id: string | null
  in_progress_title: string | null
}

export async function getFullMockStatus(): Promise<FullMockStatus> {
  const { data } = await api.get<FullMockStatus>('/student/full-mock/status')
  return data
}

export async function startFullMock(): Promise<AttemptRead> {
  const { data } = await api.post<AttemptRead>('/student/full-mock/start')
  return data
}

export async function getMyResults(params?: {
  limit?: number
  offset?: number
}): Promise<StudentResult[]> {
  const { data } = await api.get<{
    items: StudentResult[]
    total: number
    limit: number
    offset: number
  }>('/student/results', {
    params: { limit: params?.limit ?? 100, offset: params?.offset ?? 0 },
  })
  return data.items
}
