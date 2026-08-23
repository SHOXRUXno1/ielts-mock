import { Maximize, TriangleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'

type Props = {
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
 */
export function FullscreenGuardOverlay({ secondsLeft, onReturn }: Props) {
  return (
    <div
      className='fixed inset-0 z-[200] flex items-center justify-center bg-slate-950'
      // Trap the tab order inside the overlay — nothing behind it should be
      // reachable, either with the mouse or with the keyboard.
      aria-modal='true'
      role='alertdialog'
      aria-labelledby='fs-guard-title'
      aria-describedby='fs-guard-desc'
    >
      <div className='mx-4 max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl dark:bg-slate-900'>
        <div className='mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400'>
          <TriangleAlert className='size-7' />
        </div>
        <h2
          id='fs-guard-title'
          className='text-xl font-bold text-slate-900 dark:text-slate-100'
        >
          Return to fullscreen
        </h2>
        <p
          id='fs-guard-desc'
          className='mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-400'
        >
          You left fullscreen mode during the exam. Return within{' '}
          <span className='font-semibold tabular-nums text-slate-900 dark:text-slate-100'>
            {secondsLeft}s
          </span>{' '}
          or the attempt will be closed and submitted for scoring.
        </p>
        <div className='mt-6 flex flex-col items-center gap-3'>
          <div
            className='text-5xl font-bold tabular-nums text-red-600 dark:text-red-400'
            aria-live='polite'
          >
            {secondsLeft}
          </div>
          <Button
            size='lg'
            className='h-12 w-full rounded-xl bg-sky-600 text-[15px] font-semibold text-white shadow-md shadow-sky-500/25 hover:bg-sky-700'
            onClick={onReturn}
            autoFocus
          >
            <Maximize className='mr-2 size-4' />
            Return to fullscreen
          </Button>
        </div>
      </div>
    </div>
  )
}
