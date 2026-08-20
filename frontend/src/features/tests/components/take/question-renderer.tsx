import { Flag } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { mediaUrl } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { highlightCaps } from './shared/instruction-block'
import type { Question } from '../../data/schema'

type Props = {
  question: Question
  answer: Record<string, unknown>
  onAnswer: (response: Record<string, unknown>) => void
  flagged?: boolean
  onToggleFlag?: () => void
  /** Teacher preview: show answer key under the question */
  previewMode?: boolean
}

function formatAnswerKey(answerKey: Record<string, unknown> | null): string {
  if (!answerKey) return '—'
  if (typeof answerKey.correct === 'string') return answerKey.correct
  if (Array.isArray(answerKey.correct)) return answerKey.correct.map(String).join(', ')
  if (typeof answerKey.answer === 'string') return answerKey.answer
  if (Array.isArray(answerKey.answer)) return answerKey.answer.map(String).join(', ')
  try {
    return JSON.stringify(answerKey)
  } catch {
    return '—'
  }
}

// ── Shared tokens ─────────────────────────────────────────────────────────────

const chip =
  'inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-bold text-primary'

// ── Compound table / notes-card types ────────────────────────────────────────
// Used by ListeningSection when multiple Questions share the same table/notes.

export type CellTextSeg = { text: string }
export type CellGapSeg = { gap: string }
export type CellSegment = CellTextSeg | CellGapSeg
export type TableCell = string | CellSegment[]

export type TableSpec = {
  title?: string
  headers: string[]
  rows: TableCell[][]
}

export type NoteHeading = { heading: string }
export type NoteItem = string | NoteHeading | CellSegment[]
export type NotesSpec = {
  title: string
  instruction?: string
  items: NoteItem[]
}

// ── Shared segment renderer ───────────────────────────────────────────────────

function renderSegments(
  segments: CellSegment[],
  gapToQ: Map<string, Question>,
  answers: Record<string, Record<string, unknown>>,
  onAnswer: (qId: string, resp: Record<string, unknown>) => void,
): React.ReactNode {
  return segments.map((seg, i) => {
    if ('text' in seg) {
      const lines = seg.text.split('\n')
      return (
        <span key={i}>
          {lines.map((line, j) => (
            <span key={j}>
              {line}
              {j < lines.length - 1 && <br />}
            </span>
          ))}
        </span>
      )
    }
    const q = gapToQ.get(seg.gap)
    if (!q) return null
    const value = (answers[q.id]?.answer as string) ?? ''
    return (
      <span key={i} className='inline-flex items-baseline gap-1'>
        <span data-q-chip className={chip}>{q.order}</span>
        <input
          type='text'
          value={value}
          onChange={(e) => onAnswer(q.id, { answer: e.target.value })}
          className='border-0 border-b-2 border-primary/40 bg-transparent px-1 py-0.5 text-center text-sm focus:border-primary focus:outline-none'
          style={{ width: '6rem' }}
        />
      </span>
    )
  })
}

function renderTableCell(
  cell: TableCell,
  gapToQ: Map<string, Question>,
  answers: Record<string, Record<string, unknown>>,
  onAnswer: (qId: string, resp: Record<string, unknown>) => void,
): React.ReactNode {
  if (typeof cell === 'string') return <span className='leading-7'>{cell}</span>
  return (
    <span className='leading-8'>
      {renderSegments(cell, gapToQ, answers, onAnswer)}
    </span>
  )
}

// ── Compound Table Completion ─────────────────────────────────────────────────
// Renders the full table once for a group of Questions that share table_id.

