import { Clock } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import type { SectionType } from '../../data/schema'
import { SECTION_LABELS } from '../../take/constants'
import type { TimeoutDialogInfo } from '../../take/use-section-expiry-dialog'

type Props = {
  info: TimeoutDialogInfo | null
  countdown: number | null
  onContinue: () => void
}

export function TimeoutDialog({ info, countdown, onContinue }: Props) {
  const next = info?.next ?? null
  const from = info?.from

  return (
    <AlertDialog
      open={!!info}
      onOpenChange={(open) => {
        if (!open) onContinue()
      }}
    >
      <AlertDialogContent className='max-w-sm'>
        <AlertDialogHeader className='items-center text-center'>
          <div className='mx-auto mb-2 flex size-12 items-center justify-center rounded-full bg-amber-50'>
            <Clock className='size-6 text-amber-500' />
          </div>
          <AlertDialogTitle className='text-xl'>
            {from === 'speaking' ? 'Speaking session ended' : "Time's up"}
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className='space-y-1 pt-1 text-center text-sm text-muted-foreground'>
              <TimeoutCopy from={from} next={next} />
              <p className='pt-1 text-xs text-slate-400'>
                Your answers have been saved automatically.
              </p>
              {countdown != null && countdown > 0 && (
                <p className='pt-1 text-xs text-slate-500'>
                  Continues in {countdown}s
                </p>
              )}
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className='mt-2 sm:justify-center'>
          <AlertDialogAction
            className='w-full bg-blue-600 hover:bg-blue-700'
            onClick={onContinue}
          >
            {next ? `Continue to ${SECTION_LABELS[next]}` : 'Review your test'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

function TimeoutCopy({
  from,
  next,
}: {
  from: SectionType | undefined
  next: SectionType | null
}) {
  if (from === 'speaking') {
    return (
      <p>
        The speaking safety time limit has ended. Your session has been closed.
      </p>
    )
  }
  if (from && next) {
    return (
      <>
        <p className='font-medium text-slate-700'>
          {SECTION_LABELS[from]} section has ended.
        </p>
        <p>
          Moving to{' '}
          <span className='font-medium'>{SECTION_LABELS[next]}</span> next.
        </p>
      </>
    )
  }
  return (
    <p className='font-medium text-slate-700'>All sections completed.</p>
  )
}
