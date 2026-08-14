import { Label } from '@/components/ui/label'
import type { QuestionDraft } from '../question-editor'
import { AnswerVariantsInput } from './answer-variants-input'

type Props = {
  draft: QuestionDraft
  gapId: string
  questionNumber: number
  maxWords: number
  onChange: (next: QuestionDraft) => void
}

export function CompoundGapQuestionEditor({
  draft,
  gapId,
  questionNumber,
  maxWords,
  onChange,
}: Props) {
  const correct = draft.answer_key?.correct
  const variants: string[] = Array.isArray(correct)
    ? (correct as string[]).filter(Boolean)
    : typeof correct === 'string' && correct.trim()
      ? [correct.trim()]
      : []

  const handleChange = (next: string[]) => {
    onChange({
      ...draft,
      content: { ...draft.content, gap_id: gapId },
      answer_key: {
        correct: next,
        case_sensitive: false,
        max_words: maxWords,
      },
    })
  }

  return (
    <div className='space-y-3 rounded-md border border-border bg-card p-3'>
      <div className='flex items-center justify-between'>
        <p className='text-sm font-medium text-foreground'>
          Question {questionNumber}{' '}
          <span className='font-normal text-muted-foreground'>(gap_id: {gapId})</span>
        </p>
        <span className='text-xs text-muted-foreground'>Max words: {maxWords}</span>
      </div>

      <div className='space-y-1.5'>
        <Label className='text-xs text-muted-foreground'>Accepted answers</Label>
        <AnswerVariantsInput
          value={variants}
          onChange={handleChange}
          placeholder='Type answer, press Enter'
        />
        <p className='text-[11px] text-muted-foreground'>
          Press Enter to add a variant. Any match counts as correct.
        </p>
      </div>
    </div>
  )
}
