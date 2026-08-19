import { Check, CircleMinus, CircleX } from 'lucide-react'
import type { AnswerRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { type AnswerOutcome, answerOutcome } from '../lib/answers'
import {
  correctChoiceKeys,
  isChoiceReview,
  matchingPairs,
  questionStem,
  reviewFallback,
  reviewOptions,
  studentChoiceKeys,
  type ReviewOption,
} from '../lib/review'

type AnswerReviewCardProps = {
  answer: AnswerRead
  number: string
}

export function AnswerReviewCard({ answer, number }: AnswerReviewCardProps) {
  const outcome = answerOutcome(answer)
  const type = answer.question?.question_type
  const content = answer.question?.content
  const options = reviewOptions(content, type)
  const stem = questionStem(content, type)
  const pairs = matchingPairs(content, answer.response, answer.question?.answer_key)
  const showChoices = isChoiceReview(type, options)
  const fallback = reviewFallback(answer)
  const hasBlank = Boolean(stem && /_{2,}/.test(stem))
  const showFallback =
    !showChoices && !pairs && !hasBlank && !(outcome === 'correct' && stem)

  return (
    <article
      className={cn(
        'rounded-xl border border-l-2 bg-card p-4',
        outcomeRowClass(outcome),
      )}
    >
      <header className='mb-3 flex items-start justify-between gap-3'>
        <div className='min-w-0'>
          <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
            Question {number}
          </p>
          {stem ? (
            <StemText
              stem={stem}
              outcome={outcome}
              student={showChoices || pairs ? null : fallback.student}
              correct={showChoices || pairs ? null : fallback.correct}
            />
          ) : (
            <p className='mt-1 text-sm text-muted-foreground'>No question text</p>
          )}
        </div>
        <OutcomeIcon outcome={outcome} />
      </header>

      {showChoices && (
        <OptionList
          options={options}
          studentKeys={studentChoiceKeys(answer.response, options)}
          correctKeys={correctChoiceKeys(answer.question?.answer_key, options)}
        />
      )}

      {pairs && (
        <div className='space-y-2'>
          {pairs.map((pair) => {
            const right = pair.student != null && pair.student === pair.correct
            const skipped = pair.student == null || pair.student === ''
            return (
              <div
                key={pair.item}
                className='flex flex-wrap items-center gap-x-2 gap-y-1 text-sm'
              >
                <span className='min-w-24 font-medium text-foreground'>{pair.item}</span>
                <span className='text-muted-foreground'>→</span>
                {skipped ? (
                  <span className='text-muted-foreground'>—</span>
                ) : (
                  <span
                    className={cn(
                      'tabular-nums',
                      right
                        ? 'font-medium text-success-foreground'
                        : 'text-muted-foreground line-through',
                    )}
                  >
                    {pair.student}
                  </span>
                )}
                {!right && pair.correct && (
                  <span className='font-medium text-success-foreground'>
                    {pair.correct}
                  </span>
                )}
              </div>
            )
          })}
        </div>
      )}

      {showFallback && (
        <FallbackAnswers outcome={outcome} student={fallback.student} correct={fallback.correct} />
      )}
    </article>
  )
}

function StemText({
  stem,
  outcome,
  student,
  correct,
}: {
  stem: string
  outcome: AnswerOutcome
  student: string | null
  correct: string | null
}) {
  if (student == null || !/_{2,}/.test(stem)) {
    return <p className='mt-1 text-[15px] leading-relaxed text-foreground'>{stem}</p>
  }

  const parts = stem.split(/_{2,}/)
  const shown = student === '(no answer)' ? '—' : student
  return (
    <p className='mt-1 text-[15px] leading-relaxed text-foreground'>
      {parts[0]}
      <span
        className={cn(
          'mx-1 inline-flex rounded-md px-1.5 py-0.5 text-sm',
          outcome === 'correct' && 'bg-success/50 font-medium text-success-foreground',
          outcome === 'incorrect' && 'bg-destructive/10 text-muted-foreground line-through',
          outcome === 'skipped' && 'bg-muted text-muted-foreground',
        )}
      >
        {shown}
      </span>
      {outcome === 'incorrect' && correct && (
        <span className='me-1 font-medium text-success-foreground'>{correct}</span>
      )}
      {parts.slice(1).join('')}
    </p>
  )
}

function OptionList({
  options,
  studentKeys,
  correctKeys,
}: {
  options: ReviewOption[]
  studentKeys: string[]
  correctKeys: string[]
}) {
  return (
    <ul className='space-y-1.5'>
      {options.map((option) => {
        const picked = studentKeys.includes(option.letter)
        const right = correctKeys.includes(option.letter)
        return (
          <li
            key={option.letter}
            className={cn(
              'flex items-start justify-between gap-3 rounded-lg px-3 py-2 text-sm',
              picked && right && 'bg-success/40',
              picked && !right && 'bg-destructive/5',
              !picked && right && 'bg-success/25',
            )}
          >
            <p className='min-w-0 leading-relaxed'>
              <span className='me-1.5 font-semibold tabular-nums'>{option.letter}.</span>
              {option.label !== option.letter && option.label}
            </p>
            <div className='flex shrink-0 flex-col items-end gap-0.5 text-[10px] font-medium tracking-wide uppercase'>
              {picked && (
                <span className={right ? 'text-success-foreground' : 'text-destructive'}>
                  Your answer
                </span>
              )}
              {right && (
                <span className='text-success-foreground'>Correct</span>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function FallbackAnswers({
  outcome,
  student,
  correct,
}: {
  outcome: AnswerOutcome
  student: string
  correct: string
}) {
  if (outcome === 'correct') return null
  return (
    <div className='mt-1 space-y-1 text-sm'>
      <p>
        <span className='text-muted-foreground'>You: </span>
        {outcome === 'skipped' ? (
          <span className='text-muted-foreground'>—</span>
        ) : (
          <span className='text-muted-foreground line-through'>
            {student === '(no answer)' ? '—' : student}
          </span>
        )}
      </p>
      <p>
        <span className='text-muted-foreground'>Correct: </span>
        <span className='font-medium text-success-foreground'>{correct || '—'}</span>
      </p>
    </div>
  )
}

function OutcomeIcon({ outcome }: { outcome: AnswerOutcome }) {
  if (outcome === 'correct') {
    return (
      <span className='inline-flex items-center'>
        <Check className='size-4 text-success-foreground' />
        <span className='sr-only'>Correct</span>
      </span>
    )
  }
  if (outcome === 'skipped') {
    return (
      <span className='inline-flex items-center'>
        <CircleMinus className='size-4 text-warning-foreground' />
        <span className='sr-only'>Skipped</span>
      </span>
    )
  }
  return (
    <span className='inline-flex items-center'>
      <CircleX className='size-4 text-destructive' />
      <span className='sr-only'>Incorrect</span>
    </span>
  )
}

function outcomeRowClass(outcome: AnswerOutcome): string {
  if (outcome === 'incorrect') return 'border-l-destructive'
  if (outcome === 'skipped') return 'border-l-warning-foreground/60'
  return 'border-l-success-foreground/70'
}
