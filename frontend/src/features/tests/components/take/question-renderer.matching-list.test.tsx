import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { MatchingLetterRenderer } from './question-renderer'
import { matchingOptionParts, type Question } from '../../data/schema'

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

  it('shows A B C and an empty letter slot, not the question number', async () => {
    const screen = await render(
      <MatchingLetterRenderer
        questions={[makeQuestion()]}
        options={[
          'they must do this',
          'they can do this if they want to',
          "they can't do this",
        ]}
        answers={{}}
        onAnswer={() => {}}
      />,
    )

    const letters = [...screen.container.querySelectorAll('p .font-semibold')].map(
      (el) => el.textContent,
    )
    expect(letters).toEqual(['A', 'B', 'C'])
    await expect.element(screen.getByText('they must do this')).toBeVisible()
    expect(screen.container.querySelector('[data-q-chip]')?.textContent).toBe('21')
    const trigger = screen.container.querySelector('[data-slot="select-trigger"]')
    expect(trigger?.textContent).toContain('—')
    expect(trigger?.textContent).not.toContain('21')
  })
})

describe('matchingOptionParts', () => {
  it('keeps a printed letter and invents A/B/C when the seed has none', () => {
    expect(matchingOptionParts('A. they must do this', 0)).toEqual({
      letter: 'A',
      text: 'they must do this',
    })
    expect(matchingOptionParts('they must do this', 0)).toEqual({
      letter: 'A',
      text: 'they must do this',
    })
  })
})
