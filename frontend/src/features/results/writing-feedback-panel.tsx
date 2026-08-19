import { Fragment, useState } from 'react'
import {
  CheckCircle,
  ChevronDown,
  FileText,
  HelpCircle,
  XCircle,
} from 'lucide-react'
import type { EvaluationJobRead } from '@/lib/api/attempts'
import { Badge } from '@/components/ui/badge'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { BandScale, Panel, PanelBody, PanelHeader, PanelTitle } from '@/components/report'
import { formatBand } from './lib/band'

export function WritingFeedbackPanel({
  jobs,
  partNumber,
}: {
  jobs: EvaluationJobRead[]
  /** When set (single-part practice), prefer that task tab. */
  partNumber?: number | null
}) {
  const job = jobs.find((j) => j.status === 'done') ?? jobs[0]
  if (!job) {
    return (
      <Panel padding='md'>
        <p className='text-sm text-muted-foreground'>No writing evaluation yet.</p>
      </Panel>
    )
  }

  if (job.status !== 'done') {
    return null
  }

  const result = job.result as Record<string, unknown> | null
  const tasks =
    (result?.tasks as Record<string, Record<string, unknown>> | undefined) ?? {}
  const task1 = tasks.task_1
  const task2 = tasks.task_2
  const available = [
    task1 ? 'task_1' : null,
    task2 ? 'task_2' : null,
  ].filter(Boolean) as string[]
  const defaultTab =
    partNumber === 2 && task2
      ? 'task_2'
      : partNumber === 1 && task1
        ? 'task_1'
        : (available[0] ?? 'task_1')

  if (available.length === 0) {
    return (
      <Panel padding='md'>
        <p className='text-sm text-muted-foreground'>No writing evaluation yet.</p>
      </Panel>
    )
  }

  if (available.length === 1) {
    const key = available[0]
    const data = key === 'task_1' ? task1! : task2!
    return <WritingResult tasks={{ [key]: data }} />
  }

  return (
    <div className='space-y-4'>
      <Tabs defaultValue={defaultTab}>
        <TabsList>
          <TabsTrigger value='task_1'>Task 1</TabsTrigger>
          <TabsTrigger value='task_2'>Task 2</TabsTrigger>
        </TabsList>
        <TabsContent value='task_1' className='mt-4'>
          {task1 ? (
            <WritingResult tasks={{ task_1: task1 }} />
          ) : (
            <Panel padding='md'>
              <p className='text-sm text-muted-foreground'>Task 1 not attempted</p>
            </Panel>
          )}
        </TabsContent>
        <TabsContent value='task_2' className='mt-4'>
          {task2 ? (
            <WritingResult tasks={{ task_2: task2 }} />
          ) : (
            <Panel padding='md'>
              <p className='text-sm text-muted-foreground'>Task 2 not attempted</p>
            </Panel>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export function writingBandFromJobs(jobs: EvaluationJobRead[]): number | null {
  const job = jobs.find((j) => j.status === 'done') ?? jobs[0]
  if (!job) return null
  if (job.band_score != null) return job.band_score
  const result = job.result as Record<string, unknown> | null
  const tasks =
    (result?.tasks as Record<string, Record<string, unknown>> | undefined) ?? {}
  const t1 = tasks.task_1?.overall_band
  const t2 = tasks.task_2?.overall_band
  if (typeof t1 === 'number') return t1
  if (typeof t2 === 'number') return t2
  return null
}

type WritingError = {
  quote: string
  type: 'grammar' | 'lexical' | 'spelling' | 'cohesion' | 'punctuation'
  correction: string
  explanation: string
}

type KeyPoint = { point: string; covered: boolean }

type SentenceCategory =
  | 'hit_key_point'
  | 'linking_issue'
  | 'grammatical_error'
  | 'lexical_issue'
  | 'off_topic'

type SentenceAnalysisItem = {
  sentence: string
  category: SentenceCategory
  comment: string
  reference?: string
}

const SENTENCE_BORDER: Record<SentenceCategory, string> = {
  hit_key_point: 'border-l-success-foreground',
  linking_issue: 'border-l-warning-foreground',
  lexical_issue: 'border-l-warning-foreground',
  grammatical_error: 'border-l-destructive',
  off_topic: 'border-l-destructive',
}

const SENTENCE_CATEGORY_LABEL: Record<SentenceCategory, string> = {
  hit_key_point: 'Hit key point',
  linking_issue: 'Linking issue',
  lexical_issue: 'Lexical issue',
  grammatical_error: 'Grammatical error',
  off_topic: 'Off topic',
}

function parseKeyPoints(raw: unknown): KeyPoint[] {
  if (!Array.isArray(raw)) return []
  return raw
    .filter(
      (item): item is KeyPoint =>
        !!item &&
        typeof item === 'object' &&
        typeof (item as KeyPoint).point === 'string' &&
        typeof (item as KeyPoint).covered === 'boolean',
    )
    .map((item) => ({ point: item.point, covered: item.covered }))
}

function parseSentenceAnalysis(raw: unknown): SentenceAnalysisItem[] {
  if (!Array.isArray(raw)) return []
  const allowed = new Set<SentenceCategory>([
    'hit_key_point',
    'linking_issue',
    'grammatical_error',
    'lexical_issue',
    'off_topic',
  ])
  const out: SentenceAnalysisItem[] = []
  for (const item of raw) {
    if (!item || typeof item !== 'object') continue
    const row = item as Record<string, unknown>
    const sentence = row.sentence
    const category = row.category
    const comment = row.comment
    if (typeof sentence !== 'string' || !sentence.trim()) continue
    if (typeof category !== 'string' || !allowed.has(category as SentenceCategory))
      continue
    const entry: SentenceAnalysisItem = {
      sentence: sentence.trim(),
      category: category as SentenceCategory,
      comment: typeof comment === 'string' ? comment : '',
    }
    if (typeof row.reference === 'string' && row.reference.trim()) {
      entry.reference = row.reference.trim()
    }
    out.push(entry)
  }
  return out
}

function KeyPointsAnalysis({ points }: { points: KeyPoint[] }) {
  return (
    <div>
      <p className='mb-2 text-sm font-medium'>Key Points Analysis</p>
      <ul className='space-y-1.5'>
        {points.map((kp, i) => (
          <li
            key={i}
            className='flex items-start gap-2 rounded-lg border px-3 py-2 text-sm'
          >
            {kp.covered ? (
              <CheckCircle className='mt-0.5 size-4 shrink-0 text-success-foreground' />
            ) : (
              <XCircle className='mt-0.5 size-4 shrink-0 text-destructive' />
            )}
            <span className={kp.covered ? 'text-foreground' : 'text-muted-foreground'}>
              {kp.point}
            </span>
            <Badge
              variant='outline'
              className={cn(
                'ml-auto shrink-0 text-[10px]',
                kp.covered
                  ? 'border-success-foreground/30 text-success-foreground'
                  : 'border-destructive/30 text-destructive',
              )}
            >
              {kp.covered ? 'covered' : 'missed'}
            </Badge>
          </li>
        ))}
      </ul>
    </div>
  )
}

function SentenceAnalysisList({ items }: { items: SentenceAnalysisItem[] }) {
  return (
    <div>
      <p className='mb-2 text-sm font-medium'>Sentence-by-Sentence Analysis</p>
      <div className='space-y-2'>
        {items.map((item, i) => (
          <Tooltip key={i}>
            <TooltipTrigger asChild>
              <div
                className={cn(
                  'cursor-default rounded-lg border border-l-4 bg-muted/20 px-3 py-2',
                  SENTENCE_BORDER[item.category],
                )}
              >
                <div className='mb-1 flex items-center gap-2'>
                  <Badge variant='outline' className='text-[10px] capitalize'>
                    {SENTENCE_CATEGORY_LABEL[item.category]}
                  </Badge>
                  {item.reference && (
                    <span className='truncate text-[10px] text-muted-foreground'>
                      → {item.reference}
                    </span>
                  )}
                </div>
                <p className='text-sm leading-relaxed text-foreground'>
                  {item.sentence}
                </p>
                {item.comment && (
                  <p className='mt-1 line-clamp-2 text-xs text-muted-foreground'>
                    {item.comment}
                  </p>
                )}
              </div>
            </TooltipTrigger>
            {item.comment && (
              <TooltipContent className='max-w-sm text-xs'>
                {item.comment}
              </TooltipContent>
            )}
          </Tooltip>
        ))}
      </div>
    </div>
  )
}

function OptimizedCompositionCard({ text }: { text: string }) {
  return (
    <Collapsible className='rounded-lg border border-success-foreground/20 bg-success/40'>
      <CollapsibleTrigger className='flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-success-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'>
        Optimized Composition
        <ChevronDown className='size-3.5 transition-transform duration-200 [[data-state=open]_&]:rotate-180' />
      </CollapsibleTrigger>
      <CollapsibleContent className='border-t border-success-foreground/20 px-4 py-3'>
        <p className='font-serif whitespace-pre-wrap text-sm leading-relaxed text-foreground'>
          {text}
        </p>
      </CollapsibleContent>
    </Collapsible>
  )
}

const ERROR_COLORS: Record<WritingError['type'], string> = {
  grammar:
    'bg-destructive/15 text-destructive underline decoration-destructive/50 decoration-wavy',
  lexical:
    'bg-warning/40 text-warning-foreground underline decoration-warning-foreground/40 decoration-wavy',
  spelling:
    'bg-warning/50 text-warning-foreground underline decoration-warning-foreground/60 decoration-wavy',
  cohesion:
    'bg-skill-reading/15 text-skill-reading underline decoration-skill-reading/50 decoration-wavy',
  punctuation:
    'bg-skill-listening/15 text-skill-listening underline decoration-skill-listening/50 decoration-wavy',
}

const ERROR_BADGE_COLORS: Record<WritingError['type'], string> = {
  grammar: 'border-destructive/30 bg-destructive/10 text-destructive',
  lexical: 'border-warning-foreground/30 bg-warning/40 text-warning-foreground',
  spelling: 'border-warning-foreground/30 bg-warning/50 text-warning-foreground',
  cohesion: 'border-skill-reading/30 bg-skill-reading/10 text-skill-reading',
  punctuation: 'border-skill-listening/30 bg-skill-listening/10 text-skill-listening',
}

const ERROR_LEGEND: { type: WritingError['type']; label: string }[] = [
  { type: 'grammar', label: 'Grammar' },
  { type: 'lexical', label: 'Lexical' },
  { type: 'spelling', label: 'Spelling' },
  { type: 'cohesion', label: 'Cohesion' },
  { type: 'punctuation', label: 'Punctuation' },
]

function HighlightedEssay({
  text,
  errors,
  highlightType = null,
}: {
  text: string
  errors: WritingError[]
  highlightType?: WritingError['type'] | null
}) {
  if (!errors.length) {
    return (
      <p className='whitespace-pre-wrap text-sm leading-relaxed'>{text}</p>
    )
  }

  type Segment =
    | { kind: 'text'; content: string }
    | { kind: 'error'; content: string; error: WritingError }

  const segments: Segment[] = []
  let remaining = text
  let leftover = errors

  while (remaining.length > 0) {
    let bestIdx = Infinity
    let bestError: WritingError | null = null

    for (const err of leftover) {
      if (!err.quote) continue
      const idx = remaining.indexOf(err.quote)
      if (idx !== -1 && idx < bestIdx) {
        bestIdx = idx
        bestError = err
      }
    }

    if (bestError === null) {
      segments.push({ kind: 'text', content: remaining })
      break
    }

    if (bestIdx > 0) {
      segments.push({ kind: 'text', content: remaining.slice(0, bestIdx) })
    }
    segments.push({
      kind: 'error',
      content: bestError.quote,
      error: bestError,
    })
    remaining = remaining.slice(bestIdx + bestError.quote.length)
    leftover = leftover.filter((e) => e !== bestError)
  }

  return (
    <p className='whitespace-pre-wrap text-sm leading-relaxed'>
      {segments.map((seg, i) => {
        if (seg.kind === 'text') {
          return <Fragment key={i}>{seg.content}</Fragment>
        }
        const colorClass = ERROR_COLORS[seg.error.type] ?? ''
        const dimmed = highlightType != null && highlightType !== seg.error.type
        return (
          <Tooltip key={i}>
            <TooltipTrigger asChild>
              <mark
                className={cn(
                  'cursor-help rounded px-0.5',
                  colorClass,
                  dimmed && 'opacity-20 no-underline',
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

function WritingTaskCard({
  taskKey,
  taskData,
}: {
  taskKey: string
  taskData: Record<string, unknown>
}) {
  const [highlightType, setHighlightType] = useState<WritingError['type'] | null>(
    null,
  )
  const isTask1 = taskKey.includes('1')
  const label = isTask1 ? 'Task 1 — Report' : 'Task 2 — Essay'
  const overallBand = taskData.overall_band as number | undefined
  const wordCount = taskData.word_count as number | undefined
  const essayText = (taskData.text as string | undefined) ?? ''
  const strengths = taskData.strengths as string[] | undefined
  const improvements = taskData.improvements as string[] | undefined
  const rawErrors = (taskData.errors ?? []) as WritingError[]
  const keyPoints = parseKeyPoints(taskData.key_points)
  const sentenceAnalysis = parseSentenceAnalysis(taskData.sentence_analysis)
  const overallReview =
    typeof taskData.overall_review === 'string'
      ? taskData.overall_review.trim()
      : ''
  const optimized =
    typeof taskData.optimized_composition === 'string'
      ? taskData.optimized_composition.trim()
      : ''

  return (
    <Panel padding='md'>
      <PanelHeader className='items-center'>
        <div className='flex flex-wrap items-center gap-2'>
          <PanelTitle>{label}</PanelTitle>
          {wordCount != null && (
            <Badge variant='outline' className='text-xs'>
              <FileText className='mr-1 size-3' />
              {wordCount} words
            </Badge>
          )}
        </div>
        {overallBand != null && (
          <div className='text-right'>
            <p className='text-[11px] tracking-wider text-muted-foreground uppercase'>
              Task Band
            </p>
            <p className='font-manrope text-xl font-semibold tracking-tight tabular-nums'>
              {formatBand(overallBand)}
            </p>
          </div>
        )}
      </PanelHeader>
      <PanelBody>
        <div className='grid gap-6 lg:grid-cols-[minmax(0,1fr)_16rem]'>
          <div className='space-y-4'>
            {keyPoints.length > 0 && <KeyPointsAnalysis points={keyPoints} />}

            {strengths && strengths.length > 0 && (
              <FeedbackList title='Strengths' items={strengths} />
            )}
            {improvements && improvements.length > 0 && (
              <FeedbackList title='Areas for Improvement' items={improvements} />
            )}

            {sentenceAnalysis.length > 0 && (
              <SentenceAnalysisList items={sentenceAnalysis} />
            )}

            {essayText && (
              <div>
                <div className='mb-2 flex flex-wrap items-center justify-between gap-2'>
                  <p className='text-sm font-medium'>Student's Essay</p>
                  {rawErrors.length > 0 && (
                    <div className='flex flex-wrap gap-1.5'>
                      {ERROR_LEGEND.filter((item) =>
                        rawErrors.some((e) => e.type === item.type),
                      ).map((item) => {
                        const pressed = highlightType === item.type
                        return (
                          <button
                            key={item.type}
                            type='button'
                            aria-pressed={pressed}
                            onClick={() =>
                              setHighlightType((prev) =>
                                prev === item.type ? null : item.type,
                              )
                            }
                            className={cn(
                              'rounded border px-1.5 py-0.5 text-[10px] font-medium transition-opacity',
                              'focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                              ERROR_BADGE_COLORS[item.type],
                              highlightType != null && !pressed && 'opacity-40',
                            )}
                          >
                            {item.label}
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
                <ScrollArea className='h-80 rounded-lg border bg-surface-sunken'>
                  <div className='p-4'>
                    <HighlightedEssay
                      text={essayText}
                      errors={[...rawErrors]}
                      highlightType={highlightType}
                    />
                  </div>
                </ScrollArea>
              </div>
            )}

            {rawErrors.length > 0 && (
              <div>
                <p className='mb-2 text-sm font-medium'>Errors & Corrections</p>
                <div className='space-y-2'>
                  {rawErrors
                    .filter(
                      (err) => highlightType == null || err.type === highlightType,
                    )
                    .map((err, i) => (
                      <div
                        key={i}
                        className='flex flex-wrap items-start gap-2 rounded-lg border p-3 text-sm'
                      >
                        <span
                          className={cn(
                            'shrink-0 rounded border px-1.5 py-0.5 text-xs font-medium capitalize',
                            ERROR_BADGE_COLORS[err.type] ?? '',
                          )}
                        >
                          {err.type}
                        </span>
                        <span className='text-muted-foreground line-through'>
                          {err.quote}
                        </span>
                        <span className='text-muted-foreground'>→</span>
                        <span className='font-medium text-success-foreground'>
                          {err.correction}
                        </span>
                        <span className='w-full text-xs text-muted-foreground'>
                          {err.explanation}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {overallReview && (
              <div>
                <p className='mb-1 text-sm font-medium'>Overall Review</p>
                <p className='whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground'>
                  {overallReview}
                </p>
              </div>
            )}

            {optimized && <OptimizedCompositionCard text={optimized} />}
          </div>

          <aside className='lg:sticky lg:top-32 lg:self-start'>
            <CriteriaGrid
              data={taskData}
              sectionType='writing'
              isTask1={isTask1}
              sentenceAnalysis={sentenceAnalysis}
              errors={rawErrors}
              variant='rail'
            />
          </aside>
        </div>
      </PanelBody>
    </Panel>
  )
}

export function WritingResult({
  tasks,
}: {
  tasks: Record<string, Record<string, unknown>>
}) {
  const taskEntries = Object.entries(tasks).sort(([a], [b]) =>
    a.localeCompare(b),
  )

  return (
    <div className='space-y-6'>
      {taskEntries.map(([taskKey, taskData]) => (
        <WritingTaskCard key={taskKey} taskKey={taskKey} taskData={taskData} />
      ))}
    </div>
  )
}

const WRITING_TASK1_FIRST_CRITERION = [
  'task_achievement',
  'Task Achievement',
  'Band 9: Fully covers requirements; key features accurately described with clear overview. Band 7: Clearly presents and highlights key features. Band 5: Key features may be inadequately covered or inaccurate.',
] as const

const WRITING_TASK2_FIRST_CRITERION = [
  'task_response',
  'Task Response',
  'Band 9: Fully addresses all parts; fully developed position. Band 7: Clear position; relevant main ideas, some may lack development. Band 5: Partially addresses task; position not always clear.',
] as const

const WRITING_SHARED_CRITERIA = [
  [
    'coherence_cohesion',
    'Coherence & Cohesion',
    'Band 9: Cohesion attracts no attention; paragraphing is skilful. Band 7: Logical organisation; clear progression; some over-use of cohesive devices. Band 5: Organisation evident but not wholly logical.',
  ],
  [
    'lexical_resource',
    'Lexical Resource',
    'Band 9: Wide range; very natural and sophisticated control. Band 7: Sufficient range; awareness of style; occasional errors. Band 5: Limited range; noticeable spelling/word-form errors.',
  ],
  [
    'grammatical_range',
    'Grammatical Range',
    'Band 9: Full flexibility and accuracy; rare minor errors. Band 7: Variety of complex structures; frequent error-free sentences. Band 5: Limited structures; complex sentences attempted but errors frequent.',
  ],
] as const

const SPEAKING_CRITERIA = [
  ['fluency_coherence', 'Fluency & Coherence', ''],
  ['lexical_resource', 'Lexical Resource', ''],
  ['grammatical_range', 'Grammar', ''],
  ['pronunciation', 'Pronunciation', ''],
] as const

export function CriteriaGrid({
  data,
  sectionType,
  isTask1 = true,
  sentenceAnalysis = [],
  errors = [],
  variant = 'grid',
}: {
  data: Record<string, unknown>
  sectionType: string
  isTask1?: boolean
  sentenceAnalysis?: SentenceAnalysisItem[]
  errors?: WritingError[]
  variant?: 'grid' | 'rail'
}) {
  const writingFirstCriterion = isTask1
    ? WRITING_TASK1_FIRST_CRITERION
    : 'task_response' in data
      ? WRITING_TASK2_FIRST_CRITERION
      : WRITING_TASK1_FIRST_CRITERION

  const criteriaKeys =
    sectionType === 'writing'
      ? [writingFirstCriterion, ...WRITING_SHARED_CRITERIA]
      : SPEAKING_CRITERIA

  const hasLinking =
    sentenceAnalysis.some((s) => s.category === 'linking_issue') ||
    errors.some((e) => e.type === 'cohesion')
  const hasMisspelling = errors.some((e) => e.type === 'spelling')
  const hasGrammar =
    sentenceAnalysis.some((s) => s.category === 'grammatical_error') ||
    errors.some((e) => e.type === 'grammar')

  const criterionBadges: Record<string, string | undefined> = {
    coherence_cohesion: hasLinking ? 'Linking issues' : undefined,
    lexical_resource: hasMisspelling ? 'Misspelling' : undefined,
    grammatical_range: hasGrammar ? 'Grammatical errors' : undefined,
  }

  return (
    <div
      className={cn(
        variant === 'rail'
          ? 'space-y-2'
          : 'grid grid-cols-2 gap-3 sm:grid-cols-4',
      )}
    >
      {criteriaKeys.map(([key, label, descriptor]) => {
        const criterion = data[key] as
          | { band: number; feedback: string }
          | undefined
        if (!criterion) return null
        const badge = criterionBadges[key]
        const longFeedback = criterion.feedback && criterion.feedback.length > 120
        return (
          <Collapsible
            key={key}
            className={cn(
              'rounded-xl ring-1 ring-border',
              variant === 'rail' ? 'bg-card p-3' : 'border p-3',
            )}
          >
            <div className='mb-1 flex items-center justify-between gap-1'>
              <p className='text-xs text-muted-foreground'>{label}</p>
              {descriptor && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <HelpCircle className='size-3 shrink-0 text-muted-foreground/60 hover:text-muted-foreground' />
                  </TooltipTrigger>
                  <TooltipContent className='max-w-xs text-xs'>
                    {descriptor}
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
            {badge && (
              <Badge
                variant='outline'
                className='mb-1 border-warning-foreground/30 text-[10px] text-warning-foreground'
              >
                {badge}
              </Badge>
            )}
            <p
              className={cn(
                'font-semibold tabular-nums',
                variant === 'rail' ? 'text-lg' : 'text-center text-lg',
              )}
            >
              {formatBand(criterion.band)}
            </p>
            <BandScale
              band={criterion.band}
              label={label}
              className='mt-2'
            />
            {variant !== 'rail' && (
              <p className='mt-2 line-clamp-3 text-xs text-muted-foreground'>
                {criterion.feedback}
              </p>
            )}
            {(longFeedback || variant === 'rail') && criterion.feedback && (
              <>
                <CollapsibleTrigger className='mt-1 flex items-center gap-0.5 text-xs text-primary hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'>
                  <ChevronDown className='size-3 transition-transform duration-200 [[data-state=open]_&]:rotate-180' />
                  {variant === 'rail' ? 'Feedback' : 'Show more'}
                </CollapsibleTrigger>
                <CollapsibleContent className='mt-1 text-xs leading-relaxed text-muted-foreground'>
                  {criterion.feedback}
                </CollapsibleContent>
              </>
            )}
          </Collapsible>
        )
      })}
    </div>
  )
}

export function FeedbackList({
  title,
  items,
}: {
  title: string
  items: string[]
}) {
  return (
    <div>
      <p className='mb-1 text-sm font-medium'>{title}</p>
      <ul className='list-inside list-disc space-y-1 text-sm text-muted-foreground'>
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
