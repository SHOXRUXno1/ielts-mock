import { useState } from 'react'
import { Loader2, X } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import type { QuestionDraft } from '../question-editor'
import { AnswerVariantsInput } from './answer-variants-input'

type Props = {
  gapId: string
  draft: QuestionDraft
  maxWords: number
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (draft: QuestionDraft) => Promise<void>
  children: React.ReactNode
}

function variantsFromDraft(draft: QuestionDraft): string[] {
  const correct = draft.answer_key?.correct
  if (Array.isArray(correct)) return (correct as string[]).filter(Boolean)
  if (typeof correct === 'string' && correct.trim()) return [correct.trim()]
  return []
}

export function GapAnswerPopover({
  gapId,
  draft,
  maxWords,
  open,
  onOpenChange,
  onSave,
  children,
}: Props) {
  const [variants, setVariants] = useState<string[]>(() =>
    variantsFromDraft(draft),
  )
  const [saving, setSaving] = useState(false)

  const handleOpenChange = (next: boolean) => {
    if (next) {
      setVariants(variantsFromDraft(draft))
    }
    onOpenChange(next)
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
      onOpenChange(false)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save gap'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent
        className='w-80 p-0'
        align='start'
        side='bottom'
        onOpenAutoFocus={(e) => e.preventDefault()}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.preventDefault()
            handleOpenChange(false)
          }
          if ((e.metaKey || e.ctrlKey) && e.key === 's') {
            e.preventDefault()
            void handleSave()
          }
        }}
      >
        <div className='flex items-center justify-between border-b px-3 py-2'>
          <p className='text-sm font-semibold text-foreground'>Gap {gapId}</p>
          <button
            type='button'
            className='rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-muted-foreground'
            onClick={() => handleOpenChange(false)}
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
          <p className='text-[11px] text-muted-foreground'>
            Max words: {maxWords} (from group)
          </p>
          <div className='flex justify-end gap-2'>
            <Button
              type='button'
              variant='ghost'
              size='sm'
              onClick={() => onOpenChange(false)}
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
              Save
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

export function hasGapAnswer(draft: QuestionDraft | undefined): boolean {
  if (!draft?.answer_key) return false
  const correct = draft.answer_key.correct
  if (Array.isArray(correct)) return correct.length > 0
  if (typeof correct === 'string') return correct.trim().length > 0
  return false
}
