import {
  useMemo,
  useRef,
  useState,
  type ComponentType,
  type ReactNode,
} from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from '@tanstack/react-router'
import {
  ArrowLeft,
  BookOpen,
  Headphones,
  Mic,
  PenLine,
  RotateCcw,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  fetchResultDetail,
  finalizeAttempt,
  overrideBand,
  type AnswerRead,
  type AttemptDetailRead,
  type EvaluationJobRead,
  type SpeakingSessionSummary,
} from '@/lib/api/attempts'
import {
  assignSlotNumbers,
  countScoringSlots,
  type Question,
} from '@/features/tests/data/schema'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { TooltipProvider } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import {
  EvaluationProgressCard,
  SectionEvalBadge,
  isJobActive,
  jobPhase,
  showEvalProgress,
} from './evaluation-progress'
import { PracticeResultDetail } from './practice-result-detail'
import {
  CriteriaGrid,
  FeedbackList,
  WritingFeedbackPanel,
} from './writing-feedback-panel'

function AdminHeader() {
  return (
    <Header fixed>
      <Search className='me-auto' />
      <ThemeSwitch />
      <ConfigDrawer />
      <ProfileDropdown />
    </Header>
  )
}

function PageShell({ children }: { children: ReactNode }) {
  const role = useAuthStore((s) => s.auth.user?.role)
  return (
    <>
      {role !== 'student' && <AdminHeader />}
      {children}
    </>
  )
}

function formatBand(band: number | null | undefined): string {
  if (band == null) return '—'
  return band.toFixed(1)
}

function statusLabel(status: string): { label: string; variant: 'default' | 'secondary' | 'outline' } {
  switch (status) {
    case 'fully_scored':
      return { label: 'Fully scored', variant: 'default' }
    case 'auto_scored':
    case 'scored':
      return { label: 'Auto scored', variant: 'default' }
    case 'speaking_in_progress':
      return { label: 'Speaking in progress', variant: 'secondary' }
    case 'completed_without_speaking':
      return { label: 'Completed (no speaking)', variant: 'default' }
    case 'partial':
      return { label: 'Partial', variant: 'outline' }
    case 'completed':
      return { label: 'Scoring writing', variant: 'secondary' }
    case 'abandoned':
      return { label: 'Abandoned', variant: 'outline' }
    default:
      return { label: 'In Progress', variant: 'secondary' }
  }
}

