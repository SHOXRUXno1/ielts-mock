import { Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { MicLevelMeter } from './mic-level-meter'

type RecordingControlsProps = {
  recordingTime: number
  maxSeconds: number
  progress: number
  levels: number[]
  onStop: () => void
  overlay?: boolean
}

export function RecordingControls({
  recordingTime,
  maxSeconds,
  progress,
  levels,
  onStop,
  overlay = false,
}: RecordingControlsProps) {
  const remaining = Math.max(0, maxSeconds - recordingTime)

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
      <Progress value={progress} className='h-1.5 w-full' />
      <p className={cn('text-xs', overlay ? 'text-white/70' : 'text-muted-foreground')}>
        {remaining}s remaining
      </p>
    </div>
  )
}
