import { ChevronDown, ChevronUp, MessageSquare } from 'lucide-react'
import { memo, useRef, useState } from 'react'
import type { ConversationTurn } from '@/lib/api/speaking-examiner'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useTranscriptAutoscroll } from '../hooks/use-transcript-autoscroll'
import { transcriptHistorySignature } from '../lib/transcript-history'
import { TranscriptPanel } from './transcript-panel'

type Props = {
  history: ConversationTurn[]
  className?: string
}

function LiveTranscriptPanelInner({ history, className }: Props) {
  const [open, setOpen] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)
  const { onScroll } = useTranscriptAutoscroll(scrollRef, history.length, open)

  if (history.length === 0) return null

  return (
    <div
      className={cn(
        'pointer-events-auto absolute left-3 z-20 flex min-h-0 max-h-[42%] w-[min(280px,38%)] flex-col',
        'rounded-lg border border-white/10 bg-black/55 backdrop-blur-md',
        className,
      )}
    >
      <div className='flex shrink-0 items-center justify-between gap-2 border-b border-white/10 px-2 py-1.5'>
        <span className='flex items-center gap-1.5 text-[11px] font-medium text-white/90'>
          <MessageSquare className='size-3.5' />
          Transcript
        </span>
        <Button
          type='button'
          variant='ghost'
          size='icon'
          className='size-7 text-white/80 hover:bg-white/10 hover:text-white'
          aria-label={open ? 'Collapse transcript' : 'Expand transcript'}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? (
            <ChevronDown className='size-4' />
          ) : (
            <ChevronUp className='size-4' />
          )}
        </Button>
      </div>
      {open && (
        <div
          ref={scrollRef}
          onScroll={onScroll}
          className='min-h-0 flex-1 overflow-y-auto overscroll-contain scroll-smooth p-2 pt-1'
        >
          <TranscriptPanel
            history={history}
            variant='overlay'
            scrollContainer='parent'
          />
        </div>
      )}
    </div>
  )
}

export const LiveTranscriptPanel = memo(
  LiveTranscriptPanelInner,
  (prev, next) =>
    transcriptHistorySignature(prev.history) ===
      transcriptHistorySignature(next.history) && prev.className === next.className,
)

LiveTranscriptPanel.displayName = 'LiveTranscriptPanel'
