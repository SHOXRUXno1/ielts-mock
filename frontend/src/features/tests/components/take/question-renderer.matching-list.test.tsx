import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { MatchingLetterRenderer } from './question-renderer'
import type { Question } from '../../data/schema'

function makeQuestion(): Question {
  return {
    id: 'q21',
    section_id: 's1',
    question_group_id: 'g1',
    order: 21,
    question_type: 'matching_features',
    content: { question: 'Choose a writer from a list provided.' },
    answer_key: { correct: 'A' },
    task_number: null,
    min_words: null,
    image_url: null,
    essay_type: null,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  }
}

describe('MatchingLetterRenderer list title', () => {
  it('does not invent a People / Places heading for a classification box', async () => {
    const screen = await render(
      <MatchingLetterRenderer
        questions={[makeQuestion()]}
        options={[
          'A. they must do this',
          'B. they can do this if they want to',
          'C. they can\'t do this',
        ]}
        answers={{}}
        onAnswer={() => {}}
      />,
    )

    expect(screen.container.textContent).not.toContain('List of People / Places')
    expect(screen.container.textContent).not.toContain('List of Options')
    await expect.element(screen.getByText('they must do this')).toBeVisible()
  })
})
