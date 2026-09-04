import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import type { Question } from '../../data/schema'
import type { FlowStructure } from '../../data/compound'
import { CompoundCompletionRenderer } from './compound-completion-renderer'

vi.mock('@/lib/api/attempts', () => ({
  mediaUrl: (url: string) => url,
}))

function gap(id: string, n: number): Question {
  return {
    id,
    section_id: 's1',
    question_group_id: 'g1',
    order: n,
    question_type: 'flow_chart_completion',
    content: { gap_id: id },
    answer_key: null,
    task_number: null,
    min_words: null,
    image_url: null,
    essay_type: null,
    computed_number: n,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  }
}

const structure: FlowStructure = {
  variant: 'flow',
  title: 'LECTURES AND NOTE TAKING',
  instruction_words: 'THREE WORDS',
  max_words_per_gap: 3,
  steps: [
    {
      segments: [
        { type: 'text', value: 'Complete all ' },
        { type: 'gap', gap_id: 'f21' },
        { type: 'text', value: ' before lecture' },
      ],
    },
    {
      segments: [{ type: 'text', value: 'Take notes during lecture' }],
    },
    {
      segments: [
        { type: 'gap', gap_id: 'f23' },
        { type: 'text', value: ' immediately after lecture' },
      ],
    },
    {
      segments: [],
      fork: [
        {
          segments: [
            { type: 'text', value: 'Revise before ' },
            { type: 'gap', gap_id: 'f24' },
          ],
        },
        {
          segments: [
            { type: 'text', value: 'Revise every ' },
            { type: 'gap', gap_id: 'f25' },
          ],
        },
      ],
    },
  ],
}

describe('flow-chart completion', () => {
  it('renders a titled flowchart with inline blanks and a two-column fork', async () => {
    const screen = await render(
      <CompoundCompletionRenderer
        structure={structure}
        questions={[gap('f21', 21), gap('f23', 23), gap('f24', 24), gap('f25', 25)]}
        answers={{}}
        onAnswer={() => {}}
      />,
    )

    const root = screen.container.querySelector('[data-flow-chart]') as HTMLElement
    expect(root).toBeTruthy()
    await expect.element(screen.getByText('LECTURES AND NOTE TAKING')).toBeVisible()
    await expect.element(screen.getByText(/Complete all/)).toBeVisible()
    await expect.element(screen.getByText(/before lecture/)).toBeVisible()
    await expect.element(screen.getByText('Revise before')).toBeVisible()
    await expect.element(screen.getByText('Revise every')).toBeVisible()
    expect(root.textContent).toContain('↓')
    expect(root.textContent).toContain('↙')
    expect(root.textContent).toContain('↘')
    expect(root.querySelectorAll('input')).toHaveLength(4)
    const forkRow = [...root.querySelectorAll('.grid-cols-2')].find((el) =>
      el.textContent?.includes('Revise before'),
    )
    expect(forkRow).toBeTruthy()
  })
})
