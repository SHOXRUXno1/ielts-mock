import {
  BookOpen,
  Headphones,
  Loader2,
  Mic,
  PenLine,
  Play,
  X,
  type LucideIcon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  durationByType,
  estimatedTotalMinutes,
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
  const totalHours = Math.floor(totalMinutes / 60)
  const totalMins = totalMinutes % 60

  return (
    <main className='flex min-h-svh flex-col items-center justify-center px-6 py-12 sm:py-16'>
      <div className='flex w-full max-w-xl flex-col gap-8 rounded-2xl border border-border bg-card p-8 sm:p-10'>
        <header className='text-center'>
          <p className='text-[11px] font-medium tracking-[0.14em] text-muted-foreground uppercase'>
            {kicker}
          </p>
          <h1 className='mt-3 text-[26px] font-semibold leading-tight tracking-tight text-foreground'>
            {test.title}
          </h1>
          {test.description && (
            <p className='mx-auto mt-3 max-w-md text-sm leading-relaxed text-muted-foreground'>
              {test.description}
            </p>
          )}

          {totalMinutes > 0 && (
            <div
              className='mt-6 flex items-baseline justify-center gap-1.5 tabular-nums'
              aria-label={`Total time ${estimated ? 'approximately ' : ''}${totalHours ? `${totalHours} hours ` : ''}${totalMins} minutes`}
            >
              {estimated && (
                <span className='text-2xl font-medium text-muted-foreground'>~</span>
              )}
              {totalHours > 0 && (
                <>
                  <span className='text-5xl font-medium leading-none tracking-tight text-foreground'>
                    {totalHours}
                  </span>
                  <span className='mr-2 text-base text-muted-foreground'>h</span>
                </>
              )}
              <span className='text-5xl font-medium leading-none tracking-tight text-foreground'>
                {totalMins}
              </span>
              <span className='text-base text-muted-foreground'>min</span>
            </div>
          )}
        </header>

        <section aria-labelledby='exam-sections-heading'>
          <h2 id='exam-sections-heading' className='sr-only'>
            {presentTypes.length} sections in exam order
          </h2>
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
                  <li key={t} className='flex items-center gap-3 py-3.5'>
                    <span
                      aria-hidden='true'
                      className='inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-medium tabular-nums text-muted-foreground'
                    >
                      {i + 1}
                    </span>
                    <Icon
                      aria-hidden='true'
                      className='size-4 shrink-0 text-muted-foreground'
                    />
                    <span className='flex-1 truncate text-[15px] text-foreground'>
                      {SECTION_LABELS[t]}
                      {isSpeaking && (
                        <span className='ml-2 text-xs text-muted-foreground'>
                          AI Examiner
                        </span>
                      )}
                    </span>
                    <span className='shrink-0 text-sm text-muted-foreground tabular-nums'>
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
        </section>

        <div className='flex flex-col gap-6'>
          <p
            role='note'
            className='text-center text-xs leading-relaxed text-muted-foreground'
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
              Start test
            </Button>
          </div>
        </div>
      </div>
    </main>
  )
}
