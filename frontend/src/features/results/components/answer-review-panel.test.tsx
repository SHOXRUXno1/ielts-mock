import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import type { AnswerRead } from '@/lib/api/attempts'
import { AnswerReviewPanel } from './answer-review-panel'

function answer(
  id: string,
  {
    response,
    correct,
    score = correct ? 1 : 0,
    order,
    end,
    questionType = 'short_answer',
    answerKey,
  }: {
    response: unknown
    correct: boolean
    score?: number
    order: number
    end?: number
    questionType?: string
    answerKey: Record<string, unknown>
  },
): AnswerRead {
  return {
    id,
    question_id: `question-${id}`,
    response: { answer: response },
    is_correct: correct,
    score,
    section: { id: 'listening-1', type: 'listening', order: 1 },
    question: {
      id: `question-${id}`,
      section_id: 'listening-1',
      order,
      computed_number: order,
      computed_number_end: end,
      question_type: questionType,
      content: questionType === 'multi_select' ? { choose_n: 2 } : {},
      answer_key: answerKey,
    },
  }
}

const allCorrect = [
  answer('one', {
    response: 'June 6th',
    correct: true,
    order: 1,
    answerKey: { accepted_answers: ['6 June', '6th June', 'June 6'] },
  }),
]

const mixedAnswers = [
  answer('partial', {
    response: ['D', 'C'],
    correct: false,
    score: 0.5,
    order: 8,
    end: 9,
    questionType: 'multi_select',
    answerKey: { correct: ['B', 'C'] },
  }),
  answer('wrong', {
    response: 'winter',
    correct: false,
    order: 10,
    answerKey: { accepted_answers: ['summer', 'the summer'] },
  }),
]

function renderReview(answers: AnswerRead[]) {
  return render(
    <AnswerReviewPanel
      skill='listening'
      band={6.5}
      raw={null}
      answers={answers}
      attemptStatus='completed'
    />,
  )
}

describe('AnswerReviewPanel', () => {
  it('shows every answer by default when every answer is correct', async () => {
    const screen = await renderReview(allCorrect)

    await expect.element(screen.getByText('June 6th')).toBeVisible()
    await expect.element(screen.getByText('6 June | 6th June | June 6')).toBeVisible()
  })

  it('shows the complete audit by default and filters it on demand', async () => {
    const screen = await renderReview(mixedAnswers)

    await expect.element(screen.getByText('Partly correct')).toBeVisible()
    await expect.element(screen.getByText('Incorrect').first()).toBeVisible()
    await expect.element(screen.getByText('8–9')).toBeVisible()
    await expect.element(screen.getByText('1/2 marks')).toBeVisible()
    await expect.element(screen.getByText('summer | the summer')).toBeVisible()

    await screen.getByRole('button', { name: /Incorrect/ }).click()
    await expect.element(screen.getByText('Part 1')).toBeVisible()
  })
})
