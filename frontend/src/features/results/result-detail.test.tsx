import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fetchResultDetail, type AttemptDetailRead } from '@/lib/api/attempts'
import { ResultDetail } from './result-detail'

vi.mock('@/lib/api/attempts', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api/attempts')>(
    '@/lib/api/attempts',
  )
  return {
    ...actual,
    fetchResultDetail: vi.fn(),
    finalizeAttempt: vi.fn(),
    overrideBand: vi.fn(),
  }
})

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: (selector: (s: { auth: { user: { role: string } } }) => unknown) =>
    selector({ auth: { user: { role: 'student' } } }),
}))

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    useParams: () => ({ attemptId: 'attempt-1' }),
    useSearch: () => ({}),
    useNavigate: () => vi.fn(),
    Link: ({ children }: { children: ReactNode }) => <a href='#'>{children}</a>,
  }
})

const partialAttempt: AttemptDetailRead = {
  id: 'attempt-1',
  test_id: 'test-1',
  status: 'partial',
  mode: 'full_mock',
  practice_section_id: null,
  practice_part_number: null,
  practice_section_type: null,
  practice_correct: null,
  practice_total: null,
  started_at: '2026-08-19T07:00:00.000Z',
  finished_at: '2026-08-19T10:00:00.000Z',
  overall_band: null,
  listening_band: null,
  reading_band: null,
  writing_band: 8.5,
  speaking_band: 2.0,
  listening_raw: null,
  reading_raw: null,
  flagged_overtime: false,
  created_at: '2026-08-19T07:00:00.000Z',
  updated_at: '2026-08-19T10:00:00.000Z',
  answers: [],
  evaluation_jobs: [],
  speaking_session: null,
  test_title: 'Cambridge IELTS 15 – Test 1',
}

function renderDetail() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ResultDetail />
    </QueryClientProvider>,
  )
}

describe('ResultDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows a skeleton while the result is loading', async () => {
    vi.mocked(fetchResultDetail).mockImplementation(
      () => new Promise(() => undefined),
    )
    const screen = await renderDetail()
    await expect
      .element(screen.getByLabelText('Loading result'))
      .toBeInTheDocument()
  })

  it('shows an error state when the result fails to load', async () => {
    vi.mocked(fetchResultDetail).mockRejectedValue(new Error('not found'))
    const screen = await renderDetail()
    await expect.element(screen.getByText('Could not load result')).toBeInTheDocument()
    await expect
      .element(screen.getByRole('button', { name: 'Try again' }))
      .toBeInTheDocument()
  })

  it('shows an empty state when the attempt is missing', async () => {
    vi.mocked(fetchResultDetail).mockResolvedValue(
      null as unknown as AttemptDetailRead,
    )
    const screen = await renderDetail()
    await expect.element(screen.getByText('Attempt not found')).toBeInTheDocument()
  })

  it('renders a partial attempt with writing and speaking bands', async () => {
    vi.mocked(fetchResultDetail).mockResolvedValue(partialAttempt)
    const screen = await renderDetail()
    await expect
      .element(screen.getByText('Cambridge IELTS 15 – Test 1'))
      .toBeInTheDocument()
    await expect.element(screen.getByText('Partial').first()).toBeInTheDocument()
    await expect.element(screen.getByText('8.5').first()).toBeInTheDocument()
    await expect.element(screen.getByText('2.0').first()).toBeInTheDocument()
    await expect.element(screen.getByText('Not attempted').first()).toBeInTheDocument()
    await expect
      .element(screen.getByLabelText('Overall band not available'))
      .toBeInTheDocument()
    await expect
      .element(screen.getByLabelText('Listening not attempted'))
      .toBeInTheDocument()
    await expect
      .element(screen.getByRole('link', { name: /Writing/ }))
      .toBeInTheDocument()
  })
})
