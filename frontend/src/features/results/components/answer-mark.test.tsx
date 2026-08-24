import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { AnswerMark } from './answer-mark'

describe('AnswerMark', () => {
  it('shows B and D as separate marks, not struck-through text', async () => {
    const screen = await render(
      <div>
        <AnswerMark value='B' tone='wrong' optionLetters />
        <AnswerMark value='D' tone='right' optionLetters />
      </div>,
    )

    const b = screen.getByText('B')
    const d = screen.getByText('D')
    await expect.element(b).toBeVisible()
    await expect.element(d).toBeVisible()
    expect(b.element().className).not.toMatch(/line-through/)
    expect(d.element().className).not.toMatch(/line-through/)
  })

  it('colours each letter of a half-right pair against the key', async () => {
    // "Choose TWO letters": the student picked D and C, the key is B and C,
    // so C earned its mark and must not be painted wrong alongside D.
    const screen = await render(
      <AnswerMark value='D, C' tone='plain' optionLetters matchAgainst='B | C' />,
    )

    const d = screen.getByText('D')
    const c = screen.getByText('C')
    await expect.element(d).toBeVisible()
    await expect.element(c).toBeVisible()
    expect(d.element().className).toMatch(/text-destructive/)
    expect(c.element().className).toMatch(/text-success-foreground/)
  })

  it('leaves a Matching Headings numeral as written', async () => {
    // Headings are numbered i, ii, iii… so "i" is a one, not the letter I.
    const screen = await render(<AnswerMark value='i' tone='right' />)
    await expect.element(screen.getByText('i')).toBeVisible()
    expect(screen.container.textContent).not.toContain('I')
  })

  it('still strikes through a wrong word answer', async () => {
    const screen = await render(<AnswerMark value='river' tone='wrong' />)
    const word = screen.getByText('river')
    await expect.element(word).toBeVisible()
    expect(word.element().className).toMatch(/line-through/)
  })
})
