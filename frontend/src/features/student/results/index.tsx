import { useMemo, useState } from 'react'
import { Link } from '@tanstack/react-router'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  Award,
  Calendar,
  ChevronRight,
  Download,
  FileText,
  Loader2,
  Search,
  TrendingUp,
} from 'lucide-react'
import { toast } from 'sonner'
import { downloadResultPdf } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import {
  BandValue,
  EmptyState,
  Metric,
  Panel,
  SkillBandRow,
} from '@/components/report'
import { getMyResults } from '@/lib/api/student'
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
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { SKILL_KEYS } from '@/features/results/lib/skill'
import { attemptStatusMeta } from '@/features/results/lib/status'
import { formatBand } from '@/features/results/lib/band'

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

function bandFor(
  result: ResultItem,
  skill: (typeof SKILL_KEYS)[number],
): number | null {
  if (skill === 'listening') return result.listening_band
  if (skill === 'reading') return result.reading_band
  if (skill === 'writing') return result.writing_band
  return result.speaking_band
}

function ResultCard({ result }: { result: ResultItem }) {
  const statusCfg = attemptStatusMeta(result.status)
  const date = result.finished_at
    ? new Date(result.finished_at)
    : new Date(result.created_at)

  const pdfDisabled = result.status === 'in_progress'
  const download = useMutation({
    mutationFn: () => downloadResultPdf(result.id),
    onError: () => toast.error('Could not generate the PDF'),
  })

  return (
    <div className='group relative'>
      <Link
        to='/student/results/$attemptId'
        params={{ attemptId: result.id }}
        className='block rounded-2xl focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
      >
        <Panel className='transition-colors group-hover:bg-muted/30'>
          <div className='flex flex-col gap-4 sm:flex-row sm:items-start'>
            <BandValue
              band={result.overall_band}
              label='Overall'
              size='sm'
              showDescriptor={false}
            />
            <div className='min-w-0 flex-1'>
              <div className='flex items-start justify-between gap-3'>
                <h3 className='truncate pr-16 text-sm font-semibold text-foreground'>
                  {result.test_title}
                </h3>
              </div>
              <div className='mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground'>
                <span className='inline-flex items-center gap-1.5'>
                  <Calendar size={12} />
                  {date.toLocaleDateString(undefined, {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </span>
                <span className='inline-flex items-center gap-1.5'>
                  <span className={cn('size-1.5 rounded-full', statusCfg.dot)} />
                  <span className={statusCfg.text}>{statusCfg.label}</span>
                </span>
              </div>
              <div className='mt-3 space-y-1'>
                {SKILL_KEYS.map((skill) => (
                  <SkillBandRow
                    key={skill}
                    skill={skill}
                    band={bandFor(result, skill)}
                    className='px-0 py-2'
                  />
                ))}
              </div>
            </div>
          </div>
        </Panel>
      </Link>
      <div className='pointer-events-none absolute right-5 top-5 flex items-center gap-1'>
        <button
          type='button'
          aria-label='Download PDF'
          disabled={pdfDisabled || download.isPending}
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            if (pdfDisabled || download.isPending) return
            download.mutate()
          }}
          className='pointer-events-auto inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50'
        >
          {download.isPending ? (
            <Loader2 className='size-4 animate-spin' />
          ) : (
            <Download className='size-4' />
          )}
        </button>
        <ChevronRight className='size-4 shrink-0 text-muted-foreground/50 transition-colors group-hover:text-foreground' />
      </div>
    </div>
  )
}

function ResultCardSkeleton() {
  return (
    <Panel>
      <div className='flex items-start gap-4'>
        <Skeleton className='h-16 w-16 rounded-xl' />
        <div className='flex-1 space-y-3'>
          <Skeleton className='h-4 w-48' />
          <Skeleton className='h-3 w-32' />
          <Skeleton className='h-10 w-full' />
          <Skeleton className='h-10 w-full' />
        </div>
      </div>
    </Panel>
  )
}

type SortKey = 'latest' | 'oldest' | 'band_high' | 'band_low'
type StatusFilter = 'all' | 'scored' | 'in_progress' | 'abandoned'

export function StudentResults() {
  const signedIn = useAuthStore((s) => Boolean(s.auth.accessToken))
  const { data: results = [], isLoading } = useQuery({
    queryKey: ['student-results'],
    queryFn: () => getMyResults(),
    enabled: signedIn,
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
      list = list.filter((r) =>
        ['auto_scored', 'fully_scored', 'completed_without_speaking'].includes(
          r.status,
        ),
      )
    } else if (statusFilter === 'in_progress') {
      list = list.filter((r) =>
        ['in_progress', 'speaking_in_progress', 'completed', 'partial'].includes(
          r.status,
        ),
      )
    } else if (statusFilter === 'abandoned') {
      list = list.filter((r) => r.status === 'abandoned')
    }

    if (sort === 'latest') {
      list.sort(
        (a, b) =>
          new Date(b.finished_at ?? b.created_at).getTime() -
          new Date(a.finished_at ?? a.created_at).getTime(),
      )
    } else if (sort === 'oldest') {
      list.sort(
        (a, b) =>
          new Date(a.finished_at ?? a.created_at).getTime() -
          new Date(b.finished_at ?? b.created_at).getTime(),
      )
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
      <div className='flex flex-wrap items-end justify-between gap-4'>
        <div>
          <h1 className='text-2xl font-semibold tracking-tight text-foreground'>
            My Results
          </h1>
          <p className='mt-1 text-sm text-muted-foreground'>
            Track your IELTS progress across all attempts
          </p>
        </div>

        {!isLoading && results.length > 0 && (
          <div className='flex flex-wrap gap-4'>
            <Metric icon={FileText} label='Attempts' value={String(stats.total)} />
            {stats.avg != null && (
              <Metric
                icon={TrendingUp}
                label='Average'
                value={formatBand(stats.avg)}
              />
            )}
            {stats.best != null && (
              <Metric icon={Award} label='Best' value={formatBand(stats.best)} />
            )}
          </div>
        )}
      </div>

      {!isLoading && results.length > 0 && (
        <Panel padding='sm'>
          <div className='flex flex-wrap items-center gap-3'>
            <div className='relative min-w-[160px] max-w-xs flex-1'>
              <Search
                size={15}
                className='absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground'
              />
              <Input
                placeholder='Search by test name...'
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className='h-9 rounded-lg border-0 bg-muted pl-9 text-sm shadow-none focus-visible:ring-1'
              />
            </div>
            <Tabs
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as StatusFilter)}
            >
              <TabsList className='h-auto rounded-lg bg-muted p-1'>
                <TabsTrigger value='all' className='rounded-md px-3 py-1.5 text-xs'>
                  All
                </TabsTrigger>
                <TabsTrigger value='scored' className='rounded-md px-3 py-1.5 text-xs'>
                  Scored
                </TabsTrigger>
                <TabsTrigger
                  value='in_progress'
                  className='rounded-md px-3 py-1.5 text-xs'
                >
                  In progress
                </TabsTrigger>
                <TabsTrigger
                  value='abandoned'
                  className='rounded-md px-3 py-1.5 text-xs'
                >
                  Abandoned
                </TabsTrigger>
              </TabsList>
            </Tabs>
            <Select value={sort} onValueChange={(v) => setSort(v as SortKey)}>
              <SelectTrigger
                size='sm'
                className='h-8 rounded-lg border-0 bg-muted text-xs font-medium shadow-none'
              >
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
        </Panel>
      )}

      {isLoading ? (
        <div className='space-y-3'>
          {[0, 1, 2, 3].map((i) => (
            <ResultCardSkeleton key={i} />
          ))}
        </div>
      ) : results.length === 0 ? (
        <EmptyState
          icon={FileText}
          title='No results yet'
          description='Complete a test to see your scores and track your progress'
          action={
            <Button asChild className='rounded-lg' variant='outline'>
              <Link to='/student/tests'>Take a Test</Link>
            </Button>
          }
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Search}
          title='No results match your filters'
          description='Try different search or filter'
          action={
            <Button
              variant='ghost'
              size='sm'
              onClick={() => {
                setSearch('')
                setStatusFilter('all')
              }}
            >
              Clear filters
            </Button>
          }
        />
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
