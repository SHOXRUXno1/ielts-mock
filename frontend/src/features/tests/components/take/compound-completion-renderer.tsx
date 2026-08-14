import { ArrowDown } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { mediaUrl } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import type { Question } from '../../data/schema'
import type {
  CellSegment,
  CompoundStructure,
  FlowStructure,
  FormStructure,
  NoteStructure,
  SummaryStructure,
  TableStructure,
} from '../../data/compound'

type Answers = Record<string, Record<string, unknown>>
type OnAnswer = (questionId: string, response: Record<string, unknown>) => void

function buildGapMap(questions: Question[]): Map<string, Question> {
  const map = new Map<string, Question>()
  for (const q of questions) {
    const gapId = q.content.gap_id
    const gapKey = q.content.gap_key
    if (typeof gapId === 'string' && gapId) map.set(gapId, q)
    if (typeof gapKey === 'string' && gapKey) map.set(gapKey, q)
  }
  return map
}

function countWords(value: string): number {
  const trimmed = value.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).length
}

function longestCorrectWordCount(
  answerKey: Record<string, unknown> | null | undefined,
): number {
  if (!answerKey) return 0
  const correct = answerKey.correct ?? answerKey.answer
  const variants = Array.isArray(correct)
    ? correct
    : typeof correct === 'string'
      ? [correct]
      : []
  let longest = 0
  for (const v of variants) {
    const n = countWords(String(v))
    if (n > longest) longest = n
  }
  return longest
}

/** Declared limit, but never stricter than the longest accepted variant. */
function effectiveMaxWords(
  maxWords: number | undefined,
  answerKey: Record<string, unknown> | null | undefined,
): number | undefined {
  if (maxWords == null) return undefined
  return Math.max(maxWords, longestCorrectWordCount(answerKey))
}

function formatGapAnswer(answerKey: Record<string, unknown> | null): string {
  if (!answerKey) return ''
  if (typeof answerKey.correct === 'string') return answerKey.correct
  if (Array.isArray(answerKey.correct)) return answerKey.correct.map(String).join(' / ')
  if (typeof answerKey.answer === 'string') return answerKey.answer
  if (Array.isArray(answerKey.answer)) return answerKey.answer.map(String).join(' / ')
  return ''
}

/** Extract bare letter/prefix from "A. emotions" / "ii. Heading". */
function optionPrefix(opt: string): string {
  const dot = opt.indexOf('.')
  return dot > 0 ? opt.slice(0, dot).trim() : opt.trim()
}

