import { Link } from '@tanstack/react-router'
import { ArrowRight, PlayCircle } from 'lucide-react'
import { Panel } from '@/components/report'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import type { InProgressAttempt } from '@/lib/api/student'
import { ENTER } from '@/features/results/lib/motion'
import { continueTakeSearch } from '@/features/student/tests/continue-search'

type ResumeBannerProps = {
  attempt: InProgressAttempt
}

export function ResumeBanner({ attempt }: ResumeBannerProps) {
  const percent =
    attempt.total > 0
      ? Math.round((attempt.answered / attempt.total) * 100)
      : 0

  return (
    <Panel
      className={`${ENTER} border-warning/40 bg-warning/15`}
      padding='sm'
    >
      <div className='flex flex-col gap-4 sm:flex-row sm:items-center'>
        <div className='flex size-12 shrink-0 items-center justify-center rounded-xl bg-warning'>
          <PlayCircle className='size-6 text-warning-foreground' />
        </div>
        <div className='min-w-0 flex-1 space-y-2'>
          <div>
            <p className='text-sm font-semibold text-foreground'>
              Continue where you left off
            </p>
            <p className='mt-0.5 truncate text-xs text-muted-foreground'>
              {attempt.test_title} · {attempt.answered}/{attempt.total} questions
              answered
            </p>
          </div>
          <Progress
            value={percent}
            className='h-1.5 max-w-xs bg-warning/40 [&>div]:bg-warning-foreground'
          />
        </div>
        <Button asChild size='sm' className='shrink-0 rounded-lg'>
          <Link
            to='/take-test/$testId'
            params={{ testId: attempt.test_id }}
            search={continueTakeSearch(
              attempt.id,
              attempt.section,
              attempt.part,
            )}
          >
            Continue
            <ArrowRight className='ml-1.5 size-3.5' />
          </Link>
        </Button>
      </div>
    </Panel>
  )
}
