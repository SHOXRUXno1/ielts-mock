import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DirectionProvider } from '@/context/direction-provider'
import { StepWriting } from './step-writing'
import type { Section, Test } from '../data/schema'

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}))

vi.mock('@/lib/api/section-settings', () => ({
  updateSectionDuration: vi.fn(),
}))

const test: Test = {
  id: 't1',
  title: 'Cambridge IELTS 16 – Test 1',
  description: null,
  is_published: false,
  type: 'academic',
  book_name: 'Cambridge IELTS 16',
  book_slug: 'cambridge-ielts-16',
  test_number: 1,
  created_at: '',
  updated_at: '',
}

const writingSection: Section = {
  id: 'ws1',
  test_id: 't1',
  type: 'writing',
  order: 20,
  audio_url: null,
  passage: null,
  audioscript: null,
  title: null,
  passage_subtitle: null,
  question_count: 0,
  question_groups: [],
  created_at: '',
  updated_at: '',
}

describe('StepWriting', () => {
  it('renders empty Task 1/2 without crashing when questions are not loaded', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const screen = await render(
      <DirectionProvider>
        <QueryClientProvider client={qc}>
          <StepWriting
            test={test}
            sections={[writingSection]}
            sectionSettings={[]}
            questionsMap={{}}
            onRefresh={() => {}}
          />
        </QueryClientProvider>
      </DirectionProvider>,
    )

    await expect.element(screen.getByRole('tab', { name: 'Task 1' })).toBeInTheDocument()
    await expect.element(screen.getByRole('tab', { name: 'Task 2' })).toBeInTheDocument()
  })
})
