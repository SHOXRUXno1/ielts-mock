import { Link } from '@tanstack/react-router'
import { Clock, Copy, Ellipsis, Flag, Play, Printer, RotateCcw, Timer } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import type { AttemptDetailRead } from '@/lib/api/attempts'
import { ENTER } from '../lib/motion'
import { attemptStatusMeta, formatAttemptDate, formatAttemptDuration } from '../lib/status'
import { BandScale, BandValue, Metric, Panel } from '@/components/report'

export type ScoreSummaryProps = {
  attempt: AttemptDetailRead
  scoringActive: boolean
  showRetake?: boolean
  showSpeakingCta?: boolean
  onRetake?: () => void
  onFinalize?: () => void
  finalizePending?: boolean
}

export function ScoreSummary({
  attempt,
  scoringActive,
  showRetake = false,
  showSpeakingCta = false,
  onRetake,
  onFinalize,
  finalizePending = false,
}: ScoreSummaryProps) {
  const status = attemptStatusMeta(attempt.status)
  const duration = formatAttemptDuration(attempt.started_at, attempt.finished_at)
  const overall =
    scoringActive && attempt.overall_band == null ? null : attempt.overall_band
  const dialLabel =
    scoringActive && attempt.overall_band == null ? 'Pending' : 'Overall'

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      toast.success('Link copied')
    } catch {
      toast.error('Could not copy link')
    }
  }

  return (
    <Panel className={ENTER}>
      <div className='grid gap-6 lg:grid-cols-[auto_minmax(0,1fr)] lg:items-center'>
        <div className='space-y-4'>
          <BandValue band={overall} label={dialLabel} size='display' />
          <BandScale band={overall} label={dialLabel} className='max-w-56' />
        </div>

        <div className='min-w-0 space-y-4'>
          <div className='flex flex-wrap items-center gap-2.5'>
            <h1 className='text-2xl font-semibold tracking-tight text-foreground'>
              {attempt.test_title ?? 'Test Result'}
            </h1>
            <Badge variant={status.variant} className='gap-1.5 rounded-lg'>
              <span className={status.dot + ' size-1.5 rounded-full'} />
              {status.label}
            </Badge>
          </div>

          <div className='grid gap-3 sm:grid-cols-3 lg:grid-cols-4'>
            <Metric
              icon={Play}
              label='Started'
              value={formatAttemptDate(attempt.started_at)}
            />
            <Metric
              icon={Flag}
              label='Finished'
              value={formatAttemptDate(attempt.finished_at)}
            />
            <Metric icon={Clock} label='Duration' value={duration ?? '—'} />
            {attempt.flagged_overtime && (
              <Metric icon={Timer} label='Timing' value='Overtime' />
            )}
          </div>

          <Separator />

          <div className='flex flex-wrap items-center gap-2'>
            {showSpeakingCta && (
              <Button asChild size='sm' className='rounded-lg'>
                <Link to='/speaking-examiner' search={{ attemptId: attempt.id }}>
                  Continue to Speaking
                </Link>
              </Button>
            )}
            {showRetake && (
              <Button
                variant={showSpeakingCta ? 'outline' : 'default'}
                size='sm'
                className='gap-1.5 rounded-lg'
                onClick={onRetake}
              >
                <RotateCcw className='size-3.5' />
                Retake Test
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant='outline'
                  size='sm'
                  className='rounded-lg'
                  aria-label='More actions'
                >
                  <Ellipsis className='size-4' />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align='end'>
                <DropdownMenuItem onClick={() => window.print()}>
                  <Printer />
                  Print
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => void copyLink()}>
                  <Copy />
                  Copy link
                </DropdownMenuItem>
                {showSpeakingCta && onFinalize && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      disabled={finalizePending}
                      onClick={onFinalize}
                    >
                      Complete without Speaking
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </Panel>
  )
}
