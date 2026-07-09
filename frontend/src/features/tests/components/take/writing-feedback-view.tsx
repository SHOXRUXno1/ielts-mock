import { Fragment, useState } from 'react'
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import type { WritingError, WritingFeedbackResult } from '@/lib/api/feedback'

// ── Error highlight colors ──────────────────────────────────────────────────

const ERROR_COLORS: Record<WritingError['type'], string> = {
  grammar:
    'bg-red-100 text-red-800 underline decoration-red-400 decoration-wavy',
  lexical:
    'bg-amber-100 text-amber-800 underline decoration-amber-400 decoration-wavy',
  spelling:
    'bg-orange-100 text-orange-800 underline decoration-orange-500 decoration-wavy',
  cohesion:
    'bg-blue-100 text-blue-800 underline decoration-blue-400 decoration-wavy',
  punctuation:
    'bg-violet-100 text-violet-800 underline decoration-violet-400 decoration-wavy',
}

const ERROR_BADGE: Record<WritingError['type'], string> = {
  grammar: 'bg-red-100 text-red-700 border-red-200',
  lexical: 'bg-amber-100 text-amber-700 border-amber-200',
  spelling: 'bg-orange-100 text-orange-700 border-orange-200',
  cohesion: 'bg-blue-100 text-blue-700 border-blue-200',
  punctuation: 'bg-violet-100 text-violet-700 border-violet-200',
}

// ── Band descriptor tooltips ─────────────────────────────────────────────────

const WRITING_CRITERIA = [
  [
    'task_achievement',
    'Task Achievement',
    'Band 9: Fully addresses all parts; fully developed position. Band 7: Clear position; relevant main ideas. Band 5: Only partially addresses task.',
  ],
  [
    'coherence_cohesion',
    'Coherence & Cohesion',
    'Band 9: Cohesion attracts no attention; paragraphing skilful. Band 7: Logical organisation; some over-use of cohesive devices. Band 5: Organisation evident but not wholly logical.',
  ],
  [
    'lexical_resource',
    'Lexical Resource',
    'Band 9: Wide range; very natural and sophisticated control. Band 7: Sufficient range; occasional errors. Band 5: Limited range; noticeable spelling errors.',
  ],
  [
    'grammatical_range',
    'Grammatical Range',
    'Band 9: Full flexibility and accuracy. Band 7: Variety of complex structures; few errors. Band 5: Limited structures; complex attempts often have errors.',
  ],
] as const

// ── Highlighted essay ────────────────────────────────────────────────────────

function HighlightedEssay({
  text,
  errors,
}: {
  text: string
  errors: WritingError[]
}) {
  if (!errors.length) {
    return (
      <p className='whitespace-pre-wrap text-sm leading-relaxed'>{text}</p>
    )
  }

  type Seg =
    | { kind: 'text'; content: string }
    | { kind: 'error'; content: string; error: WritingError }

  const segments: Seg[] = []
  let remaining = text
  let pool = [...errors]

  while (remaining.length > 0) {
    let bestIdx = Infinity
    let bestErr: WritingError | null = null

    for (const err of pool) {
      if (!err.quote) continue
      const idx = remaining.indexOf(err.quote)
      if (idx !== -1 && idx < bestIdx) {
        bestIdx = idx
        bestErr = err
      }
    }

    if (!bestErr) {
      segments.push({ kind: 'text', content: remaining })
      break
    }
    if (bestIdx > 0) {
      segments.push({ kind: 'text', content: remaining.slice(0, bestIdx) })
    }
    segments.push({ kind: 'error', content: bestErr.quote, error: bestErr })
    remaining = remaining.slice(bestIdx + bestErr.quote.length)
    pool = pool.filter((e) => e !== bestErr)
  }

  return (
    <p className='whitespace-pre-wrap text-sm leading-relaxed'>
      {segments.map((seg, i) => {
        if (seg.kind === 'text') return <Fragment key={i}>{seg.content}</Fragment>
        return (
          <Tooltip key={i}>
            <TooltipTrigger asChild>
              <mark
                className={cn(
                  'cursor-help rounded px-0.5',
                  ERROR_COLORS[seg.error.type] ?? '',
                )}
              >
                {seg.content}
              </mark>
            </TooltipTrigger>
            <TooltipContent className='max-w-xs'>
              <p className='font-semibold capitalize'>{seg.error.type}</p>
              <p className='text-xs'>
                <span className='text-muted-foreground'>Fix: </span>
                {seg.error.correction}
              </p>
              <p className='mt-0.5 text-xs text-muted-foreground'>
                {seg.error.explanation}
              </p>
            </TooltipContent>
          </Tooltip>
        )
      })}
    </p>
  )
}

