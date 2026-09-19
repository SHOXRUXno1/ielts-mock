import { useMemo, useState, type ReactNode } from 'react'
import { Check, CircleDashed, CircleMinus, CircleX } from 'lucide-react'
import type { AnswerRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import {
  OBJECTIVE_QUESTION_TOTAL,
  answerMarks,
  answerOutcome,
  buildDisplayNumbers,
  formatCorrectAnswer,
  formatStudentAnswer,
  groupAnswersByPart,
  matchesOutcomeFilter,
  tallyMarks,
  usesOptionLetters,
  type AnswerMarks,
  type AnswerOutcome,
} from '../lib/answers'
import { accuracyByPart } from '../lib/insights'
import { ENTER } from '../lib/motion'
import { type SkillKey, skillMeta } from '../lib/skill'
import { isSectionNotAttempted } from '../lib/status'
import { AnswerMark } from './answer-mark'
import { OutcomeBar } from './outcome-bar'
import { ResultEmptyState } from './result-empty-state'
import { SkillReportHeader } from './skill-report-header'
import { Panel, PanelBody, PanelHeader, PanelTitle, PanelToolbar } from '@/components/report'

type ReviewMode = 'needs_review' | 'all' | 'correct'

type AnswerReviewPanelProps = {
  skill: Extract<SkillKey, 'listening' | 'reading'>
  band: number | null
  raw: number | null
  answers: AnswerRead[]
  attemptStatus?: string
}

const REVIEW_MODES: { value: ReviewMode; label: string }[] = [
  { value: 'needs_review', label: 'Needs review' },
  { value: 'all', label: 'All answers' },
  { value: 'correct', label: 'Correct' },
]

export function AnswerReviewPanel({
  skill,
  band,
  raw,
  answers,
  attemptStatus,
}: AnswerReviewPanelProps) {
  const [reviewMode, setReviewMode] = useState<ReviewMode>('needs_review')
  const meta = skillMeta(skill)
  const Icon = meta.icon

  const filtered = useMemo(
    () =>
      answers.filter(
        (a) => a.is_correct !== null && a.section?.type === skill,
      ),
    [answers, skill],
  )
  const displayNumbers = useMemo(() => buildDisplayNumbers(filtered), [filtered])
  const rows = useMemo(
    () =>
      [...filtered].sort((a, b) => {
        const an = parseInt(displayNumbers.get(a.id)?.match(/\d+/)?.[0] ?? '999')
        const bn = parseInt(displayNumbers.get(b.id)?.match(/\d+/)?.[0] ?? '999')
        return an - bn
      }),
    [filtered, displayNumbers],
  )

  const counts = useMemo(() => tallyMarks(rows), [rows])

  const partAccuracy = useMemo(
    () => accuracyByPart(answers, skill),
    [answers, skill],
  )

  const visible = rows.filter((row) => {
    const outcome = answerOutcome(row)
    if (reviewMode === 'all') return true
    if (reviewMode === 'correct') return outcome === 'correct'
    return !matchesOutcomeFilter(outcome, 'correct')
  })
  const groups = useMemo(
    () => groupAnswersByPart(visible, skill),
    [visible, skill],
  )

  if (isSectionNotAttempted(band, attemptStatus)) {
    return (
      <ResultEmptyState
        icon={Icon}
        title='Not attempted'
        description={`${meta.label} was not attempted during this test.`}
      />
    )
  }

  if (rows.length === 0) {
    return (
      <ResultEmptyState
        icon={Icon}
        title='No scored answers'
        description={`No scored answers for ${meta.label.toLowerCase()}.`}
      />
    )
  }

  return (
    <div className='space-y-4'>
      <SkillReportHeader
        skill={skill}
        band={band}
        variant='feature'
        extra={
          <p className='mt-1 text-sm tabular-nums text-muted-foreground'>
            {raw != null ? `${raw}/${OBJECTIVE_QUESTION_TOTAL} correct` : '—'}
          </p>
        }
      />

      <Panel className={ENTER} padding='md'>
        <PanelHeader>
          <div>
            <p className={cn('text-xs font-semibold tracking-[0.16em] uppercase', meta.accent)}>
              Accuracy overview
            </p>
            <PanelTitle className='mt-1 text-xl'>Where you earned your marks</PanelTitle>
          </div>
          <p className='max-w-sm text-sm leading-6 text-muted-foreground'>
            Compare the parts first, then use the answer review to focus your practice.
          </p>
        </PanelHeader>

        <div className='mt-6 grid gap-5 lg:grid-cols-[minmax(13rem,0.9fr)_minmax(0,1.4fr)]'>
          <div className={cn('rounded-2xl p-5', meta.surface)}>
            <p className='text-xs font-semibold tracking-[0.14em] text-muted-foreground uppercase'>Correct answers</p>
            <div className='mt-2 flex items-end gap-2'>
              <p className={cn('font-manrope text-4xl font-bold tracking-tight tabular-nums', meta.accent)}>
                {raw ?? counts.correct}
              </p>
              <p className='mb-1 text-sm text-muted-foreground'>of {counts.correct + counts.incorrect + counts.skipped}</p>
            </div>
            <p className='mt-2 text-sm text-muted-foreground'>
              {formatAccuracy(counts.correct, counts.correct + counts.incorrect + counts.skipped)} accuracy
            </p>
          </div>
          <div className='rounded-2xl border bg-surface-sunken p-5'>
            <OutcomeBar correct={counts.correct} incorrect={counts.incorrect} skipped={counts.skipped} showLegend />
            <div className='mt-5 grid grid-cols-3 gap-2'>
              <ScoreMetric label='Correct' value={counts.correct} tone='success' />
              <ScoreMetric label='Incorrect' value={counts.incorrect} tone='destructive' />
              <ScoreMetric label='Skipped' value={counts.skipped} tone='muted' />
            </div>
          </div>
        </div>

        {partAccuracy.length > 0 && (
          <div className='mt-7 border-t pt-6'>
            <div className='mb-4'>
              <p className='text-sm font-semibold'>Performance by {skill === 'listening' ? 'part' : 'passage'}</p>
              <p className='mt-1 text-sm text-muted-foreground'>Find the section where a small improvement can make the biggest difference.</p>
            </div>
            <div className='grid gap-3 sm:grid-cols-2 lg:grid-cols-4'>
            {partAccuracy.map((part) => (
              <div key={part.key} className='rounded-xl border bg-card p-4'>
                <div className='flex items-baseline justify-between gap-2'>
                  <p className='text-xs font-semibold text-foreground'>
                    {part.label}
                  </p>
                  <p className={cn('text-sm font-semibold tabular-nums', meta.accent)}>
                    {formatAccuracy(part.correct, part.total)}
                  </p>
                </div>
                <p className='mt-1 text-xs tabular-nums text-muted-foreground'>{part.correct} of {part.total} correct</p>
                <OutcomeBar
                  correct={part.correct}
                  incorrect={part.incorrect}
                  skipped={part.skipped}
                  className='mt-3'
                />
              </div>
            ))}
            </div>
          </div>
        )}

        <PanelBody className='border-t pt-6'>
          <PanelHeader className='mb-5 items-center'>
            <div>
              <p className='text-sm font-semibold'>Answer review</p>
              <p className='mt-1 text-sm text-muted-foreground'>Review missed marks first, or audit every response.</p>
            </div>
            <PanelToolbar className='gap-1 rounded-xl bg-muted/60 p-1'>
              {REVIEW_MODES.map(({ value, label }) => {
                const count =
                  value === 'needs_review'
                    ? counts.incorrect + counts.skipped
                    : value === 'all'
                      ? counts.correct + counts.incorrect + counts.skipped
                      : counts.correct
                const pressed = reviewMode === value
                return (
                  <button
                    key={value}
                    type='button'
                    aria-pressed={pressed}
                    onClick={() => setReviewMode(value)}
                    className={cn(
                      'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-150',
                      'focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                      pressed ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground',
                    )}
                  >
                    {label}
                    <span className='ms-1.5 tabular-nums opacity-75'>{count}</span>
                  </button>
                )
              })}
            </PanelToolbar>
          </PanelHeader>
          {visible.length === 0 && reviewMode === 'needs_review' ? (
            <PerfectReview onViewAll={() => setReviewMode('all')} />
          ) : visible.length === 0 ? (
            <p className='rounded-2xl border border-dashed py-10 text-center text-sm text-muted-foreground'>
              No answers in this view.
            </p>
          ) : (
            <div className='max-h-[42rem] overflow-auto rounded-2xl border bg-surface-sunken'>
              {groups.map((group) => (
                <section key={group.key} aria-label={group.label}>
                  <div className='sticky top-0 z-10 flex items-center justify-between border-y bg-card/95 px-4 py-2.5 backdrop-blur'>
                    <p className='text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase'>
                      {group.label}
                    </p>
                    <p className='text-xs tabular-nums text-muted-foreground'>
                      {group.answers.length} {group.answers.length === 1 ? 'response' : 'responses'}
                    </p>
                  </div>
                  <div className='divide-y divide-border/70'>
                    {group.answers.map((answer) => (
                      <AnswerAuditRow
                        key={answer.id}
                        answer={answer}
                        number={displayNumbers.get(answer.id) ?? String(answer.question?.order ?? '?')}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </PanelBody>
      </Panel>
    </div>
  )
}

function formatAccuracy(correct: number, total: number): string {
  if (total <= 0) return '—'
  return `${Math.round((correct / total) * 100)}%`
}

function ScoreMetric({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone: 'success' | 'destructive' | 'muted'
}) {
  const toneClass = {
    success: 'text-success-foreground',
    destructive: 'text-destructive',
    muted: 'text-muted-foreground',
  }[tone]
  return (
    <div className='rounded-xl bg-card px-3 py-2.5'>
      <p className='text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase'>
        {label}
      </p>
      <p className={cn('mt-1 font-manrope text-xl font-bold tabular-nums', toneClass)}>
        {value}
      </p>
    </div>
  )
}

function PerfectReview({ onViewAll }: { onViewAll: () => void }) {
  return (
    <div className='rounded-2xl border border-success-foreground/20 bg-success/35 px-5 py-8 text-center sm:px-8'>
      <div className='mx-auto flex size-11 items-center justify-center rounded-2xl bg-card shadow-sm'>
        <Check className='size-5 text-success-foreground' />
      </div>
      <h3 className='mt-4 font-manrope text-lg font-semibold'>Perfect review</h3>
      <p className='mx-auto mt-1 max-w-md text-sm leading-6 text-muted-foreground'>
        All scored answers are correct. Open the full audit whenever you want to review the answer key.
      </p>
      <button
        type='button'
        onClick={onViewAll}
        className='mt-5 rounded-xl bg-card px-4 py-2 text-sm font-medium shadow-sm ring-1 ring-success-foreground/15 transition-colors hover:bg-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
      >
        View all answers
      </button>
    </div>
  )
}

function AnswerAuditRow({
  answer,
  number,
}: {
  answer: AnswerRead
  number: string
}) {
  const outcome = answerOutcome(answer)
  const student = formatStudentAnswer(answer.response)
  const correct = formatCorrectAnswer(answer.question?.answer_key ?? null)
  const marks = answerMarks(answer)
  const optionLetters = usesOptionLetters(answer.question)

  return (
    <article
      className={cn(
        'grid gap-3 border-l-[3px] px-4 py-4 sm:gap-4 lg:grid-cols-[8.75rem_6.5rem_minmax(12rem,1fr)_minmax(14rem,1.15fr)] lg:items-start',
        outcomeRowClass(outcome),
      )}
    >
      <div className='pt-0.5'>
        <OutcomePill outcome={outcome} />
      </div>
      <div className='flex items-start justify-between gap-3 lg:block'>
        <div>
          <p className='text-[10px] font-semibold tracking-[0.14em] text-muted-foreground uppercase'>Question</p>
          <p className='mt-1 font-manrope text-base font-semibold tabular-nums'>{number}</p>
        </div>
        <MarksLabel marks={marks} className='mt-1 shrink-0 lg:block' />
      </div>
      <AnswerValue label='Your answer' tone={outcome === 'correct' ? 'neutral' : outcome}>
        {outcome === 'skipped' ? (
          <span className='text-muted-foreground'>No answer</span>
        ) : (
          <AnswerMark
            value={student}
            tone={outcome === 'incorrect' ? 'wrong' : 'plain'}
            optionLetters={optionLetters}
            matchAgainst={outcome === 'partial' ? correct : undefined}
          />
        )}
      </AnswerValue>
      <AnswerValue label='Accepted answer' tone='accepted'>
        {correct ? (
          <AnswerMark value={correct} tone='right' optionLetters={optionLetters} />
        ) : (
          <span className='text-muted-foreground'>No answer key provided</span>
        )}
      </AnswerValue>
    </article>
  )
}

function AnswerValue({
  label,
  tone,
  children,
}: {
  label: string
  tone: AnswerOutcome | 'accepted' | 'neutral'
  children: ReactNode
}) {
  const toneClass =
    tone === 'incorrect'
      ? 'border-destructive/20 bg-destructive/5'
      : tone === 'partial' || tone === 'skipped'
        ? 'border-warning-foreground/20 bg-warning/15'
        : tone === 'accepted'
          ? 'border-success-foreground/20 bg-success/35'
          : 'border-border/70 bg-card'
  return (
    <div className={cn('min-w-0 rounded-xl border px-3 py-3', toneClass)}>
      <p className='text-[10px] font-semibold tracking-[0.14em] text-muted-foreground uppercase'>{label}</p>
      <div className='mt-2 break-words whitespace-normal text-sm leading-6 text-foreground'>{children}</div>
    </div>
  )
}

/**
 * "1/2 marks" on questions that fill more than one question number, so a
 * half-right "Choose TWO letters" pair does not read as a plain zero.
 */
function MarksLabel({
  marks,
  className,
}: {
  marks: AnswerMarks
  className?: string
}) {
  if (marks.total <= 1) return null
  return (
    <span className={cn('text-[11px] font-normal tabular-nums opacity-80', className)}>
      {marks.earned}/{marks.total} marks
    </span>
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
  if (outcome === 'partial') {
    return (
      <span className='inline-flex items-center'>
        <CircleDashed className='size-4 text-warning-foreground' />
        <span className='sr-only'>Partly correct</span>
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

function OutcomePill({ outcome }: { outcome: AnswerOutcome }) {
  const label =
    outcome === 'correct'
      ? 'Correct'
      : outcome === 'partial'
        ? 'Partly correct'
        : outcome === 'skipped'
          ? 'Skipped'
          : 'Incorrect'
  const toneClass =
    outcome === 'correct'
      ? 'border-success-foreground/20 bg-success/35 text-success-foreground'
      : outcome === 'partial' || outcome === 'skipped'
        ? 'border-warning-foreground/20 bg-warning/20 text-warning-foreground'
        : 'border-destructive/20 bg-destructive/10 text-destructive'
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold', toneClass)}>
      <OutcomeIcon outcome={outcome} />
      {label}
    </span>
  )
}

function outcomeRowClass(outcome: AnswerOutcome): string {
  if (outcome === 'incorrect') return 'border-l-destructive bg-destructive/5'
  if (outcome === 'partial') return 'border-l-warning-foreground bg-warning/15'
  if (outcome === 'skipped') return 'border-l-warning-foreground/60 bg-warning/20'
  return 'border-l-transparent'
}
