import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { userEvent } from 'vitest/browser'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WritingSection } from './writing-section'
import type { Question } from '../../data/schema'

vi.mock('@/lib/api/feedback', () => ({
  requestWritingFeedback: vi.fn(() => Promise.resolve({})),
}))

vi.mock('@/lib/api/attempts', () => ({
  mediaUrl: (url: string) => url,
}))

function makeQuestion(overrides: Partial<Question> & { id: string }): Question {
  return {
    section_id: 's1',
    question_group_id: null,
    order: 0,
    question_type: 'essay',
    content: { prompt: 'Describe the chart below.' },
    answer_key: null,
    task_number: 1,
    min_words: 150,
    image_url: null,
    essay_type: null,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    ...overrides,
  }
}

const TASK1 = makeQuestion({ id: 'q1', order: 0, task_number: 1, min_words: 150 })
const TASK2 = makeQuestion({
  id: 'q2',
  order: 1,
  task_number: 2,
  min_words: 250,
  content: { prompt: 'Some people believe that university education should be free.' },
})

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

async function renderSection(
  overrides: {
    activeTaskIdx?: number
    answers?: Record<string, Record<string, unknown>>
  } = {},
) {
  const onAnswer = vi.fn()
  const qc = createQueryClient()

  const screen = await render(
    <QueryClientProvider client={qc}>
      <WritingSection
        questions={[TASK1, TASK2]}
        answers={overrides.answers ?? {}}
        onAnswer={onAnswer}
        attemptId='attempt-1'
        activeTaskIdx={overrides.activeTaskIdx ?? 0}
      />
    </QueryClientProvider>,
  )

  return { screen, onAnswer }
}

describe('WritingSection — single-task practice', () => {
  it('renders one task without misconfigured error', async () => {
    const onAnswer = vi.fn()
    const qc = createQueryClient()
    const screen = await render(
      <QueryClientProvider client={qc}>
        <WritingSection
          questions={[TASK2]}
          answers={{}}
          onAnswer={onAnswer}
          attemptId='attempt-1'
          activeTaskIdx={1}
        />
      </QueryClientProvider>,
    )
    await expect
      .element(screen.getByRole('heading', { name: 'Task 2' }))
      .toBeInTheDocument()
    expect(screen.getByText('Writing section misconfigured').elements().length).toBe(
      0,
    )
  })
})

describe('WritingSection — prompt area', () => {
  it('heading renders "Task 1" in normal case', async () => {
    const { screen } = await renderSection()
    await expect
      .element(screen.getByRole('heading', { name: /Task/i }))
      .toBeInTheDocument()
  })

  it('subtitle shows time recommendation', async () => {
    const { screen } = await renderSection()
    await expect
      .element(
        screen.getByText('You should spend about 20 minutes on this task.'),
      )
      .toBeInTheDocument()
  })

  it('info hint shows min word count for Task 1', async () => {
    const { screen } = await renderSection()
    await expect
      .element(screen.getByText('Write at least 150 words'))
      .toBeInTheDocument()
  })

  it('Task 2 info hint shows 250 words', async () => {
    const { screen } = await renderSection({ activeTaskIdx: 1 })
    await expect
      .element(screen.getByText('Write at least 250 words'))
      .toBeInTheDocument()
  })

  it('Task 2 prompt uses the same block as Task 1, without the extra topic line', async () => {
    const { screen } = await renderSection({ activeTaskIdx: 1 })
    await expect
      .element(
        screen.getByText(
          'Some people believe that university education should be free.',
        ),
      )
      .toBeInTheDocument()
    expect(
      screen.getByText('Write about the following topic:').elements().length,
    ).toBe(0)
  })
})

describe('WritingSection — editor area', () => {
  it('shows "Get Feedback" button, not "Submit for Feedback"', async () => {
    const { screen } = await renderSection()
    await expect
      .element(screen.getByRole('button', { name: /Get Feedback/ }))
      .toBeInTheDocument()
    expect(screen.getByText('Submit for Feedback').elements().length).toBe(0)
  })

  it('feedback button is disabled when no text entered', async () => {
    const { screen } = await renderSection()
    const btn = screen.getByRole('button', { name: /Get Feedback/ })
    await expect.element(btn).toBeDisabled()
  })
})

describe('WritingSection — word count', () => {
  it('shows "0 / 150+ words" format initially', async () => {
    const { screen } = await renderSection()
    await expect
      .element(screen.getByText('0 / 150+ words'))
      .toBeInTheDocument()
  })

  it('word count uses tabular-nums class', async () => {
    const { screen } = await renderSection()
    const el = await screen.getByText('0 / 150+ words').element()
    expect(el.className).toContain('tabular-nums')
  })
})

describe('WritingSection — feedback section', () => {
  it('shows "AI Feedback" label, not "Writing Feedback"', async () => {
    const { screen } = await renderSection()
    await expect
      .element(screen.getByText('AI Feedback'))
      .toBeInTheDocument()
    expect(screen.getByText('Writing Feedback').elements().length).toBe(0)
  })

  it('shows pre-submit hint when feedback panel is opened', async () => {
    const { screen } = await renderSection()
    const toggle = screen.getByRole('button', { name: /AI Feedback/ })
    await userEvent.click(toggle)
    await expect
      .element(
        screen.getByText('Submit your essay to receive AI feedback'),
      )
      .toBeInTheDocument()
  })

  it('hides Get Feedback and AI Feedback in a full mock', async () => {
    const onAnswer = vi.fn()
    const qc = createQueryClient()
    const screen = await render(
      <QueryClientProvider client={qc}>
        <WritingSection
          questions={[TASK1, TASK2]}
          answers={{}}
          onAnswer={onAnswer}
          attemptId='attempt-1'
          showInstantFeedback={false}
        />
      </QueryClientProvider>,
    )
    await expect
      .element(screen.getByText('0 / 150+ words'))
      .toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Get Feedback/ }).elements().length).toBe(0)
    expect(screen.getByText('AI Feedback').elements().length).toBe(0)
  })
})
