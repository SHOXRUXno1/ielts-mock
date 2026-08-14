import { useState } from 'react'
import { toast } from 'sonner'
import { Loader2, Pencil, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import type { QuestionDraft } from '../question-editor'
import { hasGapAnswer } from './gap-answer-popover'
import { AnswerVariantsInput } from './answer-variants-input'

type Props = {
  gapId: string
  /** Display number (1-based question order) */
  order: number
  draft: QuestionDraft
  maxWords: number
  onSave: (draft: QuestionDraft) => Promise<void>
  onDelete?: () => void
  className?: string
}

/** Inline visual gap chip — hides {gapN} syntax from the teacher. */
export function GapChip({
  gapId,
  order,
  draft,
  maxWords,
  onSave,
  onDelete,
  className,
}: Props) {
  const [open, setOpen] = useState(false)
  const [variants, setVariants] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const answered = hasGapAnswer(draft)

  const syncFromDraft = () => {
    const correct = draft.answer_key?.correct
    setVariants(
      Array.isArray(correct)
        ? (correct as string[]).filter(Boolean)
        : typeof correct === 'string' && correct.trim()
          ? [correct.trim()]
          : [],
    )
  }

  const handleOpenChange = (next: boolean) => {
    if (next) syncFromDraft()
    setOpen(next)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave({
        ...draft,
        content: { ...draft.content, gap_id: gapId },
        answer_key: {
          correct: variants,
          case_sensitive: false,
          max_words: maxWords,
        },
      })
      setOpen(false)
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to save gap answer'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          type='button'
          aria-label={`Gap ${order} (${gapId})${answered ? '' : ', no answer'}`}
          onClick={(e) => e.stopPropagation()}
          className={cn(
            'group/chip inline-flex h-6 items-center gap-1 rounded-md px-1.5 align-baseline text-[11px] font-bold tabular-nums transition-colors',
            answered
              ? 'bg-sky-100 text-sky-800 ring-1 ring-sky-200 hover:bg-sky-200/80'
              : 'bg-warning/10 text-warning-foreground ring-1 ring-warning/40 hover:bg-warning/20',
            className,
          )}
        >
          <span className='inline-flex size-3.5 items-center justify-center rounded-full bg-sky-600 text-[9px] text-white'>
            {order}
          </span>
          <Pencil className='size-2.5 opacity-0 transition-opacity group-hover/chip:opacity-70' />
        </button>
      </PopoverTrigger>
      <PopoverContent
        className='w-80 p-0'
        align='start'
        onOpenAutoFocus={(e) => e.preventDefault()}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.preventDefault()
            setOpen(false)
          }
          if ((e.metaKey || e.ctrlKey) && e.key === 's') {
            e.preventDefault()
            void handleSave()
          }
        }}
      >
        <div className='flex items-center justify-between border-b px-3 py-2'>
          <p className='text-sm font-semibold text-foreground'>
            Gap #{order}{' '}
            <span className='font-normal text-muted-foreground'>({gapId})</span>
          </p>
          <button
            type='button'
            className='rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-muted-foreground'
            onClick={() => setOpen(false)}
            aria-label='Close'
          >
            <X className='size-3.5' />
          </button>
        </div>
        <div className='space-y-3 p-3'>
          <div className='space-y-1.5'>
            <Label className='text-xs'>Accepted answers</Label>
            <AnswerVariantsInput
              value={variants}
              onChange={setVariants}
              placeholder='Type answer, press Enter'
              autoFocus
            />
            <p className='text-[11px] text-muted-foreground'>
              Press Enter to add a variant. Any match counts as correct.
            </p>
          </div>
          <p className='text-[11px] text-muted-foreground'>Max words: {maxWords}</p>
          <div className='flex items-center justify-between gap-2'>
            {onDelete ? (
              <Button
                type='button'
                variant='ghost'
                size='sm'
                className='text-destructive hover:text-destructive'
                onClick={() => {
                  onDelete()
                  setOpen(false)
                }}
              >
                Delete gap
              </Button>
            ) : (
              <span />
            )}
            <div className='flex gap-2'>
              <Button
                type='button'
                variant='ghost'
                size='sm'
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type='button'
                size='sm'
                disabled={saving}
                onClick={() => void handleSave()}
              >
                {saving && <Loader2 className='mr-1 size-3.5 animate-spin' />}
                Done
              </Button>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
