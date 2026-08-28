import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QuestionRenderer } from './question-renderer'
import type { Question } from '../../data/schema'

vi.mock('@/lib/api/attempts', () => ({
  mediaUrl: (url: string) => url,
}))

function makeMcq(imageUrl: string | null): Question {
  return {
    id: 'q10',
    section_id: 's1',
    question_group_id: 'g1',
    order: 10,
    question_type: 'mcq',
    content: {
      question: "Which map shows the correct location of the seller's house?",
      options: ['A', 'B', 'C'],
    },
    answer_key: { correct: 'B' },
    task_number: null,
    min_words: null,
    image_url: imageUrl,
    essay_type: null,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  }
}

describe('MCQ image', () => {
  it('shows the map when the question has image_url', async () => {
    const screen = await render(
      <QuestionRenderer
        question={makeMcq('/media/images/practice_b_t1_listening_map.png')}
        answer={{}}
        onAnswer={() => {}}
      />,
    )

    const el = screen.container.querySelector('img') as HTMLImageElement
    expect(el).toBeTruthy()
    expect(el.getAttribute('src')).toBe(
      '/media/images/practice_b_t1_listening_map.png',
    )
    await expect
      .element(
        screen.getByText("Which map shows the correct location of the seller's house?"),
      )
      .toBeVisible()
  })

  it('does not insert a blank figure when there is no image', async () => {
    const screen = await render(
      <QuestionRenderer
        question={makeMcq(null)}
        answer={{}}
        onAnswer={() => {}}
      />,
    )

    expect(screen.container.querySelector('img')).toBeNull()
  })
})
