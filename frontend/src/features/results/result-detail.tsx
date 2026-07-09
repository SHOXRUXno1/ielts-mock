import { Fragment, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getRouteApi, Link } from '@tanstack/react-router'
import {
  ArrowLeft,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  HelpCircle,
  Loader2,
  XCircle,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  fetchResultDetail,
  overrideBand,
  type AnswerRead,
  type EvaluationJobRead,
} from '@/lib/api/attempts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

const route = getRouteApi('/_authenticated/results/$attemptId')

function formatBand(band: number | null | undefined): string {
  if (band == null) return '—'
  return band.toFixed(1)
}

export function ResultDetail() {
  const { attemptId } = route.useParams()
  const queryClient = useQueryClient()

  const { data: attempt, isLoading } = useQuery({
    queryKey: ['results', attemptId],
    queryFn: () => fetchResultDetail(attemptId),
    refetchInterval: (query) => {
      const data = query.state.data
      if (
        data &&
        data.evaluation_jobs.some(
          (j) => j.status === 'pending' || j.status === 'processing',
        )
      ) {
        return 5000
      }
      return false
    },
  })

  if (isLoading) {
    return (
      <>
        <Header fixed>
          <Search className='me-auto' />
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </Header>
        <Main>
          <p className='text-muted-foreground'>Loading...</p>
        </Main>
      </>
    )
  }

  if (!attempt) {
    return (
      <>
        <Header fixed>
          <Search className='me-auto' />
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </Header>
        <Main>
          <p className='text-muted-foreground'>Attempt not found.</p>
        </Main>
      </>
    )
  }

  const sections = [
    {
      type: 'listening',
      label: 'Listening',
      band: attempt.listening_band,
      raw: attempt.listening_raw,
      total: 40,
    },
    {
      type: 'reading',
      label: 'Reading',
      band: attempt.reading_band,
      raw: attempt.reading_raw,
      total: 40,
    },
    {
      type: 'writing',
      label: 'Writing',
      band: attempt.writing_band,
      raw: null,
      total: null,
    },
    {
      type: 'speaking',
      label: 'Speaking',
      band: attempt.speaking_band,
      raw: null,
      total: null,
    },
  ]

  return (
    <TooltipProvider>
      <>
        <Header fixed>
          <Search className='me-auto' />
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </Header>

        <Main className='flex flex-1 flex-col gap-6'>
          <div>
            <Button asChild variant='ghost' size='sm' className='mb-2 -ms-3'>
              <Link to='/results'>
                <ArrowLeft className='size-4' />
                Back to results
              </Link>
            </Button>

            <div className='flex items-center gap-3'>
              <h2 className='text-2xl font-bold tracking-tight'>
                Test Result
              </h2>
              <Badge
                variant={
                  attempt.status === 'scored' ? 'default' : 'secondary'
                }
              >
                {attempt.status === 'scored'
                  ? 'Scored'
                  : attempt.status === 'completed'
                    ? 'Evaluating...'
                    : 'In Progress'}
              </Badge>
            </div>
            <p className='mt-1 text-muted-foreground'>
              Started{' '}
              {attempt.started_at
                ? new Date(attempt.started_at).toLocaleString()
                : '—'}
              {attempt.finished_at && (
                <>
                  {' '}
                  · Finished {new Date(attempt.finished_at).toLocaleString()}
                </>
              )}
            </p>
          </div>

          {/* Overall band */}
          <Card>
            <CardContent className='py-6'>
              <div className='grid grid-cols-5 gap-4 text-center'>
                <div>
                  <p className='text-xs text-muted-foreground'>Overall</p>
                  <p className='text-3xl font-bold text-primary'>
                    {formatBand(attempt.overall_band)}
                  </p>
                </div>
                {sections.map((s) => (
                  <div key={s.type}>
                    <p className='text-xs text-muted-foreground'>{s.label}</p>
                    <p className='text-2xl font-bold'>{formatBand(s.band)}</p>
                    {s.raw !== null && s.total !== null && (
                      <p className='text-xs text-muted-foreground'>
                        {s.raw}/{s.total} correct
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* R/L answer breakdown */}
          {attempt.answers.some((a) => a.is_correct !== null) && (
            <AnswerBreakdownCard answers={attempt.answers} />
          )}

          {/* AI Evaluation Jobs */}
          {attempt.evaluation_jobs.map((job) => (
            <EvaluationJobCard
              key={job.id}
              job={job}
              onOverride={() =>
                queryClient.invalidateQueries({
                  queryKey: ['results', attemptId],
                })
              }
            />
          ))}
        </Main>
      </>
    </TooltipProvider>
  )
}

// ── Answer Breakdown helpers ──────────────────────────────────────────────────

function formatStudentAnswer(response: Record<string, unknown>): string {
  const val = response.answer
  if (val == null || val === '') return '(no answer)'
  if (Array.isArray(val)) return val.join(', ')
  if (typeof val === 'object' && val !== null) {
    return Object.entries(val as Record<string, unknown>)
      .map(([k, v]) => `${k} → ${v}`)
      .join('; ')
  }
  return String(val)
}

function formatCorrectAnswer(
  answerKey: Record<string, unknown> | null,
): string {
  if (!answerKey) return '—'
  const correct = answerKey.correct ?? answerKey.answer
  if (correct == null) return '—'
  if (Array.isArray(correct)) return correct[0] !== undefined ? correct.join(' / ') : '—'
  if (typeof correct === 'object' && correct !== null) {
    return Object.entries(correct as Record<string, unknown>)
      .map(([k, v]) => `${k} → ${v}`)
      .join('; ')
  }
  return String(correct)
}

function groupBySection(answers: AnswerRead[]) {
  const map = new Map<
    string,
    { label: string; order: number; answers: AnswerRead[] }
  >()

  for (const a of answers) {
    if (a.is_correct === null) continue
    const key = a.section?.id ?? 'unknown'
    if (!map.has(key)) {
      map.set(key, {
        label: '',
        order: a.section?.order ?? 999,
        answers: [],
      })
    }
    map.get(key)!.answers.push(a)
  }

  // Sort groups by section order
  const groups = Array.from(map.entries()).sort(
    ([, a], [, b]) => a.order - b.order,
  )

  // Assign human-readable labels based on relative position within each type
  const listeningCounter = { n: 0 }
  const readingCounter = { n: 0 }

  return groups.map(([key, g]) => {
    const sec = g.answers[0]?.section
    let label = 'Other'
    if (sec) {
      if (sec.type === 'listening') {
        listeningCounter.n++
        label = `Listening Section ${listeningCounter.n}`
      } else if (sec.type === 'reading') {
        readingCounter.n++
        label = `Reading Passage ${readingCounter.n}`
      } else {
        label = `${sec.type.charAt(0).toUpperCase() + sec.type.slice(1)} Section ${sec.order}`
      }
    }
    return {
      key,
      label,
      order: g.order,
      answers: g.answers.sort(
        (x, y) => (x.question?.order ?? 0) - (y.question?.order ?? 0),
      ),
    }
  })
}

function AnswerRow({ answer }: { answer: AnswerRead }) {
  const qNum = answer.question?.order ?? '?'
  const studentVal = formatStudentAnswer(answer.response)
  const correctVal = formatCorrectAnswer(answer.question?.answer_key ?? null)

  return (
    <div className='flex flex-col gap-0.5 px-3 py-2 text-sm sm:flex-row sm:items-start sm:gap-3'>
      {/* Icon + Q# */}
      <div className='flex shrink-0 items-center gap-1.5'>
        {answer.is_correct ? (
          <CheckCircle className='size-4 text-green-600' />
        ) : (
          <XCircle className='size-4 text-destructive' />
        )}
        <span className='w-8 font-mono text-xs font-semibold text-muted-foreground'>
          Q{qNum}
        </span>
      </div>

      {/* Your answer */}
      <div className='flex min-w-0 flex-1 flex-col gap-0.5 sm:flex-row sm:gap-4'>
        <div className='flex min-w-0 flex-1 gap-1.5'>
          <span className='shrink-0 text-xs text-muted-foreground'>
            Your answer:
          </span>
          <span
            className={cn(
              'min-w-0 break-words text-xs font-medium',
              answer.is_correct ? 'text-green-700' : 'text-destructive',
            )}
          >
            {studentVal}
          </span>
        </div>

        {/* Correct answer (only show when wrong) */}
        {!answer.is_correct && (
          <div className='flex min-w-0 flex-1 gap-1.5'>
            <span className='shrink-0 text-xs text-muted-foreground'>
              Correct:
            </span>
            <span className='min-w-0 break-words text-xs font-medium text-green-700'>
              {correctVal}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function AnswerBreakdownCard({ answers }: { answers: AnswerRead[] }) {
  const groups = groupBySection(answers)
  const totalCorrect = answers.filter((a) => a.is_correct === true).length
  const totalScored = answers.filter((a) => a.is_correct !== null).length

  return (
    <Card>
      <CardHeader>
        <CardTitle>Answer Breakdown</CardTitle>
        <CardDescription>
          Reading & Listening auto-scored answers · {totalCorrect}/{totalScored}{' '}
          correct
        </CardDescription>
      </CardHeader>
      <CardContent className='space-y-6'>
        {groups.map((group) => (
          <div key={group.key}>
            <h4 className='mb-2 text-sm font-semibold'>{group.label}</h4>
            <div className='divide-y rounded-md border'>
              {group.answers.map((a) => (
                <AnswerRow key={a.id} answer={a} />
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function EvaluationJobCard({
  job,
  onOverride,
}: {
  job: EvaluationJobRead
  onOverride: () => void
}) {
  const [overrideValue, setOverrideValue] = useState(
    job.teacher_override_band?.toString() ?? '',
  )

  const mutation = useMutation({
    mutationFn: () => overrideBand(job.id, parseFloat(overrideValue)),
    onSuccess: () => {
      toast.success('Band override saved')
      onOverride()
    },
  })

  const result = job.result as Record<string, unknown> | null
  const isPending = job.status === 'pending' || job.status === 'processing'
  const isWriting = job.section_type === 'writing'

  return (
    <Card>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 capitalize'>
          {job.section_type} Evaluation
          <Badge
            variant={
              job.status === 'done'
                ? 'default'
                : job.status === 'failed'
                  ? 'destructive'
                  : 'secondary'
            }
          >
            {job.status}
          </Badge>
        </CardTitle>
        {job.processed_at && (
          <CardDescription>
            Processed {new Date(job.processed_at).toLocaleString()}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className='space-y-4'>
        {isPending && (
          <div className='flex items-center gap-2 text-sm text-muted-foreground'>
            <Loader2 className='size-4 animate-spin' />
            AI evaluation in progress...
          </div>
        )}

        {job.status === 'failed' && (
          <p className='text-sm text-destructive'>
            Error: {job.error_message}
          </p>
        )}

        {job.status === 'done' && result && (
          <>
            <div className='text-center'>
              <p className='text-xs text-muted-foreground'>AI Band</p>
              <p className='text-2xl font-bold'>
                {formatBand(job.band_score)}
              </p>
            </div>

            {isWriting && result.tasks ? (
              <WritingResult
                tasks={result.tasks as Record<string, Record<string, unknown>>}
              />
            ) : (
              <>
                <CriteriaGrid data={result} sectionType={job.section_type} />
                {result.strengths && (
                  <FeedbackList
                    title='Strengths'
                    items={result.strengths as string[]}
                  />
                )}
                {result.improvements && (
                  <FeedbackList
                    title='Areas for Improvement'
                    items={result.improvements as string[]}
                  />
                )}
                {result.transcript && (
                  <div>
                    <p className='mb-1 text-sm font-medium'>Transcript</p>
                    <p className='rounded-md border bg-muted/50 p-3 text-sm whitespace-pre-wrap'>
                      {result.transcript as string}
                    </p>
                  </div>
                )}
              </>
            )}

            <div className='flex items-end gap-3 rounded-md border p-3'>
              <div className='flex-1 space-y-1'>
                <p className='text-sm font-medium'>Teacher Override</p>
                <Input
                  type='number'
                  step='0.5'
                  min='0'
                  max='9'
                  value={overrideValue}
                  onChange={(e) => setOverrideValue(e.target.value)}
                  placeholder='e.g. 7.0'
                  className='max-w-32'
                />
              </div>
              <Button
                size='sm'
                onClick={() => mutation.mutate()}
                disabled={
                  mutation.isPending ||
                  !overrideValue ||
                  isNaN(parseFloat(overrideValue))
                }
              >
                {mutation.isPending && <Loader2 className='animate-spin' />}
                Save Override
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

/* ── Writing-specific result component ── */

type WritingError = {
  quote: string
  type: 'grammar' | 'lexical' | 'spelling' | 'cohesion' | 'punctuation'
  correction: string
  explanation: string
}

const ERROR_COLORS: Record<WritingError['type'], string> = {
  grammar: 'bg-red-100 text-red-800 underline decoration-red-400 decoration-wavy',
  lexical: 'bg-amber-100 text-amber-800 underline decoration-amber-400 decoration-wavy',
  spelling: 'bg-orange-100 text-orange-800 underline decoration-orange-500 decoration-wavy',
  cohesion: 'bg-blue-100 text-blue-800 underline decoration-blue-400 decoration-wavy',
  punctuation: 'bg-violet-100 text-violet-800 underline decoration-violet-400 decoration-wavy',
}

const ERROR_BADGE_COLORS: Record<WritingError['type'], string> = {
  grammar: 'bg-red-100 text-red-700 border-red-200',
  lexical: 'bg-amber-100 text-amber-700 border-amber-200',
  spelling: 'bg-orange-100 text-orange-700 border-orange-200',
  cohesion: 'bg-blue-100 text-blue-700 border-blue-200',
  punctuation: 'bg-violet-100 text-violet-700 border-violet-200',
}

/** Split essay text into segments, wrapping error quotes with Tooltip marks. */
function HighlightedEssay({
  text,
  errors,
}: {
  text: string
  errors: WritingError[]
}) {
  if (!errors.length) {
    return (
      <p className='whitespace-pre-wrap text-sm leading-relaxed'>{text}</p>
    )
  }

  // Build non-overlapping segments greedily (first-match wins)
  type Segment =
    | { kind: 'text'; content: string }
    | { kind: 'error'; content: string; error: WritingError }

  const segments: Segment[] = []
  let remaining = text

  while (remaining.length > 0) {
    let bestIdx = Infinity
    let bestError: WritingError | null = null

    for (const err of errors) {
      if (!err.quote) continue
      const idx = remaining.indexOf(err.quote)
      if (idx !== -1 && idx < bestIdx) {
        bestIdx = idx
        bestError = err
      }
    }

    if (bestError === null) {
      segments.push({ kind: 'text', content: remaining })
      break
    }

    if (bestIdx > 0) {
      segments.push({ kind: 'text', content: remaining.slice(0, bestIdx) })
    }
    segments.push({
      kind: 'error',
      content: bestError.quote,
      error: bestError,
    })
    remaining = remaining.slice(bestIdx + bestError.quote.length)

    // Remove matched error to avoid re-matching the same span
    errors = errors.filter((e) => e !== bestError)
  }

  return (
    <p className='whitespace-pre-wrap text-sm leading-relaxed'>
      {segments.map((seg, i) => {
        if (seg.kind === 'text') {
          return <Fragment key={i}>{seg.content}</Fragment>
        }
        const colorClass = ERROR_COLORS[seg.error.type] ?? ''
        return (
          <Tooltip key={i}>
            <TooltipTrigger asChild>
              <mark className={cn('cursor-help rounded px-0.5', colorClass)}>
                {seg.content}
              </mark>
            </TooltipTrigger>
            <TooltipContent className='max-w-xs'>
              <p className='font-semibold capitalize'>{seg.error.type}</p>
              <p className='text-xs'>
                <span className='text-muted-foreground'>Fix: </span>
                {seg.error.correction}
              </p>
              <p className='mt-0.5 text-xs text-muted-foreground'>
                {seg.error.explanation}
              </p>
            </TooltipContent>
          </Tooltip>
        )
      })}
    </p>
  )
}

function WritingResult({
  tasks,
}: {
  tasks: Record<string, Record<string, unknown>>
}) {
  const taskEntries = Object.entries(tasks).sort(([a], [b]) =>
    a.localeCompare(b),
  )

  return (
    <div className='space-y-6'>
      {taskEntries.map(([taskKey, taskData]) => {
        const isTask1 = taskKey.includes('1')
        const label = isTask1 ? 'Task 1 — Report' : 'Task 2 — Essay'
        const overallBand = taskData.overall_band as number | undefined
        const wordCount = taskData.word_count as number | undefined
        const essayText = (taskData.text as string | undefined) ?? ''
        const strengths = taskData.strengths as string[] | undefined
        const improvements = taskData.improvements as string[] | undefined
        const rawErrors = (taskData.errors ?? []) as WritingError[]

        return (
          <div key={taskKey} className='space-y-4 rounded-lg border p-4'>
            {/* Task header */}
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <h4 className='font-semibold'>{label}</h4>
                {wordCount != null && (
                  <Badge variant='outline' className='text-xs'>
                    <FileText className='mr-1 size-3' />
                    {wordCount} words
                  </Badge>
                )}
              </div>
              {overallBand != null && (
                <div className='text-right'>
                  <p className='text-xs text-muted-foreground'>Task Band</p>
                  <p className='text-xl font-bold'>
                    {formatBand(overallBand)}
                  </p>
                </div>
              )}
            </div>

            <CriteriaGrid data={taskData} sectionType='writing' isTask1={isTask1} />

            {strengths && strengths.length > 0 && (
              <FeedbackList title='Strengths' items={strengths} />
            )}
            {improvements && improvements.length > 0 && (
              <FeedbackList title='Areas for Improvement' items={improvements} />
            )}

            {/* Student essay with inline error highlights */}
            {essayText && (
              <div>
                <p className='mb-2 text-sm font-medium'>Student's Essay</p>
                <div className='max-h-80 overflow-y-auto rounded-md border bg-muted/20 p-4'>
                  <HighlightedEssay
                    text={essayText}
                    errors={[...rawErrors]}
                  />
                </div>
              </div>
            )}

            {/* Errors & corrections list */}
            {rawErrors.length > 0 && (
              <div>
                <p className='mb-2 text-sm font-medium'>
                  Errors & Corrections
                </p>
                <div className='space-y-2'>
                  {rawErrors.map((err, i) => (
                    <div
                      key={i}
                      className='flex flex-wrap items-start gap-2 rounded-md border p-3 text-sm'
                    >
                      <span
                        className={cn(
                          'shrink-0 rounded border px-1.5 py-0.5 text-xs font-medium capitalize',
                          ERROR_BADGE_COLORS[err.type] ?? '',
                        )}
                      >
                        {err.type}
                      </span>
                      <span className='line-through text-muted-foreground'>
                        {err.quote}
                      </span>
                      <span className='text-muted-foreground'>→</span>
                      <span className='font-medium text-green-700'>
                        {err.correction}
                      </span>
                      <span className='w-full text-xs text-muted-foreground'>
                        {err.explanation}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ── Criteria grid ── */

const WRITING_TASK1_FIRST_CRITERION = [
  'task_achievement',
  'Task Achievement',
  'Band 9: Fully covers requirements; key features accurately described with clear overview. Band 7: Clearly presents and highlights key features. Band 5: Key features may be inadequately covered or inaccurate.',
] as const

const WRITING_TASK2_FIRST_CRITERION = [
  'task_response',
  'Task Response',
  'Band 9: Fully addresses all parts; fully developed position. Band 7: Clear position; relevant main ideas, some may lack development. Band 5: Partially addresses task; position not always clear.',
] as const

const WRITING_SHARED_CRITERIA = [
  [
    'coherence_cohesion',
    'Coherence & Cohesion',
    'Band 9: Cohesion attracts no attention; paragraphing is skilful. Band 7: Logical organisation; clear progression; some over-use of cohesive devices. Band 5: Organisation evident but not wholly logical.',
  ],
  [
    'lexical_resource',
    'Lexical Resource',
    'Band 9: Wide range; very natural and sophisticated control. Band 7: Sufficient range; awareness of style; occasional errors. Band 5: Limited range; noticeable spelling/word-form errors.',
  ],
  [
    'grammatical_range',
    'Grammatical Range',
    'Band 9: Full flexibility and accuracy; rare minor errors. Band 7: Variety of complex structures; frequent error-free sentences. Band 5: Limited structures; complex sentences attempted but errors frequent.',
  ],
] as const

const SPEAKING_CRITERIA = [
  ['fluency_coherence', 'Fluency & Coherence', ''],
  ['lexical_resource', 'Lexical Resource', ''],
  ['grammatical_range', 'Grammar', ''],
  ['pronunciation', 'Pronunciation', ''],
] as const

function CriteriaGrid({
  data,
  sectionType,
  isTask1 = true,
}: {
  data: Record<string, unknown>
  sectionType: string
  isTask1?: boolean
}) {
  const [expandedKey, setExpandedKey] = useState<string | null>(null)

  const writingFirstCriterion = isTask1
    ? WRITING_TASK1_FIRST_CRITERION
    // Backward-compat: if new task_response key missing, fall back to task_achievement
    : ('task_response' in data ? WRITING_TASK2_FIRST_CRITERION : WRITING_TASK1_FIRST_CRITERION)

  const criteriaKeys =
    sectionType === 'writing'
      ? [writingFirstCriterion, ...WRITING_SHARED_CRITERIA]
      : SPEAKING_CRITERIA

  return (
    <div className='grid grid-cols-2 gap-3 sm:grid-cols-4'>
      {criteriaKeys.map(([key, label, descriptor]) => {
        const criterion = data[key] as
          | { band: number; feedback: string }
          | undefined
        if (!criterion) return null
        const isExpanded = expandedKey === key
        return (
          <div
            key={key}
            className='rounded-md border p-3'
          >
            <div className='mb-1 flex items-center justify-between gap-1'>
              <p className='text-xs text-muted-foreground'>{label}</p>
              {descriptor && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <HelpCircle className='size-3 shrink-0 text-muted-foreground/60 hover:text-muted-foreground' />
                  </TooltipTrigger>
                  <TooltipContent className='max-w-xs text-xs'>
                    {descriptor}
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
            <p className='text-center text-lg font-bold'>
              {formatBand(criterion.band)}
            </p>
            <p
              className={cn(
                'mt-1 text-xs text-muted-foreground',
                !isExpanded && 'line-clamp-3',
              )}
            >
              {criterion.feedback}
            </p>
            {criterion.feedback && criterion.feedback.length > 120 && (
              <button
                type='button'
                onClick={() =>
                  setExpandedKey(isExpanded ? null : key)
                }
                className='mt-1 flex items-center gap-0.5 text-xs text-primary hover:underline'
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className='size-3' /> Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className='size-3' /> Show more
                  </>
                )}
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}

function FeedbackList({
  title,
  items,
}: {
  title: string
  items: string[]
}) {
  return (
    <div>
      <p className='mb-1 text-sm font-medium'>{title}</p>
      <ul className='list-inside list-disc space-y-1 text-sm text-muted-foreground'>
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
