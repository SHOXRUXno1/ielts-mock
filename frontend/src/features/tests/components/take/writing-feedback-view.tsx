import { Fragment, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react'
import type { WritingError, WritingFeedbackResult } from '@/lib/api/feedback'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

// ── Error highlight colors ──────────────────────────────────────────────────

const ERROR_TYPES = [
  'grammar',
  'lexical',
  'spelling',
  'cohesion',
  'punctuation',
] as const

const ERROR_HIGHLIGHT =
  'bg-muted/70 text-foreground underline decoration-muted-foreground decoration-wavy'

const KNOWN_ERROR_TYPES = new Set<string>(ERROR_TYPES)

/** Keep only highlightable, non-junk errors (max 12). */
export function sanitizeWritingErrors(
  errors: WritingError[],
  essayText: string
): WritingError[] {
  const seen = new Set<string>()
  const out: WritingError[] = []

  for (const err of errors) {
    if (!err || typeof err.quote !== 'string') continue
    const quote = err.quote
    if (quote.length < 2) continue
    if (!KNOWN_ERROR_TYPES.has(err.type)) continue
    // When essay text is available, quote must appear verbatim
    if (essayText && !essayText.includes(quote)) continue
    if (seen.has(quote)) continue
    seen.add(quote)
    out.push({
      quote,
      type: err.type,
      correction: typeof err.correction === 'string' ? err.correction : '',
      explanation: typeof err.explanation === 'string' ? err.explanation : '',
    })
    if (out.length >= 12) break
  }

  return out
}

// ── Band descriptor tooltips ─────────────────────────────────────────────────

const TASK1_FIRST_CRITERION = [
  'task_achievement',
  'Task Achievement',
  'Band 9: Fully covers the requirements of the task; clear overview. Band 7: Covers requirements; key features highlighted. Band 5: Generally addresses the task but format may be inappropriate.',
] as const

const TASK2_FIRST_CRITERION = [
  'task_achievement',
  'Task Response',
  'Band 9: Fully addresses all parts; fully developed position. Band 7: Clear position; relevant main ideas. Band 5: Only partially addresses task.',
] as const

const SHARED_CRITERIA = [
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

function getWritingCriteria(taskNumber: 1 | 2) {
  const first = taskNumber === 2 ? TASK2_FIRST_CRITERION : TASK1_FIRST_CRITERION
  return [first, ...SHARED_CRITERIA] as const
}

// ── Highlighted essay (click-to-inspect, no hover tooltips) ───────────────────

function HighlightedEssay({
  text,
  errors,
}: {
  text: string
  errors: WritingError[]
}) {
  const [activeIdx, setActiveIdx] = useState<number | null>(null)

  if (!errors.length) {
    return (
      <p className='text-sm leading-relaxed whitespace-pre-wrap text-foreground'>
        {text}
      </p>
    )
  }

  type Seg =
    | { kind: 'text'; content: string }
    | { kind: 'error'; content: string; error: WritingError; errorIdx: number }

  const segments: Seg[] = []
  let remaining = text
  let pool = errors.map((error, errorIdx) => ({ error, errorIdx }))

  while (remaining.length > 0) {
    let bestIdx = Infinity
    let best: { error: WritingError; errorIdx: number } | null = null

    for (const item of pool) {
      if (!item.error.quote) continue
      const idx = remaining.indexOf(item.error.quote)
      if (idx !== -1 && idx < bestIdx) {
        bestIdx = idx
        best = item
      }
    }

    if (!best) {
      segments.push({ kind: 'text', content: remaining })
      break
    }
    if (bestIdx > 0) {
      segments.push({ kind: 'text', content: remaining.slice(0, bestIdx) })
    }
    segments.push({
      kind: 'error',
      content: best.error.quote,
      error: best.error,
      errorIdx: best.errorIdx,
    })
    remaining = remaining.slice(bestIdx + best.error.quote.length)
    pool = pool.filter((e) => e.errorIdx !== best!.errorIdx)
  }

  const activeError = activeIdx != null ? (errors[activeIdx] ?? null) : null

  return (
    <div className='space-y-3'>
      <p className='overflow-x-hidden text-sm leading-relaxed whitespace-pre-wrap text-foreground'>
        {segments.map((seg, i) => {
          if (seg.kind === 'text') {
            return <Fragment key={i}>{seg.content}</Fragment>
          }
          const isActive = activeIdx === seg.errorIdx
          return (
            <mark
              key={i}
              role='button'
              tabIndex={0}
              onClick={() =>
                setActiveIdx((prev) =>
                  prev === seg.errorIdx ? null : seg.errorIdx
                )
              }
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  setActiveIdx((prev) =>
                    prev === seg.errorIdx ? null : seg.errorIdx
                  )
                }
              }}
              className={cn(
                'cursor-pointer rounded-sm px-0.5 ring-offset-1 outline-none focus-visible:ring-2 focus-visible:ring-ring',
                ERROR_HIGHLIGHT,
                isActive && 'ring-2 ring-ring'
              )}
            >
              {seg.content}
            </mark>
          )
        })}
      </p>

      {activeError && (
        <div className='rounded-md border border-border bg-card p-3 text-xs'>
          <p className='mb-1 font-semibold text-foreground capitalize'>
            {activeError.type}
          </p>
          <p className='text-muted-foreground'>
            <span className='line-through'>{activeError.quote}</span>
            <span className='mx-1.5'>→</span>
            <span className='font-medium text-foreground'>
              {activeError.correction}
            </span>
          </p>
          {activeError.explanation && (
            <p className='mt-1.5 text-muted-foreground'>
              {activeError.explanation}
            </p>
          )}
          <button
            type='button'
            className='mt-2 rounded-sm text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
            onClick={() => setActiveIdx(null)}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  )
}

// ── Criteria grid ─────────────────────────────────────────────────────────────

function CriteriaGrid({
  data,
  taskNumber,
}: {
  data: WritingFeedbackResult
  taskNumber: 1 | 2
}) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const criteria = getWritingCriteria(taskNumber)

  return (
    <div className='grid grid-cols-1 gap-3 sm:grid-cols-2'>
      {criteria.map(([key, label, descriptor]) => {
        const criterion = data[key as keyof WritingFeedbackResult] as
          | { band: number; feedback: string }
          | null
          | undefined
        if (!criterion) return null
        const isExp = expanded === key
        return (
          <div
            key={key}
            className='rounded-md border border-border bg-muted/30 p-3'
          >
            <div className='mb-1 flex items-center justify-between gap-1'>
              <p className='text-xs font-medium text-muted-foreground'>
                {label}
              </p>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className='size-4 shrink-0 text-muted-foreground hover:text-foreground' />
                </TooltipTrigger>
                <TooltipContent className='max-w-xs text-xs'>
                  {descriptor}
                </TooltipContent>
              </Tooltip>
            </div>
            <p className='text-center text-xl font-semibold text-foreground tabular-nums'>
              {criterion.band.toFixed(1)}
            </p>
            <p
              className={cn(
                'mt-1 text-xs text-muted-foreground',
                !isExp && 'line-clamp-3'
              )}
            >
              {criterion.feedback}
            </p>
            {criterion.feedback.length > 120 && (
              <button
                type='button'
                onClick={() => setExpanded(isExp ? null : key)}
                className='mt-1 flex items-center gap-1 rounded-sm text-xs text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
              >
                {isExp ? (
                  <>
                    <ChevronUp className='size-3' />
                    Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className='size-3' />
                    Show more
                  </>
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
  taskNumber = 1,
}: {
  feedback: WritingFeedbackResult
  essayText: string
  taskNumber?: 1 | 2
}) {
  const errors = useMemo(
    () => sanitizeWritingErrors(feedback.errors ?? [], essayText),
    [feedback.errors, essayText]
  )

  return (
    <TooltipProvider>
      <div className='space-y-4 overflow-x-hidden'>
        {/* Overall band */}
        <div className='flex items-center gap-3 rounded-md border border-border bg-card p-4'>
          <div className='text-center'>
            <p className='text-xs text-muted-foreground'>Band Score</p>
            <p className='text-4xl font-semibold text-foreground tabular-nums'>
              {feedback.overall_band.toFixed(1)}
            </p>
          </div>
          <div className='min-w-0 flex-1'>
            {feedback.strengths.length > 0 && (
              <>
                <p className='mb-1 text-xs font-semibold text-muted-foreground uppercase'>
                  Strengths
                </p>
                <ul className='list-inside list-disc space-y-1 text-xs text-muted-foreground'>
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
            <p className='mb-1 text-xs font-semibold text-muted-foreground uppercase'>
              Areas for Improvement
            </p>
            <ul className='list-inside list-disc space-y-1 text-xs text-muted-foreground'>
              {feedback.improvements.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Criteria */}
        <CriteriaGrid data={feedback} taskNumber={taskNumber} />

        {/* Highlighted essay */}
        {essayText && (
          <div>
            <p className='mb-2 text-xs font-semibold text-muted-foreground uppercase'>
              Your Essay (annotated)
            </p>
            <p className='mb-2 text-xs text-muted-foreground'>
              Click a highlighted phrase to see the correction.
            </p>
            <div className='max-h-64 overflow-x-hidden overflow-y-auto rounded-md border border-border bg-muted/30 p-4'>
              <HighlightedEssay text={essayText} errors={errors} />
            </div>
          </div>
        )}

        {/* Error list — vertical cards for narrow column */}
        {errors.length > 0 && (
          <div>
            <p className='mb-2 text-xs font-semibold text-muted-foreground uppercase'>
              Errors & Corrections
            </p>
            <div className='space-y-2'>
              {errors.map((err, i) => (
                <div
                  key={i}
                  className='space-y-1.5 rounded-md border border-border bg-card p-3 text-xs'
                >
                  <span className='inline-block rounded-md border border-border bg-muted px-2 py-0.5 font-medium text-muted-foreground capitalize'>
                    {err.type}
                  </span>
                  <p className='break-words text-foreground'>
                    <span className='text-muted-foreground line-through'>
                      {err.quote}
                    </span>
                    <span className='mx-1.5 text-muted-foreground'>→</span>
                    <span className='font-medium'>{err.correction}</span>
                  </p>
                  {err.explanation && (
                    <p className='text-muted-foreground'>{err.explanation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  )
}
