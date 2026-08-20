import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BookOpen, Timer } from 'lucide-react'
import { EmptyState } from '@/components/report'
import { Button } from '@/components/ui/button'
import { getDashboard, type DashboardAttempt } from '@/lib/api/student'
import {
  fetchPracticeResults,
  type PracticeResultRow,
} from '@/lib/api/practice'
import { SKILL_META, type SkillKey } from '@/features/results/lib/skill'
import { useAuthStore } from '@/stores/auth-store'
import { AttemptList, type AttemptRowItem } from './components/attempt-list'
import { DashboardHero } from './components/dashboard-hero'
import { DashboardSkeleton } from './components/dashboard-skeleton'
import { ResumeBanner } from './components/resume-banner'
import { SkillsPanel } from './components/skills-panel'

function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
  })
}

function recentRows(attempts: DashboardAttempt[]): AttemptRowItem[] {
  return attempts.map((attempt) => ({
    id: attempt.id,
    title: attempt.test_title,
    subtitle: formatShortDate(attempt.finished_at ?? attempt.created_at),
    band: attempt.overall_band,
    fallback: attempt.status === 'completed' ? 'Evaluating' : attempt.status,
  }))
}

function practiceRows(rows: PracticeResultRow[]): AttemptRowItem[] {
  return rows.slice(0, 5).map((row) => {
    const skill = row.section_type
    const skillLabel = skill ? SKILL_META[skill as SkillKey].label : 'Practice'
    const scopeLabel =
      row.scope === 'section'
        ? `Full ${skillLabel}`
        : row.part_number != null
          ? `${skillLabel} · Part ${row.part_number}`
          : skillLabel
    return {
      id: row.id,
      title: row.test_title,
      subtitle: `${scopeLabel} · ${formatShortDate(row.finished_at ?? row.created_at)}`,
      band: row.band,
      fallback:
        row.correct != null && row.total != null
          ? `${row.correct}/${row.total}`
          : row.status,
    }
  })
}

export function StudentDashboard() {
  const firstName =
    useAuthStore((s) => s.auth.user?.full_name ?? s.auth.user?.name) ?? 'Student'
  const signedIn = useAuthStore((s) => Boolean(s.auth.accessToken))
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: getDashboard,
    enabled: signedIn,
  })
  const practiceQuery = useQuery({
    queryKey: ['student-practice-results'],
    queryFn: fetchPracticeResults,
    enabled: signedIn,
  })

  if (isLoading) return <DashboardSkeleton />

  if (isError) {
    return (
      <EmptyState
        title='Could not load your dashboard'
        description='Please try again in a moment.'
        action={
          <Button className='rounded-lg' onClick={() => void refetch()}>
            Retry
          </Button>
        }
      />
    )
  }

  const hasAttempts = (data?.tests_taken ?? 0) > 0
  const practice = Array.isArray(practiceQuery.data) ? practiceQuery.data : []
  const recent = Array.isArray(data?.recent) ? data.recent : []

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-2xl font-semibold tracking-tight text-foreground'>
          Welcome back, {firstName}
        </h1>
        <p className='mt-1 text-sm text-muted-foreground'>
          Your IELTS progress overview
        </p>
      </div>

      {data?.in_progress && <ResumeBanner attempt={data.in_progress} />}

      {hasAttempts && data ? (
        <>
          <DashboardHero data={data} />
          {data.section_bands && <SkillsPanel bands={data.section_bands} />}
        </>
      ) : (
        <EmptyState
          icon={BookOpen}
          title='Take your first IELTS test'
          description='Complete a practice test to see your band score, progress trend, and section breakdown.'
          action={
            <Button asChild className='rounded-lg'>
              <Link to='/student/tests'>
                Browse Tests
                <ArrowRight className='ml-1.5 size-3.5' />
              </Link>
            </Button>
          }
        />
      )}

      <AttemptList
        title='Practice'
        icon={<Timer className='size-3.5 text-muted-foreground' />}
        rows={practiceRows(practice)}
        viewAllTo='/student/tests'
        viewAllLabel='Practise more'
      />

      <AttemptList
        title='Recent attempts'
        rows={recentRows(recent)}
        viewAllTo='/student/results'
      />
    </div>
  )
}
