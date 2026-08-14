import { api } from '@/lib/axios'

export type StatPoint = {
  attempts: number
  delta_vs_yesterday?: number | null
  delta_percent?: number | null
}

export type DashboardStats = {
  today: StatPoint
  week: StatPoint
  month: StatPoint
}

export type DashboardAlert = {
  type: string
  severity: 'error' | 'warning'
  message: string
  action_url: string
  count: number
}

export type ActivityPoint = {
  date: string
  attempts_count: number
}

export type InProgressItem = {
  attempt_id: string
  student_name: string
  test_name: string
  current_section: string | null
  started_min_ago: number
}

export type BandBucket = {
  range: string
  count: number
  percentage: number
}

export type BandDistribution = {
  buckets: BandBucket[]
  total_scored: number
  period_days: number
}

export type SkillStat = {
  section: 'listening' | 'reading' | 'writing' | 'speaking'
  avg_band: number | null
  count: number
}

export type TopStudent = {
  student_id: string
  name: string
  avg_band: number
  attempts_count: number
}

export type PopularTest = {
  test_id: string
  title: string
  attempts_count: number
  avg_band: number | null
}

export type RecentActivityItem = {
  type: 'started' | 'finished' | 'submitted_writing'
  student_name: string
  test_name: string
  timestamp: string
  band?: number | null
  attempt_id: string
}

export type DashboardOverview = {
  total_students: number
  active_students_week: number
  published_tests: number
  draft_tests: number
  completion_rate: number | null
  avg_band: number | null
  pending_evaluations: number
}

export type AdminDashboardResponse = {
  overview: DashboardOverview
  stats: DashboardStats
  alerts: DashboardAlert[]
  activity_chart: ActivityPoint[]
  in_progress: InProgressItem[]
  band_distribution: BandDistribution
  skill_breakdown: SkillStat[]
  top_students: TopStudent[]
  popular_tests: PopularTest[]
  recent_activity: RecentActivityItem[]
}

export async function getAdminDashboard(): Promise<AdminDashboardResponse> {
  const { data } = await api.get<AdminDashboardResponse>('/admin/dashboard')
  return data
}