export function CompoundTableCompletion({
  table,
  questions,
  answers,
  onAnswer,
}: {
  table: TableSpec
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
}) {
  const gapToQ = new Map<string, Question>()
  for (const q of questions) {
    const gapId = q.content.gap_id
    const gapKey = q.content.gap_key
    if (typeof gapId === 'string' && gapId) gapToQ.set(gapId, q)
    if (typeof gapKey === 'string' && gapKey) gapToQ.set(gapKey, q)
  }

  return (
    <div className='overflow-x-auto'>
      {table.title && (
        <p className='mb-3 text-center text-[15px] font-bold text-foreground'>
          {table.title}
        </p>
      )}
      <table className='w-full border-collapse border border-border text-sm'>
        {table.headers.length > 0 && (
          <thead>
            <tr>
              {table.headers.map((h, i) => (
                <th
                  key={i}
                  className='border border-border bg-muted px-3 py-2.5 text-left text-[12px] font-semibold text-foreground'
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  className='border border-border px-3 py-2.5 align-top text-[13px] text-foreground'
                >
                  {renderTableCell(cell, gapToQ, answers, onAnswer)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Note Completion Card ──────────────────────────────────────────────────────
// Renders a bordered card with bullet-list notes and inline gap inputs.

export function NoteCompletionCard({
  notes,
  questions,
  answers,
  onAnswer,
}: {
  notes: NotesSpec
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
}) {
  const gapToQ = new Map<string, Question>()
  for (const q of questions) {
    const gapId = q.content.gap_id
    const gapKey = q.content.gap_key
    if (typeof gapId === 'string' && gapId) gapToQ.set(gapId, q)
    if (typeof gapKey === 'string' && gapKey) gapToQ.set(gapKey, q)
  }

  // Group items into runs of [headings + bullets] for flat rendering
  // Headings break out of the <ul> and render as <p> between bullet groups.
  type Block =
    | { kind: 'heading'; text: string }
    | { kind: 'bullets'; items: NoteItem[] }

  const blocks: Block[] = []
  let currentBullets: NoteItem[] = []
  for (const item of notes.items) {
    if (typeof item === 'object' && !Array.isArray(item) && 'heading' in item) {
      if (currentBullets.length > 0) {
        blocks.push({ kind: 'bullets', items: currentBullets })
        currentBullets = []
      }
      blocks.push({ kind: 'heading', text: (item as NoteHeading).heading })
    } else {
      currentBullets.push(item as string | CellSegment[])
    }
  }
  if (currentBullets.length > 0) blocks.push({ kind: 'bullets', items: currentBullets })

  // Parse word bank from instruction if it contains "Word box:" or "word box:"
  const wordBankWords: string[] = []
  let instructionText = notes.instruction ?? ''
  const wordBoxMatch = instructionText.match(/[Ww]ord\s+box\s*:(.+)/s)
  if (wordBoxMatch) {
    instructionText = instructionText.slice(0, wordBoxMatch.index).trim()
    wordBankWords.push(
      ...wordBoxMatch[1]
        .split(/[|,]/)
        .map((w) => w.trim())
        .filter(Boolean),
    )
  }

  return (
    <div className='space-y-3'>
      {/* instruction text (above card) */}
      {instructionText && (
        <p className='text-[13px] text-foreground'>{highlightCaps(instructionText)}</p>
      )}

      {/* word bank grid */}
      {wordBankWords.length > 0 && (
        <div className='rounded border border-border bg-muted p-3'>
          <p className='mb-2 text-[12px] font-semibold uppercase tracking-wide text-muted-foreground'>
            List of Words
          </p>
          <div className='flex flex-wrap gap-x-4 gap-y-1'>
            {wordBankWords.map((word, idx) => (
              <span key={idx} className='text-[13px] text-foreground'>
                <span className='mr-0.5 font-semibold text-muted-foreground'>
                  {String.fromCharCode(65 + idx)}.
                </span>{' '}
                {word}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* notes card */}
      <div className='mx-auto rounded-lg border border-border bg-card p-5'>
      <p className='mb-3 text-center text-base font-medium text-foreground'>{notes.title}</p>
      {blocks.map((block, bi) =>
        block.kind === 'heading' ? (
          <p key={bi} className='mb-1 mt-3 text-[13px] font-bold text-foreground'>
            {block.text}
          </p>
        ) : (
          <ul key={bi} className='space-y-1.5 pl-4' style={{ listStyleType: 'disc' }}>
            {block.items.map((item, i) => (
              <li key={i} className='text-[14px] leading-8 text-foreground'>
                {typeof item === 'string'
                  ? item
                  : renderSegments(item as CellSegment[], gapToQ, answers, onAnswer)}
              </li>
            ))}
          </ul>
        ),
      )}
      </div>
    </div>
  )
}

// ── Compound Matching Dropdown ────────────────────────────────────────────────
// Q17-20 (Part 2 Duties) and Q25-30 (Part 3 Opinions): each Question is a
// single MCQ row; the group shares a floating options card and a group title.

export type MatchingDropdownSpec = {
  options_pool: string[]
  group_title: string
}

export function CompoundMatchingDropdown({
  questions,
  answers,
  onAnswer,
  previewMode = false,
}: {
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  previewMode?: boolean
}) {
  const firstQ = questions[0]
  const optionsPool = (firstQ.content.options_pool as string[]) ?? []
  const groupTitle = (firstQ.content.group_title as string) ?? ''

  return (
    <div>
      {/* Floating options card (top-right) */}
      <div className='mb-4 ml-auto max-w-xs rounded-lg border border-border bg-muted p-3 text-[13px]'>
        {optionsPool.map((opt, i) => (
          <p key={i} className='leading-6 text-foreground'>
            {opt}
          </p>
        ))}
      </div>

      {/* Group title */}
      {groupTitle && (
        <p className='mb-3 text-[14px] font-bold text-foreground'>{groupTitle}</p>
      )}

      {/* One row per question: chip + label + select */}
      <div className='space-y-3'>
        {questions.map((q) => {
          const currentVal = (answers[q.id]?.answer as string) ?? ''
          const label = (q.content.label as string) ?? ''
          // Extract just the letters from options_pool for the <select>
          const letters = optionsPool.map((opt) => opt.charAt(0))
          const displayN = q.computed_number ?? q.order
          return (
            <div key={q.id} id={`q-${displayN}`} className='scroll-mt-20 space-y-1'>
              <div className='flex flex-wrap items-center gap-x-2 gap-y-1'>
                <span data-q-chip className={chip}>{displayN}</span>
                <span className='text-[14px] text-foreground'>{label}</span>
                <Select
                  value={currentVal || undefined}
                  onValueChange={(v) => onAnswer(q.id, { answer: v })}
                >
                  <SelectTrigger className='h-7 w-14 shrink-0 justify-center gap-1 border-border bg-card px-2 text-[13px] font-medium shadow-sm [&>svg]:size-3'>
                    <SelectValue placeholder='—' />
                  </SelectTrigger>
                  <SelectContent align='center' className='min-w-14'>
                    {letters.map((letter) => (
                      <SelectItem key={letter} value={letter} className='justify-center text-[13px]'>
                        {letter}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {previewMode && (
                <div className='ml-8 rounded border border-border bg-muted px-2 py-1 text-xs text-muted-foreground'>
                  Answer: {formatAnswerKey(q.answer_key)}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Compound Multi-Select Pair ────────────────────────────────────────────────
// Q21-22 and Q23-24: two Questions share one set of checkboxes.
// Each Q has its own correct letter; scoring checks if that letter is in the
// shared list stored on both Questions' answers.

export function CompoundMultiSelectPair({
  questions,
  answers,
  onAnswer,
  previewMode = false,
}: {
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  previewMode?: boolean
}) {
  const firstQ = questions[0]
  const pairQuestion = (firstQ.content.pair_question as string) ?? ''
  const options = (firstQ.content.options as string[]) ?? []
  const maxChoices = questions.length

  // Read selected list from first question (canonical source of truth)
  const selected = (answers[questions[0].id]?.answer as string[]) ?? []

  const toggle = (optLabel: string) => {
    const letter = optLabel.charAt(0)
    const next = selected.includes(letter)
      ? selected.filter((s) => s !== letter)
      : selected.length < maxChoices
        ? [...selected, letter]
        : selected

    // Dispatch same list to ALL questions in the pair
    questions.forEach((q) => onAnswer(q.id, { answer: next }))
  }

  return (
    <div className='space-y-3'>
      <p className='text-[15px] font-[500] leading-6 text-foreground'>{pairQuestion}</p>
      <div className='space-y-2'>
        {options.map((opt, i) => {
          const letter = opt.charAt(0)
          const isChecked = selected.includes(letter)
          const optId = `pair-${firstQ.id}-${i}`
          return (
            <div
              key={i}
              className={cn(
                'flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 text-[14px] transition-colors',
                isChecked
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:bg-muted',
              )}
              onClick={() => toggle(opt)}
            >
              <input
                id={optId}
                type='checkbox'
                checked={isChecked}
                readOnly
                className='size-4 cursor-pointer accent-primary'
              />
              <label htmlFor={optId} className='cursor-pointer text-foreground'>
                {opt}
              </label>
            </div>
          )
        })}
      </div>
      {previewMode && (
        <div className='rounded border border-border bg-muted px-2.5 py-1.5 text-xs text-muted-foreground'>
          Answers: {questions.map((q) => `Q${q.order}: ${formatAnswerKey(q.answer_key)}`).join(', ')}
        </div>
      )}
    </div>
  )
}

// ── Legacy single-question table (kept for backward compat) ───────────────────

type LegacyTableCell = string | { gap: true; key: string; label?: string }

type LegacyTableSpec = {
  headers: string[]
  rows: LegacyTableCell[][]
  instruction?: string
}

function LegacyTableCompletion({
  table,
  answer,
  onAnswer,
}: {
  table: LegacyTableSpec
  answer: Record<string, unknown>
  onAnswer: (response: Record<string, unknown>) => void
}) {
  const updateCell = (key: string, val: string) => {
    onAnswer({ ...answer, [key]: val })
  }

  return (
    <div className='overflow-x-auto'>
      {table.instruction && (
        <p className='mb-3 text-sm text-foreground'>
          {highlightCaps(table.instruction)}
        </p>
      )}
      <table className='w-full border-collapse border border-border text-sm'>
        {table.headers.length > 0 && (
          <thead>
            <tr>
              {table.headers.map((h, i) => (
                <th
                  key={i}
                  className='border border-border bg-muted px-3 py-2 text-left text-[12px] font-semibold text-foreground'
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => {
                if (typeof cell === 'string') {
                  return (
                    <td
                      key={ci}
                      className='border border-border px-3 py-2 text-[13px] text-foreground'
                    >
                      {cell}
                    </td>
                  )
                }
                return (
                  <td key={ci} className='border border-border px-3 py-2'>
                    <div className='flex items-center gap-1.5'>
                      {cell.label && (
                        <span className={chip}>{cell.label}</span>
                      )}
                      <input
                        type='text'
                        value={(answer[cell.key] as string) ?? ''}
                        onChange={(e) => updateCell(cell.key, e.target.value)}
                        className='border-0 border-b-2 border-primary/40 bg-transparent px-1 py-0.5 text-sm focus:border-primary focus:outline-none'
                        style={{ width: '6rem' }}
                      />
                    </div>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Gap fill — inline rendering ───────────────────────────────────────────────

function GapFillInline({
  question,
  answer,
  onAnswer,
}: {
  question: Question
  answer: Record<string, unknown>
  onAnswer: (response: Record<string, unknown>) => void
}) {
  const text = (question.content.text as string) ?? ''
  const hasBlank = /___|\{blank\}/.test(text)

  if (!hasBlank) {
    // Legacy fallback: chip + text + input below
    return (
      <div className='space-y-2'>
        <p className='text-[15px] font-[500] leading-7 text-foreground'>
          <span className={cn(chip, 'mr-1.5')}>{question.order}</span>
          {text}
        </p>
        <input
          type='text'
          value={(answer.answer as string) ?? ''}
          onChange={(e) => onAnswer({ answer: e.target.value })}
          className='border-0 border-b-2 border-primary/40 bg-transparent px-1 py-0.5 text-sm focus:border-primary focus:outline-none'
          style={{ width: '8rem' }}
          placeholder='...'
        />
      </div>
    )
  }

  const parts = text.split(/___|\{blank\}/)
  return (
    <p className='text-[15px] font-[500] leading-8 text-foreground'>
      {parts[0]}
      <span className={cn(chip, 'mx-1')}>{question.order}</span>
      <input
        type='text'
        value={(answer.answer as string) ?? ''}
        onChange={(e) => onAnswer({ answer: e.target.value })}
        className='mx-1 inline border-0 border-b-2 border-primary/40 bg-transparent text-center text-sm focus:border-primary focus:outline-none'
        style={{ width: '7rem', verticalAlign: 'baseline' }}
        placeholder='...'
      />
      {parts.slice(1).join('')}
    </p>
  )
}

// ── Main renderer ─────────────────────────────────────────────────────────────

export function QuestionRenderer({
  question,
  answer,
  onAnswer,
  flagged: _flagged,
  onToggleFlag: _onToggleFlag,
  previewMode: _previewMode = false,
}: Props) {
  const qType = question.question_type
  const content = question.content

  // ── Legacy single-Q table completion (gap_fill + content.table, no table_id)
  if (qType === 'gap_fill' && content.table && !content.table_id) {
    return (
      <div className='space-y-3'>
        {!!content.question && (
          <p className='text-[15px] font-[500] leading-7 text-foreground'>
            {content.question as string}
          </p>
        )}
        <LegacyTableCompletion
          table={content.table as LegacyTableSpec}
          answer={answer}
          onAnswer={onAnswer}
        />
      </div>
    )
  }

  // ── MCQ ──────────────────────────────────────────────────────────────────
  if (qType === 'mcq') {
    const options = (content.options as string[]) ?? []
    // Support both "question" and legacy "prompt" field names
    const questionText =
      ((content.question ?? content.prompt) as string | undefined) ?? ''
    // "Choose TWO" variant when max_choices > 1
    const maxChoices = (content.max_choices as number | undefined) ?? 1

    // Answers are stored as letters ("A", "B", "C"…). Legacy data may have stored
    // the full option text — normalise to a letter for comparison/selection.
    const textToLetter = (val: string) => {
      if (/^[A-Z]$/.test(val)) return val
      const idx = options.indexOf(val)
      return idx >= 0 ? String.fromCharCode(65 + idx) : val
    }

    if (maxChoices > 1) {
      const rawSelected = (answer.answer as string[]) ?? []
      // Normalise legacy full-text selections to letters
      const selected = rawSelected.map(textToLetter)
      const toggle = (letter: string) => {
        const next = selected.includes(letter)
          ? selected.filter((s) => s !== letter)
          : selected.length < maxChoices
            ? [...selected, letter]
            : selected
        onAnswer({ answer: next })
      }
      return (
        <div className='space-y-3'>
          <div className='space-y-1'>
            <p className='text-[15px] font-[500] text-foreground'>
              <span data-q-chip className='mr-1.5 inline-flex min-w-5 justify-center text-[15px] font-bold'>{question.order}</span>
              {questionText}
            </p>
            <p className='text-[13px] text-muted-foreground'>
              Choose {maxChoices === 2 ? 'TWO' : maxChoices} letters,{' '}
              {String.fromCharCode(65)}–
              {String.fromCharCode(64 + options.length)}.
            </p>
          </div>
          <div className='space-y-2'>
            {options.map((opt, i) => {
              const letter = String.fromCharCode(65 + i)
              const id = `${question.id}-chk-${i}`
              const checked = selected.includes(letter)
              return (
                <div
                  key={i}
                  className={cn(
                    'flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 text-[15px] transition-colors',
                    checked
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted',
                  )}
                  onClick={() => toggle(letter)}
                >
                  <Checkbox
                    id={id}
                    checked={checked}
                    onCheckedChange={() => toggle(letter)}
                  />
                  <Label
                    htmlFor={id}
                    className='cursor-pointer font-normal text-foreground'
                  >
                    <span className={cn('mr-1 text-[13px] font-medium', checked ? 'text-primary' : 'text-muted-foreground')}>{letter}.</span>{' '}
                    {opt}
                  </Label>
                </div>
              )
            })}
          </div>
        </div>
      )
    }

    // Standard single-choice MCQ — value is the letter ("A", "B", …)
    const selectedLetter = textToLetter((answer.answer as string) ?? '')
    return (
      <div className='space-y-3'>
        <p className='text-[15px] font-[500] leading-6 text-foreground'>
          <span data-q-chip className='mr-1.5 inline-flex min-w-5 justify-center text-[15px] font-bold'>{question.order}</span>
          {questionText}
        </p>
        <RadioGroup
          value={selectedLetter}
          onValueChange={(v) => onAnswer({ answer: v })}
          className='space-y-1.5 pl-6'
        >
          {options.map((opt, i) => {
            const letter = String.fromCharCode(65 + i)
            const id = `${question.id}-${i}`
            return (
              <div key={i} className='flex cursor-pointer items-center gap-2.5'>
                <RadioGroupItem value={letter} id={id} />
                <Label
                  htmlFor={id}
                  className='cursor-pointer text-[15px] font-normal leading-7 text-foreground'
                >
                  <span className='mr-1 font-medium'>{letter}.</span>
                  {opt}
                </Label>
              </div>
            )
          })}
        </RadioGroup>
      </div>
    )
  }

  // ── True / False / Not Given ─────────────────────────────────────────────
  if (qType === 'true_false_ng') {
    const opts = ['True', 'False', 'Not Given']
    return (
      <div className='space-y-2'>
        <p className='text-[15px] font-[500] leading-7 text-foreground'>
          <span data-q-chip className='mr-1.5 inline-flex min-w-5 justify-center text-[15px] font-bold'>{question.order}</span>
          {content.statement as string}
        </p>
        <RadioGroup
          value={(answer.answer as string) ?? ''}
          onValueChange={(v) => onAnswer({ answer: v })}
          className='space-y-1.5 pl-6'
        >
          {opts.map((opt) => {
            const id = `${question.id}-${opt}`
            return (
              <div key={opt} className='flex items-center gap-2.5'>
                <RadioGroupItem value={opt} id={id} />
                <Label
                  htmlFor={id}
                  className='cursor-pointer text-[15px] font-bold uppercase leading-7 text-foreground'
                >
                  {opt}
                </Label>
              </div>
            )
          })}
        </RadioGroup>
      </div>
    )
  }

  // ── Yes / No / Not Given ─────────────────────────────────────────────────
  if (qType === 'yes_no_ng') {
    const opts = ['Yes', 'No', 'Not Given']
    return (
      <div className='space-y-2'>
        <p className='text-[15px] font-[500] leading-7 text-foreground'>
          <span data-q-chip className='mr-1.5 inline-flex min-w-5 justify-center text-[15px] font-bold'>{question.order}</span>
          {content.statement as string}
        </p>
        <RadioGroup
          value={(answer.answer as string) ?? ''}
          onValueChange={(v) => onAnswer({ answer: v })}
          className='space-y-1.5 pl-6'
        >
          {opts.map((opt) => {
            const id = `${question.id}-${opt}`
            return (
              <div key={opt} className='flex items-center gap-2.5'>
                <RadioGroupItem value={opt} id={id} />
                <Label
                  htmlFor={id}
                  className='cursor-pointer text-[15px] font-bold uppercase leading-7 text-foreground'
                >
                  {opt}
                </Label>
              </div>
            )
          })}
        </RadioGroup>
      </div>
    )
  }

  // ── Sentence Completion / Short Answer ───────────────────────────────────
  if (qType === 'sentence_completion' || qType === 'short_answer') {
    const prompt = (content.prompt as string) ?? ''
    const maxWords = (content.max_words as number) ?? 3
    const studentAnswer = (answer.answer as string) ?? ''
    const wordCount = studentAnswer.trim() === '' ? 0 : studentAnswer.trim().split(/\s+/).length
    const overLimit = wordCount > maxWords

    if (qType === 'sentence_completion' && /_{2,}/.test(prompt)) {
      const parts = prompt.split(/_{2,}/)
      return (
        <div className='space-y-2'>
          <p className='text-[15px] font-[500] leading-8 text-foreground'>
            <span className='mr-1.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-medium text-muted-foreground align-middle'>
              {question.order}
            </span>
            {parts[0]}
            <input
              type='text'
              value={studentAnswer}
              onChange={(e) => onAnswer({ answer: e.target.value })}
              className={cn(
                'mx-1 inline-block h-7 w-36 rounded border bg-card px-2 text-center text-sm align-middle focus:outline-none focus:ring-1',
                overLimit
                  ? 'border-red-400 focus:border-red-500 focus:ring-red-500'
                  : 'border-border focus:border-primary focus:ring-primary',
              )}
            />
            {parts.slice(1).join('')}
          </p>
        </div>
      )
    }

    return (
      <div className='space-y-2'>
        <p className='text-[15px] font-[500] leading-7 text-foreground'>
          <span className='mr-1.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-medium text-muted-foreground align-middle'>
            {question.order}
          </span>
          {prompt}
        </p>
        <input
          type='text'
          value={studentAnswer}
          onChange={(e) => onAnswer({ answer: e.target.value })}
          className={cn(
            'w-full rounded border bg-card px-3 py-1.5 text-sm focus:outline-none focus:ring-1',
            overLimit
              ? 'border-red-400 focus:border-red-500 focus:ring-red-500'
              : 'border-border focus:border-primary focus:ring-primary',
          )}
          placeholder='Your answer...'
        />
      </div>
    )
  }

  // ── Gap fill ─────────────────────────────────────────────────────────────
  if (qType === 'gap_fill') {
    return (
      <GapFillInline question={question} answer={answer} onAnswer={onAnswer} />
    )
  }

  // ── Matching ─────────────────────────────────────────────────────────────
  if (qType === 'matching') {
    // Support both canonical (left/right) and seed (items/options) field names
    const left =
      ((content.left ?? content.items) as string[] | undefined) ?? []
    const right =
      ((content.right ?? content.options) as string[] | undefined) ?? []
    const questionText =
      ((content.question ?? content.prompt) as string | undefined) ??
      'Match the items:'
    const currentPairs = (answer.answer as Record<string, string>) ?? {}
    return (
      <div className='space-y-4'>
        <p className='text-[15px] font-[500] text-foreground'>
          <span data-q-chip className='mr-1.5 inline-flex min-w-5 justify-center text-[15px] font-bold'>{question.order}</span>
          {questionText}
        </p>
        {!!content.image_url && (
          <img
            src={mediaUrl(content.image_url as string)}
            alt='Map'
            className='max-h-64 rounded-md border border-border'
          />
        )}
        <div className='space-y-3'>
          {left.map((item) => (
            <div key={item} className='flex items-center gap-3'>
              <span className='w-40 text-sm text-foreground'>{item}</span>
              <Select
                value={currentPairs[item] ?? ''}
                onValueChange={(v) =>
                  onAnswer({ answer: { ...currentPairs, [item]: v } })
                }
              >
                <SelectTrigger className='w-48 text-sm shadow-sm'>
                  <SelectValue placeholder='Select...' />
                </SelectTrigger>
                <SelectContent>
                  {right.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ── Multi-select ────────────────────────────────────────────────────────
  if (qType === 'multi_select') {
    const options = (content.options as string[] | undefined) ?? []
    const questionText = (content.question ?? content.prompt) as string | undefined
    const chooseN =
      typeof content.choose_n === 'number' && content.choose_n >= 1
        ? content.choose_n
        : Array.isArray(question.answer_key?.correct)
          ? (question.answer_key!.correct as unknown[]).length
          : undefined

    const textToLetter = (val: string) => {
      if (/^[A-Z]$/i.test(val.trim())) return val.trim().toUpperCase()
      const idx = options.indexOf(val)
      return idx >= 0 ? String.fromCharCode(65 + idx) : val
    }
    const selected: string[] = Array.isArray(answer.answer)
      ? (answer.answer as string[]).map(textToLetter)
      : []

    const toggle = (letter: string) => {
      let next: string[]
      if (selected.includes(letter)) {
        next = selected.filter((s) => s !== letter)
      } else if (chooseN != null && selected.length >= chooseN) {
        next = selected
      } else {
        next = [...selected, letter]
      }
      onAnswer({ answer: next })
    }

    // Group header already shows "Choose TWO letters, A-E." — do not repeat under the stem.
    return (
      <div className='space-y-3'>
        {questionText && (
          <p className='text-[15px] font-[500] leading-6 text-foreground'>{questionText}</p>
        )}
        <div className='space-y-2'>
          {options.map((opt, i) => {
            const letter = String.fromCharCode(65 + i)
            const id = `${question.id}-ms-${i}`
            const checked = selected.includes(letter)
            return (
              <div
                key={i}
                className={cn(
                  'flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 text-[15px] transition-colors',
                  checked
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:bg-muted/50',
                )}
                onClick={() => toggle(letter)}
              >
                <Checkbox
                  id={id}
                  checked={checked}
                  onCheckedChange={() => toggle(letter)}
                />
                <Label htmlFor={id} className='cursor-pointer font-normal text-foreground'>
                  <span className={cn('mr-1 text-[13px] font-medium', checked ? 'text-primary' : 'text-muted-foreground')}>{letter}.</span> {opt}
                </Label>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className='text-sm text-muted-foreground'>
      Question type "{qType}" (#{question.order})
    </div>
  )
}

// ── Matching Information / Features / Headings renderer ───────────────────────

export function MatchingLetterRenderer({
  questions,
  options,
  answers,
  onAnswer,
  listTitle = 'List of Options',
  questionsTitle,
  repeatable = true,
  /** When false, options still feed the dropdown but the list card is hidden
   *  (JumpInto-style Matching Information: letters already in the instruction). */
  showOptionsList = true,
  previewMode = false,
}: {
  questions: Question[]
  options: string[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  listTitle?: string
  questionsTitle?: string
  repeatable?: boolean
  showOptionsList?: boolean
  previewMode?: boolean
}) {
  const prefixes = options.map((opt) => {
    const dot = opt.indexOf('.')
    return dot > 0 ? opt.slice(0, dot).trim() : opt.trim()
  })

  return (
    <div className='space-y-5'>
      {showOptionsList && options.length > 0 && (
        <div className='mx-auto max-w-lg rounded-lg border border-foreground/20'>
          <div className='border-b border-foreground/20 px-5 py-2.5 text-center text-[15px] font-bold text-foreground'>
            {listTitle}
          </div>
          <div className='space-y-1.5 px-6 py-4'>
            {options.map((opt, i) => (
              <p key={i} className='text-[14px] leading-relaxed text-foreground'>{opt}</p>
            ))}
            {repeatable && (
              <p className='mt-3 text-[12px] italic text-muted-foreground'>
                NB: You may use any letter more than once.
              </p>
            )}
          </div>
        </div>
      )}

      {questionsTitle && (
        <p className='text-sm font-bold text-foreground'>{questionsTitle}</p>
      )}

      <div className='space-y-2.5'>
        {questions.map((q) => {
          const statement = (q.content.question ?? q.content.stem ?? `Question ${q.order}`) as string
          const currentVal = (answers[q.id]?.answer as string) ?? ''
          const displayN = q.computed_number ?? q.order
          return (
            <div key={q.id} id={`q-${displayN}`} className='scroll-mt-20 space-y-1'>
              <div className='flex flex-wrap items-center gap-x-2 gap-y-1'>
                <span
                  data-q-chip
                  className='inline-flex min-w-[1.5rem] justify-center text-[14px] font-bold text-foreground'
                >
                  {displayN}
                </span>
                <span className='text-[14px] text-foreground'>{statement}</span>
                <Select
                  value={currentVal || undefined}
                  onValueChange={(v) => onAnswer(q.id, { answer: v })}
                >
                  <SelectTrigger className='h-7 w-14 shrink-0 justify-center gap-1 border-border bg-card px-2 text-[13px] font-medium shadow-sm [&>svg]:size-3'>
                    <SelectValue placeholder={String(displayN)} />
                  </SelectTrigger>
                  <SelectContent align='center' className='min-w-14'>
                    {prefixes.map((prefix, i) => (
                      <SelectItem key={i} value={prefix} className='justify-center text-[13px]'>
                        {prefix}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {previewMode && (
                <div className='ml-9 rounded border border-border bg-muted px-2 py-1 text-xs text-muted-foreground'>
                  Answer: {formatAnswerKey(q.answer_key)}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Map Labeling renderer (group-level: image + dropdown rows) ──────────────

export function ExamMapImage({
  src,
  caption,
  size = 'compact',
}: {
  src: string
  caption?: string
  size?: 'compact' | 'pane'
}) {
  return (
    <figure className={cn('mx-auto w-full', size === 'pane' ? 'max-w-[540px]' : 'max-w-[520px]')}>
      {caption && (
        <figcaption className='mb-1.5 text-center text-[13px] font-semibold text-foreground'>
          {caption}
        </figcaption>
      )}
      <div className='overflow-hidden rounded-md border border-border bg-white p-1.5'>
        <img
          src={mediaUrl(src)}
          alt={caption || 'Map'}
          className={cn(
            'mx-auto block h-auto w-auto max-w-full object-contain',
            size === 'pane' ? 'max-h-[min(460px,58vh)]' : 'max-h-[min(400px,52vh)]',
          )}
          onError={(e) => {
            ;(e.target as HTMLImageElement).style.display = 'none'
          }}
        />
      </div>
    </figure>
  )
}

export function MapLabelingRenderer({
  questions,
  options,
  imageUrl,
  imageCaption,
  answers,
  onAnswer,
  previewMode = false,
  showImage = true,
}: {
  questions: Question[]
  options: string[]
  imageUrl?: string
  imageCaption?: string
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  previewMode?: boolean
  showImage?: boolean
}) {
  return (
    <div className='space-y-3'>
      {showImage && imageUrl && (
        <ExamMapImage src={imageUrl} caption={imageCaption} />
      )}

      <div className='space-y-1.5'>
        {questions.map((q) => {
          const location =
            (q.content.location as string) ??
            (q.content.question as string) ??
            `Location ${q.order}`
          const currentVal = (answers[q.id]?.answer as string) ?? ''
          const displayN = q.computed_number ?? q.order
          return (
            <div key={q.id} id={`q-${displayN}`} className='scroll-mt-20 space-y-1'>
              <div className='flex flex-wrap items-center gap-x-2 gap-y-1'>
                <span
                  data-q-chip
                  className='flex size-6 shrink-0 items-center justify-center rounded-full bg-muted text-[12px] font-medium text-muted-foreground'
                >
                  {displayN}
                </span>
                <span className='min-w-0 text-[13px] text-foreground'>
                  {location}
                </span>
                <Select
                  value={currentVal || undefined}
                  onValueChange={(v) => onAnswer(q.id, { answer: v })}
                >
                  <SelectTrigger className='h-7 w-14 shrink-0 justify-center gap-1 border-border bg-card px-2 text-[13px] font-medium shadow-sm [&>svg]:size-3'>
                    <SelectValue placeholder='—' />
                  </SelectTrigger>
                  <SelectContent align='center' className='min-w-14'>
                    {options.map((lbl) => (
                      <SelectItem key={lbl} value={lbl} className='justify-center text-[13px]'>
                        {lbl}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {previewMode && (
                <div className='ml-8 rounded border border-border bg-muted px-2 py-1 text-xs text-muted-foreground'>
                  Answer: {formatAnswerKey(q.answer_key)}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Wrapper that adds optional flag button ─────────────────────────────────────

const _QuestionRenderer = QuestionRenderer

export { _QuestionRenderer as QuestionRendererCore }

// Re-export as default wrapper with flag button
export function QuestionRendererWithFlag(props: Props) {
  const { onToggleFlag, flagged, previewMode, question } = props
  const start = question.computed_number ?? question.order
  const end =
    typeof question.computed_number_end === 'number'
      ? question.computed_number_end
      : start
  return (
    <div className='relative scroll-mt-20' id={`q-${start}`}>
      {Array.from({ length: Math.max(0, end - start) }, (_, i) => (
        <span
          key={start + i + 1}
          id={`q-${start + i + 1}`}
          className='absolute'
          aria-hidden
        />
      ))}
      {onToggleFlag && (
        <button
          type='button'
          onClick={onToggleFlag}
          title={flagged ? 'Remove flag' : 'Flag for review'}
          className={cn(
            'absolute right-0 top-0 z-10 rounded p-1 transition-colors',
            flagged
              ? 'text-amber-500 hover:text-amber-600'
              : 'text-muted-foreground/40 hover:text-amber-400',
          )}
        >
          <Flag className='size-4' />
        </button>
      )}
      <QuestionRenderer {...props} />
      {previewMode && (
        <div className='mt-2 rounded border border-border bg-muted px-2.5 py-1.5 text-xs text-muted-foreground'>
          Answer: {formatAnswerKey(question.answer_key)}
        </div>
      )}
    </div>
  )
}
