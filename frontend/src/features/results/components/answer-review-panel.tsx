import { useMemo, useState } from 'react'
import { Check, CircleMinus, CircleX } from 'lucide-react'
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
  answerOutcome,
  buildDisplayNumbers,
  formatCorrectAnswer,
  formatStudentAnswer,
  groupAnswersByPart,
  type AnswerOutcome,
} from '../lib/answers'
import { accuracyByPart } from '../lib/insights'
import { ENTER } from '../lib/motion'
import { type SkillKey, skillMeta } from '../lib/skill'
import { isSectionNotAttempted } from '../lib/status'
import { OutcomeBar } from './outcome-bar'
import { ResultEmptyState } from './result-empty-state'
import { SkillReportHeader } from './skill-report-header'
import { Panel, PanelBody, PanelHeader, PanelToolbar } from '@/components/report'

type FilterKey = AnswerOutcome

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

  const counts = useMemo(() => {
    let correct = 0
    let incorrect = 0
    let skipped = 0
    for (const row of rows) {
      const outcome = answerOutcome(row)
      if (outcome === 'correct') correct += 1
      else if (outcome === 'skipped') skipped += 1
      else incorrect += 1
    }
    return { correct, incorrect, skipped }
  }, [rows])

  const partAccuracy = useMemo(
    () => accuracyByPart(answers, skill),
    [answers, skill],
  )

  const visible = rows.filter((row) => {
    if (filter == null) return true
    return answerOutcome(row) === filter
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
        extra={
          <p className='mt-1 text-sm tabular-nums text-muted-foreground'>
            {raw != null ? `${raw}/${OBJECTIVE_QUESTION_TOTAL} correct` : '—'}
          </p>
        }
      />

      <Panel className={ENTER} padding='sm'>
        <PanelHeader className='items-center'>
          <OutcomeBar
            correct={counts.correct}
            incorrect={counts.incorrect}
            skipped={counts.skipped}
            showLegend
            className='min-w-[12rem] flex-1'
          />
          <PanelToolbar className='gap-1'>
            {FILTERS.map(({ value, label }) => {
              const count = counts[value]
              const pressed = filter === value
              return (
                <button
                  key={value}
                  type='button'
                  aria-pressed={pressed}
                  onClick={() => setFilter((prev) => (prev === value ? null : value))}
                  className={cn(
                    'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors duration-150',
                    'focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                    pressed
                      ? 'bg-foreground text-background'
                      : 'bg-muted/60 text-muted-foreground hover:text-foreground',
                  )}
                >
                  {label}
                  <span className='ms-1.5 tabular-nums opacity-80'>{count}</span>
                </button>
              )
            })}
          </PanelToolbar>
        </PanelHeader>

        {partAccuracy.length > 0 && (
          <div className='mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
            {partAccuracy.map((part) => (
              <div key={part.key} className='space-y-2'>
                <div className='flex items-baseline justify-between gap-2'>
                  <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    {part.label}
                  </p>
                  <p className='text-[11px] tabular-nums text-muted-foreground'>
                    {part.correct}/{part.total}
                  </p>
                </div>
                <OutcomeBar
                  correct={part.correct}
                  incorrect={part.incorrect}
                  skipped={part.skipped}
                />
              </div>
            ))}
          </div>
        )}

        <PanelBody>
          <div className='hidden max-h-[32rem] overflow-auto rounded-xl bg-surface-sunken sm:block'>
            <Table>
              <TableHeader className='sticky top-0 z-10 bg-card'>
                <TableRow className='hover:bg-transparent'>
                  <TableHead className='h-11 w-16 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    Status
                  </TableHead>
                  <TableHead className='h-11 w-24 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    Question
                  </TableHead>
                  <TableHead className='h-11 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    My Answer
                  </TableHead>
                  <TableHead className='h-11 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                    Correct Answer
                  </TableHead>
                </TableRow>
              </TableHeader>
              {groups.map((group) => (
                <TableBody key={group.key}>
                  <TableRow className='bg-muted/40 hover:bg-muted/40'>
                    <TableCell
                      colSpan={4}
                      className='py-1.5 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'
                    >
                      {group.label}
                    </TableCell>
                  </TableRow>
                  {group.answers.map((a) => (
                    <AnswerTableRow
                      key={a.id}
                      answer={a}
                      number={displayNumbers.get(a.id) ?? String(a.question?.order ?? '?')}
                    />
                  ))}
                </TableBody>
              ))}
            </Table>
          </div>

          <div className='space-y-3 sm:hidden'>
            {groups.map((group) => (
              <div key={group.key} className='space-y-2'>
                <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                  {group.label}
                </p>
                {group.answers.map((a) => (
                  <AnswerCard
                    key={a.id}
                    answer={a}
                    number={displayNumbers.get(a.id) ?? String(a.question?.order ?? '?')}
                  />
                ))}
              </div>
            ))}
          </div>

          {visible.length === 0 && (
            <p className='py-6 text-center text-sm text-muted-foreground'>
              No answers match this filter.
            </p>
          )}
        </PanelBody>
      </Panel>
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

  return (
    <TableRow className={cn('h-11 border-l-[3px]', outcomeRowClass(outcome))}>
      <TableCell className='py-0'>
        <OutcomeIcon outcome={outcome} />
      </TableCell>
      <TableCell className='py-0 font-medium tabular-nums text-muted-foreground'>
        {number}
      </TableCell>
      <TableCell className='py-0 font-mono text-[13px]'>
        {outcome === 'skipped' ? (
          <span className='text-muted-foreground'>—</span>
        ) : outcome === 'incorrect' ? (
          <span className='text-muted-foreground line-through'>{student}</span>
        ) : (
          <span className='font-medium'>{student}</span>
        )}
      </TableCell>
      <TableCell
        className={cn(
          'py-0 font-mono text-[13px]',
          correct ? 'font-medium text-success-foreground' : 'text-muted-foreground',
        )}
      >
        {correct || '—'}
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

  return (
    <div className={cn('rounded-xl border border-l-[3px] p-3', outcomeRowClass(outcome))}>
      <div className='mb-2 flex items-center justify-between gap-2'>
        <span className='text-xs font-medium tabular-nums text-muted-foreground'>
          Question {number}
        </span>
        <OutcomeIcon outcome={outcome} />
      </div>
      <p className='font-mono text-[13px] font-medium text-foreground'>
        {outcome === 'skipped' ? (
          '—'
        ) : outcome === 'incorrect' ? (
          <span className='text-muted-foreground line-through'>{student}</span>
        ) : (
          student
        )}
      </p>
      <p className='mt-1 font-mono text-xs text-muted-foreground'>
        Correct: {correct || '—'}
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
  if (outcome === 'incorrect') return 'border-l-destructive bg-destructive/5'
  if (outcome === 'skipped') return 'border-l-warning-foreground/60 bg-warning/20'
  return 'border-l-transparent'
}
