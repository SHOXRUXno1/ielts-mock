import {
  BookOpen,
  Clock,
  Headphones,
  Loader2,
  Mic,
  PenLine,
  Play,
  ShieldCheck,
  X,
  type LucideIcon,
} from 'lucide-react'
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

const SECTION_ICONS: Record<SectionType, LucideIcon> = {
  listening: Headphones,
  reading: BookOpen,
  writing: PenLine,
  speaking: Mic,
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
    sortedSections.some((s) => s.type === t)
  )
  const durations = durationByType(test.section_settings)
  const totalMinutes = estimatedTotalMinutes(
    test.section_settings?.filter((s) => presentTypes.includes(s.section_type))
  )
  const estimated = presentTypes.some((t) => durations[t] == null)
  const kicker =
    presentTypes.length === TYPE_ORDER.length ? 'Full mock test' : 'Practice test'

  return (
    <main className='flex min-h-svh flex-col items-center justify-center px-6 py-12 sm:py-16'>
      <div className='flex w-full max-w-xl flex-col gap-8'>
        <header className='text-center'>
          <p className='text-xs font-medium tracking-wider text-muted-foreground uppercase'>
            {kicker}
          </p>
          <h1 className='mt-2 text-2xl font-semibold tracking-tight text-foreground'>
            {test.title}
          </h1>
          {test.description && (
            <p className='mx-auto mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground'>
              {test.description}
            </p>
          )}
        </header>

        <section aria-labelledby='exam-sections-heading'>
          <div className='flex flex-wrap items-center justify-between gap-3 pb-4'>
            <h2
              id='exam-sections-heading'
              className='text-sm font-medium text-foreground'
            >
              {presentTypes.length} sections in exam order
            </h2>
            <span className='inline-flex items-center gap-2 text-sm text-muted-foreground'>
              <ShieldCheck aria-hidden='true' className='size-4' />
              Timed separately
            </span>
          </div>

          <ol className='divide-y divide-border border-y border-border'>
            {presentTypes.length > 0 ? (
              presentTypes.map((t, i) => {
                const minutes = durations[t]
                const isSpeaking = t === 'speaking'
                const Icon = SECTION_ICONS[t]
                const durationLabel =
                  minutes != null
                    ? `${minutes} min`
                    : isSpeaking
                      ? `~${SPEAKING_TYPICAL_MINUTES} min`
                      : 'Untimed'

                return (
                  <li key={t} className='flex items-center gap-4 py-4'>
                    <Icon
                      aria-hidden='true'
                      className='size-5 shrink-0 text-muted-foreground'
                    />

                    <div className='min-w-0 flex-1'>
                      <div className='flex flex-wrap items-baseline gap-x-2 gap-y-1'>
                        <span className='text-xs font-medium text-muted-foreground tabular-nums'>
                          Part {i + 1}
                        </span>
                        <span className='text-base font-medium text-foreground'>
                          {SECTION_LABELS[t]}
                        </span>
                        {isSpeaking && (
                          <span className='text-xs font-medium text-muted-foreground'>
                            AI Examiner
                          </span>
                        )}
                      </div>
                      {isSpeaking && (
                        <p className='mt-1 text-sm text-muted-foreground'>
                          Live conversation · AI-paced
                        </p>
                      )}
                    </div>

                    <span className='shrink-0 text-sm font-semibold text-foreground tabular-nums'>
                      {durationLabel}
                    </span>
                  </li>
                )
              })
            ) : (
              <li
                role='status'
                className='flex flex-col gap-1 py-4 text-sm text-muted-foreground'
              >
                <span>No sections are available for this test yet.</span>
                <span>Cancel to return to the test list.</span>
              </li>
            )}
          </ol>

          <div className='flex flex-wrap items-center justify-between gap-3 pt-4'>
            <span className='inline-flex items-center gap-2 text-sm text-muted-foreground'>
              <Clock aria-hidden='true' className='size-4' />
              Total time:{' '}
              <span className='font-semibold text-foreground tabular-nums'>
                {estimated ? '~' : ''}
                {formatMinutes(totalMinutes)}
              </span>
            </span>
          </div>
        </section>

        <div className='flex flex-col gap-6'>
          <p
            role='note'
            className='text-sm leading-relaxed text-muted-foreground'
          >
            Timers start when you enter a section. Leaving a section seals it —
            you cannot return.
          </p>

          <div className='flex flex-col-reverse gap-3 sm:flex-row sm:justify-center'>
            <Button
              size='lg'
              variant='outline'
              className='h-10 w-full px-5 font-medium shadow-none sm:w-auto'
              onClick={onCancel}
              disabled={isStarting}
            >
              <X aria-hidden='true' />
              Cancel
            </Button>
            <Button
              size='lg'
              className='h-10 w-full px-5 font-medium shadow-none sm:w-auto'
              onClick={() => {
                if (EXAM_FULLSCREEN_ENFORCED) enterExamFullscreen()
                onStart()
              }}
              disabled={isStarting || presentTypes.length === 0}
              aria-busy={isStarting}
            >
              {isStarting ? (
                <Loader2 aria-hidden='true' className='animate-spin' />
              ) : (
                <Play aria-hidden='true' className='fill-current' />
              )}
              Start Test
            </Button>
          </div>
        </div>
      </div>
    </main>
  )
}
