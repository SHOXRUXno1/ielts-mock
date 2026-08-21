import { useEffect, useMemo, useRef, useState } from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
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
  countUpDuration: 900,
  toneAt: 1300,
  chipsStart: 1400,
  chipStagger: 60,
  ctaAt: 2100,
  total: 2400,
} as const

export type ScoreRevealSectionStatus = 'scored' | 'pending' | 'not_attempted'

export type ScoreRevealSection = {
  skill: SkillKey
  band: number | null
  status: ScoreRevealSectionStatus
}

export type ScoreRevealProps = {
  overallBand: number
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
  const [phase, setPhase] = useState<Phase>(() => (reduced ? 'done' : 'fade'))
  const [announcement, setAnnouncement] = useState('')
  const contentRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  const tone = bandTone(overallBand)
  const glow = toneGlow(tone)
  const toneClasses = bandToneClasses(tone)
  const descriptor = bandDescriptor(overallBand)
  const effectiveCefr = cefr ?? cefrLevel(overallBand)
  const confetti = useMemo(() => confettiPieces(CONFETTI_COUNT), [])

  // Capture and restore focus.
  useEffect(() => {
    previouslyFocused.current =
      (document.activeElement as HTMLElement | null) ?? null
    return () => {
      previouslyFocused.current?.focus?.()
    }
  }, [])

  // Phase machine — reduced motion starts already at 'done' via the state
  // initializer, so this effect is a no-op in that case.
  useEffect(() => {
    if (reduced) return
    const timers: number[] = []
    timers.push(
      window.setTimeout(() => setPhase('counting'), TIMELINE.fadeIn),
      window.setTimeout(() => setPhase('tone'), TIMELINE.toneAt),
      window.setTimeout(() => setPhase('chips'), TIMELINE.chipsStart),
      window.setTimeout(() => setPhase('done'), TIMELINE.ctaAt),
    )
    return () => {
      for (const id of timers) window.clearTimeout(id)
    }
  }, [reduced])

  const canClose = phase === 'done'

  const handleAnnounce = () => {
    const cefrPart = effectiveCefr ? `, CEFR ${effectiveCefr}` : ''
    setAnnouncement(
      `Overall band ${formatBand(overallBand)} out of 9${cefrPart}. ${descriptor ?? ''}`.trim(),
    )
  }

  const showConfetti = !reduced && tone === 'strong' && phase !== 'fade' && phase !== 'counting'
  const showToneBadge =
    reduced || phase === 'tone' || phase === 'chips' || phase === 'done'
  const showChips = reduced || phase === 'chips' || phase === 'done'
  const showCtas = reduced || phase === 'done'

  const primaryCtaLabel = tone === 'weak' ? 'Review mistakes' : 'View results'

  return (
    <DialogPrimitive.Root
      open
      onOpenChange={(open) => {
        if (!open && canClose) onClose()
      }}
    >
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className={cn(
            'fixed inset-0 z-50 bg-surface-sunken/80 backdrop-blur-md',
            'motion-safe:animate-in motion-safe:fade-in motion-safe:duration-300',
          )}
        />
        <DialogPrimitive.Content
          ref={contentRef}
          tabIndex={-1}
          onEscapeKeyDown={(event) => {
            if (!canClose) event.preventDefault()
          }}
          onPointerDownOutside={(event) => {
            if (!canClose) event.preventDefault()
          }}
          onInteractOutside={(event) => {
            if (!canClose) event.preventDefault()
          }}
          className={cn(
            'fixed inset-0 z-50 flex flex-col items-center justify-center px-6 py-10 outline-none',
            'motion-safe:animate-in motion-safe:fade-in motion-safe:duration-300',
          )}
        >
          <DialogPrimitive.Title className='sr-only'>
            {testTitle ? `${testTitle} — Score reveal` : 'Score reveal'}
          </DialogPrimitive.Title>
          <DialogPrimitive.Description className='sr-only'>
            Your band results for this mock test.
          </DialogPrimitive.Description>

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
                    } as React.CSSProperties
                  }
                />
              ))}
            </div>
          )}

          <div
            className={cn(
              'relative z-10 flex w-full max-w-xl flex-col items-center gap-6 text-center',
            )}
          >
            {testTitle && (
              <p className='text-xs font-medium uppercase tracking-wider text-muted-foreground'>
                {testTitle}
              </p>
            )}

            <div className='flex flex-col items-center gap-4'>
              <BandValue
                band={overallBand}
                label='Overall'
                size='display'
                showCefr={false}
                showDescriptor={false}
                animateFrom={reduced ? undefined : 0}
                animateDelay={reduced ? 0 : TIMELINE.countUpStart}
                animateDuration={TIMELINE.countUpDuration}
                onAnimateComplete={handleAnnounce}
                className='text-center'
              />
              <BandScale
                band={overallBand}
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
                        —
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

            <div
              className={cn(
                'flex flex-wrap items-center justify-center gap-2 transition-opacity duration-300',
                showCtas ? 'opacity-100' : 'pointer-events-none opacity-0',
              )}
            >
              <Button
                size='sm'
                className='gap-1.5 rounded-lg'
                onClick={onViewResults}
                disabled={!showCtas}
                autoFocus={showCtas}
              >
                {primaryCtaLabel}
              </Button>
              <Button
                size='sm'
                variant='outline'
                className='gap-1.5 rounded-lg'
                onClick={onDownloadPdf}
                disabled={!showCtas}
              >
                <Download className='size-3.5' />
                Download PDF
              </Button>
            </div>
          </div>

          <div
            aria-live='polite'
            aria-atomic='true'
            className='sr-only'
          >
            {announcement}
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
