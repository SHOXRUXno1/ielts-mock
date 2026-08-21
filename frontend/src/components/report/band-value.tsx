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
}

const SIZE_CLASS: Record<BandValueSize, string> = {
  display: 'text-6xl',
  lg: 'text-3xl',
  sm: 'text-xl',
}

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

// Initial value chosen once — animation/reset happens inside the effect
// through rAF/timeout callbacks so we never call setState synchronously
// in the effect body.
function initialDisplay(
  target: number | null | undefined,
  from: number | undefined,
): number | null | undefined {
  if (target == null) return target
  if (from == null) return target
  return prefersReducedMotion() ? target : from
}

function useCountUp(
  target: number | null | undefined,
  from: number | undefined,
  delay: number,
  duration: number,
  onComplete?: () => void,
): number | null | undefined {
  const [display, setDisplay] = useState<number | null | undefined>(() =>
    initialDisplay(target, from),
  )
  const completeRef = useRef(onComplete)
  useEffect(() => {
    completeRef.current = onComplete
  }, [onComplete])

  useEffect(() => {
    let raf = 0
    let cancelled = false

    const finish = (value: number | null | undefined) => {
      if (cancelled) return
      setDisplay(value)
      completeRef.current?.()
    }

    if (target == null) {
      const t = window.setTimeout(() => {
        if (!cancelled) setDisplay(target)
      }, 0)
      return () => {
        cancelled = true
        window.clearTimeout(t)
      }
    }
    if (from == null || prefersReducedMotion()) {
      const t = window.setTimeout(() => finish(target), 0)
      return () => {
        cancelled = true
        window.clearTimeout(t)
      }
    }

    let start = 0
    const tick = (now: number) => {
      if (cancelled) return
      if (start === 0) start = now
      const t = Math.max(0, Math.min(1, (now - start) / duration))
      // easeOutExpo
      const eased = t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)
      const value = from + (target - from) * eased
      setDisplay(value)
      if (t < 1) {
        raf = window.requestAnimationFrame(tick)
      } else {
        completeRef.current?.()
      }
    }

    const resetTimer = window.setTimeout(() => {
      if (cancelled) return
      setDisplay(from)
      raf = window.requestAnimationFrame(tick)
    }, delay)

    return () => {
      cancelled = true
      window.clearTimeout(resetTimer)
      if (raf) window.cancelAnimationFrame(raf)
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
}: BandValueProps) {
  const cefr = cefrLevel(band)
  const descriptor = bandDescriptor(band)
  const displayed = useCountUp(
    band,
    animateFrom,
    animateDelay,
    animateDuration,
    onAnimateComplete,
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
