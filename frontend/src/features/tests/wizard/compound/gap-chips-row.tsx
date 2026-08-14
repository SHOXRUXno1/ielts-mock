import { useState } from 'react'
import { GapAnswerPopover, hasGapAnswer } from './gap-answer-popover'
import type { GapEditHandlers } from './table-structure-editor'

type Props = {
  gapIds: string[]
  gapEdit: GapEditHandlers
}

/** Shared chip row for setting answers on compound gaps. */
export function GapChipsRow({ gapIds, gapEdit }: Props) {
  const [openGapId, setOpenGapId] = useState<string | null>(null)

  if (gapIds.length === 0) return null

  return (
    <div className='flex flex-wrap gap-2'>
      {gapIds.map((gapId) => (
        <GapAnswerPopover
          key={gapId}
          gapId={gapId}
          draft={gapEdit.getDraft(gapId)}
          maxWords={gapEdit.maxWords}
          open={openGapId === gapId}
          onOpenChange={(o) => setOpenGapId(o ? gapId : null)}
          onSave={gapEdit.onSaveGap}
        >
          <button
            type='button'
            className='rounded-md bg-sky-50 px-3 py-1.5 text-xs font-bold text-sky-800 ring-1 ring-sky-200'
          >
            GAP {gapId}
            {!hasGapAnswer(gapEdit.getDraft(gapId)) && (
              <span className='ml-2 font-medium text-warning-foreground'>⚠</span>
            )}
          </button>
        </GapAnswerPopover>
      ))}
    </div>
  )
}
