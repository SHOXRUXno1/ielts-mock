import { useMemo, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, RotateCcw, Timer } from 'lucide-react'
import { toast } from 'sonner'
import type { AttemptDetailRead } from '@/lib/api/attempts'
import {
  fetchPracticeUnits,
  startPracticeAttempt,
  type PracticeScope,
  type PracticeSectionUnit,
  type PracticeUnit,
} from '@/lib/api/practice'
import { fetchSlugRedirect } from '@/lib/api/tests'
import type { SectionType } from '@/features/tests/data/schema'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Main } from '@/components/layout/main'
import { TooltipProvider } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import {
  WritingFeedbackPanel,
  writingBandFromJobs,
} from './writing-feedback-panel'
import { EvaluationProgressCard, isJobActive } from './evaluation-progress'
import { AnswerMark } from './components/answer-mark'
import {
  answerMarks,
  answerOutcome,
  formatCorrectAnswer,
  formatStudentAnswer,
  usesOptionLetters,
} from './lib/answers'
import { formatBand } from './lib/band'
import { SKILL_META, type SkillMeta } from './lib/skill'

type Props = { attempt: AttemptDetailRead }

function bandForAttempt(
  attempt: AttemptDetailRead,
  sectionType: SectionType | null,
): number | null {
  if (!sectionType) return null
  if (sectionType === 'listening') return attempt.listening_band
  if (sectionType === 'reading') return attempt.reading_band
  if (sectionType === 'writing') return attempt.writing_band
  if (sectionType === 'speaking') return attempt.speaking_band
  return null
}

/**
 * Practice-mode result page for both single_part and single_section.
 *
 * single_part: raw score ring, no IELTS band.
 * single_section: IELTS band hero + raw score secondary.
 */
