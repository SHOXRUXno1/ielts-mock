import { memo, useEffect, useRef, useState } from 'react'
import type { ConversationTurn } from '@/lib/api/speaking-examiner'
import { cn } from '@/lib/utils'
import {
  isCueCardTurn,
  liveTurnLabel,
  previewLiveTurnText,
  shouldTruncateLiveTurn,
} from '../lib/format-live-turn'
import { transcriptHistorySignature } from '../lib/transcript-history'

type Props = {
  history: ConversationTurn[]
  className?: string
  variant?: 'default' | 'overlay'
  autoScroll?: boolean
  scrollContainer?: 'self' | 'parent'
}

type TurnBubbleProps = {
  turn: ConversationTurn
  isOverlay: boolean
  defaultCollapsed?: boolean
}

function TranscriptTurnBubble({
  turn,
  isOverlay,
  defaultCollapsed = false,
}: TurnBubbleProps) {
  const truncatable = isOverlay && shouldTruncateLiveTurn(turn.text)
  const [expanded, setExpanded] = useState(
    !defaultCollapsed && !truncatable,
  )

  const displayText =
    isOverlay && truncatable && !expanded
      ? previewLiveTurnText(turn.text)
      : turn.text

  return (
    <div
      className={cn(
        'flex shrink-0',
        turn.role === 'examiner' ? 'justify-start' : 'justify-end',
      )}
    >
      <div
        className={cn(
          'rounded-lg px-2 py-1.5',
          isOverlay ? 'max-w-full text-xs' : 'max-w-[80%] px-3 py-2 text-sm',
          turn.role === 'examiner'
            ? isOverlay
              ? 'bg-blue-500/30 text-blue-50'
              : 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-blue-100'
            : isOverlay
              ? 'bg-green-500/25 text-green-50'
              : 'bg-green-100 text-green-900 dark:bg-green-900/30 dark:text-green-100',
        )}
      >
        <span
          className={cn(
            'mb-0.5 block font-semibold opacity-70',
            isOverlay ? 'text-[10px]' : 'text-xs',
          )}
        >
          {liveTurnLabel(turn.role, turn.text)}
        </span>
        <span className='whitespace-pre-wrap break-words'>{displayText}</span>
        {truncatable && (
          <button
            type='button'
            className={cn(
              'mt-1 block text-[11px] font-medium underline underline-offset-2',
              isOverlay ? 'text-white/80 hover:text-white' : 'text-primary',
            )}
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? 'Show less' : 'Expand'}
          </button>
        )}
      </div>
    </div>
  )
}

function TranscriptPanelInner({
  history,
  className,
  variant = 'default',
  autoScroll,
  scrollContainer = 'self',
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const isOverlay = variant === 'overlay'
  const scrollOnSelf = scrollContainer === 'self'
  const shouldAutoScroll = autoScroll ?? (isOverlay && scrollOnSelf)

  useEffect(() => {
    if (!shouldAutoScroll) return
    const el = containerRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [history.length, shouldAutoScroll])

  if (history.length === 0) return null

  const visible = isOverlay ? history.slice(-8) : history
  const startIndex = history.length - visible.length

  return (
    <div
      ref={scrollOnSelf ? containerRef : undefined}
      className={cn(
        'flex min-h-0 flex-col gap-2',
        scrollOnSelf && 'flex-1 overflow-y-auto scroll-smooth',
        !isOverlay && 'rounded-lg border bg-muted/20 p-3',
        isOverlay && 'gap-1.5',
        className,
      )}
    >
      {visible.map((turn, i) => {
        const turnIndex = startIndex + i
        const turnKey = `${turn.role}-${turnIndex}`
        return (
          <TranscriptTurnBubble
            key={turnKey}
            turn={turn}
            isOverlay={isOverlay}
            defaultCollapsed={isOverlay && isCueCardTurn(turn.text)}
          />
        )
      })}
    </div>
  )
}

export const TranscriptPanel = memo(
  TranscriptPanelInner,
  (prev, next) =>
    transcriptHistorySignature(prev.history) ===
      transcriptHistorySignature(next.history) &&
    prev.variant === next.variant &&
    prev.autoScroll === next.autoScroll &&
    prev.scrollContainer === next.scrollContainer &&
    prev.className === next.className,
)

TranscriptPanel.displayName = 'TranscriptPanel'
