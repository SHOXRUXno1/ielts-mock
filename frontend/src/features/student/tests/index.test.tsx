import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DirectionProvider } from '@/context/direction-provider'
import { useAuthStore } from '@/stores/auth-store'
import { StudentTests } from './index'
import type { CatalogResponse, FullMockStatus } from '@/lib/api/student'

const catalog: CatalogResponse = {
  groups: [
    {
      name: 'Practice',
      tests: [
        {
          id: '9a8f1a55-c58f-4a86-94c6-677b74ef9eba',
          title: 'Practice set #1',
          book_name: null,
          test_type: 'academic',
          duration_minutes: 150,
          section_count: 4,
          sections: {
            listening: { score: null, completed: false },
            reading: { score: null, completed: false },
            writing: { score: null, completed: false },
            speaking: { score: null, completed: false },
          },
          overall_score: null,
          status: 'new',
          in_progress_attempt_id: null,
          last_attempt_at: null,
        },
        {
          id: '4cdab44f-db90-4122-a02b-d7df41fc400a',
          title: 'Practice set #2',
          book_name: null,
          test_type: 'academic',
          duration_minutes: 150,
          section_count: 4,
          sections: {
            listening: { score: null, completed: false },
            reading: { score: null, completed: false },
            writing: { score: null, completed: false },
            speaking: { score: null, completed: false },
          },
          overall_score: null,
          status: 'new',
          in_progress_attempt_id: null,
          last_attempt_at: null,
        },
      ],
    },
  ],
}

const mockStatus: FullMockStatus = {
  remaining: 4,
  total_published: 4,
  in_progress_attempt_id: null,
  in_progress_test_id: null,
  in_progress_title: null,
}

vi.mock('@/lib/api/student', () => ({
  getTestCatalog: () => Promise.resolve(catalog),
  getFullMockStatus: () => Promise.resolve(mockStatus),
  startFullMock: () => Promise.resolve({ id: 'a1', test_id: 't1', status: 'in_progress' }),
}))

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    Link: ({ children }: { children: ReactNode }) => <a href='#'>{children}</a>,
    useNavigate: () => vi.fn(),
  }
})

describe('StudentTests', () => {
  it('offers one full-mock start and anonymous practice cards', async () => {
    useAuthStore.getState().auth.setAccessToken('test-token')
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const screen = await render(
      <DirectionProvider>
        <QueryClientProvider client={qc}>
          <StudentTests />
        </QueryClientProvider>
      </DirectionProvider>,
    )

    await expect
      .element(screen.getByRole('heading', { name: 'Full mock' }))
      .toBeInTheDocument()
    await expect
      .element(screen.getByRole('button', { name: 'Start full mock' }))
      .toBeInTheDocument()
    await expect.element(screen.getByText('Practice set #1')).toBeInTheDocument()
    await expect.element(screen.getByText('Practice set #2')).toBeInTheDocument()
    await expect.element(screen.getByText('Practice sets')).toBeInTheDocument()
    expect(screen.container.textContent).not.toMatch(/Cambridge/i)
  })

  afterEach(() => {
    useAuthStore.getState().auth.reset()
  })
})
