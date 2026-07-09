import { Check } from 'lucide-react'

const STEP_LABELS = ['Test Info', 'Listening', 'Reading', 'Writing', 'Speaking', 'Review']

type Props = {
  currentStep: number
  totalSteps?: number
}

export function WizardProgressBar({ currentStep, totalSteps = 6 }: Props) {
  return (
    <div className='flex items-center justify-center gap-0'>
      {Array.from({ length: totalSteps }, (_, i) => {
        const step = i + 1
        const isDone = step < currentStep
        const isCurrent = step === currentStep
        return (
          <div key={step} className='flex items-center'>
            {i > 0 && (
              <div
                className={`h-px w-12 transition-colors ${isDone ? 'bg-slate-900' : 'bg-slate-200'}`}
              />
            )}
            <div className='flex flex-col items-center gap-1'>
              <div
                className={`flex size-8 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
                  isDone
                    ? 'bg-slate-900 text-white'
                    : isCurrent
                      ? 'bg-slate-900 text-white ring-4 ring-slate-200'
                      : 'bg-slate-100 text-slate-400'
                }`}
              >
                {isDone ? <Check className='size-4' /> : step}
              </div>
              <span
                className={`text-xs ${isCurrent ? 'font-medium text-slate-900' : 'text-slate-400'}`}
              >
                {STEP_LABELS[i]}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
