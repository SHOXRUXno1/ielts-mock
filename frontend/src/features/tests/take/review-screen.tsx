import { useMemo, useState } from 'react'
import { CheckCircle2, ChevronDown, Clock, Flag, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import {
  countScoringSlots,
  scoringSlotsForQuestion,
  type SectionType,
} from '../data/schema'
import { SECTION_LABELS, TYPE_ORDER } from './constants'
import { useTakeTest } from './take-test-context'

function formatElapsedMinutes(
  startedAt: string | null | undefined,
  sealedAt: string | null | undefined,
): string {
  if (!startedAt || !sealedAt) return '—'
  const a = Date.parse(startedAt)
  const b = Date.parse(sealedAt)
  if (Number.isNaN(a) || Number.isNaN(b) || b < a) return '—'
  const sec = Math.round((b - a) / 1000)
  const m = Math.max(0, Math.round(sec / 60))
  return `${m} min`
}

function hasAnswerValue(response: Record<string, unknown>): boolean {
  const vals = Object.values(response)
  return vals.some((v) => {
    if (v === '' || v === null || v === undefined) return false
    if (Array.isArray(v)) return (v as unknown[]).length > 0
    if (typeof v === 'object' && v !== null) return Object.keys(v).length > 0
    return true
  })
}

function summarizeResponse(response: Record<string, unknown>): string {
  const answer = response.answer
  if (typeof answer === 'string') {
    const trimmed = answer.trim()
    if (!trimmed) return '(empty)'
    return trimmed.length > 160 ? `${trimmed.slice(0, 160)}…` : trimmed
  }
  if (typeof response.selected === 'string') return response.selected
  if (Array.isArray(response.selected)) {
    return (response.selected as unknown[]).map(String).join(', ') || '(empty)'
  }
  const keys = Object.keys(response)
  if (keys.length === 0) return '(empty)'
  try {
    const raw = JSON.stringify(response)
    return raw.length > 160 ? `${raw.slice(0, 160)}…` : raw
  } catch {
    return '(answer)'
  }
}

export function ReviewScreen() {
  const ctx = useTakeTest()
  const {
    presentTypes,
    sortedSections,
    sectionQuestions,
    answers,
    flagged,
    progress,
    submitTest,
    isSubmitting,
    test,
  } = ctx

  const [openTypes, setOpenTypes] = useState<Set<SectionType>>(new Set())

  const sections = useMemo(() => {
    const byType = new Map(
      (progress?.sections ?? []).map((s) => [s.section_type, s]),
    )
    return TYPE_ORDER.filter((t) => presentTypes.includes(t)).map((type) => {
      const row = byType.get(type)
      const secs = sortedSections.filter((s) => s.type === type)
      const items: Array<{
        questionId: string
        label: string
        text: string
        flagged: boolean
        answered: boolean
        slots: number
      }> = []
      for (const sec of secs) {
        const qs = sectionQuestions[sec.id] ?? []
        const secAnswers = answers[sec.id] ?? {}
        for (const q of qs) {
          const resp = secAnswers[q.id] ?? {}
          const n = q.computed_number ?? q.order
          const answered = hasAnswerValue(resp)
          items.push({
            questionId: q.id,
            label: `Q${n}`,
            text: answered ? summarizeResponse(resp) : '(no answer)',
            flagged: flagged.has(q.id),
            answered,
            slots: scoringSlotsForQuestion(q),
          })
        }
      }

      const allQs = secs.flatMap((s) => sectionQuestions[s.id] ?? [])
      const totalSlots = countScoringSlots(allQs)
      const answeredSlots = items
        .filter((i) => i.answered)
        .reduce((sum, i) => sum + i.slots, 0)

      let summary: string
      if (type === 'speaking') {
        const parts = Math.max(secs.length, items.length || 0)
        summary = `Duration: ${formatElapsedMinutes(row?.started_at, row?.sealed_at)} · ${parts} part${parts === 1 ? '' : 's'}`
      } else if (type === 'writing') {
        const total = items.length
        const answered = items.filter((i) => i.answered).length
        summary = `Time: ${formatElapsedMinutes(row?.started_at, row?.sealed_at)} · ${answered}/${total} tasks`
      } else {
        summary = `Time: ${formatElapsedMinutes(row?.started_at, row?.sealed_at)} · ${answeredSlots}/${totalSlots} answered`
      }

      return {
        type: type as SectionType,
        summary,
        items,
        flaggedCount: items.filter((i) => i.flagged).length,
      }
    })
  }, [
    presentTypes,
    sortedSections,
    sectionQuestions,
    answers,
    flagged,
    progress,
  ])

  const toggle = (type: SectionType) => {
    setOpenTypes((prev) => {
      const next = new Set(prev)
      if (next.has(type)) next.delete(type)
      else next.add(type)
      return next
    })
  }

  return (
    <div className='flex h-svh flex-col bg-white'>
      <header className='flex h-14 shrink-0 items-center justify-between border-b border-slate-200 px-4 sm:px-6'>
        <div>
          <h1 className='text-sm font-semibold text-slate-900'>
            {test.title} — Review
          </h1>
          <p className='text-xs text-slate-500'>All sections completed</p>
        </div>
      </header>

      <main className='min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8'>
        <div className='mx-auto max-w-3xl space-y-4'>
          {sections.map((sec) => {
            const open = openTypes.has(sec.type)
            return (
              <Collapsible
                key={sec.type}
                open={open}
                onOpenChange={() => toggle(sec.type)}
              >
                <section className='rounded-xl border border-slate-200 bg-slate-50/60'>
                  <div className='flex items-start justify-between gap-3 px-4 py-3'>
                    <div className='min-w-0 space-y-1'>
                      <div className='flex items-center gap-2'>
                        <CheckCircle2 className='size-4 shrink-0 text-emerald-500' />
                        <h2 className='text-sm font-semibold text-slate-800'>
                          {SECTION_LABELS[sec.type]}
                        </h2>
                        {sec.flaggedCount > 0 && (
                          <span className='inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700'>
                            <Flag className='size-3' />
                            {sec.flaggedCount} flagged
                          </span>
                        )}
                      </div>
                      <p className='inline-flex items-center gap-1 text-xs text-slate-500'>
                        <Clock className='size-3.5' />
                        {sec.summary}
                      </p>
                    </div>
                    {sec.items.length > 0 && (
                      <CollapsibleTrigger asChild>
                        <button
                          type='button'
                          className='inline-flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100'
                        >
                          Expand to review answers
                          <ChevronDown
                            className={cn(
                              'size-3.5 transition-transform',
                              open && 'rotate-180',
                            )}
                          />
                        </button>
                      </CollapsibleTrigger>
                    )}
                  </div>
                  <CollapsibleContent>
                    <ul className='divide-y divide-slate-100 border-t border-slate-200 bg-white'>
                      {sec.items.length === 0 ? (
                        <li className='px-4 py-3 text-sm text-slate-400'>
                          No answers recorded
                        </li>
                      ) : (
                        sec.items.map((item) => (
                          <li
                            key={item.questionId}
                            className={`flex gap-3 px-4 py-2.5 text-sm ${
                              item.flagged ? 'bg-amber-50/60' : ''
                            }`}
                          >
                            <span className='w-10 shrink-0 font-medium text-slate-500'>
                              {item.label}
                            </span>
                            <span className='min-w-0 flex-1 whitespace-pre-wrap break-words text-slate-800'>
                              {item.text}
                            </span>
                            {item.flagged && (
                              <Flag className='mt-0.5 size-3.5 shrink-0 text-amber-500' />
                            )}
                          </li>
                        ))
                      )}
                    </ul>
                  </CollapsibleContent>
                </section>
              </Collapsible>
            )
          })}

          <div className='rounded-xl border border-slate-200 bg-white px-4 py-5'>
            <h3 className='text-sm font-semibold text-slate-900'>
              Ready to submit?
            </h3>
            <p className='mt-1 text-sm text-slate-600'>
              Once submitted, your test will be graded.
            </p>
            <Button
              className='mt-4 bg-blue-600 hover:bg-blue-700'
              onClick={submitTest}
              disabled={isSubmitting}
            >
              {isSubmitting && <Loader2 className='size-4 animate-spin' />}
              Submit test →
            </Button>
          </div>
        </div>
      </main>
    </div>
  )
}
