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
    listening: null,
    reading: null,
    writing: null,
    speaking: null,
  },
  band_trend: [],
  in_progress: null,
  recent: [],
}

vi.mock('@/lib/api/student', () => ({
  getDashboard: () => Promise.resolve(dashboard),
}))

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: () => ({
    auth: {
      user: { full_name: 'Alibek', login: 'alibek', name: 'Alibek' },
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

describe('StudentProfile', () => {
  it('renders identity and performance without the gradient banner', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const screen = await render(
      <DirectionProvider>
        <QueryClientProvider client={qc}>
          <StudentProfile />
        </QueryClientProvider>
      </DirectionProvider>,
    )

    await expect.element(screen.getByText('Profile')).toBeInTheDocument()
    await expect.element(screen.getByText('Alibek').first()).toBeInTheDocument()
    await expect.element(screen.getByText('Tests taken')).toBeInTheDocument()
    await expect.element(screen.getByText('View results')).toBeInTheDocument()
    await expect.element(screen.getByText('Sign out')).toBeInTheDocument()
  })
})
