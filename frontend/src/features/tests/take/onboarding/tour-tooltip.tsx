import type { TooltipRenderProps } from 'react-joyride'
import { ArrowLeft, ArrowRight, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TourStepData } from './tour-steps'

/**
 * Custom glassmorphism tooltip for the student onboarding tour.
 *
 * Replaces react-joyride's default card so we fully own the look: a frosted
 * glass panel (translucent + backdrop blur) that reads over both the light
 * and dark student themes, with a clear visual hierarchy —
 *
 *   [icon]            [where it is] [step N/total]
 *   Title
 *   One-line instruction
 *   ● ● ○ ○            (progress)
 *   Skip        Back   Next →
 *
 * The `where it is` pill (``step.data.hint``) orients the student spatially
 * ("Top bar", "Right panel") so they instantly grasp *what goes where*.
 *
 * Button labels come from ``primaryProps.title`` / ``backProps.title`` /
 * ``skipProps.title``, which react-joyride fills from the ``locale`` prop —
 * so wording (incl. the preStart "Start …" label) stays centralised there.
 */
export function TourTooltip({
  index,
  size,
  isLastStep,
  step,
  backProps,
  primaryProps,
  skipProps,
  tooltipProps,
}: TooltipRenderProps) {
  const data = (step.data ?? {}) as TourStepData
  const Icon = data.icon
  const isFirst = index === 0

  return (
    <div
      {...tooltipProps}
      className={cn(
        'relative w-[min(360px,calc(100vw-20px))] max-h-[calc(100svh-32px)] overflow-y-auto',
        'rounded-2xl border p-5 text-left',
        'animate-in fade-in-0 zoom-in-95 duration-200',
        // Solid card — crisp white in light, slate in dark.
        'border-slate-200 bg-white text-slate-900',
        'dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50',
        'shadow-[0_12px_48px_-8px_rgba(2,6,23,0.35)]'
      )}
    >

      {/* Header: icon badge · spatial hint · step counter */}
      <div className='mb-3 flex items-center justify-between gap-3'>
        {Icon ? (
          <span className='flex size-9 shrink-0 items-center justify-center rounded-xl bg-blue-500/15 text-blue-600 ring-1 ring-inset ring-blue-500/20 dark:text-blue-300'>
            <Icon className='size-[18px]' strokeWidth={2.25} />
          </span>
        ) : (
          <span />
        )}
        <div className='flex items-center gap-2'>
          {data.hint ? (
            <span className='rounded-full bg-slate-900/[0.06] px-2.5 py-1 text-[11px] font-medium text-slate-500 dark:bg-white/10 dark:text-slate-300'>
              {data.hint}
            </span>
          ) : null}
          <span className='text-[11px] font-semibold tabular-nums tracking-wider text-slate-400 dark:text-slate-500'>
            {index + 1}/{size}
          </span>
        </div>
      </div>

      {/* Title + instruction */}
      {step.title ? (
        <h3 className='text-[15px] font-bold leading-tight tracking-tight'>
          {step.title}
        </h3>
      ) : null}
      <div className='mt-1.5 text-[13.5px] leading-relaxed text-slate-600 dark:text-slate-300'>
        {step.content}
      </div>

      {/* Progress dots — current step is an elongated pill. */}
      <div className='mt-4 flex items-center gap-1.5'>
        {Array.from({ length: size }).map((_, i) => (
          <span
            key={i}
            className={cn(
              'h-1.5 rounded-full transition-all duration-300',
              i === index
                ? 'w-5 bg-blue-500'
                : i < index
                  ? 'w-1.5 bg-blue-500/40'
                  : 'w-1.5 bg-slate-300 dark:bg-slate-600'
            )}
          />
        ))}
      </div>

      {/* Footer: Skip (left) · Back · Primary (right) */}
      <div className='mt-3 flex items-center gap-2 border-t border-slate-200/70 pt-3 dark:border-white/10'>
        {!isLastStep ? (
          <button
            {...skipProps}
            className='mr-auto rounded-md px-1 py-1 text-[12px] font-medium text-slate-400 transition-colors hover:text-slate-600 dark:hover:text-slate-200'
          >
            {skipProps.title}
          </button>
        ) : (
          <span className='mr-auto' />
        )}

        {!isFirst ? (
          <button
            {...backProps}
            className='inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[13px] font-medium text-slate-500 transition-colors hover:bg-slate-500/10 dark:text-slate-300'
          >
            <ArrowLeft className='size-3.5' />
            {backProps.title}
          </button>
        ) : null}

        <button
          {...primaryProps}
          className='inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3.5 py-1.5 text-[13px] font-semibold text-white shadow-sm shadow-blue-600/25 transition-colors hover:bg-blue-500'
        >
          {primaryProps.title}
          {isLastStep ? (
            <Check className='size-3.5' />
          ) : (
            <ArrowRight className='size-3.5' />
          )}
        </button>
      </div>
    </div>
  )
}
