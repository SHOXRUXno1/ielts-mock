import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  GraduationCap,
  Play,
  Search,
} from 'lucide-react'
import { toast } from 'sonner'
import { EmptyState, Metric, Panel } from '@/components/report'
import { PracticePicker } from '@/features/student/practice/practice-picker'
import {
  SKILL_ICONS,
  SKILL_ORDER,
} from '@/features/student/practice/skill-icons'
import {
  getFullMockStatus,
  getTestCatalog,
  startFullMock,
  type CatalogTest,
} from '@/lib/api/student'
import { useAuthStore } from '@/stores/auth-store'
import { continueTakeSearch } from './continue-search'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

function formatDuration(minutes: number): string {
  if (minutes <= 0) return '—'
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h}h ${m}m` : `${h}h`
}

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

function PracticeCard({ test }: { test: CatalogTest }) {
  const [pickerOpen, setPickerOpen] = useState(false)
  const typeLabel = test.test_type === 'general' ? 'General' : 'Academic'

  return (
    <article className='group flex flex-col'>
      <Panel className='flex h-full flex-col transition-colors hover:bg-muted/30' padding='none'>
        <div className='flex flex-1 flex-col p-6'>
          <div className='mb-4 flex items-start justify-between gap-3'>
            <span className='inline-flex items-center rounded-full bg-muted px-2.5 py-1 text-xs font-semibold text-foreground'>
              Practice
            </span>
            <span className='rounded-md bg-muted px-2 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground'>
              {typeLabel}
            </span>
          </div>

          <h3 className='text-base font-semibold leading-snug tracking-tight text-foreground'>
            {test.title}
          </h3>
          <p className='mt-1 text-sm text-muted-foreground'>
            Drill one skill or a single part. Untimed relative to the full exam.
          </p>

          <div className='mt-4'>
            <SkillStrip test={test} />
          </div>

          <div className='mt-4 flex items-center gap-2 text-xs text-muted-foreground'>
            <span className='inline-flex items-center gap-1.5 rounded-lg bg-muted px-2 py-1'>
              <Clock size={12} />
              {formatDuration(test.duration_minutes)}
            </span>
            <span className='inline-flex items-center gap-1.5 rounded-lg bg-muted px-2 py-1'>
              {test.section_count} skills
            </span>
          </div>

          <div className='mt-6'>
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
      </div>
    </Panel>
  )
}

export function StudentTests() {
  const signedIn = useAuthStore((s) => Boolean(s.auth.accessToken))
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const catalogQuery = useQuery({
    queryKey: ['student-test-catalog'],
    queryFn: getTestCatalog,
    enabled: signedIn,
  })
  const mockQuery = useQuery({
    queryKey: ['student-full-mock-status'],
    queryFn: getFullMockStatus,
    enabled: signedIn,
  })

  const [search, setSearch] = useState('')
  const data = catalogQuery.data
  const isLoading = catalogQuery.isLoading
  const isError = catalogQuery.isError

  const allTests = useMemo(() => {
    if (!data?.groups) return []
    return data.groups.flatMap((g) => g.tests ?? [])
  }, [data])

  const filtered = useMemo(() => {
    if (!search.trim()) return allTests
    const q = search.toLowerCase()
    return allTests.filter((t) => t.title.toLowerCase().includes(q))
  }, [allTests, search])

  const startMock = useMutation({
    mutationFn: startFullMock,
    onSuccess: async (attempt) => {
      await queryClient.invalidateQueries({ queryKey: ['student-full-mock-status'] })
      await navigate({
        to: '/take-test/$testId',
        params: { testId: attempt.test_id },
      })
    },
    onError: (err: unknown) => {
      const detail = (
        err as { response?: { data?: { detail?: unknown } } }
      )?.response?.data?.detail
      const message =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail
                .map((item) =>
                  typeof item === 'string'
                    ? item
                    : (item as { msg?: string })?.msg,
                )
                .filter(Boolean)
                .join(' ')
            : ''
      toast.error(message || 'Could not start a full mock')
    },
  })

  const mock = mockQuery.data
  const canStart = (mock?.remaining ?? 0) > 0 && !mock?.in_progress_attempt_id
  const canContinue = Boolean(mock?.in_progress_attempt_id && mock.in_progress_test_id)
  const exhausted = Boolean(mock && mock.remaining === 0 && !mock.in_progress_attempt_id)

  return (
    <div className='space-y-6'>
      <Panel>
        <div className='flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between'>
          <div className='max-w-xl'>
            <p className='text-xs font-medium tracking-wider text-muted-foreground uppercase'>
              Exam conditions
            </p>
            <h1 className='mt-1 text-2xl font-semibold tracking-tight text-foreground'>
              Full mock
            </h1>
            <p className='mt-2 text-sm leading-relaxed text-muted-foreground'>
              One unused paper, assigned at random when you start. Refreshing
              this page does not pick a paper or change one already assigned.
            </p>
          </div>

          <div className='flex flex-wrap items-end gap-4'>
            {mock && (
              <Metric
                icon={GraduationCap}
                label='Remaining'
                value={String(mock.remaining)}
              />
            )}
            {canContinue ? (
              <Button
                size='lg'
                className='h-11 rounded-xl px-5'
                onClick={() =>
                  void navigate({
                    to: '/take-test/$testId',
                    params: { testId: mock!.in_progress_test_id! },
                    search: continueTakeSearch(
                      mock!.in_progress_attempt_id!,
                      mock!.in_progress_section,
                    ),
                  })
                }
              >
                Continue {mock?.in_progress_title ?? 'mock'}
                <ArrowRight size={16} className='ml-1.5' />
              </Button>
            ) : (
              <Button
                size='lg'
                className='h-11 rounded-xl px-5'
                disabled={!canStart || startMock.isPending || mockQuery.isLoading}
                onClick={() => startMock.mutate()}
              >
                <Play size={16} className='mr-1.5 fill-current' />
                {startMock.isPending ? 'Assigning…' : 'Start full mock'}
              </Button>
            )}
          </div>
        </div>
        {exhausted && (
          <p className='mt-4 text-sm text-muted-foreground'>
            You have completed every available full mock.
          </p>
        )}
      </Panel>

      <div className='flex flex-wrap items-end justify-between gap-3'>
        <div>
          <h2 className='text-lg font-semibold tracking-tight text-foreground'>
            Practice sets
          </h2>
          <p className='mt-1 text-sm text-muted-foreground'>
            Anonymous papers for section and part drills. Names stay hidden.
          </p>
        </div>
        {!isLoading && allTests.length > 0 && (
          <div className='relative min-w-[200px] max-w-sm flex-1'>
            <Search
              size={15}
              className='absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground'
            />
            <Input
              placeholder='Search practice sets…'
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className='h-10 rounded-lg border-0 bg-muted pl-9 text-sm shadow-none focus-visible:ring-1'
            />
          </div>
        )}
      </div>

      {isError ? (
        <EmptyState
          title='Could not load tests'
          description='The server did not respond. Check that the backend is running, then try again.'
          action={
            <Button
              variant='outline'
              size='sm'
              onClick={() => void catalogQuery.refetch()}
            >
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
          title='No practice sets match'
          description='Try a different search'
          action={
            <Button variant='ghost' size='sm' onClick={() => setSearch('')}>
              Clear search
            </Button>
          }
        />
      ) : (
        <div className='grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3'>
          {filtered.map((test) => (
            <PracticeCard key={test.id} test={test} />
          ))}
        </div>
      )}
    </div>
  )
}
