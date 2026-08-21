import { afterEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { BandValue } from './band-value'

function stubMatchMedia(reduced: boolean) {
  const original = window.matchMedia
  window.matchMedia = (query: string) =>
    ({
      matches: query === '(prefers-reduced-motion: reduce)' ? reduced : false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList
  return () => {
    window.matchMedia = original
  }
}

describe('BandValue', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the final band with no animateFrom and fires the callback', async () => {
    const onComplete = vi.fn()
    const screen = await render(
      <BandValue band={7} size='display' onAnimateComplete={onComplete} />,
    )
    await expect.element(screen.getByText('7.0')).toBeInTheDocument()
    expect(onComplete).toHaveBeenCalledTimes(1)
  })

  it('jumps straight to the final value when reduced motion is on', async () => {
    const restore = stubMatchMedia(true)
    const onComplete = vi.fn()
    const screen = await render(
      <BandValue
        band={7}
        size='display'
        animateFrom={1}
        animateDelay={300}
        animateDuration={900}
        onAnimateComplete={onComplete}
      />,
    )
    await expect.element(screen.getByText('7.0')).toBeInTheDocument()
    expect(onComplete).toHaveBeenCalledTimes(1)
    restore()
  })

  it('starts the count-up at the animateFrom value snapped to a half band', async () => {
    const restore = stubMatchMedia(false)
    const screen = await render(
      <BandValue
        band={9}
        size='display'
        animateFrom={1}
        animateDelay={1000}
        animateDuration={900}
      />,
    )
    // Delay is 1s — during the delay the display sits at the start value.
    await expect.element(screen.getByText('1.0')).toBeInTheDocument()
    restore()
  })

  it('animates from the starting value and completes at the target', async () => {
    const restore = stubMatchMedia(false)
    const onComplete = vi.fn()
    const displayed: number[] = []
    const screen = await render(
      <BandValue
        band={7}
        size='display'
        animateFrom={1}
        animateDelay={0}
        animateDuration={80}
        onAnimateComplete={onComplete}
        onDisplayChange={(v) => displayed.push(v)}
      />,
    )
    await expect.element(screen.getByText('7.0')).toBeInTheDocument()
    expect(onComplete).toHaveBeenCalledTimes(1)
    // Every intermediate value must be a legal IELTS half-band.
    for (const v of displayed) {
      expect(v * 2).toBe(Math.round(v * 2))
    }
    expect(displayed.at(-1)).toBe(7)
    restore()
  })

  it('renders an em dash when the band is null', async () => {
    const screen = await render(<BandValue band={null} size='display' />)
    await expect.element(screen.getByText('—')).toBeInTheDocument()
  })
})
