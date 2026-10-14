import { useCallback, useEffect, useRef, useState } from 'react'
import type { TooltipRenderProps } from 'react-joyride'
import { ArrowLeft, ArrowRight, Check, Pause } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TourStepData } from './tour-steps'

/**
 * Custom tooltip for the student onboarding tour.
 *
 *   [icon]            [where it is] [step N/total]
 *   Title
 *   One-line instruction
 *   ● ● ○ ○            (progress dots)
 *   Skip        Back   Next →
 *
 * The ``where it is`` pill (``step.data.hint``) orients the student spatially
 * ("Top bar", "Right panel") so they instantly grasp *what goes where*.
 *
 * Steps auto-advance after {@link AUTO_ADVANCE_MS} with a thin progress
 * bar at the top of the card showing the countdown. See {@link useAutoAdvance}
 * for the pause-on-hover / focus / reduced-motion / tab-hidden rules.
 *
 * Button labels come from ``primaryProps.title`` / ``backProps.title`` /
 * ``skipProps.title``, which react-joyride fills from the ``locale`` prop,
 * so wording (incl. the preStart "Start …" label) stays centralised there.
 */

/** How long each eligible step stays visible before advancing itself. */
const AUTO_ADVANCE_MS = 5000

/**
 * Drives the progress bar + auto-advance timer for a single step.
 *
 * Design decisions:
 *
 *   - The width of the bar is written to a ref'd DOM node, NOT setState — a
 *     60fps `requestAnimationFrame` loop that re-rendered the whole tooltip
 *     every frame would be wasteful and would also fight react-joyride's own
 *     re-renders.
 *   - Pause (hover / focus / tab hidden / reduced motion) is handled by
 *     bailing out of the RAF and recording the elapsed slice into
 *     ``elapsedRef`` so the next run resumes where we stopped. Resuming works
 *     because we only ever add ``now - startRef`` deltas, never read absolute
 *     wall time.
 *   - When the step changes we reset elapsed to 0; otherwise the next step
 *     would inherit the previous step's progress.
 *   - ``onCompleteRef`` keeps the callback stable through re-renders so the
 *     `useEffect` deps stay minimal (we don't want to tear down and rebuild
 *     the RAF loop every parent render).
 */
function useAutoAdvance({
  stepKey,
  enabled,
  paused,
  onComplete,
}: {
  stepKey: number
  enabled: boolean
  paused: boolean
  onComplete: () => void
}) {
  const barRef = useRef<HTMLDivElement | null>(null)
  const rafRef = useRef<number | null>(null)
  const elapsedRef = useRef(0)
  const startRef = useRef(0)
  const onCompleteRef = useRef(onComplete)

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  // Reset elapsed and the bar whenever the step changes.
  useEffect(() => {
    elapsedRef.current = 0
    if (barRef.current) barRef.current.style.width = '0%'
  }, [stepKey])

  useEffect(() => {
    if (!enabled || paused) return

    startRef.current = performance.now()
    const tick = (now: number) => {
      const total = elapsedRef.current + (now - startRef.current)
      if (total >= AUTO_ADVANCE_MS) {
        if (barRef.current) barRef.current.style.width = '100%'
        onCompleteRef.current()
        return
      }
      if (barRef.current) {
        barRef.current.style.width = `${(total / AUTO_ADVANCE_MS) * 100}%`
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)

    return () => {
      if (rafRef.current != null) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
      // Freeze what we've accumulated so a resume continues cleanly.
      elapsedRef.current += performance.now() - startRef.current
    }
  }, [enabled, paused, stepKey])

  return barRef
}

/** Respects the OS "reduce motion" preference. */
function usePrefersReducedMotion(): boolean {
  const [reduce, setReduce] = useState(
    () =>
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handler = (e: MediaQueryListEvent) => setReduce(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return reduce
}

/** True when the tab is hidden or minimised. */
function useDocumentHidden(): boolean {
  const [hidden, setHidden] = useState(
    () =>
      typeof document !== 'undefined' &&
      document.visibilityState !== 'visible'
  )
  useEffect(() => {
    const handler = () => setHidden(document.visibilityState !== 'visible')
    document.addEventListener('visibilitychange', handler)
    return () => document.removeEventListener('visibilitychange', handler)
  }, [])
  return hidden
}

export function TourTooltip({
  index,
  size,
  isLastStep,
  step,
  controls,
  backProps,
  primaryProps,
  skipProps,
  tooltipProps,
}: TooltipRenderProps) {
  const data = (step.data ?? {}) as TourStepData
  const Icon = data.icon
  const isFirst = index === 0

  // Local pause state driven by pointer / keyboard focus.
  const [hovered, setHovered] = useState(false)
  const [focused, setFocused] = useState(false)
  const prefersReducedMotion = usePrefersReducedMotion()
  const docHidden = useDocumentHidden()

  // Only the last step stays manual — "Got it" / "Start Speaking" is a
  // commitment (it closes the tour or actually starts the exam), so it must
  // be an intentional click. Reduced motion disables auto-advance entirely:
  // students who prefer less motion typically also need more reading time.
  const canAutoAdvance = !isLastStep && !prefersReducedMotion
  const paused = hovered || focused || docHidden

  const handleComplete = useCallback(() => {
    controls.next()
  }, [controls])

  const barRef = useAutoAdvance({
    stepKey: index,
    enabled: canAutoAdvance,
    paused,
    onComplete: handleComplete,
  })

  return (
    <div
      {...tooltipProps}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setFocused(true)}
      onBlur={(e) => {
        // Only clear when focus leaves the card entirely.
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
          setFocused(false)
        }
      }}
      className={cn(
        'relative w-[min(360px,calc(100vw-20px))] max-h-[calc(100svh-32px)] overflow-hidden',
        'rounded-2xl border text-left',
        'animate-in fade-in-0 zoom-in-95 duration-200',
        'border-slate-200 bg-white text-slate-900',
        'dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50',
        'shadow-[0_12px_48px_-8px_rgba(2,6,23,0.35)]'
      )}
    >
      {/* Auto-advance progress bar — thin blue sliver at the top edge. */}
      {canAutoAdvance ? (
        <div
          aria-hidden
          className='absolute inset-x-0 top-0 h-[2px] bg-slate-100 dark:bg-slate-800'
        >
          <div
            ref={barRef}
            className={cn(
              'h-full bg-blue-500 transition-opacity',
              paused && 'opacity-40'
            )}
            style={{ width: '0%' }}
          />
        </div>
      ) : null}

      <div className='p-5'>
        {/* Header: icon badge · spatial hint · step counter (+ pause chip). */}
        <div className='mb-3 flex items-center justify-between gap-3'>
          {Icon ? (
            <span className='flex size-9 shrink-0 items-center justify-center rounded-xl bg-blue-500/15 text-blue-600 ring-1 ring-inset ring-blue-500/20 dark:text-blue-300'>
              <Icon className='size-[18px]' strokeWidth={2.25} />
            </span>
          ) : (
            <span />
          )}
          <div className='flex items-center gap-2'>
            {canAutoAdvance && paused ? (
              <span
                aria-label='Paused'
                className='inline-flex items-center gap-1 rounded-full bg-slate-900/[0.06] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:bg-white/10 dark:text-slate-300'
              >
                <Pause className='size-2.5' />
                Paused
              </span>
            ) : data.hint ? (
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
    </div>
  )
}
