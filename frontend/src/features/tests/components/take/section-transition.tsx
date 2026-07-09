import { useEffect, useState } from 'react'
import { CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { SectionType } from '../../data/schema'

const LABELS: Record<SectionType, string> = {
  listening: 'Listening',
  reading: 'Reading',
  writing: 'Writing',
  speaking: 'Speaking',
}

const COUNTDOWN_SECONDS = 5

type Props = {
  fromType: SectionType
  toType: SectionType
  toIndex: number
  toDurationMinutes: number
  onContinue: () => void
}

export function SectionTransition({
  fromType,
  toType,
  toIndex,
  toDurationMinutes,
  onContinue,
}: Props) {
  const [remaining, setRemaining] = useState(COUNTDOWN_SECONDS)

  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          onContinue()
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(interval)
    // onContinue is stable (useCallback in parent) — safe to omit
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const hasTimer = toType !== 'speaking'

  return (
    <div className='absolute inset-0 z-30 flex items-center justify-center bg-slate-900/70 backdrop-blur-sm'>
      <div className='mx-4 w-full max-w-sm rounded-2xl bg-white p-8 text-center shadow-2xl'>
        {/* Completed section */}
        <div className='mb-5 flex items-center justify-center gap-2 text-emerald-600'>
          <CheckCircle2 className='size-5' />
          <span className='text-sm font-semibold'>
            {LABELS[fromType]} — Complete
          </span>
        </div>

        {/* Moving to */}
        <h2 className='text-[22px] font-bold text-slate-900'>
          Section {toIndex}: {LABELS[toType]}
        </h2>

        {hasTimer ? (
          <p className='mt-2 text-sm text-slate-500'>
            You have{' '}
            <span className='font-semibold text-slate-800'>
              {toDurationMinutes} minutes
            </span>
          </p>
        ) : (
          <p className='mt-2 text-sm text-slate-500'>
            Conducted with AI Examiner
          </p>
        )}

        {/* Countdown ring */}
        <div className='my-6 flex items-center justify-center'>
          <div className='relative flex size-16 items-center justify-center rounded-full border-4 border-slate-100'>
            <svg
              className='absolute inset-0 -rotate-90'
              viewBox='0 0 64 64'
              fill='none'
            >
              <circle
                cx='32'
                cy='32'
                r='28'
                stroke='#3b82f6'
                strokeWidth='4'
                strokeLinecap='round'
                strokeDasharray={`${2 * Math.PI * 28}`}
                strokeDashoffset={`${2 * Math.PI * 28 * (1 - remaining / COUNTDOWN_SECONDS)}`}
                className='transition-all duration-1000'
              />
            </svg>
            <span className='relative text-xl font-bold tabular-nums text-slate-900'>
              {remaining}
            </span>
          </div>
        </div>

        <Button
          size='lg'
          className='w-full bg-slate-900 hover:bg-slate-700'
          onClick={onContinue}
        >
          Continue
        </Button>
      </div>
    </div>
  )
}
