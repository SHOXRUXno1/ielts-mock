import { useMemo, useState } from 'react'
import type { AnswerRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import {
  OBJECTIVE_QUESTION_TOTAL,
  answerOutcome,
  buildDisplayNumbers,
  groupAnswersByPart,
  type AnswerOutcome,
} from '../lib/answers'
import { AnswerReviewCard } from './answer-review-card'
import { type SkillKey, skillMeta } from '../lib/skill'
import { isSectionNotAttempted } from '../lib/status'
import { AnswerOutcomeBar } from './answer-outcome-bar'
import { ReportHeader } from './report-header'
import { ResultEmptyState } from './result-empty-state'

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
      <ReportHeader
        skill={skill}
        band={band}
        extra={
          <p className='mt-1 text-sm tabular-nums text-muted-foreground'>
            {raw != null ? `${raw}/${OBJECTIVE_QUESTION_TOTAL} correct` : '—'}
          </p>
        }
      />

      <div className='rounded-2xl bg-card p-5 shadow-sm ring-1 ring-border'>
        <div className='flex flex-wrap items-center justify-between gap-3'>
          <AnswerOutcomeBar
            correct={counts.correct}
            incorrect={counts.incorrect}
            skipped={counts.skipped}
            className='min-w-[12rem] flex-1'
          />
          <div className='flex flex-wrap items-center gap-1'>
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
          </div>
        </div>

        <div className='mt-4 max-h-[36rem] space-y-5 overflow-auto pr-1'>
          {groups.map((group) => (
            <section key={group.key} className='space-y-3'>
              <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
                {group.label}
              </p>
              {group.answers.map((a) => (
                <AnswerReviewCard
                  key={a.id}
                  answer={a}
                  number={displayNumbers.get(a.id) ?? String(a.question?.order ?? '?')}
                />
              ))}
            </section>
          ))}
        </div>

        {visible.length === 0 && (
          <p className='py-6 text-center text-sm text-muted-foreground'>
            No answers match this filter.
          </p>
        )}
      </div>
    </div>
  )
}
