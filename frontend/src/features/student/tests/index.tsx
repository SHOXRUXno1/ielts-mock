import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Clock, Headphones, BookOpen, PenLine, Mic, Play, RotateCcw } from 'lucide-react'
import { getTestCatalog } from '@/lib/api/student'
import type { CatalogTest, SectionProgress } from '@/lib/api/student'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

// ── Section metadata ──────────────────────────────────────────────────────────

type SectionKey = 'listening' | 'reading' | 'writing' | 'speaking'

const SECTION_META: Record<SectionKey, { label: string; icon: React.ReactNode }> = {
  listening: { label: 'Listening', icon: <Headphones size={13} /> },
  reading:   { label: 'Reading',   icon: <BookOpen size={13} /> },
  writing:   { label: 'Writing',   icon: <PenLine size={13} /> },
  speaking:  { label: 'Speaking',  icon: <Mic size={13} /> },
}

const SECTION_ORDER: SectionKey[] = ['listening', 'reading', 'writing', 'speaking']

// ── TestCard ──────────────────────────────────────────────────────────────────

function SectionRow({ label, icon, progress }: {
  label: string
  icon: React.ReactNode
  progress: SectionProgress
}) {
  return (
    <div className='flex items-center justify-between py-0.5'>
      <div className='flex items-center gap-1.5 text-xs text-slate-500'>
        <span className='text-slate-400'>{icon}</span>
        {label}
      </div>
      {progress.completed && progress.score != null ? (
        <span className='text-xs font-semibold text-slate-800'>{progress.score.toFixed(1)}</span>
      ) : (
        <span className='text-xs text-slate-300'>—</span>
      )}
    </div>
  )
}

function TestCard({ test }: { test: CatalogTest }) {
  const hasScore = test.overall_score != null

  return (
    <div className='group relative flex flex-col rounded-xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md'>
      {/* ── Card header ── */}
      <div className='flex items-start justify-between gap-2 px-4 pt-4 pb-3'>
        <Link
          to='/take-test/$testId'
          params={{ testId: test.id }}
          className='text-sm font-bold text-slate-900 hover:underline leading-tight'
        >
          {test.title}
        </Link>
        {hasScore ? (
          <Badge className='shrink-0 bg-green-500 text-white text-xs px-2 hover:bg-green-500'>
            {test.overall_score!.toFixed(1)}
          </Badge>
        ) : (
          <Badge variant='secondary' className='shrink-0 text-xs px-2 text-slate-400'>
            —
          </Badge>
        )}
      </div>

      {/* ── Section scores ── */}
      <div className='flex-1 border-t border-slate-100 px-4 py-2'>
        {SECTION_ORDER.map((key) => {
          const meta = SECTION_META[key]
          const progress = test.sections[key]
          return (
            <SectionRow
              key={key}
              label={meta.label}
              icon={meta.icon}
              progress={progress}
            />
          )
        })}
      </div>

      {/* ── Action button ── */}
      <div className='px-4 pb-4 pt-2'>
        {test.in_progress_attempt_id ? (
          <Button
            asChild
            size='sm'
            variant='outline'
            className='w-full border-amber-400 text-amber-600 hover:bg-amber-50 text-xs'
          >
            <Link
              to='/take-test/$testId'
              params={{ testId: test.id }}
              search={{ resume: test.in_progress_attempt_id }}
            >
              <Clock size={12} className='mr-1' />
              Continue
            </Link>
          </Button>
        ) : hasScore ? (
          <Button asChild size='sm' variant='outline' className='w-full text-xs'>
            <Link to='/take-test/$testId' params={{ testId: test.id }}>
              <RotateCcw size={12} className='mr-1' />
              Retake
            </Link>
          </Button>
        ) : (
          <Button asChild size='sm' className='w-full text-xs bg-slate-900 hover:bg-slate-700'>
            <Link to='/take-test/$testId' params={{ testId: test.id }}>
              <Play size={12} className='mr-1' />
              Start
            </Link>
          </Button>
        )}
      </div>
    </div>
  )
}

// ── Skeleton card ─────────────────────────────────────────────────────────────

function TestCardSkeleton() {
  return (
    <div className='rounded-xl border border-slate-200 bg-white p-4 space-y-3'>
      <div className='flex justify-between items-start'>
        <Skeleton className='h-4 w-16' />
        <Skeleton className='h-5 w-8 rounded-full' />
      </div>
      <div className='space-y-2 pt-1'>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className='flex justify-between'>
            <Skeleton className='h-3 w-20' />
            <Skeleton className='h-3 w-6' />
          </div>
        ))}
      </div>
      <Skeleton className='h-8 w-full rounded-md mt-2' />
    </div>
  )
}

// ── StudentTests (page) ───────────────────────────────────────────────────────

export function StudentTests() {
  const { data, isLoading } = useQuery({
    queryKey: ['student-test-catalog'],
    queryFn: getTestCatalog,
  })

  return (
    <div className='space-y-8'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>Test Catalog</h1>
        <p className='text-muted-foreground text-sm mt-1'>
          Select a test to start your IELTS practice session
        </p>
      </div>

      {isLoading ? (
        <div className='space-y-8'>
          <div>
            <Skeleton className='h-5 w-48 mb-4' />
            <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
              {[0, 1, 2, 3].map((i) => <TestCardSkeleton key={i} />)}
            </div>
          </div>
        </div>
      ) : !data || data.groups.length === 0 ? (
        <div className='rounded-xl border border-dashed p-10 text-center'>
          <p className='font-medium text-muted-foreground'>No tests available yet</p>
          <p className='text-sm text-muted-foreground mt-1'>
            Your teacher will publish tests here
          </p>
        </div>
      ) : (
        <div className='space-y-10'>
          {data.groups.map((group) => (
            <section key={group.name}>
              <h2 className='text-base font-semibold text-slate-700 mb-4 tracking-tight'>
                {group.name}
              </h2>
              <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
                {group.tests.map((test) => (
                  <TestCard key={test.id} test={test} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
