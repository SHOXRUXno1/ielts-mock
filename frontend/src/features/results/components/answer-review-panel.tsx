import { useMemo, useState } from 'react'
import { Check, CircleDashed, CircleMinus, CircleX } from 'lucide-react'
import type { AnswerRead } from '@/lib/api/attempts'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
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

/** Partial answers remain in the incorrect filter, as they did before. */
type FilterKey = Exclude<AnswerOutcome, 'partial'>

type AnswerReviewPanelProps = {
  skill: Extract<SkillKey, 'listening' | 'reading'>
  band: number | null
  raw: number | null
  answers: AnswerRead[]
  attemptStatus?: string
}

const FILTERS: { value: FilterKey; label: string }[] = [
  { value: 'correct', label: 'Correct' },
  { value: 'incorrect', label: 'Incorrect' },
  { value: 'skipped', label: 'Skipped' },
]

export function AnswerReviewPanel({
  skill,
  band,
  raw,
  answers,
  attemptStatus,
}: AnswerReviewPanelProps) {
  const [filter, setFilter] = useState<FilterKey | null>(null)
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

  const visible = rows.filter(
    (row) => filter == null || matchesOutcomeFilter(answerOutcome(row), filter),
  )
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
              <p className='mt-1 text-sm text-muted-foreground'>Every answer is shown below. Use a filter to focus your review.</p>
            </div>
            <PanelToolbar className='gap-1 rounded-xl bg-muted/60 p-1'>
              {FILTERS.map(({ value, label }) => {
                const pressed = filter === value
                return (
                  <button
                    key={value}
                    type='button'
                    aria-pressed={pressed}
                    onClick={() => setFilter((previous) => (previous === value ? null : value))}
                    className={cn(
                      'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-150',
                      'focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                      pressed ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground',
                    )}
                  >
                    {label}
                    <span className='ms-1.5 tabular-nums opacity-75'>{counts[value]}</span>
                  </button>
                )
              })}
            </PanelToolbar>
          </PanelHeader>
          <div className='hidden max-h-[32rem] overflow-auto rounded-xl border bg-surface-sunken sm:block'>
            <Table>
              <TableHeader className='sticky top-0 z-10 bg-card'>
                <TableRow className='hover:bg-transparent'>
                  <TableHead className='h-11 w-20 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    Status
                  </TableHead>
                  <TableHead className='h-11 w-28 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    Question
                  </TableHead>
                  <TableHead className='h-11 min-w-48 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    Your answer
                  </TableHead>
                  <TableHead className='h-11 min-w-64 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    Accepted answer
                  </TableHead>
                </TableRow>
              </TableHeader>
              {groups.map((group) => (
                <TableBody key={group.key}>
                  <TableRow className='bg-muted/40 hover:bg-muted/40'>
                    <TableCell
                      colSpan={4}
                      className='py-2 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'
                    >
                      {group.label}
                    </TableCell>
                  </TableRow>
                    {group.answers.map((answer) => (
                      <AnswerTableRow
                        key={answer.id}
                        answer={answer}
                        number={displayNumbers.get(answer.id) ?? String(answer.question?.order ?? '?')}
                      />
                    ))}
                </TableBody>
              ))}
            </Table>
          </div>

          <div className='space-y-3 sm:hidden'>
            {groups.map((group) => (
              <section key={group.key} className='space-y-2' aria-label={group.label}>
                <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                  {group.label}
                </p>
                {group.answers.map((answer) => (
                  <AnswerCard
                    key={answer.id}
                    answer={answer}
                    number={displayNumbers.get(answer.id) ?? String(answer.question?.order ?? '?')}
                  />
                ))}
              </section>
            ))}
          </div>

          {visible.length === 0 && (
            <p className='rounded-xl border border-dashed py-8 text-center text-sm text-muted-foreground'>
              No answers match this filter.
            </p>
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

function AnswerTableRow({
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
    <TableRow className={cn('border-l-[3px]', outcomeRowClass(outcome))}>
      <TableCell className='py-2 align-top'>
        <OutcomeIcon outcome={outcome} />
      </TableCell>
      <TableCell className='py-2 align-top font-medium tabular-nums text-muted-foreground'>
        {number}
        <MarksLabel marks={marks} className='mt-0.5 block' />
      </TableCell>
      <TableCell className='min-w-48 py-2 align-top whitespace-normal'>
        {outcome === 'skipped' ? (
          <span className='text-muted-foreground'>—</span>
        ) : (
          <AnswerMark
            value={student}
            tone={outcome === 'incorrect' ? 'wrong' : 'plain'}
            optionLetters={optionLetters}
            matchAgainst={outcome === 'partial' ? correct : undefined}
          />
        )}
      </TableCell>
      <TableCell className='min-w-64 py-2 align-top whitespace-normal'>
        {correct ? (
          <AnswerMark value={correct} tone='right' optionLetters={optionLetters} />
        ) : (
          <span className='text-muted-foreground'>—</span>
        )}
      </TableCell>
    </TableRow>
  )
}

function AnswerCard({
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
    <article className={cn('rounded-xl border border-l-[3px] p-3', outcomeRowClass(outcome))}>
      <div className='mb-3 flex items-center justify-between gap-3'>
        <span className='text-xs font-medium tabular-nums text-muted-foreground'>
          Question {number}
          <MarksLabel marks={marks} className='ms-2' />
        </span>
        <OutcomeIcon outcome={outcome} />
      </div>
      <div className='space-y-2.5 text-sm'>
        <div>
          <p className='text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase'>Your answer</p>
          <div className='mt-1 break-words'>
            {outcome === 'skipped' ? (
              <span className='text-muted-foreground'>—</span>
            ) : (
              <AnswerMark
                value={student}
                tone={outcome === 'incorrect' ? 'wrong' : 'plain'}
                optionLetters={optionLetters}
                matchAgainst={outcome === 'partial' ? correct : undefined}
              />
            )}
          </div>
        </div>
        <div>
          <p className='text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase'>Accepted answer</p>
          <div className='mt-1 break-words'>
            {correct ? (
              <AnswerMark value={correct} tone='right' optionLetters={optionLetters} />
            ) : (
              <span className='text-muted-foreground'>—</span>
            )}
          </div>
        </div>
      </div>
    </article>
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

function outcomeRowClass(outcome: AnswerOutcome): string {
  if (outcome === 'incorrect') return 'border-l-destructive bg-destructive/5'
  if (outcome === 'partial') return 'border-l-warning-foreground bg-warning/15'
  if (outcome === 'skipped') return 'border-l-warning-foreground/60 bg-warning/20'
  return 'border-l-transparent'
}
