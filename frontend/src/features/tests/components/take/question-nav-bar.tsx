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
}

function buildGroups(
  currentType: SectionType,
  sortedSections: Section[],
  sectionQuestions: Record<string, Question[]>,
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

  return (
    <nav
      aria-label='Question navigator'
      className='shrink-0 border-t border-slate-200/80 bg-gradient-to-b from-white to-slate-50'
    >
      <div className='overflow-x-auto px-3 py-2.5 [scrollbar-width:thin] [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-300'>
        <div className='mx-auto flex w-max items-center gap-4'>
          {groups.map((group) => {
            const isActive = group.partIndex === currentPart
            return (
              <div
                key={group.key}
                className='flex shrink-0 items-center gap-2'
              >
                <button
                  type='button'
                  onClick={() => void nav.goToPart(group.partIndex)}
                  className={cn(
                    'shrink-0 rounded-md px-2 py-1 text-[13px] font-medium tracking-wide whitespace-nowrap',
                    isActive
                      ? 'text-slate-800'
                      : 'text-slate-500 hover:text-slate-700',
                  )}
                >
                  {group.label}
                </button>
                {!isWriting && (
                  <div
                    className={cn(
                      'flex overflow-hidden rounded-lg border bg-white shadow-sm',
                      isActive ? 'border-blue-200' : 'border-slate-200',
                    )}
                  >
                    {group.entries.map(
                      ({ question, sectionId, displayNumber }) => {
                        const resp = answers[sectionId]?.[question.id]
                        const answered = isQuestionAnswered(question, resp)
                        const isFlagged = flagged.has(question.id)
                        const isFocused = focusedNumber === String(displayNumber)
                        return (
                          <button
                            key={`${question.id}-${displayNumber}`}
                            type='button'
                            onClick={() =>
                              void nav.goToQuestion(
                                sectionId,
                                question.id,
                                displayNumber,
                              )
                            }
                            title={`Q${displayNumber}${isFlagged ? ' (flagged)' : ''}${answered ? ' (answered)' : ''}`}
                            className={cn(
                              'flex h-8 min-w-8 items-center justify-center border-r px-1.5 text-[12px] font-semibold tabular-nums last:border-r-0',
                              isActive ? 'border-blue-100' : 'border-slate-100',
                              isFlagged
                                ? 'bg-amber-50 text-amber-800 hover:bg-amber-100'
                                : answered
                                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                                  : 'bg-white text-slate-700 hover:bg-slate-50',
                              isFocused &&
                                'bg-blue-600 text-white shadow-[inset_0_0_0_2px_rgba(255,255,255,0.35)]',
                            )}
                          >
                            {displayNumber}
                          </button>
                        )
                      },
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
