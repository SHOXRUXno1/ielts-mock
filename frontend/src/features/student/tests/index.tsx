import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  GraduationCap,
  Play,
  RotateCcw,
  Search,
  Sparkles,
} from 'lucide-react'
import { EmptyState, Metric, Panel } from '@/components/report'
import { PracticePicker } from '@/features/student/practice/practice-picker'
import {
  SKILL_ICONS,
  SKILL_ORDER,
} from '@/features/student/practice/skill-icons'
import { getTestCatalog, type CatalogTest } from '@/lib/api/student'
import { useAuthStore } from '@/stores/auth-store'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

function formatDuration(minutes: number): string {
  if (minutes <= 0) return '—'
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h}h ${m}m` : `${h}h`
}

const STATUS_CONFIG = {
  new: {
    label: 'Ready to start',
    pill: 'bg-muted text-foreground',
  },
  in_progress: {
    label: 'In progress',
    pill: 'bg-warning text-warning-foreground',
  },
  completed: {
    label: 'Completed',
    pill: 'bg-success text-success-foreground',
  },
} as const

function SkillStrip({ test }: { test: CatalogTest }) {
  return (
    <div className='flex items-center gap-2'>
      {SKILL_ORDER.map((skill) => {
        const done = test.sections?.[skill]?.completed
        return (
          <div
            key={skill}
            className={cn(
              'relative flex size-9 items-center justify-center rounded-xl bg-muted ring-1 ring-border',
              done && 'ring-success-foreground/40',
            )}
            title={skill}
          >
            <img
              src={SKILL_ICONS[skill]}
              alt=''
              aria-hidden
              draggable={false}
              className='size-7 object-contain'
            />
            {done && (
              <span className='absolute -top-0.5 -right-0.5 flex size-3.5 items-center justify-center rounded-full bg-success text-success-foreground ring-2 ring-card'>
                <CheckCircle2 className='size-2.5' strokeWidth={3} />
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function TestCard({ test }: { test: CatalogTest }) {
  const statusCfg = STATUS_CONFIG[test.status] ?? STATUS_CONFIG.new
  const [pickerOpen, setPickerOpen] = useState(false)
  const typeLabel = test.test_type === 'general' ? 'General' : 'Academic'

  return (
    <article className='group flex flex-col'>
      <Panel className='flex h-full flex-col transition-colors hover:bg-muted/30' padding='none'>
        <div className='flex flex-1 flex-col p-6'>
          <div className='mb-4 flex items-start justify-between gap-3'>
            <span
              className={cn(
                'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold',
                statusCfg.pill,
              )}
            >
              {statusCfg.label}
            </span>
            <span className='rounded-md bg-muted px-2 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground'>
              {typeLabel}
            </span>
          </div>

          <h3 className='text-base font-semibold leading-snug tracking-tight text-foreground'>
            {test.title}
          </h3>
          {test.book_name && (
            <p className='mt-1 text-sm text-muted-foreground'>{test.book_name}</p>
          )}

          <div className='mt-4 flex items-center justify-between gap-3'>
            <SkillStrip test={test} />
            {test.overall_score != null && (
              <div className='flex flex-col items-end'>
                <span className='text-xs font-medium uppercase tracking-wider text-muted-foreground'>
                  Best
                </span>
                <span className='font-manrope text-lg font-semibold tabular-nums text-foreground'>
                  {test.overall_score.toFixed(1)}
                </span>
              </div>
            )}
          </div>

          <div className='mt-4 flex items-center gap-2 text-xs text-muted-foreground'>
            <span className='inline-flex items-center gap-1.5 rounded-lg bg-muted px-2 py-1'>
              <Clock size={12} />
              {formatDuration(test.duration_minutes)}
            </span>
            <span className='inline-flex items-center gap-1.5 rounded-lg bg-muted px-2 py-1'>
              <Sparkles size={12} />
              {test.section_count} skills
            </span>
          </div>

          <div className='mt-6 grid gap-2'>
            {test.in_progress_attempt_id ? (
              <Button asChild size='sm' className='h-10 w-full rounded-xl'>
                <Link
                  to='/take-test/$testId'
                  params={{ testId: test.id }}
                  search={{ resume: test.in_progress_attempt_id }}
                >
                  Continue mock
                  <ArrowRight size={14} className='ml-1.5' />
                </Link>
              </Button>
            ) : test.status === 'completed' ? (
              <Button
                asChild
                size='sm'
                variant='secondary'
                className='h-10 w-full rounded-xl'
              >
                <Link to='/take-test/$testId' params={{ testId: test.id }}>
                  <RotateCcw size={14} className='mr-1.5' />
                  Retake full mock
                </Link>
              </Button>
            ) : (
              <Button asChild size='sm' className='h-10 w-full rounded-xl'>
                <Link to='/take-test/$testId' params={{ testId: test.id }}>
                  <Play size={14} className='mr-1.5 fill-current' />
                  Start full mock
                </Link>
              </Button>
            )}

            <Button
              type='button'
              variant='outline'
              size='sm'
              className='h-10 w-full rounded-xl'
              onClick={() => setPickerOpen(true)}
            >
              Practice a section or part
            </Button>
          </div>
        </div>
      </Panel>

      {pickerOpen && (
        <PracticePicker
          testId={test.id}
          open={pickerOpen}
          onOpenChange={setPickerOpen}
        />
      )}
    </article>
  )
}

function TestCardSkeleton() {
  return (
    <Panel>
      <div className='space-y-4'>
        <div className='flex justify-between'>
          <Skeleton className='h-6 w-24 rounded-full' />
          <Skeleton className='h-6 w-16 rounded-md' />
        </div>
        <Skeleton className='h-5 w-4/5' />
        <Skeleton className='h-4 w-1/2' />
        <div className='flex gap-2'>
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className='size-9 rounded-xl' />
          ))}
        </div>
        <Skeleton className='h-10 w-full rounded-xl' />
        <Skeleton className='h-10 w-full rounded-xl' />
      </div>
    </Panel>
  )
}

type SortKey = 'latest' | 'alphabetical' | 'score'

export function StudentTests() {
  const signedIn = useAuthStore((s) => Boolean(s.auth.accessToken))
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['student-test-catalog'],
    queryFn: getTestCatalog,
    enabled: signedIn,
  })

  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'academic' | 'general'>(
    'all',
  )
  const [sort, setSort] = useState<SortKey>('latest')

  const allTests = useMemo(() => {
    if (!data?.groups) return []
    return data.groups.flatMap((g) => g.tests ?? [])
  }, [data])

  const filtered = useMemo(() => {
    let list = allTests

    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(
        (t) =>
          t.title.toLowerCase().includes(q) ||
          (t.book_name ?? '').toLowerCase().includes(q),
      )
    }

    if (typeFilter !== 'all') {
      list = list.filter((t) => t.test_type === typeFilter)
    }

    const sorted = [...list]
    if (sort === 'alphabetical') {
      sorted.sort((a, b) => a.title.localeCompare(b.title))
    } else if (sort === 'score') {
      sorted.sort((a, b) => (b.overall_score ?? -1) - (a.overall_score ?? -1))
    }

    return sorted
  }, [allTests, search, typeFilter, sort])

  const stats = useMemo(() => {
    const completed = allTests.filter((t) => t.status === 'completed').length
    const inProgress = allTests.filter((t) => t.status === 'in_progress').length
    return { total: allTests.length, completed, inProgress }
  }, [allTests])

  return (
    <div className='space-y-6'>
      <Panel>
        <div className='flex flex-wrap items-end justify-between gap-4'>
          <div className='max-w-xl'>
            <p className='text-xs font-medium tracking-wider text-muted-foreground uppercase'>
              Student library
            </p>
            <h1 className='mt-1 text-2xl font-semibold tracking-tight text-foreground'>
              Test Catalog
            </h1>
            <p className='mt-2 text-sm leading-relaxed text-muted-foreground'>
              Take a full mock under exam conditions, or drill a single section
              and part with its own timer.
            </p>
          </div>

          {!isLoading && allTests.length > 0 && (
            <div className='flex flex-wrap gap-4'>
              <Metric icon={GraduationCap} label='Available' value={String(stats.total)} />
              <Metric icon={CheckCircle2} label='Done' value={String(stats.completed)} />
              {stats.inProgress > 0 && (
                <Metric icon={Clock} label='Active' value={String(stats.inProgress)} />
              )}
            </div>
          )}
        </div>
      </Panel>

      {!isLoading && allTests.length > 0 && (
        <Panel padding='sm'>
          <div className='flex flex-wrap items-center gap-2'>
            <div className='relative min-w-[200px] flex-1'>
              <Search
                size={15}
                className='absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground'
              />
              <Input
                placeholder='Search by test or book…'
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className='h-10 rounded-lg border-0 bg-muted pl-9 text-sm shadow-none focus-visible:ring-1'
              />
            </div>
            <div className='flex items-center gap-1 rounded-lg bg-muted p-1'>
              {(['all', 'academic', 'general'] as const).map((value) => (
                <button
                  key={value}
                  type='button'
                  onClick={() => setTypeFilter(value)}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-xs font-semibold capitalize transition-colors',
                    'focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                    typeFilter === value
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {value === 'all' ? 'All' : value}
                </button>
              ))}
            </div>
            <Select value={sort} onValueChange={(v) => setSort(v as SortKey)}>
              <SelectTrigger
                size='sm'
                className='h-10 rounded-lg border-0 bg-muted text-xs font-semibold shadow-none'
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className='rounded-lg'>
                <SelectItem value='latest'>Latest first</SelectItem>
                <SelectItem value='alphabetical'>A → Z</SelectItem>
                <SelectItem value='score'>Best score</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </Panel>
      )}

      {isError ? (
        <EmptyState
          title='Could not load tests'
          description='The server did not respond. Check that the backend is running, then try again.'
          action={
            <Button variant='outline' size='sm' onClick={() => void refetch()}>
              Retry
            </Button>
          }
        />
      ) : isLoading ? (
        <div className='grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3'>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <TestCardSkeleton key={i} />
          ))}
        </div>
      ) : allTests.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title='No tests available yet'
          description='Your teacher will publish practice tests here. Check back soon!'
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Search}
          title='No tests match'
          description='Try different keywords or filters'
          action={
            <Button
              variant='ghost'
              size='sm'
              onClick={() => {
                setSearch('')
                setTypeFilter('all')
              }}
            >
              Clear filters
            </Button>
          }
        />
      ) : (
        <div className='grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3'>
          {filtered.map((test) => (
            <TestCard key={test.id} test={test} />
          ))}
        </div>
      )}
    </div>
  )
}
