import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QuestionEditor, type QuestionDraft } from './question-editor'

vi.mock('@/lib/api/attempts', () => ({
  mediaUrl: (url: string) => url,
  uploadImage: vi.fn(),
}))

function makeMcq(imageUrl: string | null): QuestionDraft {
  return {
    id: 'q10',
    order: 10,
    question_type: 'mcq',
    content: {
      question: "Which map shows the correct location of the seller's house?",
      options: ['A', 'B', 'C'],
    },
    answer_key: { correct: 'B' },
    image_url: imageUrl,
  }
}

describe('MCQ question image field', () => {
  it('shows the current map and lets the admin remove it', async () => {
    const onChange = vi.fn()
    const screen = await render(
      <QuestionEditor
        question={makeMcq('/media/images/practice_b_t1_listening_map.png')}
        questionNumber={10}
        allowedTypes={['mcq']}
        onChange={onChange}
        onDelete={() => {}}
      />,
    )

    const el = screen.container.querySelector('img') as HTMLImageElement
    expect(el).toBeTruthy()
    expect(el.getAttribute('src')).toBe(
      '/media/images/practice_b_t1_listening_map.png',
    )

    await screen.getByRole('button', { name: 'Remove' }).click()
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ image_url: null }),
    )
  })

  it('shows an upload prompt when the question has no image', async () => {
    const screen = await render(
      <QuestionEditor
        question={makeMcq(null)}
        questionNumber={10}
        allowedTypes={['mcq']}
        onChange={() => {}}
        onDelete={() => {}}
      />,
    )

    expect(screen.container.querySelector('img')).toBeNull()
    await expect
      .element(screen.getByText('Click to upload map or diagram'))
      .toBeVisible()
  })
})
