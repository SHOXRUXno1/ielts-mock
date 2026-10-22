import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import type { FormStructure } from '../../data/compound'
import type { Question } from '../../data/schema'
import { CompoundCompletionRenderer } from './compound-completion-renderer'

vi.mock('@/lib/api/attempts', () => ({
  mediaUrl: (url: string) => url,
}))

const structure: FormStructure = {
  variant: 'form',
  form_title: 'Grandview Hotel',
  instruction_words: 'NO MORE THAN TWO WORDS AND/OR A NUMBER',
  max_words_per_gap: 2,
  fields: [
    {
      type: 'gap_line',
      label: '',
      segments: [{ type: 'text', value: 'Reservation Form' }],
    },
    {
      type: 'gap_line',
      label: 'Arrival date',
      segments: [
        { type: 'gap', gap_id: 'q1' },
        { type: 'text', value: ' 13th. Number of nights: 2' },
      ],
    },
    {
      type: 'gap_line',
      label: '',
      segments: [
        { type: 'text', value: 'Credit card number ' },
        { type: 'gap', gap_id: 'q4' },
      ],
    },
  ],
}

function question(n: number): Question {
  return {
    id: `q${n}`,
    section_id: 's1',
    question_group_id: 'g1',
    order: n,
    question_type: 'form_completion',
    content: { gap_id: `q${n}` },
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

describe('Listening form appearance', () => {
  it('keeps the subtitle and inline label while rendering one input per gap', async () => {
    const screen = await render(
      <CompoundCompletionRenderer
        structure={structure}
        questions={[question(1), question(4)]}
        answers={{}}
        onAnswer={() => {}}
        compactForm
      />
    )

    expect(screen.container.textContent).toContain('Grandview Hotel')
    expect(screen.container.textContent).toContain('Reservation Form')
    expect(screen.container.textContent).toContain('Arrival date:')
    expect(screen.container.textContent).toContain('Credit card number:')
    expect(screen.container.textContent).toContain('13th. Number of nights: 2')
    expect(screen.container.querySelectorAll('input')).toHaveLength(2)
    expect(screen.container.querySelectorAll('[data-q-chip]')).toHaveLength(2)
  })
})
