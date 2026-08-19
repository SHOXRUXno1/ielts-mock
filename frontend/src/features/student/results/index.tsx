import { useMemo, useState } from 'react'
import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  Award,
  Calendar,
  ChevronRight,
  FileText,
  Search,
  TrendingUp,
} from 'lucide-react'
import { getMyResults } from '@/lib/api/student'
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
import { bandTone, bandToneClasses, formatBand } from '@/features/results/lib/band'
import { SKILL_KEYS, SKILL_META } from '@/features/results/lib/skill'
import { attemptStatusMeta } from '@/features/results/lib/status'

interface ResultItem {
  id: string
  test_title: string
  created_at: string
  finished_at: string | null
  overall_band: number | null
  listening_band: number | null
  reading_band: number | null
  writing_band: number | null
  speaking_band: number | null
  status: string
}

function ResultCard({ result }: { result: ResultItem }) {
  const statusCfg = attemptStatusMeta(result.status)
  const tone = bandToneClasses(bandTone(result.overall_band))

  const date = result.finished_at
    ? new Date(result.finished_at)
    : new Date(result.created_at)

  return (
    <Link
      to='/student/results/$attemptId'
      params={{ attemptId: result.id }}
      className='group relative block cursor-pointer rounded-xl border border-border bg-card transition-shadow duration-200 hover:shadow-sm'
    >
      <div className='flex flex-col sm:flex-row sm:items-center gap-4 p-5'>
        {/* Overall band circle */}
        <div className={cn(
          'flex size-16 shrink-0 flex-col items-center justify-center rounded-xl',
          tone.bg,
        )}>
          <span className={cn('text-xl font-bold tabular-nums', tone.text)}>
            {formatBand(result.overall_band)}
          </span>
          {result.overall_band != null && (
            <span className='text-[10px] text-muted-foreground'>band</span>
          )}
        </div>

        {/* Main info */}
        <div className='flex-1 min-w-0'>
          <h3 className='truncate text-sm font-semibold leading-snug text-foreground transition-colors duration-150 group-hover:text-primary'>
            {result.test_title}
          </h3>

          <div className='mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground'>
            <span className='inline-flex items-center gap-1.5'>
              <Calendar size={12} />
              {date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
            </span>
            <span className='inline-flex items-center gap-1.5'>
              <span className={cn('size-1.5 rounded-full', statusCfg.dot)} />
              <span className={statusCfg.text}>{statusCfg.label}</span>
            </span>
          </div>

          {/* Section bands */}
          <div className='mt-3 flex flex-wrap gap-2'>
            {SKILL_KEYS.map((key) => {
              const Icon = SKILL_META[key].icon
              const band =
                key === 'listening'
                  ? result.listening_band
                  : key === 'reading'
                    ? result.reading_band
                    : key === 'writing'
                      ? result.writing_band
                      : result.speaking_band
              const skillTone = bandToneClasses(bandTone(band))
              return (
                <div
                  key={key}
                  className='inline-flex items-center gap-1.5 rounded-lg bg-muted/60 px-2.5 py-1 text-xs'
                >
                  <Icon size={12} className={SKILL_META[key].accent} />
                  <span className='text-muted-foreground'>{SKILL_META[key].label}</span>
                  <span className={cn('font-semibold tabular-nums', skillTone.text)}>
                    {formatBand(band)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Arrow indicator */}
        <div className='flex shrink-0 items-center text-muted-foreground/50 transition-colors duration-150 group-hover:text-primary'>
          <ChevronRight size={20} />
        </div>
      </div>
    </Link>
  )
}

function ResultCardSkeleton() {
  return (
    <div className='rounded-2xl border border-border bg-card p-5'>
      <div className='flex items-center gap-4'>
        <Skeleton className='size-16 rounded-2xl' />
        <div className='flex-1 space-y-2'>
          <Skeleton className='h-4 w-48' />
          <Skeleton className='h-3 w-32' />
          <div className='flex gap-2'>
            <Skeleton className='h-6 w-24 rounded-lg' />
            <Skeleton className='h-6 w-24 rounded-lg' />
            <Skeleton className='h-6 w-24 rounded-lg' />
            <Skeleton className='h-6 w-24 rounded-lg' />
          </div>
        </div>
      </div>
    </div>
  )
}

type SortKey = 'latest' | 'oldest' | 'band_high' | 'band_low'
type StatusFilter = 'all' | 'scored' | 'in_progress' | 'abandoned'

export function StudentResults() {
  const { data: results = [], isLoading } = useQuery({
    queryKey: ['student-results'],
    queryFn: () => getMyResults(),
  })

  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<SortKey>('latest')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  const filtered = useMemo(() => {
    let list = [...results]

    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter((r) => r.test_title.toLowerCase().includes(q))
    }

    if (statusFilter === 'scored') {
      list = list.filter((r) => ['auto_scored', 'fully_scored', 'completed_without_speaking'].includes(r.status))
    } else if (statusFilter === 'in_progress') {
      list = list.filter((r) => ['in_progress', 'speaking_in_progress', 'completed', 'partial'].includes(r.status))
    } else if (statusFilter === 'abandoned') {
      list = list.filter((r) => r.status === 'abandoned')
    }

    if (sort === 'latest') {
      list.sort((a, b) => new Date(b.finished_at ?? b.created_at).getTime() - new Date(a.finished_at ?? a.created_at).getTime())
    } else if (sort === 'oldest') {
      list.sort((a, b) => new Date(a.finished_at ?? a.created_at).getTime() - new Date(b.finished_at ?? b.created_at).getTime())
    } else if (sort === 'band_high') {
      list.sort((a, b) => (b.overall_band ?? -1) - (a.overall_band ?? -1))
    } else if (sort === 'band_low') {
      list.sort((a, b) => (a.overall_band ?? 99) - (b.overall_band ?? 99))
    }

    return list
  }, [results, search, sort, statusFilter])

  const stats = useMemo(() => {
    const scored = results.filter((r) => r.overall_band != null)
    const avg = scored.length
      ? scored.reduce((acc, r) => acc + (r.overall_band ?? 0), 0) / scored.length
      : null
    const best = scored.length
      ? Math.max(...scored.map((r) => r.overall_band ?? 0))
      : null
    return { total: results.length, scored: scored.length, avg, best }
  }, [results])

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex flex-wrap items-end justify-between gap-4'>
        <div>
          <h1 className='text-xl font-semibold tracking-tight text-foreground'>
            My Results
          </h1>
          <p className='mt-0.5 text-sm text-muted-foreground'>
            Track your IELTS progress across all attempts
          </p>
        </div>

        {!isLoading && results.length > 0 && (
          <div className='flex items-center gap-2.5 text-xs text-muted-foreground'>
            <span className='inline-flex items-center gap-1.5 rounded-lg bg-muted px-2.5 py-1.5'>
              <FileText size={13} />
              {stats.total} attempts
            </span>
            {stats.avg != null && (
              <span className='inline-flex items-center gap-1.5 rounded-lg bg-primary/10 px-2.5 py-1.5 text-primary'>
                <TrendingUp size={13} />
                Avg {stats.avg.toFixed(1)}
              </span>
            )}
            {stats.best != null && (
              <span className='inline-flex items-center gap-1.5 rounded-lg bg-success px-2.5 py-1.5 text-success-foreground'>
                <Award size={13} />
                Best {stats.best.toFixed(1)}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Filters */}
      {!isLoading && results.length > 0 && (
        <div className='flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card p-3'>
          <div className='relative flex-1 min-w-[160px] max-w-xs'>
            <Search size={15} className='absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground' />
            <Input
              placeholder='Search by test name...'
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className='h-9 rounded-lg border-0 bg-muted pl-9 text-sm shadow-none focus-visible:ring-1'
            />
          </div>
          <div className='flex items-center gap-1.5 rounded-lg border border-border p-0.5'>
            {([
              { value: 'all', label: 'All' },
              { value: 'scored', label: 'Scored' },
              { value: 'in_progress', label: 'In progress' },
              { value: 'abandoned', label: 'Abandoned' },
            ] as const).map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setStatusFilter(value)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                  statusFilter === value
                    ? 'bg-foreground text-background shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <Select value={sort} onValueChange={(v) => setSort(v as SortKey)}>
            <SelectTrigger size='sm' className='h-8 rounded-lg border-0 bg-muted text-xs font-medium shadow-none'>
              <SelectValue />
            </SelectTrigger>
            <SelectContent className='rounded-lg'>
              <SelectItem value='latest'>Latest first</SelectItem>
              <SelectItem value='oldest'>Oldest first</SelectItem>
              <SelectItem value='band_high'>Highest band</SelectItem>
              <SelectItem value='band_low'>Lowest band</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Results list */}
      {isLoading ? (
        <div className='space-y-3'>
          {[0, 1, 2, 3].map((i) => <ResultCardSkeleton key={i} />)}
        </div>
      ) : results.length === 0 ? (
        <div className='flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed bg-muted/20 py-16 text-center'>
          <div className='flex size-14 items-center justify-center rounded-2xl bg-muted'>
            <FileText className='size-7 text-muted-foreground' />
          </div>
          <p className='text-base font-medium text-foreground'>No results yet</p>
          <p className='max-w-xs text-sm text-muted-foreground'>
            Complete a test to see your scores and track your progress
          </p>
          <Button asChild className='mt-3 rounded-lg' variant='outline'>
            <Link to='/student/tests'>Take a Test</Link>
          </Button>
        </div>
      ) : filtered.length === 0 ? (
        <div className='flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed bg-muted/20 py-12 text-center'>
          <Search className='size-8 text-muted-foreground/50' />
          <p className='font-medium text-foreground'>No results match your filters</p>
          <p className='text-sm text-muted-foreground'>Try different search or filter</p>
          <Button
            variant='ghost'
            size='sm'
            className='mt-2 text-xs'
            onClick={() => { setSearch(''); setStatusFilter('all') }}
          >
            Clear filters
          </Button>
        </div>
      ) : (
        <div className='space-y-3'>
          {filtered.map((result) => (
            <ResultCard key={result.id} result={result} />
          ))}
        </div>
      )}
    </div>
  )
}
