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
import { getTestCatalog, type CatalogTest } from '@/lib/api/student'
import { PracticePicker } from '@/features/student/practice/practice-picker'
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
import {
  SKILL_ICONS,
  SKILL_ORDER,
} from '@/features/student/practice/skill-icons'

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
    pill: 'bg-sky-50 text-sky-700 ring-sky-200/70 dark:bg-sky-950 dark:text-sky-300 dark:ring-sky-800',
    strip: 'from-sky-400 to-blue-500',
    soft: 'from-sky-50/80 via-white to-white dark:from-sky-950/30 dark:via-card dark:to-card',
  },
  in_progress: {
    label: 'In progress',
    pill: 'bg-amber-50 text-amber-700 ring-amber-200/70 dark:bg-amber-950 dark:text-amber-300 dark:ring-amber-800',
    strip: 'from-amber-400 to-orange-500',
    soft: 'from-amber-50/80 via-white to-white dark:from-amber-950/30 dark:via-card dark:to-card',
  },
  completed: {
    label: 'Completed',
    pill: 'bg-emerald-50 text-emerald-700 ring-emerald-200/70 dark:bg-emerald-950 dark:text-emerald-300 dark:ring-emerald-800',
    strip: 'from-emerald-400 to-teal-500',
    soft: 'from-emerald-50/70 via-white to-white dark:from-emerald-950/30 dark:via-card dark:to-card',
  },
} as const

