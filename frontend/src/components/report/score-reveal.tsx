import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { Download } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import {
  bandTone,
  bandToneClasses,
  formatBand,
  type BandTone,
} from '@/features/results/lib/band'
import { bandDescriptor, cefrLevel, type CefrLevel } from '@/features/results/lib/cefr'
import { SKILL_META, type SkillKey } from '@/features/results/lib/skill'
import { BandScale } from './band-scale'
import { BandValue } from './band-value'

export const TIMELINE = {
  fadeIn: 300,
  countUpStart: 300,
  stepMs: 200,
  chipStagger: 60,
  afterTone: 200,
  afterChips: 400,
} as const

export function climbDurationMs(from: number, to: number): number {
  const steps = Math.max(0, Math.round((to - from) * 2))
  return steps * TIMELINE.stepMs
}

export type ScoreRevealSectionStatus = 'scored' | 'pending' | 'not_attempted'

export type ScoreRevealSection = {
  skill: SkillKey
  band: number | null
  status: ScoreRevealSectionStatus
}

export type ScoreRevealProps = {
  overallBand: number | null
  cefr?: CefrLevel | null
  sections: ScoreRevealSection[]
  testTitle: string | null | undefined
  onViewResults: () => void
  onDownloadPdf: () => void
  onClose: () => void
}

type Phase = 'fade' | 'counting' | 'tone' | 'chips' | 'done'

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  })
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = () => setReduced(mq.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return reduced
}

function toneGlow(tone: BandTone): string | null {
  if (tone === 'strong') return 'var(--success)'
  if (tone === 'fair') return 'var(--warning)'
  return null
}

// Deterministic pseudo-random for confetti — no state, no drift across renders.
function confettiPieces(count: number) {
  const palette = [
    'bg-success-foreground',
    'bg-chart-1',
    'bg-chart-2',
    'bg-chart-3',
    'bg-chart-4',
    'bg-chart-5',
  ]
  return Array.from({ length: count }, (_, i) => {
    const rand = (seed: number) => {
      const x = Math.sin((i + 1) * seed) * 10000
      return x - Math.floor(x)
    }
    const left = rand(12.9898) * 100
    const delayMs = rand(78.233) * 700
    const durationMs = 1400 + rand(45.164) * 900
    const swayDeg = (rand(23.771) - 0.5) * 30
    return {
      key: i,
      color: palette[i % palette.length],
      left,
      delayMs,
      durationMs,
      swayDeg,
    }
  })
}

const CONFETTI_COUNT = 28

