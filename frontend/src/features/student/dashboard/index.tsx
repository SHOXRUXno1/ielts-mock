import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  BookOpen,
  ChevronRight,
  Clock,
  Headphones,
  Mic,
  PenLine,
  PlayCircle,
  Sparkles,
  Timer,
  TrendingUp,
  Trophy,
} from 'lucide-react'
import { getDashboard, type DashboardResponse } from '@/lib/api/student'
import {
  fetchPracticeResults,
  type PracticeResultRow,
} from '@/lib/api/practice'
import type { SectionType } from '@/features/tests/data/schema'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

const PRACTICE_TYPE_LABEL: Record<SectionType, string> = {
  listening: 'Listening',
  reading: 'Reading',
  writing: 'Writing',
  speaking: 'Speaking',
}

const SECTION_META: {
  key: keyof DashboardResponse['section_bands']
  label: string
  icon: React.ElementType
  color: string
  bg: string
}[] = [
  { key: 'listening', label: 'Listening', icon: Headphones, color: 'text-violet-600 dark:text-violet-400', bg: 'bg-violet-500' },
  { key: 'reading', label: 'Reading', icon: BookOpen, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-500' },
  { key: 'writing', label: 'Writing', icon: PenLine, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-500' },
  { key: 'speaking', label: 'Speaking', icon: Mic, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-500' },
]

function BandRing({ band }: { band: number | null }) {
  const pct = band != null ? (band / 9) * 100 : 0
  return (
    <div className='relative flex size-36 shrink-0 items-center justify-center'>
      {/* Background ring */}
      <svg className='absolute inset-0 size-full -rotate-90'>
        <circle cx='72' cy='72' r='62' fill='none' className='stroke-muted' strokeWidth='8' />
        <circle
          cx='72' cy='72' r='62' fill='none'
          className='stroke-blue-500 transition-all duration-700'
          strokeWidth='8'
          strokeLinecap='round'
          strokeDasharray={`${pct * 3.89} 389`}
        />
      </svg>
      <div className='flex flex-col items-center'>
        <span className='text-3xl font-bold text-foreground'>
          {band != null ? band.toFixed(1) : '—'}
        </span>
        <span className='text-[11px] font-medium uppercase tracking-wider text-muted-foreground'>
          Overall
        </span>
      </div>
    </div>
  )
}

function BandTrend({ points }: { points: DashboardResponse['band_trend'] }) {
  if (!Array.isArray(points) || points.length < 2) {
    return (
      <div className='flex h-full items-center justify-center text-sm text-muted-foreground'>
        <span className='text-center'>Complete more tests to see your trend</span>
      </div>
    )
  }

  const width = 560
  const height = 110
  const pad = 16
  const xs = points.map(
    (_, i) => pad + (i * (width - pad * 2)) / Math.max(1, points.length - 1),
  )
  const ys = points.map((p) => {
    const pct = Math.max(0, Math.min(1, Number(p.band ?? 0) / 9))
    return height - pad - pct * (height - pad * 2)
  })
  const line = xs
    .map((x, i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${ys[i].toFixed(1)}`)
    .join(' ')

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className='h-[110px] w-full'
      role='img'
      aria-label='Band progress'
    >
      <path d={line} fill='none' stroke='#3b82f6' strokeWidth='2.5' />
      {xs.map((x, i) => (
        <circle key={i} cx={x} cy={ys[i]} r='3.5' fill='#3b82f6' />
      ))}
    </svg>
  )
}

function SectionBar({
  label,
  icon: Icon,
  band,
  color,
  barColor,
}: {
  label: string
  icon: React.ElementType
  band: number | null
  color: string
  barColor: string
}) {
  const pct = band != null ? (band / 9) * 100 : 0
  return (
    <div className='flex items-center gap-3'>
      <div className='flex w-28 items-center gap-2.5'>
        <div className={cn('flex size-7 items-center justify-center rounded-md', color.replace('text-', 'bg-').replace('dark:', '').split(' ')[0] + '/10')}>
          <Icon size={14} className={color} />
        </div>
        <span className='text-sm text-foreground'>{label}</span>
      </div>
      <div className='relative h-2.5 flex-1 overflow-hidden rounded-full bg-muted'>
        {band != null && (
          <div
            className={cn('absolute inset-y-0 left-0 rounded-full transition-all duration-500', barColor)}
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
      <span className='w-9 text-right text-sm font-semibold tabular-nums text-foreground'>
        {band != null ? band.toFixed(1) : '—'}
      </span>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className='space-y-6'>
      <Skeleton className='h-10 w-64' />
      <div className='grid grid-cols-1 gap-4 sm:grid-cols-3'>
        <Skeleton className='h-24 rounded-2xl' />
        <Skeleton className='h-24 rounded-2xl' />
        <Skeleton className='h-24 rounded-2xl' />
      </div>
      <Skeleton className='h-52 rounded-2xl' />
      <Skeleton className='h-36 rounded-2xl' />
    </div>
  )
}

function PracticeBlock({ rows }: { rows: PracticeResultRow[] }) {
  if (rows.length === 0) return null
  return (
    <div>
      <div className='mb-3 flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          <Timer size={14} className='text-muted-foreground' />
          <h3 className='text-sm font-medium text-muted-foreground'>Practice</h3>
        </div>
        <Button
          asChild
          variant='ghost'
          size='sm'
          className='h-7 text-xs text-muted-foreground hover:text-foreground'
        >
          <Link to='/student/tests'>
            Practise more
            <ChevronRight size={14} className='ml-0.5' />
          </Link>
        </Button>
      </div>
      <div className='space-y-2'>
        {rows.slice(0, 5).map((a) => {
          const skill = a.section_type
            ? PRACTICE_TYPE_LABEL[a.section_type]
            : 'Practice'
          const scopeLabel =
            a.scope === 'section'
              ? `Full ${skill}`
              : a.part_number != null
                ? `${skill} · Part ${a.part_number}`
                : skill
          return (
            <Link
              key={a.id}
              to='/student/results/$attemptId'
              params={{ attemptId: a.id }}
              className='group flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3.5 transition-all hover:border-blue-200 hover:shadow-md dark:hover:border-blue-800/50'
            >
              <div className='min-w-0'>
                <p className='truncate text-sm font-medium text-foreground transition-colors group-hover:text-blue-700 dark:group-hover:text-blue-400'>
                  {a.test_title}
                </p>
                <p className='mt-0.5 text-xs text-muted-foreground'>
                  {scopeLabel}
                  <span className='mx-1.5 text-muted-foreground/40'>·</span>
                  {(a.finished_at
                    ? new Date(a.finished_at)
                    : new Date(a.created_at)
                  ).toLocaleDateString('en-GB', {
                    day: 'numeric',
                    month: 'short',
                  })}
                </p>
              </div>
              <div className='flex items-center gap-2.5'>
                {a.band != null ? (
                  <span className='rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-950 dark:text-blue-400'>
                    Band {a.band.toFixed(1)}
                  </span>
                ) : a.correct != null && a.total != null ? (
                  <span className='rounded-lg bg-muted px-2.5 py-1 text-xs font-semibold tabular-nums'>
                    {a.correct}/{a.total}
                  </span>
                ) : (
                  <Badge variant='secondary' className='text-xs'>
                    {a.status}
                  </Badge>
                )}
                <ChevronRight
                  size={16}
                  className='text-muted-foreground/50 transition-colors group-hover:text-blue-500'
                />
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

export function StudentDashboard() {
  const firstName =
    useAuthStore((s) => s.auth.user?.full_name ?? s.auth.user?.name) ?? 'Student'
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: getDashboard,
  })
  const practiceQuery = useQuery({
    queryKey: ['student-practice-results'],
    queryFn: fetchPracticeResults,
  })

  if (isLoading) return <DashboardSkeleton />

  if (isError) {
    return (
      <div className='flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed bg-muted/20 py-16 text-center'>
        <p className='text-base font-medium text-foreground'>
          Could not load your dashboard
        </p>
        <p className='max-w-sm text-sm text-muted-foreground'>
          Please try again in a moment.
        </p>
        <Button className='mt-2 rounded-lg' onClick={() => void refetch()}>
          Retry
        </Button>
      </div>
    )
  }

  const hasAttempts = (data?.tests_taken ?? 0) > 0
  const practiceRows = Array.isArray(practiceQuery.data) ? practiceQuery.data : []
  const recentRows = Array.isArray(data?.recent) ? data.recent : []

  return (
    <div className='space-y-6'>
      {/* Welcome */}
      <div>
        <h1 className='text-xl font-semibold tracking-tight text-foreground'>
          Welcome back, {firstName}
        </h1>
        <p className='mt-0.5 text-sm text-muted-foreground'>
          Your IELTS progress overview
        </p>
      </div>

      {/* Quick stats row */}
      {hasAttempts && data && (
        <div className='grid grid-cols-1 gap-3 sm:grid-cols-3'>
          <div className='flex items-center gap-3.5 rounded-2xl border border-border bg-card p-4 transition-shadow hover:shadow-md'>
            <div className='flex size-11 items-center justify-center rounded-xl bg-blue-50 dark:bg-blue-950'>
              <BookOpen size={20} className='text-blue-600 dark:text-blue-400' />
            </div>
            <div>
              <p className='text-2xl font-bold text-foreground'>{data.tests_taken}</p>
              <p className='text-xs text-muted-foreground'>Tests Taken</p>
            </div>
          </div>
          <div className='flex items-center gap-3.5 rounded-2xl border border-border bg-card p-4 transition-shadow hover:shadow-md'>
            <div className='flex size-11 items-center justify-center rounded-xl bg-amber-50 dark:bg-amber-950'>
              <TrendingUp size={20} className='text-amber-600 dark:text-amber-400' />
            </div>
            <div>
              <p className='text-2xl font-bold text-foreground'>
                {data.avg_band != null ? data.avg_band.toFixed(1) : '—'}
              </p>
              <p className='text-xs text-muted-foreground'>Average Band</p>
            </div>
          </div>
          <div className='flex items-center gap-3.5 rounded-2xl border border-border bg-card p-4 transition-shadow hover:shadow-md'>
            <div className='flex size-11 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-950'>
              <Trophy size={20} className='text-emerald-600 dark:text-emerald-400' />
            </div>
            <div>
              <p className='text-2xl font-bold text-foreground'>
                {data.best_band != null ? data.best_band.toFixed(1) : '—'}
              </p>
              <p className='text-xs text-muted-foreground'>Best Score</p>
            </div>
          </div>
        </div>
      )}

      {/* Continue test widget */}
      {data?.in_progress && (
        <div className='overflow-hidden rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 dark:border-amber-800/50 dark:from-amber-950/50 dark:to-orange-950/50'>
          <div className='flex items-center gap-4 p-5'>
            <div className='flex size-12 shrink-0 items-center justify-center rounded-xl bg-amber-100 dark:bg-amber-900'>
              <PlayCircle size={24} className='text-amber-600 dark:text-amber-400' />
            </div>
            <div className='min-w-0 flex-1'>
              <p className='text-sm font-semibold text-foreground'>
                Continue where you left off
              </p>
              <p className='mt-0.5 truncate text-xs text-muted-foreground'>
                {data.in_progress.test_title} · {data.in_progress.answered}/{data.in_progress.total} questions answered
              </p>
              <div className='mt-2 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-amber-200/50 dark:bg-amber-800/30'>
                <div
                  className='h-full rounded-full bg-amber-500 transition-all'
                  style={{
                    width: `${data.in_progress.total > 0 ? (data.in_progress.answered / data.in_progress.total) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
            <Button
              asChild
              size='sm'
              className='shrink-0 rounded-lg bg-amber-600 text-white shadow-sm hover:bg-amber-700 dark:bg-amber-600 dark:hover:bg-amber-500'
            >
              <Link
                to='/take-test/$testId'
                params={{ testId: data.in_progress.test_id }}
                search={{ resume: data.in_progress.id }}
              >
                Continue
                <ArrowRight size={14} className='ml-1.5' />
              </Link>
            </Button>
          </div>
        </div>
      )}

      {/* Band ring + trend chart */}
      {hasAttempts ? (
        <div className='rounded-2xl border border-border bg-card p-6'>
          <div className='mb-4 flex items-center gap-2'>
            <Sparkles size={14} className='text-blue-500' />
            <h3 className='text-sm font-medium text-muted-foreground'>Band Progress</h3>
          </div>
          <div className='flex flex-col gap-6 sm:flex-row sm:items-center'>
            <BandRing band={data?.avg_band ?? null} />
            <div className='min-w-0 flex-1'>
              <p className='mb-2 text-xs text-muted-foreground'>
                Last {data?.band_trend?.length ?? 0} attempts
              </p>
              <BandTrend points={data?.band_trend ?? []} />
            </div>
          </div>
        </div>
      ) : (
        <div className='flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed bg-muted/20 py-16 text-center'>
          <div className='flex size-14 items-center justify-center rounded-2xl bg-blue-50 dark:bg-blue-950'>
            <BookOpen className='size-7 text-blue-500 dark:text-blue-400' />
          </div>
          <p className='text-base font-medium text-foreground'>
            Take your first IELTS test
          </p>
          <p className='max-w-sm text-sm text-muted-foreground'>
            Complete a practice test to see your band score, progress trend, and section breakdown.
          </p>
          <Button asChild className='mt-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700'>
            <Link to='/student/tests'>
              Browse Tests
              <ArrowRight size={14} className='ml-1.5' />
            </Link>
          </Button>
        </div>
      )}

      {/* Section breakdown */}
      {hasAttempts && data?.section_bands && (
        <div className='rounded-2xl border border-border bg-card p-6'>
          <h3 className='mb-4 text-sm font-medium text-muted-foreground'>
            Section Averages
          </h3>
          <div className='space-y-3.5'>
            {SECTION_META.map(({ key, label, icon, color, bg }) => (
              <SectionBar
                key={key}
                label={label}
                icon={icon}
                band={data.section_bands[key]}
                color={color}
                barColor={bg}
              />
            ))}
          </div>
        </div>
      )}

      {/* Practice (kept separate from mock stats) */}
      <PracticeBlock rows={practiceRows} />

      {/* Recent attempts */}
      {recentRows.length > 0 && (
        <div>
          <div className='mb-3 flex items-center justify-between'>
            <h3 className='text-sm font-medium text-muted-foreground'>
              Recent Attempts
            </h3>
            <Button asChild variant='ghost' size='sm' className='h-7 text-xs text-muted-foreground hover:text-foreground'>
              <Link to='/student/results'>
                View All
                <ChevronRight size={14} className='ml-0.5' />
              </Link>
            </Button>
          </div>
          <div className='space-y-2'>
            {recentRows.map((a) => (
              <Link
                key={a.id}
                to='/student/results/$attemptId'
                params={{ attemptId: a.id }}
                className='group flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3.5 transition-all hover:shadow-md hover:border-blue-200 dark:hover:border-blue-800/50'
              >
                <div className='min-w-0'>
                  <p className='truncate text-sm font-medium text-foreground group-hover:text-blue-700 dark:group-hover:text-blue-400 transition-colors'>
                    {a.test_title}
                  </p>
                  <p className='mt-0.5 flex items-center gap-1 text-xs text-muted-foreground'>
                    <Clock size={11} />
                    {(a.finished_at
                      ? new Date(a.finished_at)
                      : new Date(a.created_at)
                    ).toLocaleDateString('en-GB', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </p>
                </div>
                <div className='flex items-center gap-2.5'>
                  {a.overall_band != null ? (
                    <span className={cn(
                      'rounded-lg px-2.5 py-1 text-xs font-semibold',
                      a.overall_band >= 7
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400'
                        : a.overall_band >= 5.5
                          ? 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-400'
                          : 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400',
                    )}>
                      Band {a.overall_band}
                    </span>
                  ) : (
                    <Badge variant='secondary' className='text-xs'>
                      {a.status === 'completed' ? 'Evaluating' : a.status}
                    </Badge>
                  )}
                  <ChevronRight size={16} className='text-muted-foreground/50 group-hover:text-blue-500 transition-colors' />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
