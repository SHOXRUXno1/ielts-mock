import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import {
  ArrowLeft,
  BookOpen,
  Headphones,
  Loader2,
  Mic,
  Pencil,
  PenLine,
  Phone,
  Trash2,
  UserCheck,
  Users,
} from 'lucide-react'
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { toast } from 'sonner'
import { fetchStudentResults } from '@/lib/api/attempts'
import { apiErrorMessage } from '@/lib/api/error'
import { deleteStudent, updateStudent } from '@/lib/api/students'
import type { Student } from '@/features/students/data/schema'
import { AttemptRowActions } from '@/features/results/components/attempt-row-actions'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { ThemeSwitch } from '@/components/theme-switch'
import { cn } from '@/lib/utils'

const SCORED_STATUSES = new Set([
  'auto_scored',
  'fully_scored',
  'scored',
  'completed_without_speaking',
])

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0][0]?.toUpperCase() ?? '?'
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

function relativeDate(iso: string | null): string {
  if (!iso) return '—'
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
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function formatBand(band: number | null): string {
  if (band === null) return '—'
  return band % 1 === 0 ? band.toFixed(1) : String(band)
}

function StatusBadge({ status }: { status: string }) {
  if (SCORED_STATUSES.has(status)) {
    return (
      <Badge className='border-0 bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950 dark:text-emerald-400'>
        Scored
      </Badge>
    )
  }
  if (status === 'completed' || status === 'speaking_in_progress') {
    return (
      <Badge className='border-0 bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-950 dark:text-blue-400'>
        Evaluating
      </Badge>
    )
  }
  if (status === 'in_progress') {
    return (
      <Badge className='border-0 bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-950 dark:text-amber-400'>
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

const SECTION_META = [
  { key: 'listening' as const, label: 'Listening', icon: Headphones },
  { key: 'reading' as const, label: 'Reading', icon: BookOpen },
  { key: 'writing' as const, label: 'Writing', icon: PenLine },
  { key: 'speaking' as const, label: 'Speaking', icon: Mic },
]

export type StudentResultDetailProps = {
  studentId: string
  backTo?: '/results' | '/students'
  backLabel?: string
  /** Opens edit flow (requires StudentsProvider on the page). */
  onEdit?: (student: Student) => void
}

export function StudentResultDetail({
  studentId,
  backTo = '/results',
  backLabel,
  onEdit,
}: StudentResultDetailProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [deleteOpen, setDeleteOpen] = useState(false)

  const resolvedBackLabel =
    backLabel ?? (backTo === '/students' ? 'Back to Students' : 'Back to Results')

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['student-results', studentId],
    queryFn: () => fetchStudentResults(studentId),
  })

  const invalidateAll = () => {
    void queryClient.invalidateQueries({ queryKey: ['student-results', studentId] })
    void queryClient.invalidateQueries({ queryKey: ['students'] })
    void queryClient.invalidateQueries({ queryKey: ['results'] })
  }

  const deleteMutation = useMutation({
    mutationFn: () => deleteStudent(studentId),
    onSuccess: () => {
      toast.success('Student deactivated', {
        description: 'They can no longer sign in. Past attempts remain in Results.',
      })
      setDeleteOpen(false)
      invalidateAll()
      void navigate({ to: backTo })
    },
    onError: (err) =>
      toast.error(apiErrorMessage(err, 'Could not deactivate this student.')),
  })

  const activateMutation = useMutation({
    mutationFn: () => updateStudent(studentId, { is_active: true }),
    onSuccess: () => {
      toast.success('Student activated', {
        description: 'They can sign in again.',
      })
      invalidateAll()
    },
    onError: (err) =>
      toast.error(apiErrorMessage(err, 'Could not activate this student.')),
  })

  if (isLoading) {
    return (
      <>
        <Header fixed>
          <div className='me-auto' />
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </Header>
        <Main>
          <div className='flex h-64 flex-col items-center justify-center gap-3'>
            <Loader2 className='size-8 animate-spin text-muted-foreground' />
            <p className='text-sm text-muted-foreground'>Loading student profile…</p>
          </div>
        </Main>
      </>
    )
  }

  if (isError || !data) {
    return (
      <>
        <Header fixed>
          <div className='me-auto' />
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </Header>
        <Main>
          <div className='mx-auto flex max-w-md flex-col items-center gap-3 py-16 text-center'>
            <p className='text-lg font-medium'>Student not found</p>
            <p className='text-sm text-muted-foreground'>
              {apiErrorMessage(error, 'This student may have been removed or the link is invalid.')}
            </p>
            <Button asChild variant='outline' className='mt-2'>
              <Link to={backTo}>
                <ArrowLeft className='mr-1.5 size-4' />
                {resolvedBackLabel}
              </Link>
            </Button>
          </div>
        </Main>
      </>
    )
  }

  const { student, stats, band_progression, section_averages, attempts } = data
  const displayName = student.full_name || student.login
  const chartData = band_progression.map((p) => ({
    label: new Date(p.date).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
    }),
    band: p.band,
    test: p.test_name,
  }))

  const studentForEdit: Student = {
    id: student.id,
    login: student.login,
    full_name: student.full_name,
    phone: student.phone ?? null,
    group_name: student.group_name ?? null,
    role: 'student',
    is_active: student.is_active ?? true,
    created_at: student.created_at,
  }

  return (
    <>
      <Header fixed>
        <div className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-6'>
        <Link
          to={backTo}
          className='inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground'
        >
          <ArrowLeft className='size-4' />
          {resolvedBackLabel}
        </Link>

        {/* Profile header */}
        <div className='rounded-xl border bg-card p-6'>
          <div className='flex flex-wrap items-start justify-between gap-4'>
            <div className='flex min-w-0 items-start gap-4'>
              <span className='flex size-16 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xl font-semibold text-blue-700 dark:bg-blue-950 dark:text-blue-300'>
                {getInitials(displayName)}
              </span>
              <div className='min-w-0 space-y-2'>
                <div className='flex flex-wrap items-center gap-2'>
                  <h1 className='truncate text-xl font-semibold tracking-tight'>
                    {displayName}
                  </h1>
                  {student.is_active ? (
                    <Badge
                      variant='outline'
                      className='border-emerald-300 text-emerald-700 dark:border-emerald-800 dark:text-emerald-400'
                    >
                      Active
                    </Badge>
                  ) : (
                    <Badge variant='outline' className='text-muted-foreground'>
                      Inactive
                    </Badge>
                  )}
                </div>

                <p className='text-sm text-muted-foreground'>
                  <code className='rounded bg-muted px-1.5 py-0.5 text-xs'>
                    {student.login}
                  </code>
                </p>

                <div className='flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground'>
                  {student.phone && (
                    <span className='inline-flex items-center gap-1.5'>
                      <Phone className='size-3.5' />
                      {student.phone}
                    </span>
                  )}
                  {student.group_name && (
                    <span className='inline-flex items-center gap-1.5'>
                      <Users className='size-3.5' />
                      {student.group_name}
                    </span>
                  )}
                  <span>Joined {relativeDate(student.created_at)}</span>
                </div>
              </div>
            </div>

            <div className='flex flex-wrap items-center gap-2'>
              {onEdit && (
                <Button
                  variant='outline'
                  className='gap-1.5'
                  onClick={() => onEdit(studentForEdit)}
                >
                  <Pencil className='size-4' />
                  Edit
                </Button>
              )}
              {!student.is_active ? (
                <Button
                  variant='outline'
                  className='gap-1.5 text-emerald-700 hover:text-emerald-800 dark:text-emerald-400'
                  onClick={() => activateMutation.mutate()}
                  disabled={activateMutation.isPending}
                >
                  {activateMutation.isPending ? (
                    <Loader2 className='size-4 animate-spin' />
                  ) : (
                    <UserCheck className='size-4' />
                  )}
                  Activate
                </Button>
              ) : (
                <Button
                  variant='outline'
                  className='gap-1.5 text-destructive hover:bg-destructive/10 hover:text-destructive'
                  onClick={() => setDeleteOpen(true)}
                >
                  <Trash2 className='size-4' />
                  Deactivate
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className='grid grid-cols-2 gap-4 lg:grid-cols-4'>
          {[
            { label: 'Attempts', value: String(stats.attempts_count) },
            { label: 'Best Band', value: formatBand(stats.best_band) },
            { label: 'Avg Band', value: formatBand(stats.average_band) },
            { label: 'Last Attempt', value: relativeDate(stats.last_attempt_at) },
          ].map((c) => (
            <div key={c.label} className='rounded-xl border bg-card px-5 py-4'>
              <p className='text-2xl font-bold tabular-nums tracking-tight'>{c.value}</p>
              <p className='mt-0.5 text-xs text-muted-foreground'>{c.label}</p>
            </div>
          ))}
        </div>

        {/* Band progression */}
        <div className='rounded-xl border bg-card p-5'>
          <h2 className='mb-1 text-sm font-medium'>Band progression</h2>
          <p className='mb-4 text-xs text-muted-foreground'>
            Last {band_progression.length || 0} scored attempts
          </p>
          {chartData.length < 2 ? (
            <div className='flex flex-col items-center justify-center gap-1 rounded-lg border border-dashed bg-muted/20 py-10 text-center'>
              <p className='text-sm font-medium text-muted-foreground'>
                Not enough data for a trend
              </p>
              <p className='max-w-xs text-xs text-muted-foreground'>
                At least two scored attempts are needed to show band progression.
              </p>
            </div>
          ) : (
            <ResponsiveContainer width='100%' height={200}>
              <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                <XAxis
                  dataKey='label'
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 9]}
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  width={28}
                />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                    background: 'var(--card)',
                    color: 'var(--card-foreground)',
                  }}
                  formatter={(value) => [
                    typeof value === 'number' ? value.toFixed(1) : String(value ?? '—'),
                    'Band',
                  ]}
                  labelFormatter={(_, payload) => {
                    const row = payload?.[0]?.payload as
                      | { label?: string; test?: string }
                      | undefined
                    if (row?.test) return `${row.label ?? ''} · ${row.test}`
                    return String(row?.label ?? '')
                  }}
                />
                <Line
                  type='monotone'
                  dataKey='band'
                  stroke='#3b82f6'
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Section averages */}
        <div className='rounded-xl border bg-card p-5'>
          <h2 className='mb-4 text-sm font-medium'>Section averages</h2>
          <div className='space-y-3'>
            {SECTION_META.map(({ key, label, icon: Icon }) => {
              const band = section_averages[key]
              const pct = band != null ? (band / 9) * 100 : 0
              return (
                <div key={key} className='flex items-center gap-3'>
                  <Icon className='size-4 shrink-0 text-muted-foreground' />
                  <span className='w-20 text-sm text-muted-foreground'>{label}</span>
                  <div className='h-2 flex-1 overflow-hidden rounded-full bg-muted'>
                    <div
                      className={cn(
                        'h-full rounded-full bg-blue-500 transition-all',
                        band == null && 'opacity-0',
                      )}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className='w-8 text-right text-sm font-medium tabular-nums text-foreground'>
                    {formatBand(band)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Attempts table */}
        <div>
          <div className='mb-3 flex items-center justify-between gap-2'>
            <h2 className='text-sm font-medium'>All attempts</h2>
            <span className='text-xs text-muted-foreground'>
              {attempts.length} total
            </span>
          </div>
          {attempts.length === 0 ? (
            <div className='flex flex-col items-center justify-center gap-1 rounded-xl border border-dashed bg-muted/20 py-12 text-center'>
              <p className='text-sm font-medium text-muted-foreground'>No attempts yet</p>
              <p className='max-w-sm text-xs text-muted-foreground'>
                When this student completes a test, scores and history will appear here.
              </p>
            </div>
          ) : (
            <div className='overflow-hidden rounded-xl border bg-card'>
              <div className='overflow-x-auto'>
                <table className='w-full'>
                  <thead>
                    <tr className='border-b bg-muted/30'>
                      <th className='px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        Test
                      </th>
                      <th className='px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        Date
                      </th>
                      <th className='px-3 py-3 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        Status
                      </th>
                      <th className='px-3 py-3 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        Overall
                      </th>
                      <th className='px-3 py-3 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        L
                      </th>
                      <th className='px-3 py-3 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        R
                      </th>
                      <th className='px-3 py-3 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        W
                      </th>
                      <th className='px-3 py-3 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground'>
                        S
                      </th>
                      <th className='px-4 py-3' />
                    </tr>
                  </thead>
                  <tbody>
                    {attempts.map((a) => (
                      <tr
                        key={a.id}
                        className='border-b border-border/50 last:border-0 hover:bg-muted/40'
                      >
                        <td className='px-4 py-3 text-sm font-medium'>{a.test_title}</td>
                        <td className='px-3 py-3 text-sm text-muted-foreground'>
                          {relativeDate(a.created_at)}
                        </td>
                        <td className='px-3 py-3 text-center'>
                          <StatusBadge status={a.status} />
                        </td>
                        <td className='px-3 py-3 text-center text-sm font-semibold tabular-nums'>
                          {formatBand(a.overall_band)}
                        </td>
                        <td className='px-3 py-3 text-center text-sm tabular-nums text-muted-foreground'>
                          {formatBand(a.listening_band)}
                        </td>
                        <td className='px-3 py-3 text-center text-sm tabular-nums text-muted-foreground'>
                          {formatBand(a.reading_band)}
                        </td>
                        <td className='px-3 py-3 text-center text-sm tabular-nums text-muted-foreground'>
                          {formatBand(a.writing_band)}
                        </td>
                        <td className='px-3 py-3 text-center text-sm tabular-nums text-muted-foreground'>
                          {formatBand(a.speaking_band)}
                        </td>
                        <td className='px-4 py-3 text-right'>
                          <AttemptRowActions
                            attemptId={a.id}
                            invalidateKeys={[
                              ['results'],
                              ['student-results', studentId],
                            ]}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </Main>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Deactivate this student?</AlertDialogTitle>
            <AlertDialogDescription>
              <span className='font-medium text-foreground'>{displayName}</span> will
              be deactivated and can no longer sign in. Their past attempts remain in
              Results.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className='bg-destructive text-destructive-foreground hover:bg-destructive/90'
              disabled={deleteMutation.isPending}
              onClick={(e) => {
                e.preventDefault()
                deleteMutation.mutate()
              }}
            >
              {deleteMutation.isPending && <Loader2 className='mr-2 size-4 animate-spin' />}
              Deactivate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
