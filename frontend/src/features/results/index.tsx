import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  BookOpen,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock,
  Download,
  Percent,
  Search,
  Trophy,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { fetchResults } from '@/lib/api/attempts'
import type { AttemptListItem } from '@/lib/api/attempts'
import { AttemptRowActions } from '@/features/results/components/attempt-row-actions'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { ThemeSwitch } from '@/components/theme-switch'

const PAGE_SIZE = 20

const SCORED_STATUSES = new Set([
  'auto_scored',
  'fully_scored',
  'scored',
  'completed_without_speaking',
])

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

function relativeDate(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diffSec = Math.floor((now - then) / 1000)
  if (diffSec < 60) return 'just now'
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h ago`
  const diffD = Math.floor(diffH / 24)
  if (diffD < 7) return `${diffD}d ago`
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

function getInitials(name: string | null): string {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`
  return value
}

function downloadResultsCsv(rows: AttemptListItem[], filename: string) {
  const header =
    'Student Name,Test,Date,Status,Overall,Listening,Reading,Writing,Speaking'
  const lines = rows.map((r) =>
    [
      csvEscape(r.student_name ?? ''),
      csvEscape(r.test_title),
      new Date(r.created_at).toISOString(),
      r.status,
      r.overall_band ?? '',
      r.listening_band ?? '',
      r.reading_band ?? '',
      r.writing_band ?? '',
      r.speaking_band ?? '',
    ].join(','),
  )
  const blob = new Blob([[header, ...lines].join('\n')], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function exportFilename(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `results-export-${y}-${m}-${day}.csv`
}

// ── Status badges ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  if (SCORED_STATUSES.has(status)) {
    return (
      <Badge className='border-0 bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/40 dark:text-emerald-400'>
        Scored
      </Badge>
    )
  }
  if (status === 'completed' || status === 'speaking_in_progress') {
    return (
      <Badge className='border-0 bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/40 dark:text-blue-400'>
        Evaluating
      </Badge>
    )
  }
  if (status === 'in_progress') {
    return (
      <Badge className='border-0 bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/40 dark:text-amber-400'>
        In Progress
      </Badge>
    )
  }
  return (
    <Badge variant='outline' className='text-muted-foreground'>
      Abandoned
    </Badge>
  )
}

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
  const scored = results.filter((r) => SCORED_STATUSES.has(r.status))
  const withBand = scored.filter((r) => r.overall_band != null && r.overall_band > 0)
  const best = withBand.length ? Math.max(...withBand.map((r) => r.overall_band!)) : null
  const avg = withBand.length
    ? withBand.reduce((s, r) => s + r.overall_band!, 0) / withBand.length
    : null
  const rate = results.length > 0 ? Math.round((scored.length / results.length) * 100) : 0

  const cards = [
    {
      icon: BookOpen,
      label: 'Total Attempts',
      value: String(results.length),
      sub: `${scored.length} scored`,
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950/30',
    },
    {
      icon: Trophy,
      label: 'Best Band',
      value: best !== null ? best.toFixed(1) : '—',
      sub: 'overall band',
      color: 'text-emerald-600',
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    },
    {
      icon: Clock,
      label: 'Average Band',
      value: avg !== null ? avg.toFixed(1) : '—',
      sub: `across ${withBand.length} scored`,
      color: 'text-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-950/30',
    },
    {
      icon: Percent,
      label: 'Completion Rate',
      value: `${rate}%`,
      sub: `${scored.length} of ${results.length}`,
      color: 'text-violet-600',
      bg: 'bg-violet-50 dark:bg-violet-950/30',
    },
  ]

  return (
    <div className='grid grid-cols-2 gap-4 lg:grid-cols-4'>
      {cards.map(({ icon: Icon, label, value, sub, color, bg }) => (
        <div key={label} className='flex items-center gap-4 rounded-xl border bg-card px-5 py-4'>
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

// ── Filter / sort types ───────────────────────────────────────────────────────

type Filter = 'all' | 'scored' | 'evaluating' | 'in_progress'
type SortKey = 'student' | 'date' | 'overall' | 'listening' | 'reading' | 'writing' | 'speaking'
type SortDir = 'asc' | 'desc'
type DatePreset = 'all' | 'today' | '7d' | '30d' | 'custom'

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'scored', label: 'Scored' },
  { key: 'evaluating', label: 'Evaluating' },
  { key: 'in_progress', label: 'In Progress' },
]

function matchesFilter(status: string, filter: Filter): boolean {
  if (filter === 'all') return true
  if (filter === 'scored') return SCORED_STATUSES.has(status)
  if (filter === 'evaluating') return status === 'completed' || status === 'speaking_in_progress'
  return status === 'in_progress'
}

function compareItems(a: AttemptListItem, b: AttemptListItem, key: SortKey, dir: SortDir): number {
  let cmp = 0
  switch (key) {
    case 'student':
      cmp = (a.student_name ?? '').localeCompare(b.student_name ?? '')
      break
    case 'date':
      cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      break
    case 'overall':
      cmp = (a.overall_band ?? -1) - (b.overall_band ?? -1)
      break
    case 'listening':
      cmp = (a.listening_band ?? -1) - (b.listening_band ?? -1)
      break
    case 'reading':
      cmp = (a.reading_band ?? -1) - (b.reading_band ?? -1)
      break
    case 'writing':
      cmp = (a.writing_band ?? -1) - (b.writing_band ?? -1)
      break
    case 'speaking':
      cmp = (a.speaking_band ?? -1) - (b.speaking_band ?? -1)
      break
  }
  return dir === 'asc' ? cmp : -cmp
}

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <ChevronDown className='size-3 text-muted-foreground/40' />
  return dir === 'asc' ? (
    <ChevronUp className='size-3 text-primary' />
  ) : (
    <ChevronDown className='size-3 text-primary' />
  )
}

function useDebouncedValue(value: string, delayMs: number): string {
  const [debounced, setDebounced] = useState(value)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  useEffect(() => {
    timer.current = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer.current)
  }, [value, delayMs])
  return debounced
}

