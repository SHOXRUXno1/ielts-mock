import { Maximize, RotateCcw, TriangleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { FullscreenViolationKind } from './use-fullscreen-guard'

type Props = {
  kind: FullscreenViolationKind
  secondsLeft: number
  onReturn: () => void
}

/**
 * Blocking overlay shown while the exam is out of fullscreen mid-test.
 *
 * Opaque, not translucent: leaving fullscreen must not become a way to read
 * the questions with the exam UI in a smaller window. The Return button is
 * the only visible action — its click also gives the browser the user
 * gesture that `requestFullscreen` requires.
 *
 * Two tones, because the two situations are not equally the student's fault.
 * A deliberate exit is on a countdown and says so. A page that came back up
 * outside fullscreen (reload, crash recovery) is merely blocked, and saying
 * "your attempt will be closed" there would be both untrue and cruel.
 */
export function FullscreenGuardOverlay({ kind, secondsLeft, onReturn }: Props) {
  const isExit = kind === 'exit'

  return (
    <div
      className='fixed inset-0 z-[200] flex items-center justify-center bg-slate-950'
      // Nothing behind this should be reachable, by mouse or by keyboard.
      aria-modal='true'
      role='alertdialog'
      aria-labelledby='fs-guard-title'
      aria-describedby='fs-guard-desc'
    >
      <div className='mx-4 max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl dark:bg-slate-900'>
        <div
          className={
            'mx-auto mb-4 flex size-14 items-center justify-center rounded-full ' +
            (isExit
              ? 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400'
              : 'bg-sky-100 text-sky-600 dark:bg-sky-950 dark:text-sky-400')
          }
        >
          {isExit ? (
            <TriangleAlert className='size-7' />
          ) : (
            <RotateCcw className='size-7' />
          )}
        </div>

        <h2
          id='fs-guard-title'
          className='text-xl font-bold text-slate-900 dark:text-slate-100'
        >
          {isExit ? 'Return to fullscreen' : 'Your exam is still here'}
        </h2>

        <p
          id='fs-guard-desc'
          className='mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-400'
        >
          {isExit ? (
            <>
              You left fullscreen mode during the exam. Return within{' '}
              <span className='font-semibold tabular-nums text-slate-900 dark:text-slate-100'>
                {secondsLeft}s
              </span>{' '}
              or the attempt will be closed and submitted for scoring.
            </>
          ) : (
            <>
              The page reloaded, so the exam is no longer in fullscreen. Your
              answers and your progress are saved. Go back to fullscreen to
              carry on — section timers keep running in the meantime.
            </>
          )}
        </p>

        <div className='mt-6 flex flex-col items-center gap-3'>
          {isExit && (
            <div
              className='text-5xl font-bold tabular-nums text-red-600 dark:text-red-400'
              aria-live='polite'
            >
              {secondsLeft}
            </div>
          )}
          <Button
            size='lg'
            className='h-12 w-full rounded-xl bg-sky-600 text-[15px] font-semibold text-white shadow-md shadow-sky-500/25 hover:bg-sky-700'
            onClick={onReturn}
            autoFocus
          >
            <Maximize className='mr-2 size-4' />
            {isExit ? 'Return to fullscreen' : 'Continue in fullscreen'}
          </Button>
        </div>
      </div>
    </div>
  )
}