function SkillStrip({ test }: { test: CatalogTest }) {
  return (
    <div className='flex items-center gap-1.5'>
      {SKILL_ORDER.map((skill) => {
        const done = test.sections[skill]?.completed
        return (
          <div
            key={skill}
            className={cn(
              'relative flex size-9 items-center justify-center rounded-xl bg-white/90 shadow-sm ring-1 ring-black/5 dark:bg-background/70',
              done && 'ring-emerald-300/70 dark:ring-emerald-700/60',
            )}
            title={skill}
          >
            <img
              src={SKILL_ICONS[skill]}
              alt=''
              aria-hidden
              draggable={false}
              className='size-7 object-contain drop-shadow-[0_3px_6px_rgba(15,23,42,0.12)]'
            />
            {done && (
              <span className='absolute -right-0.5 -top-0.5 flex size-3.5 items-center justify-center rounded-full bg-emerald-500 text-white ring-2 ring-white dark:ring-card'>
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
  const typeLabel =
    test.test_type === 'general' ? 'General' : 'Academic'

  return (
    <article
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-b shadow-sm transition-all duration-200',
        statusCfg.soft,
        'hover:-translate-y-0.5 hover:border-border hover:shadow-md',
      )}
    >
      <div
        className={cn(
          'h-1 w-full bg-gradient-to-r',
          statusCfg.strip,
        )}
      />

      <div className='flex flex-1 flex-col px-5 pb-4 pt-4'>
        <div className='mb-3 flex items-start justify-between gap-3'>
          <span
            className={cn(
              'inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1',
              statusCfg.pill,
            )}
          >
            {statusCfg.label}
          </span>
          <span className='rounded-md bg-muted/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground'>
            {typeLabel}
          </span>
        </div>

        <h3 className='text-[16px] font-semibold leading-snug tracking-tight text-foreground transition-colors group-hover:text-sky-700 dark:group-hover:text-sky-300'>
          {test.title}
        </h3>
        {test.book_name && (
          <p className='mt-1 text-[12.5px] text-muted-foreground'>
            {test.book_name}
          </p>
        )}

        <div className='mt-4 flex items-center justify-between gap-3'>
          <SkillStrip test={test} />
          {test.overall_score != null && (
            <div className='flex flex-col items-end'>
              <span className='text-[10px] font-medium uppercase tracking-wider text-muted-foreground'>
                Best
              </span>
              <span className='text-lg font-bold tabular-nums text-emerald-600 dark:text-emerald-400'>
                {test.overall_score.toFixed(1)}
              </span>
            </div>
          )}
        </div>

        <div className='mt-4 flex items-center gap-3 text-[12px] text-muted-foreground'>
          <span className='inline-flex items-center gap-1.5 rounded-lg bg-muted/70 px-2 py-1'>
            <Clock size={12} className='opacity-70' />
            {formatDuration(test.duration_minutes)}
          </span>
          <span className='inline-flex items-center gap-1.5 rounded-lg bg-muted/70 px-2 py-1'>
            <Sparkles size={12} className='opacity-70' />
            {test.section_count} skills
          </span>
        </div>

        <div className='mt-5 grid gap-2'>
          {test.in_progress_attempt_id ? (
            <Button
              asChild
              size='sm'
              className='h-10 w-full rounded-xl bg-amber-500 text-[13px] font-semibold text-white shadow-sm hover:bg-amber-600'
            >
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
              className='h-10 w-full rounded-xl bg-foreground text-[13px] font-semibold text-background hover:bg-foreground/90'
            >
              <Link to='/take-test/$testId' params={{ testId: test.id }}>
                <RotateCcw size={14} className='mr-1.5' />
                Retake full mock
              </Link>
            </Button>
          ) : (
            <Button
              asChild
              size='sm'
              className='h-10 w-full rounded-xl bg-sky-600 text-[13px] font-semibold text-white shadow-sm hover:bg-sky-700'
            >
              <Link to='/take-test/$testId' params={{ testId: test.id }}>
                <Play size={14} className='mr-1.5 fill-current' />
                Start full mock
              </Link>
            </Button>
          )}

          <button
            type='button'
            onClick={() => setPickerOpen(true)}
            className='flex h-10 w-full items-center justify-center gap-2 rounded-xl border border-border/80 bg-white/70 text-[13px] font-semibold text-foreground transition-colors hover:bg-muted/60 dark:bg-background/40'
          >
            <span className='flex -space-x-1.5'>
              {SKILL_ORDER.slice(0, 3).map((skill) => (
                <img
                  key={skill}
                  src={SKILL_ICONS[skill]}
                  alt=''
                  aria-hidden
                  className='size-5 rounded-full bg-white object-contain ring-1 ring-border'
                />
              ))}
            </span>
            Practice a section or part
          </button>
        </div>
      </div>

      <PracticePicker
        testId={test.id}
        open={pickerOpen}
        onOpenChange={setPickerOpen}
      />
    </article>
  )
}

function TestCardSkeleton() {
  return (
    <div className='overflow-hidden rounded-2xl border border-border bg-card'>
      <Skeleton className='h-1 w-full rounded-none' />
      <div className='space-y-4 p-5'>
        <div className='flex justify-between'>
          <Skeleton className='h-6 w-24 rounded-full' />
          <Skeleton className='h-6 w-16 rounded-md' />
        </div>
        <Skeleton className='h-5 w-4/5' />
        <Skeleton className='h-3 w-1/2' />
        <div className='flex gap-1.5'>
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className='size-9 rounded-xl' />
          ))}
        </div>
        <Skeleton className='h-10 w-full rounded-xl' />
        <Skeleton className='h-10 w-full rounded-xl' />
      </div>
    </div>
  )
}

type SortKey = 'latest' | 'alphabetical' | 'score'

export function StudentTests() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['student-test-catalog'],
    queryFn: getTestCatalog,
  })

  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'academic' | 'general'>(
    'all',
  )
  const [sort, setSort] = useState<SortKey>('latest')

  const allTests = useMemo(() => {
    if (!data) return []
    return data.groups.flatMap((g) => g.tests)
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
      {/* Header */}
      <div className='relative overflow-hidden rounded-2xl border border-border/70 bg-gradient-to-br from-sky-50 via-background to-violet-50/40 p-5 dark:from-sky-950/30 dark:via-background dark:to-violet-950/20 sm:p-6'>
        <div className='relative z-10 flex flex-wrap items-end justify-between gap-4'>
          <div className='max-w-xl'>
            <p className='text-[11px] font-semibold uppercase tracking-[0.14em] text-sky-700/80 dark:text-sky-300/80'>
              Student library
            </p>
            <h1 className='mt-1 text-2xl font-semibold tracking-tight text-foreground'>
              Test Catalog
            </h1>
            <p className='mt-1.5 text-sm leading-relaxed text-muted-foreground'>
              Take a full mock under exam conditions, or drill a single section
              and part with its own timer.
            </p>
          </div>

          {!isLoading && allTests.length > 0 && (
            <div className='flex flex-wrap gap-2'>
              <div className='rounded-xl border border-border/60 bg-white/80 px-3.5 py-2 shadow-sm dark:bg-background/60'>
                <p className='text-[10px] font-medium uppercase tracking-wider text-muted-foreground'>
                  Available
                </p>
                <p className='text-lg font-bold tabular-nums'>{stats.total}</p>
              </div>
              <div className='rounded-xl border border-emerald-200/70 bg-emerald-50/90 px-3.5 py-2 shadow-sm dark:border-emerald-900 dark:bg-emerald-950/50'>
                <p className='text-[10px] font-medium uppercase tracking-wider text-emerald-700/80 dark:text-emerald-400/80'>
                  Done
                </p>
                <p className='text-lg font-bold tabular-nums text-emerald-700 dark:text-emerald-400'>
                  {stats.completed}
                </p>
              </div>
              {stats.inProgress > 0 && (
                <div className='rounded-xl border border-amber-200/70 bg-amber-50/90 px-3.5 py-2 shadow-sm dark:border-amber-900 dark:bg-amber-950/50'>
                  <p className='text-[10px] font-medium uppercase tracking-wider text-amber-700/80 dark:text-amber-400/80'>
                    Active
                  </p>
                  <p className='text-lg font-bold tabular-nums text-amber-700 dark:text-amber-400'>
                    {stats.inProgress}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      {!isLoading && allTests.length > 0 && (
        <div className='flex flex-wrap items-center gap-2.5 rounded-2xl border border-border/70 bg-card/80 p-2.5 shadow-sm backdrop-blur'>
          <div className='relative min-w-[200px] flex-1'>
            <Search
              size={15}
              className='absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground'
            />
            <Input
              placeholder='Search by test or book…'
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className='h-10 rounded-xl border-0 bg-muted/70 pl-9 text-sm shadow-none focus-visible:ring-1'
            />
          </div>
          <div className='flex items-center gap-1 rounded-xl bg-muted/60 p-1'>
            {(['all', 'academic', 'general'] as const).map((value) => (
              <button
                key={value}
                type='button'
                onClick={() => setTypeFilter(value)}
                className={cn(
                  'rounded-lg px-3 py-1.5 text-xs font-semibold capitalize transition-all',
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
              className='h-10 rounded-xl border-0 bg-muted/70 text-xs font-semibold shadow-none'
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent className='rounded-xl'>
              <SelectItem value='latest'>Latest first</SelectItem>
              <SelectItem value='alphabetical'>A → Z</SelectItem>
              <SelectItem value='score'>Best score</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Grid */}
      {isError ? (
        <div className='flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed bg-muted/20 py-16 text-center'>
          <p className='text-base font-medium text-foreground'>
            Could not load tests
          </p>
          <p className='max-w-xs text-sm text-muted-foreground'>
            The server did not respond. Check that the backend is running, then
            try again.
          </p>
          <Button
            variant='outline'
            size='sm'
            className='mt-1'
            onClick={() => void refetch()}
          >
            Retry
          </Button>
        </div>
      ) : isLoading ? (
        <div className='grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3'>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <TestCardSkeleton key={i} />
          ))}
        </div>
      ) : allTests.length === 0 ? (
        <div className='flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed bg-muted/20 py-16 text-center'>
          <div className='flex size-14 items-center justify-center rounded-2xl bg-muted'>
            <GraduationCap className='size-7 text-muted-foreground' />
          </div>
          <p className='text-base font-medium text-foreground'>
            No tests available yet
          </p>
          <p className='max-w-xs text-sm text-muted-foreground'>
            Your teacher will publish practice tests here. Check back soon!
          </p>
        </div>
      ) : filtered.length === 0 ? (
        <div className='flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed bg-muted/20 py-12 text-center'>
          <Search className='size-8 text-muted-foreground/50' />
          <p className='font-medium text-foreground'>No tests match</p>
          <p className='text-sm text-muted-foreground'>
            Try different keywords or filters
          </p>
          <Button
            variant='ghost'
            size='sm'
            className='mt-2 text-xs'
            onClick={() => {
              setSearch('')
              setTypeFilter('all')
            }}
          >
            Clear filters
          </Button>
        </div>
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
