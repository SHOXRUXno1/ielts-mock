import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DirectionProvider } from '@/context/direction-provider'
import type { DashboardResponse } from '@/lib/api/student'
import { StudentProfile } from './index'

const dashboard: DashboardResponse = {
  tests_taken: 2,
  avg_band: 6.2,
  best_band: 9,
  section_bands: {
    listening: 7,
    reading: 6.5,
    writing: 5.5,
    speaking: 6,
  },
  band_trend: [],
  in_progress: null,
  recent: [],
}

vi.mock('@/lib/api/student', () => ({
  getDashboard: () => Promise.resolve(dashboard),
  getMyResults: () =>
    Promise.resolve([
      {
        id: 'a1',
        test_id: 't1',
        test_title: 'Cambridge IELTS 15 – Test 1',
        status: 'fully_scored',
        overall_band: 6.5,
        listening_band: 7,
        reading_band: 6.5,
        writing_band: 5.5,
        speaking_band: 6,
        started_at: '2026-01-15T00:00:00.000Z',
        finished_at: '2026-01-15T02:00:00.000Z',
        created_at: '2026-01-15T00:00:00.000Z',
      },
    ]),
}))

vi.mock('@/lib/api/practice', () => ({
  fetchPracticeResults: () => Promise.resolve([]),
}))

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: () => ({
    auth: {
      user: {
        full_name: 'Alibek',
        login: 'alibek',
        name: 'Alibek',
        exp: Date.UTC(2026, 11, 31, 12, 0, 0) / 1000,
      },
      reset: vi.fn(),
    },
  }),
}))

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    Link: ({ children }: { children: ReactNode }) => <a href='#'>{children}</a>,
  }
})

function renderProfile() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <DirectionProvider>
      <QueryClientProvider client={qc}>
        <StudentProfile />
      </QueryClientProvider>
    </DirectionProvider>,
  )
}

describe('StudentProfile', () => {
  it('renders identity, skill averages, and lifetime stats', async () => {
    const screen = await renderProfile()

    await expect.element(screen.getByText('Profile')).toBeInTheDocument()
    await expect.element(screen.getByText('Alibek').first()).toBeInTheDocument()
    await expect.element(screen.getByText('Skill averages')).toBeInTheDocument()
    await expect.element(screen.getByText('View all results')).toBeInTheDocument()
    await expect.element(screen.getByText('Strongest')).toBeInTheDocument()
    await expect.element(screen.getByText('Focus on')).toBeInTheDocument()
    await expect.element(screen.getByText('Mock tests')).toBeInTheDocument()
    await expect.element(screen.getByText('Sign out')).toBeInTheDocument()
  })
})