export function PracticeResultDetail({ attempt }: Props) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const isWholeSection = attempt.mode === 'single_section'
  const sectionType: SectionType | null = (
    attempt.practice_section_type ??
    (attempt.practice_section_id
      ? attempt.answers.find(
          (a) => a.section?.id === attempt.practice_section_id,
        )?.section?.type ?? null
      : null)
  ) as SectionType | null

  const meta = sectionType ? SKILL_META[sectionType] : null
  const partNumber = attempt.practice_part_number ?? null
  const band = bandForAttempt(attempt, sectionType)
  const writingJobs = attempt.evaluation_jobs.filter(
    (j) => j.section_type === 'writing',
  )
  const writingBand = band ?? writingBandFromJobs(writingJobs)
  const writingPending = sectionType === 'writing' && isJobActive(writingJobs)

  const correct = attempt.practice_correct ?? 0
  const total = attempt.practice_total ?? 0
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0
  const isObjective =
    sectionType === 'listening' || sectionType === 'reading'

  const unitsQuery = useQuery({
    queryKey: ['practice-units', attempt.test_id],
    queryFn: () => fetchPracticeUnits(attempt.test_id),
  })

  const slugsQuery = useQuery({
    queryKey: ['slug-redirect', attempt.test_id],
    queryFn: () => fetchSlugRedirect(attempt.test_id),
    staleTime: Infinity,
  })

  const nextPart = useMemo<PracticeUnit | null>(() => {
    if (isWholeSection || !unitsQuery.data || !sectionType || partNumber == null)
      return null
    const units = unitsQuery.data.units.filter((u) => u.is_enabled)
    const idx = units.findIndex(
      (u) => u.section_type === sectionType && u.part_number === partNumber,
    )
    if (idx === -1) return null
    return units[(idx + 1) % units.length] ?? null
  }, [unitsQuery.data, sectionType, partNumber, isWholeSection])

  const nextSkill = useMemo<PracticeSectionUnit | null>(() => {
    if (!isWholeSection || !unitsQuery.data || !sectionType) return null
    const sections = (unitsQuery.data.sections ?? []).filter((s) => s.is_enabled)
    const idx = sections.findIndex((s) => s.section_type === sectionType)
    if (idx === -1) return null
    return sections[(idx + 1) % sections.length] ?? null
  }, [unitsQuery.data, sectionType, isWholeSection])

  const startPartMutation = useMutation({
    mutationFn: async (unit: PracticeUnit) => {
      const attemptOut = await startPracticeAttempt(attempt.test_id, {
        section_type: unit.section_type,
        scope: 'part',
        part_number: unit.part_number,
      })
      const slugs = slugsQuery.data ?? (await fetchSlugRedirect(attempt.test_id))
      return { attempt: attemptOut, slugs, unit, scope: 'part' as PracticeScope }
    },
    onSuccess: async ({ attempt: newAttempt, slugs, unit, scope }) => {
      await queryClient.invalidateQueries({
        queryKey: ['practice-units', attempt.test_id],
      })
      await navigate({
        to: '/practice/$bookSlug/$testSlug/$section/$part',
        params: {
          bookSlug: slugs.book_slug,
          testSlug: `test-${slugs.test_number}`,
          section: unit.section_type,
          part: String(unit.part_number),
        },
        search: { attempt: newAttempt.id, scope },
      })
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to start practice'
      toast.error(detail)
    },
  })

  const startSectionMutation = useMutation({
    mutationFn: async (unit: PracticeSectionUnit) => {
      const attemptOut = await startPracticeAttempt(attempt.test_id, {
        section_type: unit.section_type,
        scope: 'section',
      })
      const slugs = slugsQuery.data ?? (await fetchSlugRedirect(attempt.test_id))
      return { attempt: attemptOut, slugs, unit, scope: 'section' as PracticeScope }
    },
    onSuccess: async ({ attempt: newAttempt, slugs, unit, scope }) => {
      await queryClient.invalidateQueries({
        queryKey: ['practice-units', attempt.test_id],
      })
      await navigate({
        to: '/practice/$bookSlug/$testSlug/$section/$part',
        params: {
          bookSlug: slugs.book_slug,
          testSlug: `test-${slugs.test_number}`,
          section: unit.section_type,
          part: '1',
        },
        search: { attempt: newAttempt.id, scope },
      })
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to start practice'
      toast.error(detail)
    },
  })

  const filteredAnswers = useMemo(() => {
    if (isWholeSection && sectionType) {
      return attempt.answers
        .filter(
          (a) =>
            a.is_correct !== null &&
            (a.section?.type === sectionType ||
              a.question?.section_id != null),
        )
        .filter((a) => {
          // Prefer section.type when present; otherwise include all scored.
          if (a.section?.type) return a.section.type === sectionType
          return true
        })
        .sort((a, b) => {
          const aN = a.question?.computed_number ?? a.question?.order ?? 0
          const bN = b.question?.computed_number ?? b.question?.order ?? 0
          return aN - bN
        })
    }
    if (!attempt.practice_section_id) return []
    return attempt.answers
      .filter(
        (a) =>
          a.is_correct !== null &&
          a.section?.id === attempt.practice_section_id,
      )
      .sort((a, b) => {
        const aN = a.question?.computed_number ?? a.question?.order ?? 0
        const bN = b.question?.computed_number ?? b.question?.order ?? 0
        return aN - bN
      })
  }, [attempt, isWholeSection, sectionType])

  const currentPart = useMemo(() => {
    if (isWholeSection || !unitsQuery.data || !sectionType || partNumber == null)
      return null
    return (
      unitsQuery.data.units.find(
        (u) => u.section_type === sectionType && u.part_number === partNumber,
      ) ?? null
    )
  }, [unitsQuery.data, sectionType, partNumber, isWholeSection])

  const currentSection = useMemo(() => {
    if (!isWholeSection || !unitsQuery.data || !sectionType) return null
    return (
      (unitsQuery.data.sections ?? []).find(
        (s) => s.section_type === sectionType,
      ) ?? null
    )
  }, [unitsQuery.data, sectionType, isWholeSection])

  const duration =
    attempt.finished_at && attempt.started_at
      ? Math.max(
          0,
          Math.round(
            (new Date(attempt.finished_at).getTime() -
              new Date(attempt.started_at).getTime()) /
              60000,
          ),
        )
      : null

  const pending =
    startPartMutation.isPending || startSectionMutation.isPending

  return (
    <TooltipProvider>
    <Main className='flex flex-1 flex-col gap-6'>
      <div>
        <Button
          asChild
          variant='ghost'
          size='sm'
          className='mb-3 -ms-3 gap-1.5 rounded-lg text-muted-foreground hover:text-foreground'
        >
          <Link to='/student/tests'>
            <ArrowLeft className='size-4' />
            Back to tests
          </Link>
        </Button>

        <Card className='overflow-hidden border-border'>
          <div className={cn('h-1.5', meta?.surface ?? 'bg-primary/10')} />
          <CardContent className='flex flex-col gap-6 py-6 sm:flex-row sm:items-center'>
            {sectionType === 'writing' ? (
              writingBand != null ? (
                <BandHero
                  band={writingBand}
                  meta={meta}
                  correct={0}
                  total={0}
                />
              ) : (
                <EvaluatingHero meta={meta} pending={writingPending} />
              )
            ) : isWholeSection && band != null ? (
              <BandHero band={band} meta={meta} correct={correct} total={total} />
            ) : isObjective ? (
              <ScoreRing correct={correct} total={total} pct={pct} meta={meta} />
            ) : (
              <EvaluatingHero meta={meta} pending />
            )}

            <div className='min-w-0 flex-1 space-y-2'>
              <div className='flex flex-wrap items-center gap-2'>
                {meta && (
                  <Badge variant='outline' className={cn('rounded-lg', meta.accent)}>
                    <meta.icon className='me-1 size-3' />
                    {isWholeSection
                      ? `Full ${meta.label}`
                      : `${meta.label}${partNumber != null ? ` · Part ${partNumber}` : ''}`}
                  </Badge>
                )}
                <Badge variant='secondary' className='rounded-lg'>
                  Practice
                </Badge>
              </div>
              <h1 className='text-xl font-semibold tracking-tight text-foreground'>
                {attempt.test_title ?? 'Practice result'}
              </h1>
              <p className='text-sm text-muted-foreground'>
                {attempt.finished_at
                  ? `Finished ${new Date(attempt.finished_at).toLocaleString()}`
                  : 'In progress'}
                {duration != null && duration > 0 && (
                  <>
                    <span className='mx-1.5 text-muted-foreground/50'>·</span>
                    <Timer className='me-1 inline size-3' />
                    {duration} min
                  </>
                )}
              </p>

              <div className='flex flex-wrap gap-2 pt-1'>
                {isWholeSection ? (
                  <>
                    <RetryButton
                      disabled={pending || !currentSection}
                      onClick={() =>
                        currentSection &&
                        startSectionMutation.mutate(currentSection)
                      }
                    />
                    {nextSkill && (
                      <Button
                        size='sm'
                        variant='outline'
                        className='gap-1.5 rounded-lg'
                        disabled={pending}
                        onClick={() => startSectionMutation.mutate(nextSkill)}
                      >
                        Next skill
                        <span className='text-muted-foreground'>
                          · {SKILL_META[nextSkill.section_type].label}
                        </span>
                      </Button>
                    )}
                  </>
                ) : (
                  <>
                    <RetryButton
                      disabled={pending || !currentPart}
                      onClick={() =>
                        currentPart && startPartMutation.mutate(currentPart)
                      }
                    />
                    {nextPart && (
                      <Button
                        size='sm'
                        variant='outline'
                        className='gap-1.5 rounded-lg'
                        disabled={pending}
                        onClick={() => startPartMutation.mutate(nextPart)}
                      >
                        Next part
                        <span className='text-muted-foreground'>
                          · {SKILL_META[nextPart.section_type].label} Part{' '}
                          {nextPart.part_number}
                        </span>
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {isObjective && (
        <BreakdownCard sectionType={sectionType!} title='Answer breakdown'>
          {filteredAnswers.length === 0 ? (
            <p className='py-6 text-center text-sm text-muted-foreground'>
              No scored answers to review for this{' '}
              {isWholeSection ? 'section' : 'part'}.
            </p>
          ) : (
            <div className='overflow-hidden rounded-lg border'>
              <Table>
                <TableHeader>
                  <TableRow className='bg-muted/40 hover:bg-muted/40'>
                    <TableHead className='h-9 w-20 text-xs uppercase tracking-wide text-muted-foreground'>
                      #
                    </TableHead>
                    <TableHead className='h-9 text-xs uppercase tracking-wide text-muted-foreground'>
                      My answer
                    </TableHead>
                    <TableHead className='h-9 text-xs uppercase tracking-wide text-muted-foreground'>
                      Correct answer
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAnswers.map((a) => {
                    const outcome = answerOutcome(a)
                    const marks = answerMarks(a)
                    const optionLetters = usesOptionLetters(a.question)
                    const student = formatStudentAnswer(a.response)
                    const correctText = formatCorrectAnswer(
                      a.question?.answer_key ?? null,
                    )
                    return (
                      <TableRow
                        key={a.id}
                        className={cn(
                          'border-l-2',
                          outcome === 'correct'
                            ? 'border-l-transparent'
                            : outcome === 'skipped'
                              ? 'border-l-warning-foreground/60 bg-warning/20'
                              : outcome === 'partial'
                                ? 'border-l-warning-foreground bg-warning/15'
                                : 'border-l-destructive bg-destructive/5',
                        )}
                      >
                        <TableCell className='py-2 font-medium tabular-nums text-muted-foreground'>
                          {a.question?.computed_number ??
                            a.question?.order ??
                            '?'}
                          {marks.total > 1 && (
                            <span className='block text-[11px] font-normal opacity-80'>
                              {marks.earned}/{marks.total} marks
                            </span>
                          )}
                        </TableCell>
                        <TableCell className='py-2'>
                          {outcome === 'skipped' ? (
                            <span className='text-muted-foreground'>—</span>
                          ) : (
                            <AnswerMark
                              value={student}
                              tone={outcome === 'incorrect' ? 'wrong' : 'plain'}
                              optionLetters={optionLetters}
                              matchAgainst={
                                outcome === 'partial' ? correctText : undefined
                              }
                            />
                          )}
                        </TableCell>
                        <TableCell className='py-2'>
                          {correctText ? (
                            <AnswerMark
                              value={correctText}
                              tone='right'
                              optionLetters={optionLetters}
                            />
                          ) : (
                            <span className='text-muted-foreground'>—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </BreakdownCard>
      )}

      {sectionType === 'writing' && (
        <div className='space-y-4'>
          <EvaluationProgressCard jobs={writingJobs} section='writing' />
          {writingJobs.some((j) => j.status === 'done') && (
            <BreakdownCard sectionType='writing' title='Writing feedback'>
              <WritingFeedbackPanel jobs={writingJobs} partNumber={partNumber} />
            </BreakdownCard>
          )}
        </div>
      )}
    </Main>
    </TooltipProvider>
  )
}

function BandHero({
  band,
  meta,
  correct,
  total,
}: {
  band: number
  meta: SkillMeta | null
  correct: number
  total: number
}) {
  const pct = (band / 9) * 100
  const circumference = 2 * Math.PI * 48
  const dash = (pct / 100) * circumference
  return (
    <div className='relative flex size-32 shrink-0 items-center justify-center'>
      <svg className='absolute inset-0 size-full -rotate-90'>
        <circle
          cx='64'
          cy='64'
          r='48'
          fill='none'
          className='stroke-muted'
          strokeWidth='8'
        />
        <circle
          cx='64'
          cy='64'
          r='48'
          fill='none'
          className={cn(
            'transition-all duration-700',
            meta?.ring ?? 'stroke-primary',
          )}
          strokeWidth='8'
          strokeLinecap='round'
          strokeDasharray={`${dash} ${circumference}`}
        />
      </svg>
      <div className='relative flex flex-col items-center'>
        <span className='text-2xl font-bold tabular-nums text-foreground'>
          {formatBand(band)}
        </span>
        <span className='text-[10px] font-medium uppercase tracking-wider text-muted-foreground'>
          Band
        </span>
        {total > 0 && (
          <span className='mt-0.5 text-[10px] text-muted-foreground'>
            {correct}/{total}
          </span>
        )}
      </div>
    </div>
  )
}

function EvaluatingHero({
  meta,
  pending,
}: {
  meta: SkillMeta | null
  pending?: boolean
}) {
  return (
    <div
      className={cn(
        'flex size-32 shrink-0 flex-col items-center justify-center rounded-full border-4',
        meta?.surface ?? 'bg-muted',
        'border-muted',
      )}
    >
      <span className='px-3 text-center text-xs font-medium text-muted-foreground'>
        {pending ? 'Evaluating…' : 'No score yet'}
      </span>
    </div>
  )
}

function ScoreRing({
  correct,
  total,
  pct,
  meta,
}: {
  correct: number
  total: number
  pct: number
  meta: SkillMeta | null
}) {
  const circumference = 2 * Math.PI * 48
  const dash = (pct / 100) * circumference
  return (
    <div className='relative flex size-32 shrink-0 items-center justify-center'>
      <svg className='absolute inset-0 size-full -rotate-90'>
        <circle
          cx='64'
          cy='64'
          r='48'
          fill='none'
          className='stroke-muted'
          strokeWidth='8'
        />
        <circle
          cx='64'
          cy='64'
          r='48'
          fill='none'
          className={cn(
            'transition-all duration-700',
            meta?.ring ?? 'stroke-primary',
          )}
          strokeWidth='8'
          strokeLinecap='round'
          strokeDasharray={`${dash} ${circumference}`}
        />
      </svg>
      <div className='relative flex flex-col items-center'>
        <span className='text-2xl font-bold text-foreground tabular-nums'>
          {correct}
          <span className='text-base text-muted-foreground'>/{total}</span>
        </span>
        <span className='text-[10px] font-medium uppercase tracking-wider text-muted-foreground'>
          {pct}% correct
        </span>
      </div>
    </div>
  )
}

function BreakdownCard({
  sectionType,
  title,
  children,
}: {
  sectionType: SectionType | null
  title: string
  children: ReactNode
}) {
  const meta = sectionType ? SKILL_META[sectionType] : null
  return (
    <Card>
      <CardContent className='py-5'>
        <div className='mb-4 flex items-center gap-2'>
          {meta && (
            <div className={cn('rounded-lg p-1.5', meta.surface)}>
              <meta.icon className={cn('size-4', meta.accent)} />
            </div>
          )}
          <h2 className='text-base font-semibold'>{title}</h2>
        </div>
        {children}
      </CardContent>
    </Card>
  )
}

function RetryButton({
  disabled,
  onClick,
}: {
  disabled: boolean
  onClick: () => void
}) {
  return (
    <Button
      size='sm'
      className='gap-1.5 rounded-lg'
      disabled={disabled}
      onClick={onClick}
    >
      <RotateCcw className='size-3.5' />
      Try again
    </Button>
  )
}

