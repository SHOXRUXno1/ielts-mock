import { useMemo, useState } from 'react'
import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  Award,
  BookOpen,
  Calendar,
  ChevronRight,
  FileText,
  Headphones,
  MessageSquare,
  Mic,
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

function bandColor(band: number | null): string {
  if (band === null) return 'text-muted-foreground'
  if (band >= 7) return 'text-emerald-600 dark:text-emerald-400'
  if (band >= 5.5) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-500 dark:text-red-400'
}

function bandBg(band: number | null): string {
  if (band === null) return 'bg-muted'
  if (band >= 7) return 'bg-emerald-50 dark:bg-emerald-950'
  if (band >= 5.5) return 'bg-amber-50 dark:bg-amber-950'
  return 'bg-red-50 dark:bg-red-950'
}

function formatBand(band: number | null): string {
  if (band === null) return '—'
  return band % 1 === 0 ? band.toFixed(1) : String(band)
}

const STATUS_CONFIG: Record<string, { label: string; dot: string; text: string }> = {
  in_progress: { label: 'In Progress', dot: 'bg-amber-500', text: 'text-amber-700 dark:text-amber-400' },
  completed: { label: 'Evaluating', dot: 'bg-blue-500', text: 'text-blue-700 dark:text-blue-400' },
  auto_scored: { label: 'Scored', dot: 'bg-emerald-500', text: 'text-emerald-700 dark:text-emerald-400' },
  fully_scored: { label: 'Fully Scored', dot: 'bg-emerald-500', text: 'text-emerald-700 dark:text-emerald-400' },
  speaking_in_progress: { label: 'Speaking…', dot: 'bg-violet-500', text: 'text-violet-700 dark:text-violet-400' },
  completed_without_speaking: { label: 'Completed', dot: 'bg-emerald-500', text: 'text-emerald-700 dark:text-emerald-400' },
  partial: { label: 'Partial', dot: 'bg-orange-500', text: 'text-orange-700 dark:text-orange-400' },
  abandoned: { label: 'Abandoned', dot: 'bg-slate-400', text: 'text-muted-foreground' },
}

const SECTION_ICONS = {
  listening: Headphones,
  reading: BookOpen,
  writing: MessageSquare,
  speaking: Mic,
}

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
  const statusCfg = STATUS_CONFIG[result.status] ?? {
    label: result.status,
    dot: 'bg-slate-400',
    text: 'text-muted-foreground',
  }

  const date = result.finished_at
    ? new Date(result.finished_at)
    : new Date(result.created_at)

  const sections = [
    { key: 'listening', band: result.listening_band },
    { key: 'reading', band: result.reading_band },
    { key: 'writing', band: result.writing_band },
    { key: 'speaking', band: result.speaking_band },
  ] as const

  return (
    <Link
      to='/student/results/$attemptId'
      params={{ attemptId: result.id }}
      className='group relative block cursor-pointer rounded-2xl border border-border bg-card transition-all duration-200 hover:shadow-lg hover:border-blue-200 dark:hover:border-blue-800/50'
    >
      <div className='flex flex-col sm:flex-row sm:items-center gap-4 p-5'>
        {/* Overall band circle */}
        <div className={cn(
          'flex size-16 shrink-0 flex-col items-center justify-center rounded-2xl',
          bandBg(result.overall_band),
        )}>
          <span className={cn('text-xl font-bold', bandColor(result.overall_band))}>
            {formatBand(result.overall_band)}
          </span>
          {result.overall_band != null && (
            <span className='text-[10px] text-muted-foreground'>band</span>
          )}
        </div>

        {/* Main info */}
        <div className='flex-1 min-w-0'>
          <h3 className='text-sm font-semibold text-foreground leading-snug group-hover:text-blue-700 dark:group-hover:text-blue-400 transition-colors truncate'>
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
            {sections.map(({ key, band }) => {
              const Icon = SECTION_ICONS[key]
              return (
                <div
                  key={key}
                  className='inline-flex items-center gap-1.5 rounded-lg bg-muted/60 px-2.5 py-1 text-xs'
                >
                  <Icon size={12} className='text-muted-foreground' />
                  <span className='capitalize text-muted-foreground'>{key}</span>
                  <span className={cn('font-semibold', bandColor(band))}>
                    {formatBand(band)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Arrow indicator */}
        <div className='shrink-0 flex items-center text-muted-foreground/50 group-hover:text-blue-500 transition-colors'>
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
    queryFn: getMyResults,
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
              <span className='inline-flex items-center gap-1.5 rounded-lg bg-blue-50 px-2.5 py-1.5 text-blue-700 dark:bg-blue-950 dark:text-blue-400'>
                <TrendingUp size={13} />
                Avg {stats.avg.toFixed(1)}
              </span>
            )}
            {stats.best != null && (
              <span className='inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 py-1.5 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400'>
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
