import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { ArrowUpRight, BookOpen, Clock, Trophy } from 'lucide-react'
import { useState } from 'react'
import { fetchResults } from '@/lib/api/attempts'
import type { AttemptListItem } from '@/lib/api/attempts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

// ── Helpers ───────────────────────────────────────────────────────────────────

function bandColor(band: number | null): string {
  if (band === null) return 'text-muted-foreground'
  if (band >= 7.5) return 'text-emerald-600 dark:text-emerald-400'
  if (band >= 6.0) return 'text-blue-600 dark:text-blue-400'
  if (band >= 5.0) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-500 dark:text-red-400'
}

function bandBg(band: number | null): string {
  if (band === null) return 'bg-muted/50'
  if (band >= 7.5) return 'bg-emerald-50 dark:bg-emerald-950/40'
  if (band >= 6.0) return 'bg-blue-50 dark:bg-blue-950/40'
  if (band >= 5.0) return 'bg-amber-50 dark:bg-amber-950/40'
  return 'bg-red-50 dark:bg-red-950/40'
}

function formatBand(band: number | null): string {
  if (band === null) return '—'
  return band % 1 === 0 ? band.toFixed(1) : String(band)
}

function formatDate(iso: string): { date: string; time: string } {
  const d = new Date(iso)
  return {
    date: d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }),
    time: d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
  }
}

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'scored':
      return (
        <Badge className='bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/40 dark:text-emerald-400 border-0'>
          Scored
        </Badge>
      )
    case 'completed':
      return (
        <Badge className='bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/40 dark:text-blue-400 border-0'>
          Evaluating
        </Badge>
      )
    case 'in_progress':
      return (
        <Badge className='bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/40 dark:text-amber-400 border-0'>
          In Progress
        </Badge>
      )
    case 'abandoned':
      return (
        <Badge variant='outline' className='text-muted-foreground'>
          Abandoned
        </Badge>
      )
    default:
      return (
        <Badge variant='outline' className='text-muted-foreground'>
          {status}
        </Badge>
      )
  }
}

// ── Band pill ─────────────────────────────────────────────────────────────────

function BandPill({ band }: { band: number | null }) {
  return (
    <span
      className={`inline-flex items-center justify-center rounded-md px-2.5 py-0.5 text-sm font-semibold tabular-nums ${bandBg(band)} ${bandColor(band)}`}
    >
      {formatBand(band)}
    </span>
  )
}

// ── Summary cards ─────────────────────────────────────────────────────────────

