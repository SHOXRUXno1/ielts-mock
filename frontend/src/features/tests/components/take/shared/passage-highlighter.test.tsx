import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { PassageHighlighter } from './passage-highlighter'

describe('PassageHighlighter copy behavior', () => {
  it('blocks copy events when copying is disabled and keeps text selectable', async () => {
    const screen = await render(
      <PassageHighlighter sectionId='reading-1' allowCopy={false}>
        Passage text
      </PassageHighlighter>,
    )
    const passage = screen.container.querySelector('.passage-highlighter')
    expect(passage?.classList.contains('select-text')).toBe(true)

    const copyEvent = new Event('copy', { bubbles: true, cancelable: true })
    passage?.dispatchEvent(copyEvent)

    expect(copyEvent.defaultPrevented).toBe(true)
  })

  it('leaves copy events unchanged by default', async () => {
    const screen = await render(
      <PassageHighlighter sectionId='reading-1'>Passage text</PassageHighlighter>,
    )
    const passage = screen.container.querySelector('.passage-highlighter')
    const copyEvent = new Event('copy', { bubbles: true, cancelable: true })

    passage?.dispatchEvent(copyEvent)

    expect(copyEvent.defaultPrevented).toBe(false)
  })
})