function startOfDay(d: Date): Date {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  return x
}

function datePresetRange(
  preset: DatePreset,
  customFrom: string,
  customTo: string,
): { from: Date | null; to: Date | null } {
  const now = new Date()
  if (preset === 'all') return { from: null, to: null }
  if (preset === 'today') return { from: startOfDay(now), to: null }
  if (preset === '7d') {
    const from = startOfDay(now)
    from.setDate(from.getDate() - 7)
    return { from, to: null }
  }
  if (preset === '30d') {
    const from = startOfDay(now)
    from.setDate(from.getDate() - 30)
    return { from, to: null }
  }
  return {
    from: customFrom ? startOfDay(new Date(customFrom)) : null,
    to: customTo
      ? (() => {
          const t = startOfDay(new Date(customTo))
          t.setHours(23, 59, 59, 999)
          return t
        })()
      : null,
  }
}

// ── Sortable header ───────────────────────────────────────────────────────────

function SortableHeader({
  label,
  sortKey: key,
  currentKey,
  currentDir,
  onSort,
  center = false,
}: {
  label: string
  sortKey: SortKey
  currentKey: SortKey
  currentDir: SortDir
  onSort: (key: SortKey) => void
  center?: boolean
}) {
  return (
    <th
      className={`cursor-pointer select-none px-3 py-3 text-xs font-medium uppercase tracking-wide text-muted-foreground transition-colors hover:text-foreground ${center ? 'text-center' : 'text-left'}`}
      onClick={() => onSort(key)}
    >
      <span className='inline-flex items-center gap-1'>
        {label}
        <SortIcon active={currentKey === key} dir={currentDir} />
      </span>
    </th>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────

export function Results() {
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const [sortKey, setSortKey] = useState<SortKey>('date')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [page, setPage] = useState(0)

  const [selectedTestIds, setSelectedTestIds] = useState<Set<string>>(new Set())
  const [datePreset, setDatePreset] = useState<DatePreset>('all')
  const [customFrom, setCustomFrom] = useState('')
  const [customTo, setCustomTo] = useState('')
  const [bandMin, setBandMin] = useState('')
  const [bandMax, setBandMax] = useState('')

  const { data: results = [], isLoading } = useQuery({
    queryKey: ['results'],
    queryFn: () => fetchResults(),
  })

  const tests = useMemo(() => {
    const map = new Map<string, string>()
    for (const r of results) {
      if (!map.has(r.test_id)) map.set(r.test_id, r.test_title)
    }
    return [...map.entries()].map(([id, title]) => ({ id, title }))
  }, [results])

  const handleSort = useCallback(
    (key: SortKey) => {
      if (key === sortKey) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
      } else {
        setSortKey(key)
        setSortDir(key === 'date' ? 'desc' : 'asc')
      }
    },
    [sortKey],
  )

  useEffect(() => setPage(0), [
    filter,
    debouncedSearch,
    sortKey,
    sortDir,
    selectedTestIds,
    datePreset,
    customFrom,
    customTo,
    bandMin,
    bandMax,
  ])

  const processed = useMemo(() => {
    let list = results

    if (filter !== 'all') {
      list = list.filter((r) => matchesFilter(r.status, filter))
    }

    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase()
      list = list.filter(
        (r) =>
          (r.student_name ?? '').toLowerCase().includes(q) ||
          r.test_title.toLowerCase().includes(q),
      )
    }

    if (selectedTestIds.size > 0) {
      list = list.filter((r) => selectedTestIds.has(r.test_id))
    }

    const { from, to } = datePresetRange(datePreset, customFrom, customTo)
    if (from || to) {
      list = list.filter((r) => {
        const t = new Date(r.created_at).getTime()
        if (from && t < from.getTime()) return false
        if (to && t > to.getTime()) return false
        return true
      })
    }

    const minB = bandMin !== '' ? Number(bandMin) : null
    const maxB = bandMax !== '' ? Number(bandMax) : null
    if (minB != null || maxB != null) {
      list = list.filter((r) => {
        if (r.overall_band == null) return false
        if (minB != null && r.overall_band < minB) return false
        if (maxB != null && r.overall_band > maxB) return false
        return true
      })
    }

    return [...list].sort((a, b) => compareItems(a, b, sortKey, sortDir))
  }, [
    results,
    filter,
    debouncedSearch,
    selectedTestIds,
    datePreset,
    customFrom,
    customTo,
    bandMin,
    bandMax,
    sortKey,
    sortDir,
  ])

  const totalPages = Math.max(1, Math.ceil(processed.length / PAGE_SIZE))
  const pageItems = processed.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const showFrom = processed.length === 0 ? 0 : page * PAGE_SIZE + 1
  const showTo = Math.min((page + 1) * PAGE_SIZE, processed.length)

  const counts: Record<Filter, number> = useMemo(
    () => ({
      all: results.length,
      scored: results.filter((r) => matchesFilter(r.status, 'scored')).length,
      evaluating: results.filter((r) => matchesFilter(r.status, 'evaluating')).length,
      in_progress: results.filter((r) => matchesFilter(r.status, 'in_progress')).length,
    }),
    [results],
  )

  const resetFilters = () => {
    setSearch('')
    setFilter('all')
    setSelectedTestIds(new Set())
    setDatePreset('all')
    setCustomFrom('')
    setCustomTo('')
    setBandMin('')
    setBandMax('')
    setPage(0)
  }

  const dateLabel =
    datePreset === 'all'
      ? 'All time'
      : datePreset === 'today'
        ? 'Today'
        : datePreset === '7d'
          ? 'Last 7 days'
          : datePreset === '30d'
            ? 'Last 30 days'
            : 'Custom'

  const bandChip =
    bandMin !== '' || bandMax !== ''
      ? `Band ${bandMin || '0'}–${bandMax || '9'}`
      : null

  return (
    <>
      <Header fixed>
        <div className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-6'>
        <div>
          <h2 className='text-2xl font-bold tracking-tight'>Results</h2>
          <p className='mt-1 text-sm text-muted-foreground'>
            View test attempt results and AI evaluation feedback.
          </p>
        </div>

        {!isLoading && results.length > 0 && <SummaryCards results={results} />}

        {!isLoading && results.length > 0 && (
          <div className='space-y-3'>
            <div className='relative max-w-sm'>
              <Search
                size={14}
                className='absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground'
              />
              <Input
                placeholder='Search students or tests...'
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className='h-9 pl-9 text-sm'
              />
            </div>

            {/* Advanced filters */}
            <div className='flex flex-wrap items-center gap-2'>
              {/* Test multi-select */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant='outline' size='sm' className='h-8 gap-1 text-xs'>
                    {selectedTestIds.size > 0 ? `Tests (${selectedTestIds.size})` : 'Test'}
                    <ChevronDown className='size-3' />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className='w-64 p-2' align='start'>
                  <div className='mb-2 flex gap-1'>
                    <Button
                      variant='ghost'
                      size='sm'
                      className='h-7 text-xs'
                      onClick={() => setSelectedTestIds(new Set(tests.map((t) => t.id)))}
                    >
                      Select all
                    </Button>
                    <Button
                      variant='ghost'
                      size='sm'
                      className='h-7 text-xs'
                      onClick={() => setSelectedTestIds(new Set())}
                    >
                      Clear
                    </Button>
                  </div>
                  <div className='max-h-48 space-y-1 overflow-y-auto'>
                    {tests.map((t) => (
                      <label
                        key={t.id}
                        className='flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-muted'
                      >
                        <Checkbox
                          checked={selectedTestIds.has(t.id)}
                          onCheckedChange={(checked) => {
                            setSelectedTestIds((prev) => {
                              const next = new Set(prev)
                              if (checked) next.add(t.id)
                              else next.delete(t.id)
                              return next
                            })
                          }}
                        />
                        <span className='truncate'>{t.title}</span>
                      </label>
                    ))}
                  </div>
                </PopoverContent>
              </Popover>

              {/* Date range */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant='outline' size='sm' className='h-8 gap-1 text-xs'>
                    {dateLabel}
                    <ChevronDown className='size-3' />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className='w-64 space-y-2 p-3' align='start'>
                  {(
                    [
                      ['all', 'All time'],
                      ['today', 'Today'],
                      ['7d', 'Last 7 days'],
                      ['30d', 'Last 30 days'],
                      ['custom', 'Custom'],
                    ] as const
                  ).map(([key, label]) => (
                    <button
                      key={key}
                      type='button'
                      className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm hover:bg-muted ${datePreset === key ? 'bg-muted font-medium' : ''}`}
                      onClick={() => setDatePreset(key)}
                    >
                      {datePreset === key && <Check className='size-3.5' />}
                      {label}
                    </button>
                  ))}
                  {datePreset === 'custom' && (
                    <div className='space-y-2 border-t pt-2'>
                      <Input
                        type='date'
                        value={customFrom}
                        onChange={(e) => setCustomFrom(e.target.value)}
                        className='h-8 text-xs'
                      />
                      <Input
                        type='date'
                        value={customTo}
                        onChange={(e) => setCustomTo(e.target.value)}
                        className='h-8 text-xs'
                      />
                    </div>
                  )}
                </PopoverContent>
              </Popover>

              {/* Band range */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant='outline' size='sm' className='h-8 gap-1 text-xs'>
                    {bandChip ?? 'Any band'}
                    <ChevronDown className='size-3' />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className='w-56 space-y-2 p-3' align='start'>
                  <div className='flex items-center gap-2'>
                    <Input
                      type='number'
                      min={0}
                      max={9}
                      step={0.5}
                      placeholder='Min'
                      value={bandMin}
                      onChange={(e) => setBandMin(e.target.value)}
                      className='h-8 text-xs'
                    />
                    <span className='text-xs text-muted-foreground'>—</span>
                    <Input
                      type='number'
                      min={0}
                      max={9}
                      step={0.5}
                      placeholder='Max'
                      value={bandMax}
                      onChange={(e) => setBandMax(e.target.value)}
                      className='h-8 text-xs'
                    />
                  </div>
                  <Button
                    variant='ghost'
                    size='sm'
                    className='h-7 w-full text-xs'
                    onClick={() => {
                      setBandMin('')
                      setBandMax('')
                    }}
                  >
                    Clear
                  </Button>
                </PopoverContent>
              </Popover>

              <Button variant='ghost' size='sm' className='h-8 text-xs' onClick={resetFilters}>
                Reset
              </Button>
              <Button
                variant='outline'
                size='sm'
                className='h-8 gap-1 text-xs'
                onClick={() => {
                  downloadResultsCsv(processed, exportFilename())
                  toast.success(`Exported ${processed.length} rows`)
                }}
              >
                <Download className='size-3.5' />
                Export CSV
              </Button>
            </div>

            {/* Applied chips */}
            {(selectedTestIds.size > 0 || datePreset !== 'all' || bandChip) && (
              <div className='flex flex-wrap gap-2'>
                {[...selectedTestIds].map((id) => {
                  const title = tests.find((t) => t.id === id)?.title ?? id
                  return (
                    <button
                      key={id}
                      type='button'
                      className='inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs text-blue-700'
                      onClick={() =>
                        setSelectedTestIds((prev) => {
                          const next = new Set(prev)
                          next.delete(id)
                          return next
                        })
                      }
                    >
                      Test: {title}
                      <X className='size-3' />
                    </button>
                  )
                })}
                {datePreset !== 'all' && (
                  <button
                    type='button'
                    className='inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs text-blue-700'
                    onClick={() => {
                      setDatePreset('all')
                      setCustomFrom('')
                      setCustomTo('')
                    }}
                  >
                    {dateLabel}
                    <X className='size-3' />
                  </button>
                )}
                {bandChip && (
                  <button
                    type='button'
                    className='inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs text-blue-700'
                    onClick={() => {
                      setBandMin('')
                      setBandMax('')
                    }}
                  >
                    {bandChip}
                    <X className='size-3' />
                  </button>
                )}
              </div>
            )}

            {/* Status tabs */}
            <div className='flex gap-1 border-b'>
              {FILTERS.map(({ key, label }) => {
                const count = counts[key]
                if (key !== 'all' && count === 0) return null
                return (
                  <button
                    key={key}
                    type='button'
                    onClick={() => setFilter(key)}
                    className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
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
          </div>
        )}

        {isLoading ? (
          <div className='space-y-3'>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className='h-14 animate-pulse rounded-xl bg-muted/50' />
            ))}
          </div>
        ) : results.length === 0 ? (
          <div className='flex flex-col items-center justify-center gap-3 rounded-xl border bg-card py-20'>
            <BookOpen className='size-10 text-muted-foreground/40' />
            <p className='font-medium text-muted-foreground'>No test attempts yet</p>
            <p className='text-sm text-muted-foreground/60'>
              Students haven&apos;t taken any tests.
            </p>
          </div>
        ) : processed.length === 0 ? (
          <div className='rounded-xl border bg-card py-16 text-center text-muted-foreground'>
            No attempts match your filters.
            <button
              type='button'
              className='ml-2 text-primary underline underline-offset-2'
              onClick={resetFilters}
            >
              Reset
            </button>
          </div>
        ) : (
          <div className='overflow-hidden rounded-xl border bg-card'>
            <div className='overflow-x-auto'>
              <table className='w-full'>
                <thead>
                  <tr className='border-b bg-muted/30'>
                    <SortableHeader
                      label='Student'
                      sortKey='student'
                      currentKey={sortKey}
                      currentDir={sortDir}
                      onSort={handleSort}
                    />
                    <th className='px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                      Test
                    </th>
                    <SortableHeader
                      label='Date'
                      sortKey='date'
                      currentKey={sortKey}
                      currentDir={sortDir}
                      onSort={handleSort}
                    />
                    <th className='px-3 py-3 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                      Status
                    </th>
                    <SortableHeader
                      label='Overall'
                      sortKey='overall'
                      currentKey={sortKey}
                      currentDir={sortDir}
                      onSort={handleSort}
                      center
                    />
                    <SortableHeader
                      label='L'
                      sortKey='listening'
                      currentKey={sortKey}
                      currentDir={sortDir}
                      onSort={handleSort}
                      center
                    />
                    <SortableHeader
                      label='R'
                      sortKey='reading'
                      currentKey={sortKey}
                      currentDir={sortDir}
                      onSort={handleSort}
                      center
                    />
                    <SortableHeader
                      label='W'
                      sortKey='writing'
                      currentKey={sortKey}
                      currentDir={sortDir}
                      onSort={handleSort}
                      center
                    />
                    <SortableHeader
                      label='S'
                      sortKey='speaking'
                      currentKey={sortKey}
                      currentDir={sortDir}
                      onSort={handleSort}
                      center
                    />
                    <th className='py-3 pl-3 pr-4' />
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((r) => (
                    <tr
                      key={r.id}
                      className='group border-b border-border/50 last:border-0 transition-colors hover:bg-muted/40'
                    >
                      <td className='px-3 py-3'>
                        <div className='flex items-center gap-2.5'>
                          <span className='flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300'>
                            {getInitials(r.student_name)}
                          </span>
                          {r.student_id ? (
                            <Link
                              to='/results/students/$studentId'
                              params={{ studentId: r.student_id }}
                              className='truncate text-sm font-medium hover:underline'
                            >
                              {r.student_name ?? 'Unknown'}
                            </Link>
                          ) : (
                            <span className='truncate text-sm font-medium'>
                              {r.student_name ?? 'Unknown'}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className='px-3 py-3'>
                        <p className='text-sm leading-snug'>{r.test_title}</p>
                      </td>
                      <td className='px-3 py-3 text-sm text-muted-foreground'>
                        {relativeDate(r.created_at)}
                      </td>
                      <td className='px-3 py-3 text-center'>
                        <StatusBadge status={r.status} />
                      </td>
                      <td className='px-3 py-3 text-center'>
                        <BandPill band={r.overall_band} />
                      </td>
                      <td className='px-3 py-3 text-center'>
                        <BandPill band={r.listening_band} />
                      </td>
                      <td className='px-3 py-3 text-center'>
                        <BandPill band={r.reading_band} />
                      </td>
                      <td className='px-3 py-3 text-center'>
                        <BandPill band={r.writing_band} />
                      </td>
                      <td className='px-3 py-3 text-center'>
                        <BandPill band={r.speaking_band} />
                      </td>
                      <td className='py-3 pl-3 pr-4 text-right'>
                        <AttemptRowActions attemptId={r.id} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {processed.length > PAGE_SIZE && (
              <div className='flex items-center justify-between border-t px-6 py-3'>
                <p className='text-xs tabular-nums text-muted-foreground'>
                  Showing {showFrom}–{showTo} of {processed.length}
                </p>
                <div className='flex items-center gap-1'>
                  <Button
                    variant='outline'
                    size='sm'
                    disabled={page === 0}
                    onClick={() => setPage((p) => p - 1)}
                    className='h-8 w-8 p-0'
                  >
                    <ChevronLeft className='size-4' />
                  </Button>
                  <span className='px-2 text-xs tabular-nums text-muted-foreground'>
                    {page + 1} / {totalPages}
                  </span>
                  <Button
                    variant='outline'
                    size='sm'
                    disabled={page >= totalPages - 1}
                    onClick={() => setPage((p) => p + 1)}
                    className='h-8 w-8 p-0'
                  >
                    <ChevronRight className='size-4' />
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </Main>
    </>
  )
}