export function GapInput({
  question,
  value,
  onChange,
  maxWords,
  readOnly = false,
  previewMode = false,
  /** When set (word-bank summary), render a letter dropdown instead of text. */
  choiceOptions,
}: {
  question: Question
  value: string
  onChange: (questionId: string, answer: string) => void
  maxWords?: number
  readOnly?: boolean
  previewMode?: boolean
  choiceOptions?: string[]
}) {
  const limit = effectiveMaxWords(maxWords, question.answer_key)
  const overLimit = limit != null && countWords(value) > limit
  const hint = previewMode ? formatGapAnswer(question.answer_key) : ''
  const inputSize = Math.min(40, Math.max(12, value.length + 2))
  const letters =
    choiceOptions && choiceOptions.length > 0
      ? choiceOptions.map(optionPrefix)
      : null

  const displayN = question.computed_number ?? question.order

  return (
    <span
      id={`q-${displayN}`}
      className='mx-0.5 inline-flex scroll-mt-20 items-center gap-1 align-middle'
    >
      <span
        data-q-chip
        data-q-n={displayN}
        className='inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-medium text-muted-foreground'
      >
        {displayN}
      </span>
      <span className='inline-flex flex-col items-center'>
        {letters ? (
          <Select
            value={value || undefined}
            onValueChange={(v) => {
              if (readOnly) return
              onChange(question.id, v)
            }}
            disabled={readOnly}
          >
            <SelectTrigger
              aria-label={`Question ${question.order}`}
              className={cn(
                'h-7 min-w-14 justify-center gap-1 border bg-card px-1.5 text-center text-[13px] font-medium shadow-sm [&>svg]:size-3',
                readOnly && 'cursor-default bg-muted',
                'border-border',
              )}
            >
              <SelectValue placeholder={String(displayN)} />
            </SelectTrigger>
            <SelectContent align='center' className='min-w-14'>
              {letters.map((letter) => (
                <SelectItem key={letter} value={letter} className='justify-center text-[13px]'>
                  {letter}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <input
            type='text'
            value={value}
            size={inputSize}
            readOnly={readOnly}
            disabled={readOnly}
            onChange={(e) => {
              if (readOnly) return
              onChange(question.id, e.target.value)
            }}
            aria-label={`Question ${question.order}`}
            className={cn(
              'inline-block h-7 min-w-32 max-w-[18rem] rounded-md border bg-card px-2 text-center text-[13px] shadow-sm transition-colors focus:outline-none focus:ring-1',
              readOnly && 'cursor-default bg-muted',
              overLimit
                ? 'border-destructive focus:border-destructive focus:ring-destructive/30'
                : 'border-border focus:border-primary focus:ring-primary/30',
            )}
          />
        )}
        {previewMode && hint && (
          <span className='mt-0.5 text-[9px] font-medium leading-none text-success-foreground'>
            {hint}
          </span>
        )}
      </span>
    </span>
  )
}

function renderSegments(
  segments: CellSegment[],
  gapToQ: Map<string, Question>,
  answers: Answers,
  onAnswer: OnAnswer,
  maxWords: number | undefined,
  readOnly: boolean | undefined,
  previewMode?: boolean,
  choiceOptions?: string[],
) {
  return segments.map((seg, i) => {
    if (seg.type === 'text') {
      const lines = seg.value.split('\n')
      return (
        <span key={i}>
          {lines.map((line, j) => (
            <span key={j}>
              {j > 0 && <br />}
              {line}
            </span>
          ))}
        </span>
      )
    }
    const q = gapToQ.get(seg.gap_id)
    if (!q) return null
    return (
      <GapInput
        key={i}
        question={q}
        value={(answers[q.id]?.answer as string) ?? ''}
        onChange={(id, answer) => onAnswer(id, { answer })}
        maxWords={maxWords}
        readOnly={readOnly}
        previewMode={previewMode}
        choiceOptions={choiceOptions}
      />
    )
  })
}

function renderTableCell(
  cell: TableStructure['rows'][number][number],
  gapToQ: Map<string, Question>,
  answers: Answers,
  onAnswer: OnAnswer,
  maxWords: number | undefined,
  readOnly: boolean | undefined,
  highlighted?: boolean,
  previewMode?: boolean,
) {
  const body =
    cell.variant === 'bullets' ? (
      <ul className='list-disc space-y-2 pl-4'>
        {cell.bullets.map((bullet, i) => (
          <li key={i} className='leading-loose'>
            {renderSegments(
              bullet.segments,
              gapToQ,
              answers,
              onAnswer,
              maxWords,
              readOnly,
              previewMode,
            )}
          </li>
        ))}
      </ul>
    ) : (
      <span className='leading-loose'>
        {renderSegments(
          cell.segments,
          gapToQ,
          answers,
          onAnswer,
          maxWords,
          readOnly,
          previewMode,
        )}
      </span>
    )

  return (
    <div
      className={cn(
        'rounded-sm transition-colors duration-200',
        highlighted && 'bg-sky-100/80 ring-2 ring-sky-300 ring-inset',
      )}
    >
      {body}
    </div>
  )
}

function TableCompletion({
  structure,
  questions,
  answers,
  onAnswer,
  readOnly,
  highlightCell,
  previewMode,
}: {
  structure: TableStructure
  questions: Question[]
  answers: Answers
  onAnswer: OnAnswer
  readOnly?: boolean
  highlightCell?: { row: number; col: number } | null
  previewMode?: boolean
}) {
  const gapToQ = buildGapMap(questions)
  const maxWords = structure.max_words_per_gap

  return (
    <div className='overflow-x-auto rounded-lg border border-border bg-card p-4'>
      {structure.title && (
        <p className='mb-3 text-center text-[15px] font-bold text-foreground'>
          {structure.title}
        </p>
      )}
      <table className='w-full border-collapse border border-border text-sm'>
        {structure.headers.length > 0 && (
          <thead>
            <tr>
              {structure.headers.map((h, i) => (
                <th
                  key={i}
                  className='border border-border bg-muted px-3 py-2.5 text-center text-[13px] font-bold text-foreground'
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {structure.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  className='border border-border px-3 py-2.5 align-top text-[13px] text-foreground'
                >
                  {renderTableCell(
                    cell,
                    gapToQ,
                    answers,
                    onAnswer,
                    maxWords,
                    readOnly,
                    highlightCell?.row === ri && highlightCell?.col === ci,
                    previewMode,
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function NoteCompletion({
  structure,
  questions,
  answers,
  onAnswer,
  readOnly,
  previewMode,
}: {
  structure: NoteStructure
  questions: Question[]
  answers: Answers
  onAnswer: OnAnswer
  readOnly?: boolean
  previewMode?: boolean
}) {
  const gapToQ = buildGapMap(questions)
  const maxWords = structure.max_words_per_gap

  return (
    <div className='mx-auto rounded-lg border border-border bg-card px-8 py-7'>
      {structure.title && (
        <p className='mb-6 text-center text-[17px] font-bold text-foreground'>
          {structure.title}
        </p>
      )}
      {structure.sections.map((section, si) => (
        <div key={si}>
          {section.heading && (
            <p
              className={cn(
                'mb-2.5 text-[14px] font-bold text-foreground',
                si > 0 && 'mt-6',
              )}
            >
              {section.heading}
            </p>
          )}
          {structure.bullets === false ? (
            <div className='space-y-2'>
              {section.items.map((item, ii) => (
                <div
                  key={ii}
                  className='text-[14px] leading-7 text-foreground'
                >
                  {renderSegments(
                    stripIndent(item.segments),
                    gapToQ,
                    answers,
                    onAnswer,
                    maxWords,
                    readOnly,
                    previewMode,
                  )}
                </div>
              ))}
            </div>
          ) : (
            <ul className='space-y-1.5'>
              {section.items.map((item, ii) => {
                const nested = isNested(item.segments)
                return (
                  <li
                    key={ii}
                    className={cn(
                      'list-disc text-[14px] leading-7 text-foreground marker:text-foreground',
                      nested ? 'ml-11 list-[circle]' : 'ml-5',
                    )}
                  >
                    {renderSegments(
                      stripIndent(item.segments),
                      gapToQ,
                      answers,
                      onAnswer,
                      maxWords,
                      readOnly,
                      previewMode,
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      ))}
    </div>
  )
}

/** Leading spaces in the first text segment mark a nested sub-bullet. */
function isNested(segments: CellSegment[]): boolean {
  const first = segments[0]
  return first?.type === 'text' && /^\s{2,}/.test(first.value)
}

function stripIndent(segments: CellSegment[]): CellSegment[] {
  const first = segments[0]
  if (first?.type !== 'text' || !/^\s+/.test(first.value)) return segments
  return [{ ...first, value: first.value.replace(/^\s+/, '') }, ...segments.slice(1)]
}

function FormCompletion({
  structure,
  questions,
  answers,
  onAnswer,
  readOnly,
  previewMode,
}: {
  structure: FormStructure
  questions: Question[]
  answers: Answers
  onAnswer: OnAnswer
  readOnly?: boolean
  previewMode?: boolean
}) {
  const gapToQ = buildGapMap(questions)
  const maxWords = structure.max_words_per_gap

  return (
    <div className='mx-auto max-w-xl rounded-lg border border-border bg-card p-6'>
      <p className='mb-6 text-center text-sm font-medium uppercase tracking-wide text-foreground'>
        {structure.form_title}
      </p>
      <div className='space-y-4'>
        {structure.fields.map((field, fi) => (
          <div key={fi} className='flex flex-wrap items-baseline gap-2 text-[14px]'>
            <span className='min-w-[7rem] font-semibold text-foreground'>
              {field.label}:
            </span>
            {field.type === 'static' ? (
              <span className='text-muted-foreground'>{field.value}</span>
            ) : (
              <span className='inline-flex flex-wrap items-baseline gap-1'>
                {renderSegments(
                  field.segments,
                  gapToQ,
                  answers,
                  onAnswer,
                  maxWords,
                  readOnly,
                  previewMode,
                )}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function SummaryCompletion({
  structure,
  questions,
  answers,
  onAnswer,
  readOnly,
  previewMode,
}: {
  structure: SummaryStructure
  questions: Question[]
  answers: Answers
  onAnswer: OnAnswer
  readOnly?: boolean
  previewMode?: boolean
}) {
  const gapToQ = buildGapMap(questions)
  const maxWords = structure.max_words_per_gap
  const options = structure.options ?? []
  const title = structure.title?.trim() || ''

  return (
    <div className='space-y-5'>
      {options.length > 0 && (
        <div className='mx-auto max-w-xs rounded-lg border border-foreground/20'>
          <div className='space-y-1.5 px-6 py-4'>
            {options.map((opt, i) => (
              <p key={i} className='text-[14px] leading-relaxed text-foreground'>
                {opt}
              </p>
            ))}
          </div>
        </div>
      )}
      <div className='rounded-lg border border-foreground/20 bg-card px-8 py-7'>
        {title && (
          <p className='mb-5 text-center text-[16px] font-bold text-foreground'>
            {title}
          </p>
        )}
        <div className='space-y-4'>
          {structure.paragraphs.map((paragraph, pi) => (
            <p key={pi} className='text-[14px] leading-8 text-foreground'>
              {renderSegments(
                paragraph.segments,
                gapToQ,
                answers,
                onAnswer,
                maxWords,
                readOnly,
                previewMode,
                options.length > 0 ? options : undefined,
              )}
            </p>
          ))}
        </div>
      </div>
    </div>
  )
}

function FlowCompletion({
  structure,
  questions,
  answers,
  onAnswer,
  readOnly,
  previewMode,
}: {
  structure: FlowStructure
  questions: Question[]
  answers: Answers
  onAnswer: OnAnswer
  readOnly?: boolean
  previewMode?: boolean
}) {
  const gapToQ = buildGapMap(questions)
  const maxWords = structure.max_words_per_gap

  return (
    <div className='mx-auto max-w-xl rounded-lg border border-border bg-card p-6'>
      {structure.title && (
        <p className='mb-6 text-center text-sm font-medium text-foreground'>
          {structure.title}
        </p>
      )}
      <div className='flex flex-col items-center'>
        {structure.steps.map((step, si) => (
          <div key={si} className='flex w-full flex-col items-center'>
            <div className='w-full rounded-lg border border-border px-4 py-3 text-sm leading-relaxed text-foreground'>
              {renderSegments(
                step.segments,
                gapToQ,
                answers,
                onAnswer,
                maxWords,
                readOnly,
                previewMode,
              )}
            </div>
            {si < structure.steps.length - 1 && (
              <ArrowDown className='my-2 size-6 text-muted-foreground' />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export function CompoundCompletionRenderer({
  structure,
  questions,
  answers,
  onAnswer,
  readOnly = false,
  highlightCell = null,
  previewMode = false,
}: {
  structure: CompoundStructure
  questions: Question[]
  answers: Answers
  onAnswer: OnAnswer
  readOnly?: boolean
  highlightCell?: { row: number; col: number } | null
  previewMode?: boolean
}) {
  const body = (() => {
    switch (structure.variant) {
      case 'table':
        return (
          <TableCompletion
            structure={structure}
            questions={questions}
            answers={answers}
            onAnswer={onAnswer}
            readOnly={readOnly}
            highlightCell={highlightCell}
            previewMode={previewMode}
          />
        )
      case 'notes':
        return (
          <NoteCompletion
            structure={structure}
            questions={questions}
            answers={answers}
            onAnswer={onAnswer}
            readOnly={readOnly}
            previewMode={previewMode}
          />
        )
      case 'form':
        return (
          <FormCompletion
            structure={structure}
            questions={questions}
            answers={answers}
            onAnswer={onAnswer}
            readOnly={readOnly}
            previewMode={previewMode}
          />
        )
      case 'summary':
        return (
          <SummaryCompletion
            structure={structure}
            questions={questions}
            answers={answers}
            onAnswer={onAnswer}
            readOnly={readOnly}
            previewMode={previewMode}
          />
        )
      case 'flow':
        return (
          <FlowCompletion
            structure={structure}
            questions={questions}
            answers={answers}
            onAnswer={onAnswer}
            readOnly={readOnly}
            previewMode={previewMode}
          />
        )
      default:
        return null
    }
  })()

  if (!body) return null
  if (!structure.image_url) return body

  return (
    <div className='space-y-3'>
      <div className='flex justify-center'>
        <img
          src={mediaUrl(structure.image_url)}
          alt='Diagram'
          className='max-w-lg rounded-lg border border-border'
          onError={(e) => {
            ;(e.target as HTMLImageElement).style.display = 'none'
          }}
        />
      </div>
      {body}
    </div>
  )
}
