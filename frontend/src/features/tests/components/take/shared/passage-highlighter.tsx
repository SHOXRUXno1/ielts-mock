import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { createPortal } from 'react-dom'
import { Copy, Eraser, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export type HighlightColor = 'yellow' | 'green' | 'blue' | 'pink'

type PassageHighlight = {
  id: string
  text: string
  startOffset: number
  endOffset: number
  color: HighlightColor
}

type ToolbarState = {
  x: number
  y: number
  /** When set, toolbar is editing an existing highlight */
  highlightId?: string
  /** Pending selection range offsets (for new highlight) */
  startOffset?: number
  endOffset?: number
  text?: string
}

const COLORS: { id: HighlightColor; className: string; label: string }[] = [
  { id: 'yellow', className: 'bg-yellow-300', label: 'Yellow' },
  { id: 'green', className: 'bg-green-300', label: 'Green' },
  { id: 'blue', className: 'bg-blue-300', label: 'Blue' },
  { id: 'pink', className: 'bg-pink-300', label: 'Pink' },
]

const supportsHighlightAPI =
  typeof CSS !== 'undefined' &&
  'highlights' in CSS &&
  typeof globalThis.Highlight === 'function'

function storageKey(
  attemptId: string | null | undefined,
  sectionId: string,
  suffix?: string,
) {
  const base = `highlight:${attemptId ?? 'preview'}:${sectionId}`
  return suffix ? `${base}:${suffix}` : base
}

function cssHighlightName(color: HighlightColor, namespace: string) {
  return `${namespace}-${color}`
}

function loadHighlights(key: string): PassageHighlight[] {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const parsed = JSON.parse(raw) as PassageHighlight[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveHighlights(key: string, items: PassageHighlight[]) {
  try {
    localStorage.setItem(key, JSON.stringify(items))
  } catch {
    // quota / private mode
  }
}

function getTextOffset(root: Node, target: Node, offset: number): number {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let total = 0
  let node: Node | null
  while ((node = walker.nextNode())) {
    if (node === target) return total + offset
    total += node.textContent?.length ?? 0
  }
  return total
}

function rangeFromOffsets(
  root: Node,
  start: number,
  end: number,
): Range | null {
  if (end <= start) return null
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let total = 0
  let startNode: Text | null = null
  let startOff = 0
  let endNode: Text | null = null
  let endOff = 0
  let node: Node | null

  while ((node = walker.nextNode())) {
    const len = node.textContent?.length ?? 0
    if (!startNode && total + len >= start) {
      startNode = node as Text
      startOff = start - total
    }
    if (total + len >= end) {
      endNode = node as Text
      endOff = end - total
      break
    }
    total += len
  }

  if (!startNode || !endNode) return null
  try {
    const range = document.createRange()
    range.setStart(startNode, Math.min(startOff, startNode.length))
    range.setEnd(endNode, Math.min(endOff, endNode.length))
    return range
  } catch {
    return null
  }
}

function findHighlightAtOffset(
  highlights: PassageHighlight[],
  offset: number,
): PassageHighlight | undefined {
  return highlights.find((h) => offset >= h.startOffset && offset < h.endOffset)
}

function unwrapMarks(root: HTMLElement) {
  root.querySelectorAll('mark[data-passage-highlight]').forEach((mark) => {
    const parent = mark.parentNode
    if (!parent) return
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark)
    parent.removeChild(mark)
    parent.normalize()
  })
}

function applyMarkFallback(root: HTMLElement, highlights: PassageHighlight[]) {
  unwrapMarks(root)
  // Apply from end so earlier offsets stay valid
  const sorted = [...highlights].sort((a, b) => b.startOffset - a.startOffset)
  for (const h of sorted) {
    const range = rangeFromOffsets(root, h.startOffset, h.endOffset)
    if (!range || range.collapsed) continue
    try {
      const mark = document.createElement('mark')
      mark.dataset.passageHighlight = h.id
      mark.dataset.color = h.color
      mark.className = cn(
        'rounded-sm px-0.5',
        h.color === 'yellow' && 'bg-yellow-200/80',
        h.color === 'green' && 'bg-green-200/80',
        h.color === 'blue' && 'bg-blue-200/80',
        h.color === 'pink' && 'bg-pink-200/80',
      )
      range.surroundContents(mark)
    } catch {
      // Cross-element ranges may fail; skip gracefully
    }
  }
}

function clearCssHighlights(namespace: string) {
  if (!supportsHighlightAPI) return
  for (const c of COLORS) {
    CSS.highlights.delete(cssHighlightName(c.id, namespace))
  }
}

function applyCssHighlights(
  root: HTMLElement,
  highlights: PassageHighlight[],
  namespace: string,
) {
  clearCssHighlights(namespace)
  const byColor = new Map<HighlightColor, Range[]>()
  for (const h of highlights) {
    const range = rangeFromOffsets(root, h.startOffset, h.endOffset)
    if (!range || range.collapsed) continue
    const list = byColor.get(h.color) ?? []
    list.push(range)
    byColor.set(h.color, list)
  }
  for (const [color, ranges] of byColor) {
    CSS.highlights.set(
      cssHighlightName(color, namespace),
      new Highlight(...ranges),
    )
  }
}

type Props = {
  attemptId?: string | null
  sectionId: string
  /** Separate localStorage / CSS highlight namespace (e.g. "questions") */
  storageKeySuffix?: string
  children: ReactNode
  className?: string
}

export function PassageHighlighter({
  attemptId,
  sectionId,
  storageKeySuffix,
  children,
  className,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const toolbarRef = useRef<HTMLDivElement>(null)
  const key = storageKey(attemptId, sectionId, storageKeySuffix)
  const highlightNamespace = storageKeySuffix || 'passage'
  const [highlights, setHighlights] = useState<PassageHighlight[]>(() =>
    loadHighlights(key),
  )
  const [toolbar, setToolbar] = useState<ToolbarState | null>(null)

  // Reload when section / attempt changes
  useEffect(() => {
    setHighlights(loadHighlights(key))
    setToolbar(null)
  }, [key])

  const persist = useCallback(
    (next: PassageHighlight[]) => {
      setHighlights(next)
      saveHighlights(key, next)
    },
    [key],
  )

  // Render highlights after DOM updates
  useLayoutEffect(() => {
    const root = containerRef.current
    if (!root) return

    if (supportsHighlightAPI) {
      applyCssHighlights(root, highlights, highlightNamespace)
      return () => clearCssHighlights(highlightNamespace)
    }

    applyMarkFallback(root, highlights)
    return () => unwrapMarks(root)
  }, [highlights, children, highlightNamespace])

  // Clamp toolbar position to stay within viewport
  useLayoutEffect(() => {
    const el = toolbarRef.current
    if (!el || !toolbar) return
    const rect = el.getBoundingClientRect()
    const pad = 8
    const halfW = rect.width / 2

    let left = toolbar.x - halfW
    if (left < pad) left = pad
    else if (left + rect.width > window.innerWidth - pad) left = window.innerWidth - pad - rect.width

    el.style.left = `${left}px`
    el.style.top = `${Math.max(pad, toolbar.y - 8 - rect.height)}px`
  }, [toolbar, highlights.length])

  const closeToolbar = useCallback(() => {
    setToolbar(null)
  }, [])

  const handlePointerUp = useCallback(() => {
    const root = containerRef.current
    if (!root) return

    // Defer so selection is finalized
    requestAnimationFrame(() => {
      const sel = window.getSelection()
      if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
        return
      }

      const range = sel.getRangeAt(0)
      if (!root.contains(range.commonAncestorContainer)) return

      const text = sel.toString().trim()
      if (!text) return

      const startOffset = getTextOffset(
        root,
        range.startContainer,
        range.startOffset,
      )
      const endOffset = getTextOffset(root, range.endContainer, range.endOffset)
      if (endOffset <= startOffset) return

      const rect = range.getBoundingClientRect()
      setToolbar({
        x: rect.left + rect.width / 2,
        y: rect.top,
        startOffset,
        endOffset,
        text: sel.toString(),
      })
    })
  }, [])

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      const root = containerRef.current
      if (!root) return

      // If there's an active selection, let pointerup handle the toolbar
      const sel = window.getSelection()
      if (sel && !sel.isCollapsed && sel.toString().trim()) return

      // Click on existing highlight → show remove toolbar
      const range = document.caretRangeFromPoint?.(e.clientX, e.clientY)
      if (!range || !root.contains(range.startContainer)) {
        // Also check mark fallback
        const mark = (e.target as HTMLElement).closest?.(
          'mark[data-passage-highlight]',
        )
        if (mark instanceof HTMLElement && mark.dataset.passageHighlight) {
          const id = mark.dataset.passageHighlight
          const h = highlights.find((item) => item.id === id)
          if (h) {
            const rect = mark.getBoundingClientRect()
            setToolbar({
              x: rect.left + rect.width / 2,
              y: rect.top,
              highlightId: h.id,
            })
            return
          }
        }
        return
      }

      const offset = getTextOffset(root, range.startContainer, range.startOffset)
      const hit = findHighlightAtOffset(highlights, offset)
      if (!hit) return

      const hitRange = rangeFromOffsets(root, hit.startOffset, hit.endOffset)
      const rect = hitRange?.getBoundingClientRect()
      setToolbar({
        x: rect ? rect.left + rect.width / 2 : e.clientX,
        y: rect ? rect.top : e.clientY,
        highlightId: hit.id,
      })
    },
    [highlights],
  )

  // Close toolbar on outside click / Escape
  useEffect(() => {
    if (!toolbar) return

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeToolbar()
    }
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node
      if (toolbarRef.current?.contains(t)) return
      if (containerRef.current?.contains(t)) {
        // Allow selection interactions inside passage; close only if not selecting
        const sel = window.getSelection()
        if (sel && !sel.isCollapsed) return
      }
      closeToolbar()
    }

    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onDown)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onDown)
    }
  }, [toolbar, closeToolbar])

  const applyColor = (color: HighlightColor) => {
    if (!toolbar) return

    if (toolbar.highlightId) {
      // Recolor existing
      persist(
        highlights.map((h) =>
          h.id === toolbar.highlightId ? { ...h, color } : h,
        ),
      )
      closeToolbar()
      window.getSelection()?.removeAllRanges()
      return
    }

    if (
      toolbar.startOffset == null ||
      toolbar.endOffset == null ||
      !toolbar.text
    ) {
      return
    }

    const next: PassageHighlight = {
      id: crypto.randomUUID(),
      text: toolbar.text,
      startOffset: toolbar.startOffset,
      endOffset: toolbar.endOffset,
      color,
    }

    // Drop overlapping highlights
    const filtered = highlights.filter(
      (h) => h.endOffset <= next.startOffset || h.startOffset >= next.endOffset,
    )
    persist([...filtered, next])
    closeToolbar()
    window.getSelection()?.removeAllRanges()
  }

  const removeHighlight = () => {
    if (!toolbar?.highlightId) {
      window.getSelection()?.removeAllRanges()
      closeToolbar()
      return
    }
    persist(highlights.filter((h) => h.id !== toolbar.highlightId))
    closeToolbar()
  }

  const clearAll = () => {
    persist([])
    closeToolbar()
  }

  const copySelection = async () => {
    const text =
      toolbar?.text ??
      (toolbar?.highlightId
        ? highlights.find((h) => h.id === toolbar.highlightId)?.text
        : undefined)
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      // ignore
    }
  }

  return (
    <>
      <div ref={containerRef} className={cn('passage-highlighter select-text', className)} onMouseUp={handlePointerUp} onTouchEnd={handlePointerUp} onClick={handleClick}>
        {children}
      </div>

      {toolbar &&
        createPortal(
          <div
            ref={toolbarRef}
            role='toolbar'
            aria-label='Text highlight'
            className='fixed z-[100] flex items-center gap-1.5 rounded-full border border-border bg-card px-2 py-1.5 shadow-lg'
            style={{ left: toolbar.x, top: toolbar.y }}
            onMouseDown={(e) => e.preventDefault()}
          >
            {COLORS.map((c) => (
              <button
                key={c.id}
                type='button'
                title={c.label}
                aria-label={`Highlight ${c.label}`}
                className={cn(
                  'size-5 rounded-full border border-black/10 transition-transform hover:scale-110',
                  c.className,
                )}
                onClick={() => applyColor(c.id)}
              />
            ))}
            <span className='mx-0.5 h-4 w-px bg-border' />
            <button
              type='button'
              title='Copy'
              aria-label='Copy text'
              className='flex size-6 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground'
              onClick={() => void copySelection()}
            >
              <Copy className='size-3.5' />
            </button>
            {highlights.length > 0 && (
              <button
                type='button'
                title='Clear all highlights'
                aria-label='Clear all highlights'
                className='flex size-6 items-center justify-center rounded-full text-muted-foreground hover:bg-destructive/10 hover:text-destructive'
                onClick={clearAll}
              >
                <Eraser className='size-3.5' />
              </button>
            )}
            <button
              type='button'
              title={toolbar.highlightId ? 'Remove highlight' : 'Close'}
              aria-label={toolbar.highlightId ? 'Remove highlight' : 'Close'}
              className='flex size-6 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground'
              onClick={removeHighlight}
            >
              <X className='size-3.5' />
            </button>
          </div>,
          document.body,
        )}
    </>
  )
}
