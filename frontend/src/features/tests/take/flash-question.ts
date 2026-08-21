import { questionAnchorId } from './question-anchor'

const FLASH_CLASS = 'question-anchor-flash'
const FLASH_MS = 1500
const PANE_PAD = 16

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

/**
 * Align a short group to the top of the pane so "Questions 37–40" stays on
 * screen. A long group keeps the target question near the top instead of
 * centering it (center pushes the group title off).
 */
export function groupAwareScrollTop(args: {
  paneScrollTop: number
  paneTop: number
  paneHeight: number
  questionTop: number
  groupTop?: number
  groupHeight?: number
  padding?: number
}): number {
  const pad = args.padding ?? PANE_PAD
  const groupTop = args.groupTop
  const groupHeight = args.groupHeight
  if (
    groupTop != null &&
    groupHeight != null &&
    groupHeight <= args.paneHeight - pad
  ) {
    return Math.max(0, args.paneScrollTop + (groupTop - args.paneTop) - pad)
  }
  return Math.max(0, args.paneScrollTop + (args.questionTop - args.paneTop) - pad)
}

function findScrollParent(el: HTMLElement): HTMLElement | null {
  let p = el.parentElement
  while (p && p !== document.body) {
    const oy = window.getComputedStyle(p).overflowY
    if (
      (oy === 'auto' || oy === 'scroll' || oy === 'overlay') &&
      p.scrollHeight > p.clientHeight + 1
    ) {
      return p
    }
    p = p.parentElement
  }
  return null
}

function scrollQuestionIntoExamPane(root: HTMLElement): void {
  const group = root.closest<HTMLElement>('[data-question-group]')
  const pane =
    root.closest<HTMLElement>('[data-exam-scroll-pane]') ??
    findScrollParent(root)
  if (!pane) return

  const paneRect = pane.getBoundingClientRect()
  const groupRect = group?.getBoundingClientRect()
  const top = groupAwareScrollTop({
    paneScrollTop: pane.scrollTop,
    paneTop: paneRect.top,
    paneHeight: pane.clientHeight,
    questionTop: root.getBoundingClientRect().top,
    groupTop: groupRect?.top,
    groupHeight: groupRect?.height,
  })
  pane.scrollTo({ top, behavior: 'smooth' })
}

/** Scroll the question into the exam pane, then pulse its number chip. */
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
  scrollQuestionIntoExamPane(root)
  window.setTimeout(() => flashQuestionAnchor(displayNumber), 280)
}
