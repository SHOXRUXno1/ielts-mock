import { afterEach, describe, expect, it, vi } from 'vitest'
import { userEvent } from 'vitest/browser'
import { render } from 'vitest-browser-react'
import { ScoreReveal, type ScoreRevealSection } from './score-reveal'

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

const scoredSections: ScoreRevealSection[] = [
  { skill: 'listening', band: 7.5, status: 'scored' },
  { skill: 'reading', band: 7, status: 'scored' },
  { skill: 'writing', band: null, status: 'pending' },
  { skill: 'speaking', band: null, status: 'pending' },
]

describe('ScoreReveal', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the final state and announces once when reduced motion is on', async () => {
    const restore = stubMatchMedia(true)
    const onView = vi.fn()
    const onDownload = vi.fn()
    const onClose = vi.fn()
    const screen = await render(
      <ScoreReveal
        overallBand={7}
        sections={scoredSections}
        testTitle='Cambridge IELTS 15 – Test 1'
        onViewResults={onView}
        onDownloadPdf={onDownload}
        onClose={onClose}
      />,
    )
    await expect
      .element(screen.getByLabelText(/Overall band 7\.0/))
      .toBeInTheDocument()
    // Pending chips render an em dash.
    const dashes = screen.getByText('—').all()
    expect(dashes.length).toBeGreaterThanOrEqual(2)
    // Single aria-live announcement mentions the final band.
    const live = document.querySelector('[aria-live="polite"]')
    expect(live?.textContent).toContain('Overall band 7.0')
    // Primary CTA is "View results" (band 7 → strong).
    const view = screen.getByRole('button', { name: 'View results' })
    await expect.element(view).toBeInTheDocument()
    await userEvent.click(view)
    expect(onView).toHaveBeenCalledTimes(1)
    restore()
  })

  it('uses "Review mistakes" as the primary CTA when band is weak', async () => {
    const restore = stubMatchMedia(true)
    const screen = await render(
      <ScoreReveal
        overallBand={4.5}
        sections={scoredSections}
        testTitle='Test'
        onViewResults={() => {}}
        onDownloadPdf={() => {}}
        onClose={() => {}}
      />,
    )
    await expect
      .element(screen.getByRole('button', { name: 'Review mistakes' }))
      .toBeInTheDocument()
    restore()
  })

  it('exposes the Download PDF button and invokes the handler', async () => {
    const restore = stubMatchMedia(true)
    const onDownload = vi.fn()
    const screen = await render(
      <ScoreReveal
        overallBand={7}
        sections={scoredSections}
        testTitle='Test'
        onViewResults={() => {}}
        onDownloadPdf={onDownload}
        onClose={() => {}}
      />,
    )
    const btn = screen.getByRole('button', { name: /download pdf/i })
    await userEvent.click(btn)
    expect(onDownload).toHaveBeenCalledTimes(1)
    restore()
  })

  it('keeps the CTAs disabled during the sequence and enables them once done', async () => {
    const restore = stubMatchMedia(false)
    const screen = await render(
      <ScoreReveal
        overallBand={7}
        sections={scoredSections}
        testTitle='Test'
        onViewResults={() => {}}
        onDownloadPdf={() => {}}
        onClose={() => {}}
      />,
    )
    // During the sequence, both CTAs must be disabled.
    const view = screen.getByRole('button', { name: 'View results' })
    await expect.element(view).toBeDisabled()
    // After the full 2.4s timeline the primary CTA is enabled.
    await expect
      .element(screen.getByRole('button', { name: 'View results' }), {
        timeout: 4000,
      })
      .toBeEnabled()
    restore()
  })
})