export function ResultDetail() {
  const { attemptId } = useParams({ strict: false }) as { attemptId: string }
  const role = useAuthStore((s) => s.auth.user?.role)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const pollStartedAt = useRef<number | null>(null)

  const { data: attempt, isLoading } = useQuery({
    queryKey: ['results', attemptId],
    queryFn: () => fetchResultDetail(attemptId),
    refetchInterval: (query) => {
      const data = query.state.data
      const pending =
        !!data &&
        data.evaluation_jobs.some(
          (j) => j.status === 'pending' || j.status === 'processing',
        )
      if (!pending) {
        pollStartedAt.current = null
        return false
      }
      if (pollStartedAt.current == null) {
        pollStartedAt.current = Date.now()
      }
      // Burst for the first 30s (writing jobs often finish quickly), then back off.
      return Date.now() - pollStartedAt.current < 30_000 ? 5_000 : 15_000
    },
  })

  if (isLoading) {
    return (
      <PageShell>
        <Main>
          <p className='text-muted-foreground'>Loading...</p>
        </Main>
      </PageShell>
    )
  }

  if (!attempt) {
    return (
      <PageShell>
        <Main>
          <p className='text-muted-foreground'>Attempt not found.</p>
        </Main>
      </PageShell>
    )
  }

  if (attempt.mode !== 'full_mock') {
    return (
      <PageShell>
        <PracticeResultDetail attempt={attempt} />
      </PageShell>
    )
  }

  const status = statusLabel(attempt.status)
  const writingJobs = attempt.evaluation_jobs.filter((j) => j.section_type === 'writing')
  const speakingJobs = attempt.evaluation_jobs.filter((j) => j.section_type === 'speaking')
  const writingActive = isJobActive(writingJobs)
  const speakingActive = isJobActive(speakingJobs)
  const scoringActive = writingActive || speakingActive
  const showWritingProgress = showEvalProgress(writingJobs)
  const showSpeakingProgress = showEvalProgress(speakingJobs)
  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['results', attemptId] })

  return (
    <TooltipProvider>
      <PageShell>
        <Main className='flex flex-1 flex-col gap-6'>
          <div>
            <Button asChild variant='ghost' size='sm' className='mb-3 -ms-3 gap-1.5 rounded-lg text-muted-foreground hover:text-foreground'>
              <Link to={role === 'student' ? '/student/results' : '/results'}>
                <ArrowLeft className='size-4' />
                Back to results
              </Link>
            </Button>

            <div className='overflow-hidden rounded-2xl border border-border bg-card'>
              <div className='relative h-2 bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-600' />
              <div className='flex flex-col gap-4 px-6 py-6 sm:flex-row sm:items-center sm:justify-between'>
                {/* Overall band ring */}
                <div className='relative flex size-28 shrink-0 items-center justify-center'>
                  <svg className='absolute inset-0 size-full -rotate-90'>
                    <circle cx='56' cy='56' r='48' fill='none' className='stroke-muted' strokeWidth='7' />
                    <circle
                      cx='56' cy='56' r='48' fill='none'
                      className='stroke-blue-500 transition-all duration-700'
                      strokeWidth='7'
                      strokeLinecap='round'
                      strokeDasharray={`${attempt.overall_band != null ? (attempt.overall_band / 9) * 301.6 : 0} 301.6`}
                    />
                  </svg>
                  <div className='relative flex flex-col items-center'>
                    <span className='text-2xl font-bold text-foreground'>
                      {scoringActive && attempt.overall_band == null
                        ? '—'
                        : formatBand(attempt.overall_band)}
                    </span>
                    <span className='text-[10px] font-medium uppercase tracking-wider text-muted-foreground'>
                      {scoringActive && attempt.overall_band == null
                        ? 'Pending'
                        : 'Overall'}
                    </span>
                  </div>
                </div>

                <div className='min-w-0 flex-1 space-y-1.5'>
                  <div className='flex flex-wrap items-center gap-2.5'>
                    <h2 className='text-xl font-semibold tracking-tight text-foreground'>
                      {attempt.test_title ?? 'Test Result'}
                    </h2>
                    <Badge variant={status.variant} className='rounded-lg'>{status.label}</Badge>
                  </div>
                  <p className='text-sm text-muted-foreground'>
                    Started{' '}
                    {attempt.started_at
                      ? new Date(attempt.started_at).toLocaleString()
                      : '—'}
                    {attempt.finished_at && (
                      <>
                        {' · Finished '}
                        {new Date(attempt.finished_at).toLocaleString()}
                      </>
                    )}
                  </p>
                  {role === 'student' && attempt.test_id && (
                    <Button
                      variant='outline'
                      size='sm'
                      className='mt-2 gap-1.5 rounded-lg'
                      onClick={() => {
                        navigate({
                          to: '/take-test/$testId',
                          params: { testId: attempt.test_id },
                        })
                      }}
                    >
                      <RotateCcw className='size-3.5' />
                      Retake Test
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {(showWritingProgress || showSpeakingProgress) && (
            <div className='space-y-3'>
              {showWritingProgress && (
                <EvaluationProgressCard jobs={writingJobs} section='writing' />
              )}
              {showSpeakingProgress && (
                <EvaluationProgressCard jobs={speakingJobs} section='speaking' />
              )}
            </div>
          )}

          <Tabs defaultValue='overview' className='gap-4'>
            <TabsList className='h-auto w-full flex-wrap justify-start rounded-xl bg-muted/50 p-1'>
              <TabsTrigger value='overview' className='rounded-lg'>Overview</TabsTrigger>
              <TabsTrigger value='listening' className='rounded-lg'>Listening</TabsTrigger>
              <TabsTrigger value='reading' className='rounded-lg'>Reading</TabsTrigger>
              <TabsTrigger value='writing' className='rounded-lg'>Writing</TabsTrigger>
              <TabsTrigger value='speaking' className='rounded-lg'>Speaking</TabsTrigger>
            </TabsList>

            <TabsContent value='overview'>
              <OverviewTab attempt={attempt} attemptId={attemptId} />
            </TabsContent>
            <TabsContent value='listening'>
              <ObjectiveSectionTab
                title='Listening'
                band={attempt.listening_band}
                raw={attempt.listening_raw}
                sectionType='listening'
                answers={attempt.answers}
                attemptStatus={attempt.status}
              />
            </TabsContent>
            <TabsContent value='reading'>
              <ObjectiveSectionTab
                title='Reading'
                band={attempt.reading_band}
                raw={attempt.reading_raw}
                sectionType='reading'
                answers={attempt.answers}
                attemptStatus={attempt.status}
              />
            </TabsContent>
            <TabsContent value='writing'>
              <WritingTab jobs={writingJobs} onOverride={invalidate} />
            </TabsContent>
            <TabsContent value='speaking'>
              <SpeakingTab
                attempt={attempt}
                attemptId={attemptId}
                jobs={speakingJobs}
                onOverride={invalidate}
              />
            </TabsContent>
          </Tabs>
        </Main>
      </PageShell>
    </TooltipProvider>
  )
}

const TERMINAL_STATUSES = new Set([
  'auto_scored', 'fully_scored', 'completed_without_speaking', 'partial',
])

const SECTION_COLORS: Record<string, { bg: string; icon: string; bar: string }> = {
  Listening: { bg: 'bg-violet-50 dark:bg-violet-950', icon: 'text-violet-600 dark:text-violet-400', bar: 'bg-violet-500' },
  Reading: { bg: 'bg-blue-50 dark:bg-blue-950', icon: 'text-blue-600 dark:text-blue-400', bar: 'bg-blue-500' },
  Writing: { bg: 'bg-emerald-50 dark:bg-emerald-950', icon: 'text-emerald-600 dark:text-emerald-400', bar: 'bg-emerald-500' },
  Speaking: { bg: 'bg-amber-50 dark:bg-amber-950', icon: 'text-amber-600 dark:text-amber-400', bar: 'bg-amber-500' },
}

function BandCard({
  label,
  band,
  raw,
  total,
  icon: Icon,
  cta,
  attemptStatus,
  evalJobs,
}: {
  label: string
  band: number | null
  raw?: number | null
  total?: number | null
  icon: ComponentType<{ className?: string }>
  cta?: React.ReactNode
  attemptStatus?: string
  evalJobs?: EvaluationJobRead[]
}) {
  const isNotAttempted = band == null && attemptStatus && TERMINAL_STATUSES.has(attemptStatus)
  const colors = SECTION_COLORS[label] ?? { bg: 'bg-muted', icon: 'text-muted-foreground', bar: 'bg-primary' }
  const pct = band != null ? (band / 9) * 100 : 0
  const evalPhase = evalJobs ? jobPhase(evalJobs) : 'none'
  const showEval = evalPhase === 'queued' || evalPhase === 'scoring' || evalPhase === 'failed'

  return (
    <div className='rounded-2xl border border-border bg-card p-5 transition-shadow hover:shadow-md'>
      <div className='flex items-center gap-2.5 mb-3'>
        <div className={cn('flex size-9 items-center justify-center rounded-lg', colors.bg)}>
          <Icon className={cn('size-4', colors.icon)} />
        </div>
        <span className='text-sm font-medium text-foreground'>{label}</span>
      </div>
      {isNotAttempted && !showEval ? (
        <Badge variant='outline' className='w-fit text-xs'>Not attempted</Badge>
      ) : showEval ? (
        <SectionEvalBadge jobs={evalJobs ?? []} />
      ) : (
        <>
          <p className='text-3xl font-bold text-foreground'>{formatBand(band)}</p>
          {band != null && (
            <div className='mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted'>
              <div className={cn('h-full rounded-full transition-all duration-500', colors.bar)} style={{ width: `${pct}%` }} />
            </div>
          )}
        </>
      )}
      {!isNotAttempted && !showEval && raw != null && total != null && (
        <p className='mt-2 text-xs text-muted-foreground'>
          {raw}/{total} correct
        </p>
      )}
      {cta}
    </div>
  )
}

function OverviewTab({
  attempt,
  attemptId,
}: {
  attempt: AttemptDetailRead
  attemptId: string
}) {
  const isAdmin = useAuthStore((s) => s.auth.user?.role) === 'admin'
  const queryClient = useQueryClient()
  const finalizeMut = useMutation({
    mutationFn: () => finalizeAttempt(attemptId),
    onSuccess: () => {
      toast.success('Test completed without speaking')
      queryClient.invalidateQueries({ queryKey: ['results', attemptId] })
    },
  })
  const showSpeakingCta = isAdmin && (attempt.status === 'auto_scored' || attempt.status === 'speaking_in_progress')

  return (
    <div className='space-y-6'>
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <BandCard
          label='Listening'
          band={attempt.listening_band}
          raw={attempt.listening_raw}
          total={40}
          icon={Headphones}
          attemptStatus={attempt.status}
        />
        <BandCard
          label='Reading'
          band={attempt.reading_band}
          raw={attempt.reading_raw}
          total={40}
          icon={BookOpen}
          attemptStatus={attempt.status}
        />
        <BandCard label='Writing' band={attempt.writing_band} icon={PenLine} attemptStatus={attempt.status} evalJobs={attempt.evaluation_jobs.filter((j) => j.section_type === 'writing')} />
        <BandCard
          label='Speaking'
          band={attempt.speaking_band}
          icon={Mic}
          attemptStatus={attempt.status}
          evalJobs={attempt.evaluation_jobs.filter((j) => j.section_type === 'speaking')}
          cta={
            showSpeakingCta ? (
              <div className='mt-1 flex flex-col gap-1.5'>
                <Button asChild size='sm' className='w-full'>
                  <Link to='/speaking-examiner' search={{ attemptId }}>
                    Continue to Speaking →
                  </Link>
                </Button>
                <Button
                  size='sm'
                  variant='outline'
                  className='w-full'
                  disabled={finalizeMut.isPending}
                  onClick={() => finalizeMut.mutate()}
                >
                  Complete without Speaking
                </Button>
              </div>
            ) : undefined
          }
        />
      </div>

      <div className='rounded-2xl border border-border bg-card p-6'>
        <h3 className='text-base font-semibold text-foreground'>Overall summary</h3>
        <p className='mt-1 text-sm text-muted-foreground'>
          Available section bands are averaged and rounded to the nearest 0.5
          (IELTS half-up). Speaking is included once scored.
        </p>
        <div className='mt-4 grid gap-3 sm:grid-cols-5'>
          {(
            [
              ['Overall', attempt.overall_band],
              ['Listening', attempt.listening_band],
              ['Reading', attempt.reading_band],
              ['Writing', attempt.writing_band],
              ['Speaking', attempt.speaking_band],
            ] as const
          ).map(([label, band]) => {
            const isOverall = label === 'Overall'
            return (
              <div key={label} className={cn(
                'rounded-xl border p-4 text-center transition-shadow',
                isOverall ? 'bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800' : 'bg-card',
              )}>
                <p className='text-xs text-muted-foreground'>{label}</p>
                <p className={cn(
                  'mt-1 text-xl font-bold',
                  isOverall ? 'text-blue-700 dark:text-blue-400' : 'text-foreground',
                )}>{formatBand(band)}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function ObjectiveSectionTab({
  title,
  band,
  raw,
  sectionType,
  answers,
  attemptStatus,
}: {
  title: string
  band: number | null
  raw: number | null
  sectionType: 'listening' | 'reading'
  answers: AnswerRead[]
  attemptStatus?: string
}) {
  const isNotAttempted = band == null && attemptStatus && TERMINAL_STATUSES.has(attemptStatus)
  const filtered = useMemo(
    () =>
      answers.filter(
        (a) => a.is_correct !== null && a.section?.type === sectionType,
      ),
    [answers, sectionType],
  )
  const displayNumbers = buildDisplayNumbers(filtered)
  const rows = useMemo(
    () =>
      [...filtered].sort((a, b) => {
        const an = parseInt(displayNumbers.get(a.id)?.match(/\d+/)?.[0] ?? '999')
        const bn = parseInt(displayNumbers.get(b.id)?.match(/\d+/)?.[0] ?? '999')
        return an - bn
      }),
    [filtered, displayNumbers],
  )

  if (isNotAttempted) {
    return (
      <Card>
        <CardContent className='py-8 text-center'>
          <Badge variant='outline' className='text-sm'>Not attempted</Badge>
          <p className='mt-2 text-sm text-muted-foreground'>
            This section was not attempted during the test.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className='flex flex-wrap items-baseline gap-2 text-base'>
          <span>
            {title} Band {formatBand(band)}
          </span>
          {raw != null && (
            <span className='text-sm font-normal text-muted-foreground'>
              ({raw}/40 correct)
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className='text-sm text-muted-foreground'>No scored answers for this section.</p>
        ) : (
          <div className='overflow-hidden rounded-lg border'>
            <Table>
              <TableHeader>
                <TableRow className='bg-muted/50 hover:bg-muted/50'>
                  <TableHead className='h-9 w-24 text-xs font-medium tracking-wide text-muted-foreground uppercase'>
                    Question
                  </TableHead>
                  <TableHead className='h-9 text-xs font-medium tracking-wide text-muted-foreground uppercase'>
                    My Answer
                  </TableHead>
                  <TableHead className='h-9 text-xs font-medium tracking-wide text-muted-foreground uppercase'>
                    Correct Answer
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((a) => {
                  const studentAnswer = formatStudentAnswer(a.response)
                  const skipped = studentAnswer === '(no answer)'
                  const correct = a.is_correct === true
                  const correctAnswer = formatCorrectAnswer(a.question?.answer_key ?? null)

                  return (
                    <TableRow
                      key={a.id}
                      className={cn(
                        'border-l-4 border-b-background/60',
                        correct &&
                          'border-l-green-500 bg-green-50 hover:bg-green-50 dark:bg-green-950/30 dark:hover:bg-green-950/30',
                        !correct &&
                          !skipped &&
                          'border-l-red-500 bg-red-50 hover:bg-red-50 dark:bg-red-950/30 dark:hover:bg-red-950/30',
                        skipped &&
                          'border-l-amber-500 bg-amber-50 hover:bg-amber-50 dark:bg-amber-950/30 dark:hover:bg-amber-950/30',
                      )}
                    >
                      <TableCell className='py-2 font-medium text-muted-foreground tabular-nums'>
                        {displayNumbers.get(a.id) ?? String(a.question?.order ?? '?')}
                      </TableCell>
                      <TableCell
                        className={cn(
                          'py-2 font-medium',
                          skipped && 'text-muted-foreground',
                        )}
                      >
                        {skipped ? '—' : studentAnswer}
                      </TableCell>
                      <TableCell
                        className={cn(
                          'py-2',
                          correctAnswer
                            ? 'font-medium text-green-700 dark:text-green-400'
                            : 'text-muted-foreground',
                        )}
                      >
                        {correctAnswer || '—'}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function WritingTab({
  jobs,
  onOverride,
}: {
  jobs: EvaluationJobRead[]
  onOverride: () => void
}) {
  const isAdmin = useAuthStore((s) => s.auth.user?.role) === 'admin'
  const job = jobs.find((j) => j.status === 'done') ?? jobs[0]
  const phase = jobPhase(jobs)
  return (
    <div className='space-y-4'>
      {isAdmin && job && <EvaluationJobHeader job={job} onOverride={onOverride} />}
      {(phase === 'queued' || phase === 'scoring' || phase === 'failed') && (
        <EvaluationProgressCard jobs={jobs} section='writing' />
      )}
      <WritingFeedbackPanel jobs={jobs} />
    </div>
  )
}

function SpeakingTab({
  attempt,
  attemptId,
  jobs,
  onOverride,
}: {
  attempt: AttemptDetailRead
  attemptId: string
  jobs: EvaluationJobRead[]
  onOverride: () => void
}) {
  const isAdmin = useAuthStore((s) => s.auth.user?.role) === 'admin'
  const queryClient = useQueryClient()
  const finalizeMut = useMutation({
    mutationFn: () => finalizeAttempt(attemptId),
    onSuccess: () => {
      toast.success('Test completed without speaking')
      queryClient.invalidateQueries({ queryKey: ['results', attemptId] })
    },
  })

  const session: SpeakingSessionSummary | null | undefined = attempt.speaking_session
  const hasBand = attempt.speaking_band != null && attempt.speaking_band > 0
  const job = jobs.find((j) => j.status === 'done') ?? jobs[0]
  const scoreJson =
    (job?.result as Record<string, unknown> | null) ??
    session?.score_json ??
    null
  const speakingPhase = jobPhase(jobs)

  if (speakingPhase === 'queued' || speakingPhase === 'scoring' || speakingPhase === 'failed') {
    return <EvaluationProgressCard jobs={jobs} section='speaking' />
  }

  if (hasBand || scoreJson) {
    return (
      <div className='space-y-4'>
        <Card>
          <CardHeader>
            <CardTitle className='text-base'>
              Speaking Band {formatBand(attempt.speaking_band ?? session?.overall_band)}
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            {scoreJson && (
              <CriteriaGrid data={scoreJson} sectionType='speaking' />
            )}
            {Array.isArray(scoreJson?.strengths) && (
              <FeedbackList
                title='Strengths'
                items={scoreJson.strengths as string[]}
              />
            )}
            {Array.isArray(scoreJson?.improvements) && (
              <FeedbackList
                title='Areas for Improvement'
                items={scoreJson.improvements as string[]}
              />
            )}
            {typeof scoreJson?.transcript === 'string' && scoreJson.transcript && (
              <div>
                <p className='mb-1 text-sm font-medium'>Transcript</p>
                <p className='whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm'>
                  {scoreJson.transcript as string}
                </p>
              </div>
            )}
            {session?.history_json && session.history_json.length > 0 && (
              <div>
                <p className='mb-2 text-sm font-medium'>Conversation</p>
                <div className='max-h-80 space-y-2 overflow-y-auto rounded-md border p-3'>
                  {session.history_json.map((turn, i) => (
                    <div key={i} className='text-sm'>
                      <span className='font-semibold capitalize'>{turn.role}: </span>
                      <span className='text-muted-foreground'>{turn.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {isAdmin && job && <EvaluationJobHeader job={job} onOverride={onOverride} />}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (session && session.status === 'in_progress') {
    return (
      <Card>
        <CardContent className='flex flex-col items-start gap-4 py-10'>
          <div>
            <h3 className='text-lg font-semibold'>Speaking test in progress</h3>
            <p className='mt-1 text-sm text-muted-foreground'>
              {isAdmin
                ? 'The student has an active AI examiner session.'
                : 'Resume your AI examiner session to finish and receive a band score.'}
            </p>
          </div>
          {isAdmin && (
            <Button asChild>
              <Link to='/speaking-examiner' search={{ attemptId }}>
                Resume Session →
              </Link>
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  const showFinalize = isAdmin && (attempt.status === 'auto_scored' || attempt.status === 'speaking_in_progress')

  return (
    <Card>
      <CardContent className='flex flex-col items-start gap-4 py-10'>
        <div className='max-w-lg space-y-2'>
          <h3 className='text-lg font-semibold'>Speaking test not started</h3>
          <p className='text-sm text-muted-foreground'>
            {isAdmin
              ? 'The speaking section has not been taken yet.'
              : 'The speaking section is not available in this view.'}
          </p>
        </div>
        {isAdmin && (
          <div className='flex flex-wrap gap-2'>
            <Button asChild>
              <Link to='/speaking-examiner' search={{ attemptId }}>
                Continue to Speaking →
              </Link>
            </Button>
            {showFinalize && (
              <Button
                variant='outline'
                disabled={finalizeMut.isPending}
                onClick={() => finalizeMut.mutate()}
              >
                Complete without Speaking
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function EvaluationJobHeader({
  job,
  onOverride,
}: {
  job: EvaluationJobRead
  onOverride: () => void
}) {
  const isAdmin = useAuthStore((s) => s.auth.user?.role) === 'admin'
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

  return (
    <Card>
      <CardContent className='flex flex-wrap items-center justify-between gap-4 py-4'>
        <div>
          <p className='text-xs text-muted-foreground'>AI Band</p>
          <p className='text-2xl font-bold'>{formatBand(job.band_score)}</p>
          <Badge variant='secondary' className='mt-1 capitalize'>
            {job.status}
          </Badge>
        </div>
        {isAdmin && (
          <div className='flex items-end gap-2'>
            <div>
              <p className='mb-1 text-xs text-muted-foreground'>Teacher override</p>
              <Input
                type='number'
                min={0}
                max={9}
                step={0.5}
                className='w-24'
                value={overrideValue}
                onChange={(e) => setOverrideValue(e.target.value)}
              />
            </div>
            <Button
              size='sm'
              disabled={mutation.isPending || overrideValue === ''}
              onClick={() => mutation.mutate()}
            >
              Save
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
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
  if (!answerKey) return ''
  // Gap fill / sentence completion / short answer use accepted_answers
  const accepted = answerKey.accepted_answers
  if (Array.isArray(accepted) && accepted.length > 0) {
    return accepted.join(' | ')
  }
  const correct = answerKey.correct ?? answerKey.answer
  // Legacy matching/map_labeling: {"answers": ["A", "B", ...]}
  if (correct == null) {
    const legacy = answerKey.answers
    if (Array.isArray(legacy) && legacy.length > 0) {
      return legacy.join(' | ')
    }
    return ''
  }
  if (Array.isArray(correct)) {
    const sorted = [...correct].sort()
    return sorted.length > 0 ? sorted.join(' | ') : ''
  }
  if (typeof correct === 'object' && correct !== null) {
    return Object.entries(correct as Record<string, unknown>)
      .map(([_k, v]) => String(v))
      .join(' | ')
  }
  return String(correct)
}

function snapshotAsQuestion(
  q: NonNullable<AnswerRead['question']>,
): Question {
  return {
    id: q.id,
    section_id: q.section_id,
    question_group_id: q.question_group_id ?? null,
    order: q.order,
    question_type: q.question_type as Question['question_type'],
    content: q.content,
    answer_key: q.answer_key,
    task_number: q.task_number ?? null,
    min_words: null,
    image_url: null,
    essay_type: null,
    computed_number: q.computed_number ?? null,
    computed_number_end: q.computed_number_end ?? null,
    created_at: '',
    updated_at: '',
  }
}

/** IELTS display numbers (Listening 1–40, Reading cumulative across passages). */
function buildDisplayNumbers(answers: AnswerRead[]): Map<string, string> {
  const map = new Map<string, string>()
  const bySection = new Map<string, AnswerRead[]>()
  for (const a of answers) {
    if (a.is_correct === null || !a.section || !a.question) continue
    const list = bySection.get(a.section.id) ?? []
    list.push(a)
    bySection.set(a.section.id, list)
  }

  const sections = Array.from(bySection.entries()).sort(([, a], [, b]) => {
    const ao = a[0]?.section?.order ?? 999
    const bo = b[0]?.section?.order ?? 999
    return ao - bo
  })

  let readingOffset = 0
  for (const [, sectionAnswers] of sections) {
    const sec = sectionAnswers[0]?.section
    if (!sec) continue
    const qs = sectionAnswers
      .map((a) => a.question)
      .filter((q): q is NonNullable<typeof q> => q != null)
      .map(snapshotAsQuestion)
      .sort((a, b) => {
        const aN = a.computed_number ?? a.order
        const bN = b.computed_number ?? b.order
        return aN - bN
      })

    // Dedupe by question id (defensive)
    const seen = new Set<string>()
    const uniqueQs = qs.filter((q) => {
      if (seen.has(q.id)) return false
      seen.add(q.id)
      return true
    })

    const useComputed = uniqueQs.every(
      (q) => typeof q.computed_number === 'number' && q.computed_number >= 1,
    )

    let ranges: Map<string, { start: number; end: number }>
    if (useComputed) {
      ranges = new Map(
        uniqueQs.map((q) => {
          const start = q.computed_number as number
          const end =
            typeof q.computed_number_end === 'number'
              ? q.computed_number_end
              : start
          return [q.id, { start, end }]
        }),
      )
      if (sec.type === 'reading') {
        readingOffset += countScoringSlots(uniqueQs)
      }
    } else if (sec.type === 'listening') {
      ranges = assignSlotNumbers(uniqueQs, (sec.order - 1) * 10)
    } else if (sec.type === 'reading') {
      ranges = assignSlotNumbers(uniqueQs, readingOffset)
      readingOffset += countScoringSlots(uniqueQs)
    } else {
      ranges = new Map(
        uniqueQs.map((q) => [q.id, { start: q.order, end: q.order }]),
      )
    }

    for (const a of sectionAnswers) {
      const qid = a.question?.id
      if (!qid) continue
      const range = ranges.get(qid)
      if (!range) {
        map.set(a.id, String(a.question?.order ?? '?'))
        continue
      }
      map.set(
        a.id,
        range.end !== range.start
          ? `${range.start}–${range.end}`
          : String(range.start),
      )
    }
  }
  return map
}
