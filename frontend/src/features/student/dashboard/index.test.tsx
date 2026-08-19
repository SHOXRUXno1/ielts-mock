import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DirectionProvider } from '@/context/direction-provider'
import type { DashboardResponse } from '@/lib/api/student'
import { StudentDashboard } from './index'

const dashboard: DashboardResponse = {
  tests_taken: 2,
  avg_band: 6.5,
  best_band: 7.5,
  section_bands: {
    listening: 7,
    reading: 6.5,
    writing: 6,
    speaking: 6.5,
  },
  band_trend: [
    { attempt_id: 'a1', band: 6, date: '2026-01-01T00:00:00.000Z' },
    { attempt_id: 'a2', band: 7, date: '2026-02-01T00:00:00.000Z' },
  ],
  in_progress: null,
  recent: [
    {
      id: 'a2',
      test_id: 't1',
      test_title: 'Cambridge IELTS 15 – Test 1',
      overall_band: 7,
      status: 'fully_scored',
      finished_at: '2026-02-01T00:00:00.000Z',
      created_at: '2026-02-01T00:00:00.000Z',
    },
  ],
}

vi.mock('@/lib/api/student', () => ({
  getDashboard: () => Promise.resolve(dashboard),
}))

vi.mock('@/lib/api/practice', () => ({
  fetchPracticeResults: () => Promise.resolve([]),
}))

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: (selector: (s: { auth: { user: { full_name: string } } }) => unknown) =>
    selector({ auth: { user: { full_name: 'Alibek' } } }),
}))

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    Link: ({ children }: { children: ReactNode }) => <a href='#'>{children}</a>,
  }
})

describe('StudentDashboard', () => {
  it('renders the score overview without crashing', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const screen = await render(
      <DirectionProvider>
        <QueryClientProvider client={qc}>
          <StudentDashboard />
        </QueryClientProvider>
      </DirectionProvider>,
    )

    await expect
      .element(screen.getByText('Welcome back, Alibek'))
      .toBeInTheDocument()
    await expect.element(screen.getByText('Skills')).toBeInTheDocument()
    await expect
      .element(screen.getByText('Cambridge IELTS 15 – Test 1'))
      .toBeInTheDocument()
    await expect.element(screen.getByText('Listening')).toBeInTheDocument()
  })
})
