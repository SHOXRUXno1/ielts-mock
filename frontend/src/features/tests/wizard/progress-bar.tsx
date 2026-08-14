import { AlertCircle, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

export type StepStatus = 'complete' | 'partial' | 'empty' | 'warning' | 'locked'

const STEP_LABELS = ['Test Info', 'Listening', 'Reading', 'Writing', 'Speaking', 'Review']

type Props = {
  currentStep: number
  statuses: StepStatus[]
  onStepClick?: (step: number) => void
}

function stepStyle(status: StepStatus, isCurrent: boolean) {
  if (isCurrent) {
    return 'bg-primary text-primary-foreground ring-4 ring-primary/20'
  }
  switch (status) {
    case 'complete':
      return 'bg-primary text-primary-foreground'
    case 'partial':
      return 'bg-warning/30 text-warning-foreground'
    case 'warning':
      return 'bg-warning/30 text-warning-foreground'
    case 'locked':
      return 'bg-muted text-muted-foreground/50'
    case 'empty':
    default:
      return 'bg-muted text-muted-foreground'
  }
}

function connectorStyle(status: StepStatus) {
  switch (status) {
    case 'complete':
      return 'bg-primary'
    case 'partial':
    case 'warning':
      return 'bg-warning/40'
    default:
      return 'bg-border'
  }
}

function StepIcon({ status, step }: { status: StepStatus; step: number }) {
  if (status === 'complete') return <Check className='size-3.5' />
  if (status === 'warning') return <AlertCircle className='size-3.5' />
  return <span>{step}</span>
}

export function WizardProgressBar({ currentStep, statuses, onStepClick }: Props) {
  const totalSteps = STEP_LABELS.length

  return (
    <>
      {/* Desktop: full stepper */}
      <nav className='hidden items-center justify-center gap-0 sm:flex' aria-label='Progress'>
        {Array.from({ length: totalSteps }, (_, i) => {
          const step = i + 1
          const isCurrent = step === currentStep
          const status = statuses[i] ?? 'empty'
          const clickable = !!onStepClick && !isCurrent && status !== 'locked'

          return (
            <div key={step} className='flex items-center'>
              {i > 0 && (
                <div
                  className={cn('h-px w-10 transition-colors md:w-14', connectorStyle(statuses[i - 1] ?? 'empty'))}
                />
              )}
              <button
                type='button'
                disabled={!clickable}
                onClick={() => onStepClick?.(step)}
                className={cn(
                  'flex flex-col items-center gap-1 rounded-lg px-1 py-0.5 transition-opacity',
                  clickable
                    ? 'cursor-pointer hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
                    : 'cursor-default',
                  status === 'locked' && 'opacity-50',
                )}
              >
                <div
                  className={cn(
                    'flex size-8 items-center justify-center rounded-full text-xs font-semibold transition-colors',
                    stepStyle(status, isCurrent),
                  )}
                >
                  {isCurrent ? step : <StepIcon status={status} step={step} />}
                </div>
                <span
                  className={cn(
                    'text-[11px]',
                    isCurrent ? 'font-medium text-foreground' : 'text-muted-foreground',
                  )}
                >
                  {STEP_LABELS[i]}
                </span>
              </button>
            </div>
          )
        })}
      </nav>

      {/* Mobile: compact bar */}
      <div className='flex items-center gap-3 sm:hidden'>
        <span className='text-xs font-medium text-foreground'>
          Step {currentStep} of {totalSteps}
        </span>
        <span className='text-xs text-muted-foreground'>
          {STEP_LABELS[currentStep - 1]}
        </span>
        <div className='ml-auto flex gap-1'>
          {Array.from({ length: totalSteps }, (_, i) => {
            const status = statuses[i] ?? 'empty'
            const isCurrent = i + 1 === currentStep
            return (
              <div
                key={i}
                className={cn(
                  'h-1.5 w-5 rounded-full transition-colors',
                  isCurrent
                    ? 'bg-primary'
                    : status === 'complete'
                      ? 'bg-primary/60'
                      : status === 'partial' || status === 'warning'
                        ? 'bg-warning/50'
                        : 'bg-border',
                )}
              />
            )
          })}
        </div>
      </div>
    </>
  )
}
