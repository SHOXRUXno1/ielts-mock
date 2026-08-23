import { Clock, Loader2, Play, ShieldCheck, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  durationByType,
  estimatedTotalMinutes,
  formatMinutes,
  SPEAKING_TYPICAL_MINUTES,
} from '../data/duration-rules'
import type { Section, SectionType, TestDetail } from '../data/schema'
import { SECTION_LABELS, TYPE_ORDER } from './constants'
import {
  enterExamFullscreen,
  EXAM_FULLSCREEN_ENFORCED,
} from './exam-fullscreen'
import { cn } from '@/lib/utils'
import { SKILL_ICONS } from '@/features/student/practice/skill-icons'

const SECTION_ICONS = SKILL_ICONS

const SECTION_THEME: Record<
  SectionType,
  { soft: string; ring: string; chip: string }
> = {
  listening: {
    soft: 'from-sky-50 to-white dark:from-sky-950/40 dark:to-card',
    ring: 'ring-sky-200/70 dark:ring-sky-800/50',
    chip: 'bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300',
  },
  reading: {
    soft: 'from-emerald-50 to-white dark:from-emerald-950/40 dark:to-card',
    ring: 'ring-emerald-200/70 dark:ring-emerald-800/50',
    chip: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  },
  writing: {
    soft: 'from-violet-50 to-white dark:from-violet-950/40 dark:to-card',
    ring: 'ring-violet-200/70 dark:ring-violet-800/50',
    chip: 'bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300',
  },
  speaking: {
    soft: 'from-amber-50 to-white dark:from-amber-950/40 dark:to-card',
    ring: 'ring-amber-200/70 dark:ring-amber-800/50',
    chip: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  },
}

type Props = {
  test: TestDetail
  sortedSections: Section[]
  onStart: () => void
  onCancel: () => void
  isStarting: boolean
}