export function ScoreReveal({
  overallBand,
  cefr,
  sections,
  testTitle,
  onViewResults,
  onDownloadPdf,
  onClose,
}: ScoreRevealProps) {
  const reduced = usePrefersReducedMotion()
  const pendingSections = sections.some((section) => section.status === 'pending')
  const waiting = overallBand == null && pendingSections
  const [phase, setPhase] = useState<Phase>(() =>
    overallBand == null && !pendingSections ? 'done' : 'fade',
  )
  const [announcement, setAnnouncement] = useState('')
  const [liveBand, setLiveBand] = useState<number | null>(() =>
    overallBand == null ? null : 1,
  )
  const climbMs =
    overallBand == null ? 0 : climbDurationMs(1, overallBand)
  const contentRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  const tone = bandTone(overallBand)
  const glow = toneGlow(tone)
  const toneClasses = bandToneClasses(tone)
  const descriptor = bandDescriptor(overallBand)
  const effectiveCefr = cefr ?? cefrLevel(overallBand)
  const confetti = useMemo(() => confettiPieces(CONFETTI_COUNT), [])
  const countUpDuration = Math.max(TIMELINE.stepMs, climbMs)
  const skipLabel =
    !waiting && overallBand != null && tone === 'weak'
      ? 'Review mistakes'
      : waiting || overallBand == null
        ? 'View answers'
        : 'View results'

  // Capture and restore focus. Plain overlay — no Radix Dialog — so the
  // submit AlertDialog closing cannot auto-dismiss this screen.
  useEffect(() => {
    previouslyFocused.current =
      (document.activeElement as HTMLElement | null) ?? null
    contentRef.current?.focus()
    return () => {
      previouslyFocused.current?.focus?.()
    }
  }, [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
      }
      if (event.key !== 'Tab' || !contentRef.current) return
      const nodes = contentRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      )
      if (nodes.length === 0) {
        event.preventDefault()
        return
      }
      const first = nodes[0]
      const last = nodes[nodes.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  // Phase machine — starts only once the overall band is known so the
  // count-up (1 → band, 200ms per half-step) can finish before the CTAs.
  // Reduced motion still runs the number ticks; it only skips confetti.
  useEffect(() => {
    if (overallBand == null) return
    const toneAt = TIMELINE.countUpStart + climbMs
    const chipsAt = toneAt + TIMELINE.afterTone
    const ctaAt = chipsAt + TIMELINE.afterChips
    const timers = [
      window.setTimeout(() => setPhase('counting'), TIMELINE.fadeIn),
      window.setTimeout(() => setPhase('tone'), toneAt),
      window.setTimeout(() => setPhase('chips'), chipsAt),
      window.setTimeout(() => setPhase('done'), ctaAt),
    ]
    return () => {
      for (const id of timers) window.clearTimeout(id)
    }
  }, [overallBand, climbMs])

  const handleAnnounce = () => {
    if (overallBand == null) return
    const cefrPart = effectiveCefr ? `, CEFR ${effectiveCefr}` : ''
    setAnnouncement(
      `Overall band ${formatBand(overallBand)} out of 9${cefrPart}. ${descriptor ?? ''}`.trim(),
    )
  }

  const showConfetti =
    !reduced &&
    !waiting &&
    tone === 'strong' &&
    (phase === 'tone' || phase === 'chips' || phase === 'done')
  const showToneBadge =
    !waiting && (phase === 'tone' || phase === 'chips' || phase === 'done')
  const showChips = waiting || phase === 'chips' || phase === 'done'
  const showDownload = !waiting && overallBand != null && phase === 'done'

  return (
    <div
      role='dialog'
      aria-modal='true'
      aria-labelledby='score-reveal-title'
      aria-describedby='score-reveal-desc'
      className={cn(
        'fixed inset-0 z-[200] flex flex-col items-center justify-center overflow-hidden bg-surface-sunken/90 px-6 py-10 backdrop-blur-md',
        'motion-safe:animate-in motion-safe:fade-in motion-safe:duration-300',
      )}
    >
      <h2 id='score-reveal-title' className='sr-only'>
        {testTitle ? `${testTitle} — Score reveal` : 'Score reveal'}
      </h2>
      <p id='score-reveal-desc' className='sr-only'>
        Your band results for this mock test.
      </p>

      {glow && (
        <div
          aria-hidden
          className='pointer-events-none absolute inset-0 opacity-25'
          style={{
            background: `radial-gradient(closest-side, ${glow}, transparent 70%)`,
          }}
        />
      )}

      {showConfetti && (
            <div
              aria-hidden
              className='pointer-events-none absolute inset-0 overflow-hidden'
            >
              {confetti.map((p) => (
                <span
                  key={p.key}
                  className={cn(
                    'absolute top-0 h-3 w-1.5 rounded-sm',
                    p.color,
                    'motion-safe:animate-[confetti-fall_var(--conf-dur)_ease-out_var(--conf-delay)_both]',
                  )}
                  style={
                    {
                      left: `${p.left}%`,
                      transform: `rotate(${p.swayDeg}deg)`,
                      // Custom properties for animation timing.
                      ['--conf-dur' as string]: `${p.durationMs}ms`,
                      ['--conf-delay' as string]: `${p.delayMs}ms`,
                    } as CSSProperties
                  }
                />
              ))}
        </div>
      )}

      <div
        ref={contentRef}
        tabIndex={-1}
        className='relative z-10 flex w-full max-w-xl flex-col items-center gap-6 text-center outline-none'
      >
            {testTitle && (
              <p className='text-xs font-medium uppercase tracking-wider text-muted-foreground'>
                {testTitle}
              </p>
            )}

            <div className='flex flex-col items-center gap-4'>
              <BandValue
                band={overallBand}
                label={waiting ? 'Scoring' : 'Overall'}
                size='display'
                showCefr={false}
                showDescriptor={false}
                animateFrom={waiting ? undefined : 1}
                animateDelay={waiting ? 0 : TIMELINE.countUpStart}
                animateDuration={countUpDuration}
                onAnimateComplete={handleAnnounce}
                onDisplayChange={setLiveBand}
                className='text-center'
              />
              <BandScale
                band={waiting ? null : liveBand}
                label='Overall'
                barClass={
                  tone === 'strong'
                    ? 'bg-success-foreground'
                    : tone === 'fair'
                      ? 'bg-warning-foreground'
                      : tone === 'weak'
                        ? 'bg-destructive'
                        : 'bg-primary'
                }
                className='max-w-64'
              />
            </div>

            <div
              className={cn(
                'flex flex-wrap items-center justify-center gap-2 transition-opacity duration-300',
                showToneBadge ? 'opacity-100' : 'opacity-0',
              )}
            >
              {descriptor && (
                <Badge
                  className={cn(
                    'gap-1.5 rounded-lg border-0',
                    toneClasses.bg,
                    toneClasses.text,
                  )}
                >
                  {descriptor}
                </Badge>
              )}
              {effectiveCefr && (
                <Badge variant='outline' className='rounded-md text-xs'>
                  CEFR {effectiveCefr}
                </Badge>
              )}
            </div>

            <ul
              className={cn(
                'grid w-full grid-cols-2 gap-3 sm:grid-cols-4',
                showChips ? '' : 'pointer-events-none',
              )}
            >
              {sections.map((section, i) => {
                const meta = SKILL_META[section.skill]
                const Icon = meta.icon
                const empty = section.band == null
                return (
                  <li
                    key={section.skill}
                    className={cn(
                      'flex flex-col items-center gap-2 rounded-xl border border-border/60 bg-card px-3 py-3 shadow-sm',
                      showChips
                        ? 'motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 motion-safe:fill-mode-both motion-safe:duration-300'
                        : 'opacity-0',
                    )}
                    style={
                      showChips && !reduced
                        ? { animationDelay: `${i * TIMELINE.chipStagger}ms` }
                        : undefined
                    }
                  >
                    <span
                      className={cn(
                        'flex size-9 items-center justify-center rounded-lg',
                        meta.surface,
                      )}
                    >
                      <Icon className={cn('size-4', meta.accent)} />
                    </span>
                    <span className='text-xs font-medium uppercase tracking-wider text-muted-foreground'>
                      {meta.label}
                    </span>
                    {empty ? (
                      <span className='font-manrope text-xl font-semibold tabular-nums text-muted-foreground'>
                        {section.status === 'pending' ? '…' : '—'}
                      </span>
                    ) : (
                      <span
                        className={cn(
                          'font-manrope text-xl font-semibold tabular-nums',
                          meta.accent,
                        )}
                      >
                        {formatBand(section.band)}
                      </span>
                    )}
                  </li>
                )
              })}
            </ul>

            <div className='flex flex-wrap items-center justify-center gap-2'>
              <Button
                size='sm'
                className='gap-1.5 rounded-lg'
                onClick={onViewResults}
                autoFocus
              >
                {skipLabel}
              </Button>
              {showDownload && (
                <Button
                  size='sm'
                  variant='outline'
                  className='gap-1.5 rounded-lg'
                  onClick={onDownloadPdf}
                >
                  <Download className='size-3.5' />
                  Download PDF
                </Button>
              )}
            </div>

        <div aria-live='polite' aria-atomic='true' className='sr-only'>
          {announcement}
        </div>
      </div>
    </div>
  )
}
