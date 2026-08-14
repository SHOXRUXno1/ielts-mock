import type { CellSegment } from '../../data/compound'
import type { QuestionDraft } from '../question-editor'
import { GapChip } from './gap-chip'

export type GapEditApi = {
  getDraft: (gapId: string) => QuestionDraft
  onSaveGap: (draft: QuestionDraft) => Promise<void>
  maxWords: number
  /** Map gap_id → display order (1-based) */
  gapOrder: Map<string, number>
}

/** Read-only visual render of segments (text + gap chips). */
export function SegmentsDisplay({
  segments,
  gapEdit,
  onDeleteGap,
}: {
  segments: CellSegment[]
  gapEdit?: GapEditApi
  onDeleteGap?: (gapId: string) => void
}) {
  if (segments.length === 0) {
    return <span className='text-muted-foreground'>&nbsp;</span>
  }

  return (
    <span className='whitespace-pre-wrap text-sm leading-relaxed text-foreground'>
      {segments.map((seg, i) => {
        if (seg.type === 'text') {
          if (!seg.value) return null
          return <span key={i}>{seg.value}</span>
        }
        if (!gapEdit) {
          return (
            <span
              key={i}
              className='mx-0.5 inline-block rounded bg-sky-100 px-1.5 text-[11px] font-bold text-sky-800'
            >
              ___
            </span>
          )
        }
        const order = gapEdit.gapOrder.get(seg.gap_id) ?? 0
        return (
          <GapChip
            key={i}
            gapId={seg.gap_id}
            order={order || 1}
            draft={gapEdit.getDraft(seg.gap_id)}
            maxWords={gapEdit.maxWords}
            onSave={gapEdit.onSaveGap}
            onDelete={
              onDeleteGap ? () => onDeleteGap(seg.gap_id) : undefined
            }
            className='mx-0.5'
          />
        )
      })}
    </span>
  )
}

/**
 * Focus-mode editor: text segments as inputs, gaps as chips.
 * No raw {gapN} syntax shown.
 */
export function SegmentsInlineEditor({
  segments,
  onChange,
  gapEdit,
  onAddGap,
  onDeleteGap,
  autoFocus,
}: {
  segments: CellSegment[]
  onChange: (next: CellSegment[]) => void
  gapEdit?: GapEditApi
  onAddGap: () => void
  onDeleteGap: (gapId: string) => void
  autoFocus?: boolean
}) {
  const updateText = (index: number, value: string) => {
    onChange(
      segments.map((s, i) =>
        i === index && s.type === 'text' ? { type: 'text', value } : s,
      ),
    )
  }

  // Ensure we always have at least one text segment to type into
  const editable =
    segments.length === 0
      ? ([{ type: 'text' as const, value: '' }] as CellSegment[])
      : segments

  return (
    <div className='space-y-2'>
      <div className='flex min-h-[2.5rem] flex-wrap items-center gap-0.5 rounded-md border border-sky-200 bg-card px-2 py-1.5'>
        {editable.map((seg, i) => {
          if (seg.type === 'text') {
            return (
              <input
                key={i}
                type='text'
                value={seg.value}
                autoFocus={autoFocus && i === 0}
                onChange={(e) => updateText(i, e.target.value)}
                onClick={(e) => e.stopPropagation()}
                placeholder={editable.length === 1 ? 'Type cell text…' : ''}
                className='min-w-[2rem] flex-1 border-0 bg-transparent px-0.5 text-sm outline-none placeholder:text-muted-foreground'
                style={{ width: `${Math.max(2, seg.value.length + 1)}ch` }}
              />
            )
          }
          if (!gapEdit) return null
          const order = gapEdit.gapOrder.get(seg.gap_id) ?? 0
          return (
            <GapChip
              key={i}
              gapId={seg.gap_id}
              order={order || 1}
              draft={gapEdit.getDraft(seg.gap_id)}
              maxWords={gapEdit.maxWords}
              onSave={gapEdit.onSaveGap}
              onDelete={() => onDeleteGap(seg.gap_id)}
              className='mx-0.5'
            />
          )
        })}
      </div>
      <button
        type='button'
        onClick={(e) => {
          e.stopPropagation()
          onAddGap()
        }}
        className='text-[11px] font-medium text-sky-700 hover:text-sky-900'
      >
        + Add Gap
      </button>
    </div>
  )
}
