import { useRouterState } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import type { Question, Section, SectionType } from '../../data/schema'
import {
  isQuestionAnswered,
  questionNavEntries,
  type QuestionNavEntry,
} from '../../take/answered'
import { useTakeTest } from '../../take/take-test-context'
import { useTestNavigation } from '../../take/use-test-navigation'

type PartGroup = {
  key: string
  label: string
  partIndex: number
  sectionId: string
  entries: QuestionNavEntry[]
  /**
   * Writing only — the task's own question object, carried through so the
   * segmented control at the bottom can read its response and show a
   * word-count status dot without a second lookup.
   */
  writingQuestion?: Question
}

/** Count whitespace-delimited words, matching writing-section's own logic. */
function countWords(text: string): number {
  return text
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length
}

function buildGroups(
  currentType: SectionType,
  sortedSections: Section[],
  sectionQuestions: Record<string, Question[]>
): PartGroup[] {
  if (currentType === 'speaking') return []

  if (currentType === 'writing') {
    const writingSec = sortedSections.find((s) => s.type === 'writing')
    if (!writingSec) return []
    const qs = [...(sectionQuestions[writingSec.id] ?? [])]
      .filter((q) => q.question_type === 'essay' || q.task_number != null)
      .sort((a, b) => (a.task_number ?? a.order) - (b.task_number ?? b.order))
    return qs.map((q, i) => ({
      key: q.id,
      label: `Task ${q.task_number ?? i + 1}`,
      partIndex: i + 1,
      sectionId: writingSec.id,
      entries: [],
      writingQuestion: q,
    }))
  }

  const siblings = sortedSections
    .filter((s) => s.type === currentType)
    .sort((a, b) => a.order - b.order)

  const prefix = currentType === 'reading' ? 'Passage' : 'Part'

  return siblings.map((section, i) => ({
    key: section.id,
    label: `${prefix} ${i + 1}`,
    partIndex: i + 1,
    sectionId: section.id,
    entries: questionNavEntries(sectionQuestions[section.id] ?? [], section.id),
  }))
}

