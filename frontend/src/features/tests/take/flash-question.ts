import { questionAnchorId } from './question-anchor'

const FLASH_CLASS = 'question-anchor-flash'
const FLASH_MS = 1500

function resolveRoot(id: string): HTMLElement | null {
  const el = document.getElementById(id)
  if (!el) return null
  // Multi-slot dummy anchors are empty absolute spans — use the real wrapper.
  if (el.offsetHeight < 4 && el.offsetWidth < 4) {
    return el.closest<HTMLElement>('[id^="q-"]') ?? el.parentElement
  }
  return el
}

function resolveChip(root: HTMLElement | null, n: number): HTMLElement | null {
  if (root) {
    const exactInRoot = root.querySelector<HTMLElement>(
      `[data-q-chip][data-q-n="${n}"]`,
    )
    if (exactInRoot) return exactInRoot
    // Gap / MCQ chip lives on the #q-N node itself.
    if (root.matches(`[data-q-chip][data-q-n="${n}"]`)) return root
    const tagged = root.querySelector<HTMLElement>('[data-q-chip]')
    if (tagged) return tagged
    const circle = root.querySelector<HTMLElement>('.rounded-full')
    if (circle) return circle
  }
  return document.querySelector<HTMLElement>(`[data-q-chip][data-q-n="${n}"]`)
}

export function flashQuestionAnchor(displayNumber: number): void {
  const root = resolveRoot(questionAnchorId(displayNumber))
  const chip = resolveChip(root, displayNumber)
  if (!chip) return
  chip.classList.remove(FLASH_CLASS)
  void chip.offsetWidth
  chip.classList.add(FLASH_CLASS)
  window.setTimeout(() => chip.classList.remove(FLASH_CLASS), FLASH_MS)
}

/** Scroll the question into view, then pulse its number chip. */
export function scrollAndFlashQuestion(
  displayNumber: number,
  attempt = 0,
): void {
  const root = resolveRoot(questionAnchorId(displayNumber))
  if (!root) {
    if (attempt < 16) {
      window.setTimeout(
        () => scrollAndFlashQuestion(displayNumber, attempt + 1),
        50,
      )
    }
    return
  }
  root.scrollIntoView({ behavior: 'smooth', block: 'center' })
  window.setTimeout(() => flashQuestionAnchor(displayNumber), 280)
}
