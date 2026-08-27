import { useRef, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams, useSearch } from '@tanstack/react-router'
import { ArrowLeft, FileQuestion } from 'lucide-react'
import { toast } from 'sonner'
import { fetchResultDetail, finalizeAttempt } from '@/lib/api/attempts'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent } from '@/components/ui/tabs'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useAuthStore } from '@/stores/auth-store'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { EvaluationProgressCard, isJobActive, showEvalProgress } from './evaluation-progress'
import { PracticeResultDetail } from './practice-result-detail'
import { AnswerReviewPanel } from './components/answer-review-panel'
import { OverviewPanel } from './components/overview-panel'
import { ResultDetailSkeleton } from './components/result-detail-skeleton'
import { ResultEmptyState } from './components/result-empty-state'
import { ResultErrorState } from './components/result-error-state'
import { ResultNav } from './components/result-nav'
import { ScoreSummary } from './components/score-summary'
import { SpeakingReportPanel } from './components/speaking-report-panel'
import { WritingReportPanel } from './components/writing-report-panel'
import { RESULT_TABS, type ResultTab } from './lib/tabs'

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

export function ResultDetail() {
  const { attemptId } = useParams({ strict: false }) as { attemptId: string }
  const search = useSearch({ strict: false }) as {
    tab?: ResultTab
  }
  const tab = search.tab ?? 'overview'
  const role = useAuthStore((s) => s.auth.user?.role)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const pollStartedAt = useRef<number | null>(null)

  const { data: attempt, isLoading, isError, refetch } = useQuery({
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
      return Date.now() - pollStartedAt.current < 30_000 ? 5_000 : 15_000
    },
  })

  const finalizeMut = useMutation({
    mutationFn: () => finalizeAttempt(attemptId),
    onSuccess: () => {
      toast.success('Test completed without speaking')
      void queryClient.invalidateQueries({ queryKey: ['results', attemptId] })
    },
  })

  if (isLoading) {
    return (
      <PageShell>
        <Main>
          <ResultDetailSkeleton />
        </Main>
      </PageShell>
    )
  }

  if (isError) {
    return (
      <PageShell>
        <Main>
          <ResultErrorState onRetry={() => void refetch()} />
        </Main>
      </PageShell>
    )
  }

  if (!attempt) {
    return (
      <PageShell>
        <Main>
          <ResultEmptyState
            icon={FileQuestion}
            title='Attempt not found'
            description='This result is unavailable or the link is no longer valid.'
          />
        </Main>
      </PageShell>
    )
  }

  const answers = Array.isArray(attempt.answers) ? attempt.answers : []
  const evaluationJobs = Array.isArray(attempt.evaluation_jobs)
    ? attempt.evaluation_jobs
    : []
  const report = { ...attempt, answers, evaluation_jobs: evaluationJobs }

  if (report.mode !== 'full_mock') {
    return (
      <PageShell>
        <PracticeResultDetail attempt={report} />
      </PageShell>
    )
  }

  const writingJobs = evaluationJobs.filter((j) => j.section_type === 'writing')
  const speakingJobs = evaluationJobs.filter((j) => j.section_type === 'speaking')
  const writingActive = isJobActive(writingJobs)
  const speakingActive = isJobActive(speakingJobs)
  const scoringActive = writingActive || speakingActive
  const showWritingProgress = showEvalProgress(writingJobs)
  const showSpeakingProgress = showEvalProgress(speakingJobs)
  const isAdmin = role === 'admin'
  const showSpeakingCta =
    isAdmin &&
    (report.status === 'auto_scored' || report.status === 'speaking_in_progress')

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['results', attemptId] })

  const setTab = (next: string) => {
    const value = (RESULT_TABS as readonly string[]).includes(next)
      ? (next as ResultTab)
      : 'overview'
    void navigate({
      to: '.',
      search: (prev) => ({ ...prev, tab: value }),
      replace: true,
    })
  }

  const finalizeButton = showSpeakingCta ? (
    <Button
      size='sm'
      variant='outline'
      className='rounded-lg'
      disabled={finalizeMut.isPending}
      onClick={() => finalizeMut.mutate()}
    >
      Complete without Speaking
    </Button>
  ) : null

  return (
    <TooltipProvider>
      <PageShell>
        <Main className='flex flex-1 flex-col gap-6'>
          <div>
            <Button
              asChild
              variant='ghost'
              size='sm'
              className='mb-3 -ms-3 gap-1.5 rounded-lg text-muted-foreground hover:text-foreground'
            >
              <Link to={role === 'student' ? '/student/results' : '/results'}>
                <ArrowLeft className='size-4' />
                Back to results
              </Link>
            </Button>
            <ScoreSummary
              attempt={report}
              scoringActive={scoringActive}
              showRetake={role === 'student' && !!report.test_id}
              showSpeakingCta={showSpeakingCta}
              onRetake={() => {
                void navigate({
                  to: '/take-test/$testId',
                  params: { testId: report.test_id },
                })
              }}
              onFinalize={() => finalizeMut.mutate()}
              finalizePending={finalizeMut.isPending}
            />
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

          <Tabs value={tab} onValueChange={setTab} className='gap-4'>
            <ResultNav attempt={report} role={role} />

            <TabsContent value='overview'>
              <OverviewPanel attempt={report} />
            </TabsContent>
            <TabsContent value='listening'>
              <AnswerReviewPanel
                skill='listening'
                band={report.listening_band}
                raw={report.listening_raw}
                answers={report.answers}
                attemptStatus={report.status}
              />
            </TabsContent>
            <TabsContent value='reading'>
              <AnswerReviewPanel
                skill='reading'
                band={report.reading_band}
                raw={report.reading_raw}
                answers={report.answers}
                attemptStatus={report.status}
              />
            </TabsContent>
            <TabsContent value='writing'>
              <WritingReportPanel
                jobs={writingJobs}
                isAdmin={isAdmin}
                onOverride={invalidate}
              />
            </TabsContent>
            <TabsContent value='speaking'>
              <SpeakingReportPanel
                attempt={report}
                attemptId={attemptId}
                jobs={speakingJobs}
                isAdmin={isAdmin}
                onOverride={invalidate}
                finalizeAction={finalizeButton}
              />
            </TabsContent>
          </Tabs>
        </Main>
      </PageShell>
    </TooltipProvider>
  )
}