function SummaryCards({ results }: { results: AttemptListItem[] }) {
  const scored = results.filter((r) => r.status === 'scored')
  const best = scored.length
    ? Math.max(...scored.map((r) => r.overall_band ?? 0))
    : null
  const avg =
    scored.length
      ? scored.reduce((s, r) => s + (r.overall_band ?? 0), 0) / scored.length
      : null

  const cards = [
    {
      icon: BookOpen,
      label: 'Total Attempts',
      value: results.length,
      sub: `${scored.length} scored`,
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950/30',
    },
    {
      icon: Trophy,
      label: 'Best Score',
      value: best !== null ? best.toFixed(1) : '—',
      sub: 'overall band',
      color: 'text-emerald-600',
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    },
    {
      icon: Clock,
      label: 'Average Score',
      value: avg !== null ? avg.toFixed(1) : '—',
      sub: 'overall band',
      color: 'text-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-950/30',
    },
  ]

  return (
    <div className='grid grid-cols-3 gap-4'>
      {cards.map(({ icon: Icon, label, value, sub, color, bg }) => (
        <div
          key={label}
          className='rounded-xl border bg-card px-5 py-4 flex items-center gap-4'
        >
          <div className={`rounded-lg p-2.5 ${bg}`}>
            <Icon className={`size-5 ${color}`} />
          </div>
          <div>
            <p className='text-2xl font-bold tabular-nums'>{value}</p>
            <p className='text-xs text-muted-foreground'>{label}</p>
            <p className='text-xs text-muted-foreground/70'>{sub}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Filter tabs ───────────────────────────────────────────────────────────────

type Filter = 'all' | 'scored' | 'completed' | 'in_progress'

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'scored', label: 'Scored' },
  { key: 'completed', label: 'Evaluating' },
  { key: 'in_progress', label: 'In Progress' },
]

// ── Row ───────────────────────────────────────────────────────────────────────

function ResultRow({ r, index }: { r: AttemptListItem; index: number }) {
  const { date, time } = formatDate(r.created_at)

  return (
    <tr className='group border-b border-border/50 last:border-0 hover:bg-muted/40 transition-colors'>
      <td className='py-3.5 pl-6 pr-3 text-sm text-muted-foreground tabular-nums w-10'>
        {index + 1}
      </td>
      <td className='py-3.5 px-3'>
        <p className='font-medium text-sm leading-snug'>{r.test_title}</p>
        <p className='text-xs text-muted-foreground mt-0.5'>
          {date} · {time}
        </p>
      </td>
      <td className='py-3.5 px-3 text-center'>
        <StatusBadge status={r.status} />
      </td>
      <td className='py-3.5 px-3 text-center'>
        <BandPill band={r.overall_band} />
      </td>
      <td className='py-3.5 px-3 text-center'>
        <BandPill band={r.listening_band} />
      </td>
      <td className='py-3.5 px-3 text-center'>
        <BandPill band={r.reading_band} />
      </td>
      <td className='py-3.5 px-3 text-center'>
        <BandPill band={r.writing_band} />
      </td>
      <td className='py-3.5 px-3 text-center'>
        <BandPill band={r.speaking_band} />
      </td>
      <td className='py-3.5 pl-3 pr-6 text-right'>
        <Button asChild size='sm' variant='ghost' className='gap-1.5 text-xs'>
          <Link to='/results/$attemptId' params={{ attemptId: r.id }}>
            View
            <ArrowUpRight className='size-3.5' />
          </Link>
        </Button>
      </td>
    </tr>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────

export function Results() {
  const [filter, setFilter] = useState<Filter>('all')

  const { data: results = [], isLoading } = useQuery({
    queryKey: ['results'],
    queryFn: fetchResults,
  })

  const filtered =
    filter === 'all' ? results : results.filter((r) => r.status === filter)

  const counts: Record<Filter, number> = {
    all: results.length,
    scored: results.filter((r) => r.status === 'scored').length,
    completed: results.filter((r) => r.status === 'completed').length,
    in_progress: results.filter((r) => r.status === 'in_progress').length,
  }

  return (
    <>
      <Header fixed>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-6'>
        {/* Page title */}
        <div>
          <h2 className='text-2xl font-bold tracking-tight'>Results</h2>
          <p className='text-muted-foreground text-sm mt-1'>
            View test attempt results and AI evaluation feedback.
          </p>
        </div>

        {!isLoading && results.length > 0 && (
          <SummaryCards results={results} />
        )}

        {/* Filter tabs */}
        {!isLoading && results.length > 0 && (
          <div className='flex gap-1 border-b'>
            {FILTERS.map(({ key, label }) => {
              const count = counts[key]
              if (key !== 'all' && count === 0) return null
              return (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    filter === key
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {label}
                  {count > 0 && (
                    <span className='ml-1.5 rounded-full bg-muted px-1.5 py-0.5 text-xs tabular-nums'>
                      {count}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        )}

        {/* Table */}
        {isLoading ? (
          <div className='space-y-3'>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className='h-16 rounded-xl bg-muted/50 animate-pulse' />
            ))}
          </div>
        ) : results.length === 0 ? (
          <div className='flex flex-col items-center justify-center rounded-xl border bg-card py-20 gap-3'>
            <BookOpen className='size-10 text-muted-foreground/40' />
            <p className='text-muted-foreground font-medium'>No test attempts yet</p>
            <p className='text-sm text-muted-foreground/60'>Take a test to see results here.</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className='rounded-xl border bg-card py-16 text-center text-muted-foreground'>
            No attempts match this filter.
          </div>
        ) : (
          <div className='rounded-xl border bg-card overflow-hidden'>
            <table className='w-full'>
              <thead>
                <tr className='border-b bg-muted/30'>
                  <th className='py-3 pl-6 pr-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide w-10'>
                    #
                  </th>
                  <th className='py-3 px-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                    Test
                  </th>
                  <th className='py-3 px-3 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                    Status
                  </th>
                  <th className='py-3 px-3 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                    Overall
                  </th>
                  <th className='py-3 px-3 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                    Listening
                  </th>
                  <th className='py-3 px-3 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                    Reading
                  </th>
                  <th className='py-3 px-3 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                    Writing
                  </th>
                  <th className='py-3 px-3 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                    Speaking
                  </th>
                  <th className='py-3 pl-3 pr-6' />
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <ResultRow key={r.id} r={r} index={i} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Main>
    </>
  )
}
