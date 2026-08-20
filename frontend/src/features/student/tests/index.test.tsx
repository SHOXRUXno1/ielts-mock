import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DirectionProvider } from '@/context/direction-provider'
import { useAuthStore } from '@/stores/auth-store'
import { StudentTests } from './index'
import type { CatalogResponse } from '@/lib/api/student'

const catalog: CatalogResponse = {
  groups: [
    {
      name: 'Cambridge IELTS 9',
      tests: [
        {
          id: '9a8f1a55-c58f-4a86-94c6-677b74ef9eba',
          title: 'Cambridge IELTS 9 – Test 4',
          book_name: 'Cambridge IELTS 9',
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
    {
      name: 'Other',
      tests: [
        {
          id: '4cdab44f-db90-4122-a02b-d7df41fc400a',
          title: 'Cambridge IELTS 16 – Test 1',
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

vi.mock('@/lib/api/student', () => ({
  getTestCatalog: () => Promise.resolve(catalog),
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

describe('StudentTests', () => {
  it('renders published catalog cards without crashing', async () => {
    useAuthStore.getState().auth.setAccessToken('test-token')
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const screen = await render(
      <DirectionProvider>
        <QueryClientProvider client={qc}>
          <StudentTests />
        </QueryClientProvider>
      </DirectionProvider>,
    )

    await expect.element(screen.getByText('Test Catalog')).toBeInTheDocument()
    await expect
      .element(screen.getByText('Cambridge IELTS 9 – Test 4'))
      .toBeInTheDocument()
    await expect
      .element(screen.getByText('Cambridge IELTS 16 – Test 1'))
      .toBeInTheDocument()
    await expect.element(screen.getByText('Start full mock').first()).toBeInTheDocument()
  })

  afterEach(() => {
    useAuthStore.getState().auth.reset()
  })
})
