import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { TranscriptPanel } from './transcript-panel'

describe('TranscriptPanel autoScroll', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('uses instant scrollTop on self container for default variant', async () => {
    let scrollTop = 0
    const scrollHeightSpy = vi
      .spyOn(HTMLElement.prototype, 'scrollHeight', 'get')
      .mockReturnValue(400)
    const scrollTopGetSpy = vi
      .spyOn(HTMLElement.prototype, 'scrollTop', 'get')
      .mockImplementation(function (this: HTMLElement) {
        return scrollTop
      })
    const scrollTopSetSpy = vi
      .spyOn(HTMLElement.prototype, 'scrollTop', 'set')
      .mockImplementation((_value: number) => {
        scrollTop = _value
      })

    await render(
      <TranscriptPanel
        history={[
          { role: 'examiner', text: 'Hello' },
          { role: 'candidate', text: 'Hi' },
        ]}
        autoScroll
      />,
    )

    await vi.waitFor(() => expect(scrollTop).toBe(400))

    scrollHeightSpy.mockRestore()
    scrollTopGetSpy.mockRestore()
    scrollTopSetSpy.mockRestore()
  })

  it('does not auto-scroll when autoScroll is false', async () => {
    let scrollTop = 0
    vi.spyOn(HTMLElement.prototype, 'scrollHeight', 'get').mockReturnValue(400)
    vi.spyOn(HTMLElement.prototype, 'scrollTop', 'get').mockImplementation(
      () => scrollTop,
    )
    vi.spyOn(HTMLElement.prototype, 'scrollTop', 'set').mockImplementation(
      (value: number) => {
        scrollTop = value
      },
    )

    await render(
      <TranscriptPanel
        history={[{ role: 'candidate', text: 'Answer' }]}
        autoScroll={false}
      />,
    )

    expect(scrollTop).toBe(0)
  })

  it('does not scroll overlay content when scrollContainer is parent', async () => {
    let scrollTop = 0
    vi.spyOn(HTMLElement.prototype, 'scrollHeight', 'get').mockReturnValue(400)
    vi.spyOn(HTMLElement.prototype, 'scrollTop', 'get').mockImplementation(
      () => scrollTop,
    )
    vi.spyOn(HTMLElement.prototype, 'scrollTop', 'set').mockImplementation(
      (value: number) => {
        scrollTop = value
      },
    )

    await render(
      <TranscriptPanel
        history={[
          { role: 'examiner', text: 'Hello' },
          { role: 'candidate', text: 'Hi' },
        ]}
        variant='overlay'
        scrollContainer='parent'
      />,
    )

    expect(scrollTop).toBe(0)
  })
})
