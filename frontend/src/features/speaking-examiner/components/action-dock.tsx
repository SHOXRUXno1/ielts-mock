import { Loader2, Mic, Volume2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { Phase } from '../types/phase'
import { RecordingControls } from './recording-controls'

type ActionDockProps = {
  phase: Phase
  recordingTime: number
  maxRecordingSeconds: number
  recordingProgress: number
  micLevels: number[]
  onStartRecording: () => void
  onStopRecording: () => void
  endTestButton: ReactNode
  variant?: 'dock' | 'overlay'
}

export function ActionDock({
  phase,
  recordingTime,
  maxRecordingSeconds,
  recordingProgress,
  micLevels,
  onStartRecording,
  onStopRecording,
  endTestButton,
  variant = 'dock',
}: ActionDockProps) {
  const isOverlay = variant === 'overlay'

  return (
    <div
      className={cn(
        'flex w-full flex-col items-center gap-2',
        isOverlay
          ? 'pointer-events-auto bg-gradient-to-t from-black/90 via-black/55 to-transparent px-4 pb-3 pt-10'
          : 'border-t bg-background px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]',
      )}
    >
      {phase === 'playing' && (
        <Button
          size='lg'
          disabled
          aria-busy='true'
          className={cn('w-full max-w-xs sm:max-w-sm', isOverlay && 'opacity-90')}
        >
          <Volume2 className='mr-2 size-4' />
          Examiner speaking...
        </Button>
      )}

      {phase === 'prep' && (
        <Button
          size='lg'
          disabled
          aria-busy='true'
          className={cn('w-full max-w-xs sm:max-w-sm', isOverlay && 'opacity-90')}
        >
          Preparation time — mic disabled
        </Button>
      )}

      {phase === 'ready' && (
        <Button
          size='lg'
          className='min-h-12 w-full max-w-xs bg-green-600 hover:bg-green-700 sm:max-w-sm'
          onClick={onStartRecording}
        >
          <Mic className='mr-2 size-4' />
          Tap to speak
        </Button>
      )}

      {phase === 'recording' && (
        <RecordingControls
          recordingTime={recordingTime}
          maxSeconds={maxRecordingSeconds}
          progress={recordingProgress}
          levels={micLevels}
          onStop={onStopRecording}
          overlay={isOverlay}
        />
      )}

      {(phase === 'transcribing' || phase === 'thinking') && (
        <Button
          size='lg'
          disabled
          aria-busy='true'
          className={cn('w-full max-w-xs sm:max-w-sm', isOverlay && 'opacity-90')}
        >
          <Loader2 className='mr-2 size-4 animate-spin' />
          Processing...
        </Button>
      )}

      {phase === 'scoring' && (
        <div className='flex flex-col items-center gap-2 py-1'>
          <Loader2
            className={cn(
              'size-8 animate-spin',
              isOverlay ? 'text-white' : 'text-primary',
            )}
          />
          <p
            className={cn(
              'text-sm',
              isOverlay ? 'text-white/80' : 'text-muted-foreground',
            )}
          >
            Calculating your score...
          </p>
        </div>
      )}

      {endTestButton}
    </div>
  )
}