// ── Criteria grid ─────────────────────────────────────────────────────────────

function CriteriaGrid({ data }: { data: WritingFeedbackResult }) {
  const [expanded, setExpanded] = useState<string | null>(null)

  return (
    <div className='grid grid-cols-2 gap-3'>
      {WRITING_CRITERIA.map(([key, label, descriptor]) => {
        const criterion = data[key as keyof WritingFeedbackResult] as
          | { band: number; feedback: string }
          | null
          | undefined
        if (!criterion) return null
        const isExp = expanded === key
        return (
          <div key={key} className='rounded-lg border border-slate-200 bg-slate-50 p-3'>
            <div className='mb-1 flex items-center justify-between gap-1'>
              <p className='text-xs font-medium text-slate-500'>{label}</p>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className='size-3 shrink-0 text-slate-400 hover:text-slate-600' />
                </TooltipTrigger>
                <TooltipContent className='max-w-xs text-xs'>
                  {descriptor}
                </TooltipContent>
              </Tooltip>
            </div>
            <p className='text-center text-xl font-bold text-slate-800'>
              {criterion.band.toFixed(1)}
            </p>
            <p className={cn('mt-1 text-xs text-slate-500', !isExp && 'line-clamp-3')}>
              {criterion.feedback}
            </p>
            {criterion.feedback.length > 120 && (
              <button
                type='button'
                onClick={() => setExpanded(isExp ? null : key)}
                className='mt-1 flex items-center gap-0.5 text-xs text-blue-600 hover:underline'
              >
                {isExp ? (
                  <><ChevronUp className='size-3' />Show less</>
                ) : (
                  <><ChevronDown className='size-3' />Show more</>
                )}
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Main exported component ───────────────────────────────────────────────────

export function WritingFeedbackView({
  feedback,
  essayText,
}: {
  feedback: WritingFeedbackResult
  essayText: string
}) {
  return (
    <TooltipProvider>
      <div className='space-y-4'>
        {/* Overall band */}
        <div className='flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4'>
          <div className='text-center'>
            <p className='text-xs text-slate-400'>Band Score</p>
            <p className='text-4xl font-bold text-slate-900'>
              {feedback.overall_band.toFixed(1)}
            </p>
          </div>
          <div className='flex-1'>
            {feedback.strengths.length > 0 && (
              <>
                <p className='mb-1 text-xs font-semibold uppercase text-slate-500'>
                  Strengths
                </p>
                <ul className='list-inside list-disc space-y-0.5 text-xs text-slate-600'>
                  {feedback.strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>

        {/* Improvements */}
        {feedback.improvements.length > 0 && (
          <div>
            <p className='mb-1 text-xs font-semibold uppercase text-slate-500'>
              Areas for Improvement
            </p>
            <ul className='list-inside list-disc space-y-1 text-xs text-slate-600'>
              {feedback.improvements.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Criteria */}
        <CriteriaGrid data={feedback} />

        {/* Highlighted essay */}
        {essayText && (
          <div>
            <p className='mb-2 text-xs font-semibold uppercase text-slate-500'>
              Your Essay (annotated)
            </p>
            <div className='max-h-64 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-4'>
              <HighlightedEssay
                text={essayText}
                errors={[...feedback.errors]}
              />
            </div>
          </div>
        )}

        {/* Error list */}
        {feedback.errors.length > 0 && (
          <div>
            <p className='mb-2 text-xs font-semibold uppercase text-slate-500'>
              Errors & Corrections
            </p>
            <div className='space-y-2'>
              {feedback.errors.map((err, i) => (
                <div
                  key={i}
                  className='flex flex-wrap items-start gap-2 rounded-lg border border-slate-200 bg-white p-3 text-xs'
                >
                  <span
                    className={cn(
                      'rounded border px-1.5 py-0.5 font-medium capitalize',
                      ERROR_BADGE[err.type] ?? '',
                    )}
                  >
                    {err.type}
                  </span>
                  <span className='text-slate-400 line-through'>{err.quote}</span>
                  <span className='text-slate-400'>→</span>
                  <span className='font-medium text-emerald-700'>{err.correction}</span>
                  <span className='w-full text-slate-400'>{err.explanation}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  )
}
