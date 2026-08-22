import { Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import {
  COUNTDOWN_VISIBLE_SECONDS,
  type RecordingLimit,
} from '../constants/recording-limits'
import { MicLevelMeter } from './mic-level-meter'

type RecordingControlsProps = {
  recordingTime: number
  limit: RecordingLimit
  progress: number
  levels: number[]
  onStop: () => void
  overlay?: boolean
}

/**
 * A real examiner gives no visible clock, and one here makes candidates rush,
 * which costs them the Fluency & Coherence marks the timer was never meant to
 * touch. So time feedback stays hidden until it is actionable: a wrap-up cue
 * at the soft limit, a countdown only for the last few seconds.
 */
export function RecordingControls({
  recordingTime,
  limit,
  progress,
  levels,
  onStop,
  overlay = false,
}: RecordingControlsProps) {
  const remaining = Math.max(0, limit.hardSeconds - recordingTime)
  const isWrappingUp = recordingTime >= limit.softSeconds
  const showCountdown = remaining <= COUNTDOWN_VISIBLE_SECONDS

  return (
    <div className='flex w-full max-w-xs flex-col items-center gap-2 sm:max-w-sm'>
      <MicLevelMeter levels={levels} className='h-6' />
      <p
        className={cn(
          'flex items-center gap-2 text-sm font-medium',
          overlay ? 'text-red-300' : 'text-red-600 dark:text-red-400',
        )}
      >
        <span className='animate-pulse text-red-400'>●</span>
        Recording
      </p>
      <Button
        size='lg'
        variant='destructive'
        className='min-h-12 w-full'
        onClick={onStop}
      >
        <Square className='mr-2 size-4' />
        Stop
      </Button>

      {isWrappingUp && (
        <>
          <Progress value={progress} className='h-1.5 w-full' />
          <p
            aria-live='polite'
            className={cn(
              'text-xs font-medium',
              overlay ? 'text-amber-300' : 'text-amber-600 dark:text-amber-400',
            )}
          >
            {showCountdown
              ? `Finish your thought — ${remaining}s`
              : 'Start wrapping up your answer'}
          </p>
        </>
      )}
    </div>
  )
}