export function IntroScreen({
  test,
  sortedSections,
  onStart,
  onCancel,
  isStarting,
}: Props) {
  const presentTypes = TYPE_ORDER.filter((t) =>
    sortedSections.some((s) => s.type === t),
  )
  const durations = durationByType(test.section_settings)
  const totalMinutes = estimatedTotalMinutes(
    test.section_settings?.filter((s) => presentTypes.includes(s.section_type)),
  )
  const estimated = presentTypes.some((t) => durations[t] == null)

  return (
    <div className='relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 py-10'>
      {/* Soft atmosphere */}
      <div
        aria-hidden
        className='pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(56,189,248,0.14),_transparent_55%),radial-gradient(ellipse_at_bottom,_rgba(167,139,250,0.10),_transparent_50%)] dark:bg-[radial-gradient(ellipse_at_top,_rgba(14,165,233,0.12),_transparent_55%),radial-gradient(ellipse_at_bottom,_rgba(124,58,237,0.10),_transparent_50%)]'
      />

      <div className='relative z-10 flex w-full max-w-xl flex-col gap-6'>
        {/* Header */}
        <div className='text-center'>
          <div className='mx-auto mb-4 flex items-center justify-center gap-2'>
            {presentTypes.map((t) => (
              <img
                key={t}
                src={SECTION_ICONS[t]}
                alt=''
                aria-hidden
                draggable={false}
                className='size-12 object-contain drop-shadow-[0_8px_16px_rgba(15,23,42,0.14)] sm:size-14'
              />
            ))}
          </div>
          <p className='text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-700/80 dark:text-sky-300/80'>
            Full mock test
          </p>
          <h1 className='mt-1.5 text-2xl font-semibold tracking-tight text-foreground sm:text-[28px]'>
            {test.title}
          </h1>
          {test.description && (
            <p className='mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground'>
              {test.description}
            </p>
          )}
        </div>

        {/* Sections */}
        <div className='overflow-hidden rounded-2xl border border-border/70 bg-card/90 shadow-sm backdrop-blur'>
          <div className='flex items-center justify-between border-b border-border/70 px-5 py-3.5'>
            <h2 className='text-[11px] font-semibold uppercase tracking-wider text-muted-foreground'>
              {presentTypes.length} sections in exam order
            </h2>
            <span className='inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground'>
              <ShieldCheck className='size-3.5' />
              Timed separately
            </span>
          </div>

          <div className='space-y-2.5 p-3 sm:p-4'>
            {presentTypes.map((t, i) => {
              const minutes = durations[t]
              const isSpeaking = t === 'speaking'
              const theme = SECTION_THEME[t]
              const durationLabel =
                minutes != null
                  ? `${minutes} min`
                  : isSpeaking
                    ? `~${SPEAKING_TYPICAL_MINUTES} min`
                    : 'Untimed'

              return (
                <div
                  key={t}
                  className={cn(
                    'flex items-center gap-3.5 rounded-2xl border bg-gradient-to-r p-3 ring-1 transition-transform hover:-translate-y-0.5',
                    theme.soft,
                    theme.ring,
                  )}
                >
                  <div className='flex size-14 shrink-0 items-center justify-center rounded-2xl bg-white/85 shadow-sm ring-1 ring-black/5 dark:bg-background/60'>
                    <img
                      src={SECTION_ICONS[t]}
                      alt=''
                      aria-hidden
                      draggable={false}
                      className='size-11 object-contain drop-shadow-[0_6px_10px_rgba(15,23,42,0.12)]'
                    />
                  </div>

                  <div className='min-w-0 flex-1'>
                    <div className='flex flex-wrap items-center gap-2'>
                      <span className='text-[11px] font-semibold text-muted-foreground'>
                        Part {i + 1}
                      </span>
                      <span className='text-[15px] font-semibold tracking-tight text-foreground'>
                        {SECTION_LABELS[t]}
                      </span>
                      {isSpeaking && (
                        <span
                          className={cn(
                            'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
                            theme.chip,
                          )}
                        >
                          AI Examiner
                        </span>
                      )}
                    </div>
                    <p className='mt-0.5 text-[12px] text-muted-foreground'>
                      {isSpeaking
                        ? 'Live conversation · AI-paced'
                        : 'Exam timer starts when you enter'}
                    </p>
                  </div>

                  <div className='shrink-0 text-right'>
                    <p className='text-sm font-semibold tabular-nums text-foreground'>
                      {durationLabel}
                    </p>
                    {isSpeaking && minutes == null && (
                      <p className='text-[10px] text-muted-foreground'>
                        AI-paced
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div className='flex flex-wrap items-center gap-2 border-t border-border/70 bg-muted/30 px-5 py-3'>
            <Clock className='size-4 text-muted-foreground' />
            <span className='text-sm text-foreground'>
              Total time:{' '}
              <span className='font-semibold'>
                {estimated ? '~' : ''}
                {formatMinutes(totalMinutes)}
              </span>
            </span>
            <span className='ms-auto text-[11px] text-muted-foreground'>
              Leave a section to seal it — no going back
            </span>
          </div>
        </div>

        {/* Note + actions */}
        <div className='space-y-4'>
          <p className='rounded-xl border border-border/60 bg-white/70 px-4 py-3 text-center text-[13px] leading-relaxed text-muted-foreground dark:bg-background/50'>
            Timers start when you enter a section. Leaving a section seals it —
            you cannot return.
          </p>
          <div className='flex flex-col-reverse items-stretch gap-2.5 sm:flex-row sm:items-center sm:justify-center'>
            <Button
              size='lg'
              variant='outline'
              className='h-12 rounded-xl px-8 text-[15px] font-semibold'
              onClick={onCancel}
              disabled={isStarting}
            >
              <X className='mr-2 size-4' />
              Cancel
            </Button>
            <Button
              size='lg'
              className='h-12 rounded-xl bg-sky-600 px-10 text-[15px] font-semibold text-white shadow-md shadow-sky-500/25 hover:bg-sky-700'
              onClick={() => {
                if (EXAM_FULLSCREEN_ENFORCED) enterExamFullscreen()
                onStart()
              }}
              disabled={isStarting}
            >
              {isStarting ? (
                <Loader2 className='mr-2 size-4 animate-spin' />
              ) : (
                <Play className='mr-2 size-4 fill-current' />
              )}
              Start Test
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
