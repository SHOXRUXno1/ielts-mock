import { useEffect, useRef, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { BAND_MAX, formatBand } from '@/features/results/lib/band'
import { bandDescriptor, cefrLevel } from '@/features/results/lib/cefr'

type BandValueSize = 'display' | 'lg' | 'sm'

type BandValueProps = {
  band: number | null | undefined
  label?: string
  size?: BandValueSize
  showCefr?: boolean
  showDescriptor?: boolean
  className?: string
  animateFrom?: number
  animateDelay?: number
  animateDuration?: number
  onAnimateComplete?: () => void
  onDisplayChange?: (band: number) => void
}

const SIZE_CLASS: Record<BandValueSize, string> = {
  display: 'text-6xl',
  lg: 'text-3xl',
  sm: 'text-xl',
}

function snapHalfBand(value: number): number {
  return Math.round(value * 2) / 2
}

function halfBandSteps(from: number, to: number): number[] {
  const start = snapHalfBand(from)
  const end = to
  const steps: number[] = []
  for (let v = start; v < end - 0.01; v += 0.5) {
    steps.push(snapHalfBand(v))
  }
  steps.push(end)
  return steps
}

function initialDisplay(
  target: number | null | undefined,
  from: number | undefined,
): number | null | undefined {
  if (target == null) return target
  if (from == null) return target
  if (target <= from) return target
  return snapHalfBand(from)
}

function useCountUp(
  target: number | null | undefined,
  from: number | undefined,
  delay: number,
  duration: number,
  onComplete?: () => void,
  onDisplayChange?: (band: number) => void,
): number | null | undefined {
  const [display, setDisplay] = useState<number | null | undefined>(() =>
    initialDisplay(target, from),
  )
  const completeRef = useRef(onComplete)
  const displayChangeRef = useRef(onDisplayChange)
  useEffect(() => {
    completeRef.current = onComplete
  }, [onComplete])
  useEffect(() => {
    displayChangeRef.current = onDisplayChange
  }, [onDisplayChange])

  useEffect(() => {
    let cancelled = false
    let delayTimer = 0
    let stepTimer = 0

    const commit = (value: number) => {
      setDisplay(value)
      displayChangeRef.current?.(value)
    }

    const finish = (value: number | null | undefined) => {
      if (cancelled) return
      setDisplay(value)
      if (typeof value === 'number') displayChangeRef.current?.(value)
      completeRef.current?.()
    }

    if (target == null) {
      delayTimer = window.setTimeout(() => {
        if (!cancelled) setDisplay(target)
      }, 0)
      return () => {
        cancelled = true
        window.clearTimeout(delayTimer)
      }
    }
    if (from == null || target <= from) {
      delayTimer = window.setTimeout(() => finish(target), 0)
      return () => {
        cancelled = true
        window.clearTimeout(delayTimer)
      }
    }

    const steps = halfBandSteps(from, target)
    const gaps = Math.max(1, steps.length - 1)
    const stepMs = Math.max(80, Math.round(duration / gaps))

    delayTimer = window.setTimeout(() => {
      if (cancelled) return
      let i = 0
      commit(steps[0]!)
      if (steps.length === 1) {
        completeRef.current?.()
        return
      }
      stepTimer = window.setInterval(() => {
        if (cancelled) return
        i += 1
        const value = steps[i]
        if (value == null) {
          window.clearInterval(stepTimer)
          completeRef.current?.()
          return
        }
        commit(value)
        if (i >= steps.length - 1) {
          window.clearInterval(stepTimer)
          completeRef.current?.()
        }
      }, stepMs)
    }, delay)

    return () => {
      cancelled = true
      window.clearTimeout(delayTimer)
      window.clearInterval(stepTimer)
    }
  }, [target, from, delay, duration])

  return display
}

export function BandValue({
  band,
  label = 'Overall',
  size = 'lg',
  showCefr = true,
  showDescriptor = true,
  className,
  animateFrom,
  animateDelay = 0,
  animateDuration = 900,
  onAnimateComplete,
  onDisplayChange,
}: BandValueProps) {
  const cefr = cefrLevel(band)
  const descriptor = bandDescriptor(band)
  const displayed = useCountUp(
    band,
    animateFrom,
    animateDelay,
    animateDuration,
    onAnimateComplete,
    onDisplayChange,
  )
  const aria =
    band == null
      ? `${label} band not available`
      : `${label} band ${formatBand(band)} out of ${BAND_MAX}${cefr ? `, CEFR ${cefr}` : ''}`

  return (
    <div className={cn('min-w-0', className)} role='img' aria-label={aria}>
      <p
        className={cn(
          'font-manrope font-semibold tracking-tight tabular-nums text-foreground',
          SIZE_CLASS[size],
        )}
      >
        {formatBand(displayed)}
      </p>
      {label && size === 'display' && (
        <p className='mt-1 text-xs font-medium tracking-wider text-muted-foreground uppercase'>
          {label}
        </p>
      )}
      {(showDescriptor || showCefr) && (descriptor || cefr) && (
        <div
          className={cn(
            'flex flex-wrap items-center gap-2',
            size === 'display' ? 'mt-2' : 'mt-1',
          )}
        >
          {showDescriptor && descriptor && (
            <span className='text-sm text-muted-foreground'>{descriptor}</span>
          )}
          {showCefr && cefr && (
            <Badge variant='outline' className='rounded-md text-xs'>
              {cefr}
            </Badge>
          )}
        </div>
      )}
    </div>
  )
}
