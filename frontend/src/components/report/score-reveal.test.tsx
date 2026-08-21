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

  it('starts the overall at 1.0 then lands on the final band', async () => {
    const restore = stubMatchMedia(false)
    const onView = vi.fn()
    const screen = await render(
      <ScoreReveal
        overallBand={7}
        sections={scoredSections}
        testTitle='Cambridge IELTS 15 – Test 1'
        onViewResults={onView}
        onDownloadPdf={() => {}}
        onClose={() => {}}
      />,
    )
    const overall = screen.getByLabelText(/Overall band 7\.0/)
    await expect.element(overall.getByText('1.0')).toBeInTheDocument()
    await expect.element(overall.getByText('7.0'), { timeout: 8000 }).toBeInTheDocument()
    const pendingMarks = screen.getByText('…').all()
    expect(pendingMarks.length).toBeGreaterThanOrEqual(2)
    const view = screen.getByRole('button', { name: 'View results' })
    await expect.element(view, { timeout: 8000 }).toBeEnabled()
    const live = document.querySelector('[aria-live="polite"]')
    expect(live?.textContent).toContain('Overall band 7.0')
    await userEvent.click(view)
    expect(onView).toHaveBeenCalledTimes(1)
    restore()
  })

  it('shows a pending overall as an em dash until the band arrives', async () => {
    const restore = stubMatchMedia(false)
    const screen = await render(
      <ScoreReveal
        overallBand={null}
        sections={scoredSections}
        testTitle='Test'
        onViewResults={() => {}}
        onDownloadPdf={() => {}}
        onClose={() => {}}
      />,
    )
    await expect.element(screen.getByText('Scoring')).toBeInTheDocument()
    const dashes = screen.getByText('—').all()
    expect(dashes.length).toBeGreaterThanOrEqual(1)
    await expect
      .element(screen.getByRole('button', { name: 'View answers' }))
      .toBeEnabled()
    restore()
  })

  it('lets the student leave when scoring never produces an overall', async () => {
    const restore = stubMatchMedia(false)
    const onView = vi.fn()
    const emptySections: ScoreRevealSection[] = [
      { skill: 'listening', band: null, status: 'not_attempted' },
      { skill: 'reading', band: null, status: 'not_attempted' },
      { skill: 'writing', band: null, status: 'not_attempted' },
      { skill: 'speaking', band: null, status: 'not_attempted' },
    ]
    const screen = await render(
      <ScoreReveal
        overallBand={null}
        sections={emptySections}
        testTitle='Test'
        onViewResults={onView}
        onDownloadPdf={() => {}}
        onClose={() => {}}
      />,
    )
    await expect.element(screen.getByText('Overall')).toBeInTheDocument()
    const view = screen.getByRole('button', { name: 'View answers' })
    await expect.element(view).toBeEnabled()
    await userEvent.click(view)
    expect(onView).toHaveBeenCalledTimes(1)
    restore()
  })

  it('uses "Review mistakes" as the primary CTA when band is weak', async () => {
    const restore = stubMatchMedia(false)
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
      .element(screen.getByRole('button', { name: 'Review mistakes' }), {
        timeout: 8000,
      })
      .toBeEnabled()
    restore()
  })

  it('exposes the Download PDF button and invokes the handler', async () => {
    const restore = stubMatchMedia(false)
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
    await expect.element(btn, { timeout: 8000 }).toBeEnabled()
    await userEvent.click(btn)
    expect(onDownload).toHaveBeenCalledTimes(1)
    restore()
  })

  it('keeps View answers enabled during the sequence and reveals Download once done', async () => {
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
    const view = screen.getByRole('button', { name: 'View results' })
    await expect.element(view).toBeEnabled()
    await expect
      .element(screen.getByRole('button', { name: /download pdf/i }), {
        timeout: 8000,
      })
      .toBeEnabled()
    restore()
  })
})
