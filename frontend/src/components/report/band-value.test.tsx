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
        animateFrom={0}
        animateDelay={300}
        animateDuration={900}
        onAnimateComplete={onComplete}
      />,
    )
    await expect.element(screen.getByText('7.0')).toBeInTheDocument()
    expect(onComplete).toHaveBeenCalledTimes(1)
    restore()
  })

  it('animates from the starting value and completes at the target', async () => {
    const restore = stubMatchMedia(false)
    const onComplete = vi.fn()
    const screen = await render(
      <BandValue
        band={7}
        size='display'
        animateFrom={0}
        animateDelay={0}
        animateDuration={80}
        onAnimateComplete={onComplete}
      />,
    )
    await expect.element(screen.getByText('7.0')).toBeInTheDocument()
    expect(onComplete).toHaveBeenCalledTimes(1)
    restore()
  })

  it('renders an em dash when the band is null', async () => {
    const screen = await render(<BandValue band={null} size='display' />)
    await expect.element(screen.getByText('—')).toBeInTheDocument()
  })
})
