import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Question, Section, SectionType } from '../../data/schema'

type SectionAnswers = Record<string, Record<string, unknown>>

type Props = {
  sortedSections: Section[]
  sectionQuestions: Record<string, Question[]>
  answers: Record<string, SectionAnswers>
  flagged: Set<string>
  currentType: SectionType
  onJump: (sectionId: string, questionId: string) => void
  onClose: () => void
}

function isAnswered(response: Record<string, unknown> | undefined): boolean {
  if (!response) return false
  return Object.values(response).some((v) => {
    if (v === '' || v === null || v === undefined) return false
    if (Array.isArray(v)) return v.length > 0
    if (typeof v === 'object') return Object.keys(v as object).length > 0
    return true
  })
}

const LABELS: Record<string, string> = {
  listening: 'Listening',
  reading:   'Reading',
  writing:   'Writing',
  speaking:  'Speaking',
}

export function QuestionPalette({
  sortedSections,
  sectionQuestions,
  answers,
  flagged,
  currentType,
  onJump,
  onClose,
}: Props) {
  type Entry = { question: Question; sectionId: string }
  const groups: { label: string; type: SectionType; isCurrent: boolean; entries: Entry[] }[] = []

  for (const section of sortedSections) {
    const qs = [...(sectionQuestions[section.id] ?? [])].sort((a, b) => a.order - b.order)
    if (qs.length === 0) continue
    const sectionType = section.type as SectionType
    groups.push({
      label: LABELS[sectionType] ?? sectionType,
      type: sectionType,
      isCurrent: sectionType === currentType,
      entries: qs.map((q) => ({ question: q, sectionId: section.id })),
    })
  }

  return (
    <div className='fixed inset-0 z-50 flex items-end justify-center sm:items-center'>
      {/* Backdrop */}
      <div
        className='absolute inset-0 bg-black/30 backdrop-blur-sm'
        onClick={onClose}
      />

      {/* Panel */}
      <div className='relative z-10 flex max-h-[80vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:rounded-2xl'>
        {/* Header */}
        <div className='flex items-center justify-between border-b border-slate-200 px-5 py-4'>
          <h2 className='text-[15px] font-bold text-slate-900'>Question Navigator</h2>
          <button
            type='button'
            onClick={onClose}
            className='rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700'
          >
            <X className='size-5' />
          </button>
        </div>

        {/* Legend */}
        <div className='flex items-center gap-4 border-b border-slate-100 px-5 py-2.5'>
          {[
            { color: 'bg-white border-slate-300', label: 'Not answered' },
            { color: 'bg-emerald-500', label: 'Answered' },
            { color: 'bg-amber-400', label: 'Flagged' },
          ].map(({ color, label }) => (
            <div key={label} className='flex items-center gap-1.5'>
              <div className={cn('size-3 rounded-sm border', color)} />
              <span className='text-[12px] text-slate-500'>{label}</span>
            </div>
          ))}
        </div>

        {/* Content */}
        <div className='overflow-y-auto px-5 py-4'>
          {groups.map((group, gi) => (
            <div key={gi} className={gi > 0 ? 'mt-5' : ''}>
              <div className='mb-2 flex items-center gap-2'>
                <p className='text-[13px] font-semibold uppercase tracking-wide text-slate-500'>
                  {group.label}
                </p>
                {group.isCurrent && (
                  <span className='rounded bg-blue-100 px-1.5 py-0.5 text-[11px] font-medium text-blue-600'>
                    Current
                  </span>
                )}
              </div>
              <div className='flex flex-wrap gap-2'>
                {group.entries.map(({ question, sectionId }) => {
                  const resp = answers[sectionId]?.[question.id]
                  const answered = isAnswered(resp)
                  const isFlagged = flagged.has(question.id)
                  return (
                    <button
                      key={question.id}
                      type='button'
                      onClick={() => { onJump(sectionId, question.id); onClose() }}
                      title={`Q${question.order}${isFlagged ? ' (flagged)' : ''}${answered ? ' (answered)' : ''}`}
                      className={cn(
                        'flex size-9 items-center justify-center rounded-md border text-[13px] font-semibold transition-colors',
                        isFlagged
                          ? 'border-amber-400 bg-amber-400 text-white hover:bg-amber-500'
                          : answered
                            ? 'border-emerald-500 bg-emerald-500 text-white hover:bg-emerald-600'
                            : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
                      )}
                    >
                      {question.order}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
