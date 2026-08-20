import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { QuestionRangeTitle } from './question-range-title'

describe('QuestionRangeTitle', () => {
  it('shows a single question number', async () => {
    const screen = await render(<QuestionRangeTitle min={9} max={9} />)
    await expect.element(screen.getByText('Question')).toBeVisible()
    expect(screen.container.textContent?.replace(/\s+/g, ' ').trim()).toBe(
      'Question 9',
    )
  })

  it('shows an IELTS range, not every number in between', async () => {
    const screen = await render(<QuestionRangeTitle min={5} max={7} />)
    const text = screen.container.textContent?.replace(/\s+/g, ' ').trim() ?? ''
    expect(text.startsWith('Questions 5–7')).toBe(true)
    expect(text).not.toContain('5–6–7')
  })
})