export function QuestionNavBar() {
  const ctx = useTakeTest()
  const nav = useTestNavigation()

  const {
    sortedSections,
    sectionQuestions,
    answers,
    flagged,
    isPractice,
    practiceScope,
  } = ctx
  const currentType = nav.currentType
  const currentPart = nav.currentPart
  const hash = useRouterState({ select: (s) => s.location.hash })
  const focusedNumber = /^#q-(\d+)$/.exec(hash)?.[1]

  if (currentType === 'speaking') return null

  let groups = buildGroups(currentType, sortedSections, sectionQuestions)
  if (isPractice && practiceScope === 'part') {
    groups = groups.filter((g) => g.partIndex === currentPart)
  }
  if (groups.length === 0) return null

  const isWriting = currentType === 'writing'

  if (isWriting) {
    return (
      <nav
        aria-label='Writing task navigator'
        data-tour='question-navigator'
        className='shrink-0 border-t border-border bg-background pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]'
      >
        <div className='mx-auto flex w-max items-center gap-1 rounded-xl bg-muted/60 p-1 shadow-inner ring-1 ring-black/[0.03] dark:ring-white/[0.03]'>
          {groups.map((group) => {
            const isActive = group.partIndex === currentPart
            const q = group.writingQuestion
            const resp = q
              ? (answers[group.sectionId]?.[q.id] as
                  | { answer?: string }
                  | undefined)
              : undefined
            const text = typeof resp?.answer === 'string' ? resp.answer : ''
            const words = countWords(text)
            const minWords =
              q?.min_words ??
              (q?.content?.min_words as number | undefined) ??
              (group.partIndex === 1 ? 150 : 250)
            // Three-state status for the leading dot:
            //   empty      — nothing written yet
            //   partial    — some text, still below the task minimum
            //   complete   — at or above the minimum
            const status: 'empty' | 'partial' | 'complete' =
              words === 0
                ? 'empty'
                : words < minWords
                  ? 'partial'
                  : 'complete'
            return (
              <button
                key={group.key}
                type='button'
                onClick={() => void nav.goToPart(group.partIndex)}
                aria-current={isActive ? 'page' : undefined}
                className={cn(
                  'inline-flex min-h-10 items-center gap-2 rounded-lg px-4 text-[13px] font-semibold whitespace-nowrap transition-all',
                  isActive
                    ? 'bg-background text-foreground shadow-sm ring-1 ring-black/[0.04] dark:ring-white/[0.06]'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    'size-2 shrink-0 rounded-full ring-1 ring-inset transition-colors',
                    status === 'complete' &&
                      'bg-emerald-500 ring-emerald-600/40',
                    status === 'partial' && 'bg-amber-400 ring-amber-500/40',
                    status === 'empty' &&
                      'bg-transparent ring-slate-400/60 dark:ring-slate-500/60'
                  )}
                />
                {group.label}
                {words > 0 ? (
                  <span className='text-[11px] font-medium tabular-nums text-muted-foreground'>
                    {words}
                  </span>
                ) : null}
              </button>
            )
          })}
        </div>
      </nav>
    )
  }

  return (
    <nav
      aria-label='Question navigator'
      data-tour='question-navigator'
      className='shrink-0 border-t border-border bg-gradient-to-b from-background to-muted/50 student-dark:bg-none'
    >
      <div className='[scrollbar-width:thin] overflow-x-auto px-3 pt-2.5 pb-[max(0.625rem,env(safe-area-inset-bottom))] [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-muted-foreground/30'>
        <div className='mx-auto flex w-max items-center gap-4'>
          {groups.map((group) => {
            const isActive = group.partIndex === currentPart
            return (
              <div key={group.key} className='flex shrink-0 items-center gap-2'>
                <button
                  type='button'
                  onClick={() => void nav.goToPart(group.partIndex)}
                  className={cn(
                    'flex min-h-11 shrink-0 items-center rounded-md px-2 py-1 text-[13px] font-medium tracking-wide whitespace-nowrap lg:min-h-0',
                    isActive
                      ? 'text-foreground'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {group.label}
                </button>
                <div
                  className={cn(
                    'flex overflow-hidden rounded-lg border bg-background shadow-sm',
                    isActive
                      ? 'border-blue-200 dark:border-blue-800'
                      : 'border-border'
                  )}
                >
                  {group.entries.map(
                    ({ question, sectionId, displayNumber }) => {
                      const resp = answers[sectionId]?.[question.id]
                      const answered = isQuestionAnswered(question, resp)
                      const isFlagged = flagged.has(question.id)
                      const isFocused =
                        focusedNumber === String(displayNumber)
                      return (
                        <button
                          key={`${question.id}-${displayNumber}`}
                          type='button'
                          onClick={() =>
                            void nav.goToQuestion(
                              sectionId,
                              question.id,
                              displayNumber
                            )
                          }
                          title={`Q${displayNumber}${isFlagged ? ' (flagged)' : ''}${answered ? ' (answered)' : ''}`}
                          className={cn(
                            'flex h-11 min-w-11 items-center justify-center border-r px-1.5 text-[13px] font-semibold tabular-nums last:border-r-0 lg:h-8 lg:min-w-8 lg:text-[12px]',
                            isActive
                              ? 'border-blue-100 dark:border-blue-900'
                              : 'border-border',
                            isFlagged
                              ? 'bg-amber-50 text-amber-800 hover:bg-amber-100 student-dark:bg-amber-950/40 student-dark:text-amber-200 student-dark:hover:bg-amber-950/60'
                              : answered
                                ? 'bg-blue-600 text-white hover:bg-blue-700'
                                : 'bg-background text-foreground hover:bg-muted',
                            isFocused &&
                              'bg-blue-600 text-white shadow-[inset_0_0_0_2px_rgba(255,255,255,0.35)]'
                          )}
                        >
                          {displayNumber}
                        </button>
                      )
                    }
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
