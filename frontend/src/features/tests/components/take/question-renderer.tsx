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
import { cn } from '@/lib/utils'
import type { Question } from '../../data/schema'

type Props = {
  question: Question
  answer: Record<string, unknown>
  onAnswer: (response: Record<string, unknown>) => void
  flagged?: boolean
  onToggleFlag?: () => void
}

// ── Shared tokens ─────────────────────────────────────────────────────────────

const chip =
  'inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[11px] font-bold text-slate-600'

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
        <span className={chip}>{q.order}</span>
        <input
          type='text'
          value={value}
          onChange={(e) => onAnswer(q.id, { answer: e.target.value })}
          className='border-0 border-b-2 border-slate-800 bg-transparent px-1 py-0.5 text-center text-[14px] focus:border-blue-600 focus:outline-none'
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
  const gapToQ = new Map(
    questions.map((q) => [q.content.gap_key as string, q]),
  )

  return (
    <div className='overflow-x-auto'>
      {table.title && (
        <p className='mb-3 text-center text-[15px] font-bold text-slate-900'>
          {table.title}
        </p>
      )}
      <table className='w-full border-collapse border border-slate-900 text-[14px]'>
        {table.headers.length > 0 && (
          <thead>
            <tr>
              {table.headers.map((h, i) => (
                <th
                  key={i}
                  className='border border-slate-900 bg-slate-100 px-3 py-2.5 text-left text-[13px] font-bold text-slate-800'
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
                  className='border border-slate-900 px-3 py-2.5 align-top text-slate-800'
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
  const gapToQ = new Map(
    questions.map((q) => [q.content.gap_key as string, q]),
  )

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
        <p className='text-[13px] text-slate-700'>{instructionText}</p>
      )}

      {/* word bank grid */}
      {wordBankWords.length > 0 && (
        <div className='rounded border border-slate-300 bg-slate-50 p-3'>
          <p className='mb-2 text-[12px] font-semibold uppercase tracking-wide text-slate-500'>
            List of Words
          </p>
          <div className='flex flex-wrap gap-x-4 gap-y-1'>
            {wordBankWords.map((word, idx) => (
              <span key={idx} className='text-[13px] text-slate-800'>
                <span className='mr-0.5 font-semibold text-slate-500'>
                  {String.fromCharCode(65 + idx)}.
                </span>{' '}
                {word}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* notes card */}
      <div className='mx-auto rounded-sm border border-slate-900 bg-white p-5'>
      <p className='mb-3 text-[14px] font-bold text-slate-900'>{notes.title}</p>
      {blocks.map((block, bi) =>
        block.kind === 'heading' ? (
          <p key={bi} className='mb-1 mt-3 text-[13px] font-bold text-slate-900'>
            {block.text}
          </p>
        ) : (
          <ul key={bi} className='space-y-1.5 pl-4' style={{ listStyleType: 'disc' }}>
            {block.items.map((item, i) => (
              <li key={i} className='text-[14px] leading-8 text-slate-800'>
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
}: {
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
}) {
  const firstQ = questions[0]
  const optionsPool = (firstQ.content.options_pool as string[]) ?? []
  const groupTitle = (firstQ.content.group_title as string) ?? ''

  return (
    <div>
      {/* Floating options card (top-right) */}
      <div className='mb-4 ml-auto max-w-xs rounded border border-slate-900 bg-white p-3 text-[13px]'>
        {optionsPool.map((opt, i) => (
          <p key={i} className='leading-6 text-slate-800'>
            {opt}
          </p>
        ))}
      </div>

      {/* Group title */}
      {groupTitle && (
        <p className='mb-3 text-[14px] font-bold text-slate-900'>{groupTitle}</p>
      )}

      {/* One row per question: chip + label + select */}
      <div className='space-y-3'>
        {questions.map((q) => {
          const currentVal = (answers[q.id]?.answer as string) ?? ''
          const label = (q.content.label as string) ?? ''
          // Extract just the letters from options_pool for the <select>
          const letters = optionsPool.map((opt) => opt.charAt(0))
          return (
            <div key={q.id} className='flex items-center gap-3'>
              <span className={chip}>{q.order}</span>
              <span className='flex-1 text-[14px] text-slate-800'>{label}</span>
              <select
                value={currentVal}
                onChange={(e) => onAnswer(q.id, { answer: e.target.value })}
                className='rounded border border-slate-300 bg-white px-2 py-1 text-[13px] text-slate-800 focus:border-blue-500 focus:outline-none'
              >
                <option value=''>—</option>
                {letters.map((letter) => (
                  <option key={letter} value={letter}>
                    {letter}
                  </option>
                ))}
              </select>
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
}: {
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
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
      <p className='text-[15px] font-[500] leading-6 text-slate-900'>{pairQuestion}</p>
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
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-slate-200 hover:bg-slate-50',
              )}
              onClick={() => toggle(opt)}
            >
              <input
                id={optId}
                type='checkbox'
                checked={isChecked}
                readOnly
                className='size-4 cursor-pointer accent-blue-600'
              />
              <label htmlFor={optId} className='cursor-pointer text-slate-800'>
                {opt}
              </label>
            </div>
          )
        })}
      </div>
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
        <p className='mb-3 text-[14px] font-semibold text-slate-700'>
          {table.instruction}
        </p>
      )}
      <table className='w-full border-collapse border border-slate-900 text-[14px]'>
        {table.headers.length > 0 && (
          <thead>
            <tr>
              {table.headers.map((h, i) => (
                <th
                  key={i}
                  className='border border-slate-900 bg-slate-100 px-3 py-2 text-left text-[13px] font-bold text-slate-800'
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
                      className='border border-slate-900 px-3 py-2 text-slate-800'
                    >
                      {cell}
                    </td>
                  )
                }
                return (
                  <td key={ci} className='border border-slate-900 px-3 py-2'>
                    <div className='flex items-center gap-1.5'>
                      {cell.label && (
                        <span className={chip}>{cell.label}</span>
                      )}
                      <input
                        type='text'
                        value={(answer[cell.key] as string) ?? ''}
                        onChange={(e) => updateCell(cell.key, e.target.value)}
                        className='border-0 border-b-2 border-slate-800 bg-transparent px-1 py-0.5 text-[15px] focus:border-blue-600 focus:outline-none'
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
        <p className='text-[15px] font-[500] leading-7 text-slate-900'>
          <span className={cn(chip, 'mr-1.5')}>{question.order}</span>
          {text}
        </p>
        <input
          type='text'
          value={(answer.answer as string) ?? ''}
          onChange={(e) => onAnswer({ answer: e.target.value })}
          className='border-0 border-b-2 border-slate-800 bg-transparent px-1 py-0.5 text-[14px] focus:border-blue-600 focus:outline-none'
          style={{ width: '8rem' }}
          placeholder='...'
        />
      </div>
    )
  }

  const parts = text.split(/___|\{blank\}/)
  return (
    <p className='text-[15px] font-[500] leading-8 text-slate-900'>
      {parts[0]}
      <span className={cn(chip, 'mx-1')}>{question.order}</span>
      <input
        type='text'
        value={(answer.answer as string) ?? ''}
        onChange={(e) => onAnswer({ answer: e.target.value })}
        className='mx-1 inline border-0 border-b-2 border-slate-800 bg-transparent text-center text-[14px] focus:border-blue-600 focus:outline-none'
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
}: Props) {
  const qType = question.question_type
  const content = question.content

  // ── Legacy single-Q table completion (gap_fill + content.table, no table_id)
  if (qType === 'gap_fill' && content.table && !content.table_id) {
    return (
      <div className='space-y-3'>
        {!!content.question && (
          <p className='text-[15px] font-[500] leading-7 text-slate-900'>
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

    if (maxChoices > 1) {
      const selected = (answer.answer as string[]) ?? []
      const toggle = (opt: string) => {
        const next = selected.includes(opt)
          ? selected.filter((s) => s !== opt)
          : selected.length < maxChoices
            ? [...selected, opt]
            : selected
        onAnswer({ answer: next })
      }
      return (
        <div className='space-y-3'>
          <div className='space-y-1'>
            <p className='text-[16px] font-bold text-slate-900'>
              {question.order}
            </p>
            <p className='text-[15px] font-[500] text-slate-900'>
              {questionText}
            </p>
            <p className='text-[13px] text-slate-500'>
              Choose {maxChoices === 2 ? 'TWO' : maxChoices} letters,{' '}
              {String.fromCharCode(65)}–
              {String.fromCharCode(64 + options.length)}.
            </p>
          </div>
          <div className='space-y-2'>
            {options.map((opt, i) => {
              const id = `${question.id}-chk-${i}`
              const checked = selected.includes(opt)
              return (
                <div
                  key={i}
                  className={cn(
                    'flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 text-[15px] transition-colors',
                    checked
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 hover:bg-slate-50',
                  )}
                  onClick={() => toggle(opt)}
                >
                  <Checkbox
                    id={id}
                    checked={checked}
                    onCheckedChange={() => toggle(opt)}
                  />
                  <Label
                    htmlFor={id}
                    className='cursor-pointer font-normal text-slate-800'
                  >
                    <span className='mr-1 font-semibold'>
                      {String.fromCharCode(65 + i)}.
                    </span>{' '}
                    {opt}
                  </Label>
                </div>
              )
            })}
          </div>
        </div>
      )
    }

    // Standard single-choice MCQ
    return (
      <div className='space-y-3'>
        <div className='space-y-1'>
          <p className='text-[16px] font-bold text-slate-900'>
            {question.order}
          </p>
          <p className='text-[15px] font-[500] leading-6 text-slate-900'>
            {questionText}
          </p>
        </div>
        <RadioGroup
          value={(answer.answer as string) ?? ''}
          onValueChange={(v) => onAnswer({ answer: v })}
          className='space-y-2'
        >
          {options.map((opt, i) => {
            const id = `${question.id}-${i}`
            const isSelected = answer.answer === opt
            return (
              <div
                key={i}
                className={cn(
                  'flex cursor-pointer items-start gap-3 rounded-lg border px-4 py-2.5 text-[15px] transition-colors',
                  isSelected
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-slate-200 hover:bg-slate-50',
                )}
                onClick={() => onAnswer({ answer: opt })}
              >
                <RadioGroupItem value={opt} id={id} className='mt-0.5' />
                <Label
                  htmlFor={id}
                  className='cursor-pointer font-normal text-slate-800'
                >
                  <span className='mr-1 font-semibold'>
                    {String.fromCharCode(65 + i)}.
                  </span>{' '}
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
        <p className='text-[15px] font-[500] leading-7 text-slate-900'>
          <span className={cn(chip, 'mr-1.5')}>{question.order}</span>
          {content.statement as string}
        </p>
        <RadioGroup
          value={(answer.answer as string) ?? ''}
          onValueChange={(v) => onAnswer({ answer: v })}
          className='flex gap-2'
        >
          {opts.map((opt) => {
            const id = `${question.id}-${opt}`
            const selected = answer.answer === opt
            return (
              <div
                key={opt}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 transition-colors',
                  selected
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-slate-200 hover:bg-slate-50',
                )}
                onClick={() => onAnswer({ answer: opt })}
              >
                <RadioGroupItem value={opt} id={id} />
                <Label
                  htmlFor={id}
                  className='cursor-pointer text-[12px] font-semibold uppercase tracking-wide text-slate-700'
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
        <p className='text-[15px] font-[500] leading-7 text-slate-900'>
          <span className={cn(chip, 'mr-1.5')}>{question.order}</span>
          {content.statement as string}
        </p>
        <RadioGroup
          value={(answer.answer as string) ?? ''}
          onValueChange={(v) => onAnswer({ answer: v })}
          className='flex gap-2'
        >
          {opts.map((opt) => {
            const id = `${question.id}-${opt}`
            const selected = answer.answer === opt
            return (
              <div
                key={opt}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 transition-colors',
                  selected
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-slate-200 hover:bg-slate-50',
                )}
                onClick={() => onAnswer({ answer: opt })}
              >
                <RadioGroupItem value={opt} id={id} />
                <Label
                  htmlFor={id}
                  className='cursor-pointer text-[12px] font-semibold uppercase tracking-wide text-slate-700'
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
          <p className='text-[15px] font-[500] leading-8 text-slate-900'>
            <span className={cn(chip, 'mr-1.5')}>{question.order}</span>
            {parts[0]}
            <input
              type='text'
              value={studentAnswer}
              onChange={(e) => onAnswer({ answer: e.target.value })}
              className={cn(
                'mx-1 inline border-0 border-b-2 bg-transparent text-center text-[14px] focus:outline-none',
                overLimit ? 'border-red-500' : 'border-slate-800 focus:border-blue-600',
              )}
              style={{ width: '9rem', verticalAlign: 'baseline' }}
              placeholder='...'
            />
            {parts.slice(1).join('')}
          </p>
          <p className={cn('text-[11px]', overLimit ? 'font-semibold text-red-500' : 'text-slate-400')}>
            {wordCount} / {maxWords} word{maxWords !== 1 ? 's' : ''}
            {overLimit && ' — too many words'}
          </p>
        </div>
      )
    }

    return (
      <div className='space-y-2'>
        <p className='text-[15px] font-[500] leading-7 text-slate-900'>
          <span className={cn(chip, 'mr-1.5')}>{question.order}</span>
          {prompt}
        </p>
        <input
          type='text'
          value={studentAnswer}
          onChange={(e) => onAnswer({ answer: e.target.value })}
          className={cn(
            'w-full rounded border px-3 py-1.5 text-[14px] focus:outline-none',
            overLimit
              ? 'border-red-400 focus:border-red-500'
              : 'border-slate-300 focus:border-blue-500',
          )}
          placeholder='Your answer...'
        />
        <p className={cn('text-[11px]', overLimit ? 'font-semibold text-red-500' : 'text-slate-400')}>
          {wordCount} / {maxWords} word{maxWords !== 1 ? 's' : ''}
          {overLimit && ' — too many words'}
        </p>
      </div>
    )
  }

  // ── Gap fill ─────────────────────────────────────────────────────────────
  if (qType === 'gap_fill') {
    return (
      <GapFillInline question={question} answer={answer} onAnswer={onAnswer} />
    )
  }

  // ── Matching / Map labeling ──────────────────────────────────────────────
  if (qType === 'matching' || qType === 'map_labeling') {
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
        <div className='space-y-1'>
          <p className='text-[16px] font-bold text-slate-900'>
            {question.order}
          </p>
          <p className='text-[15px] font-[500] text-slate-900'>
            {questionText}
          </p>
        </div>
        {!!content.image_url && (
          <img
            src={content.image_url as string}
            alt='Map'
            className='max-h-64 rounded-md border border-slate-200'
          />
        )}
        <div className='space-y-3'>
          {left.map((item) => (
            <div key={item} className='flex items-center gap-3'>
              <span className='w-40 text-sm text-slate-700'>{item}</span>
              <Select
                value={currentPairs[item] ?? ''}
                onValueChange={(v) =>
                  onAnswer({ answer: { ...currentPairs, [item]: v } })
                }
              >
                <SelectTrigger className='w-48 text-sm'>
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
    const selected: string[] = Array.isArray(answer.answer)
      ? (answer.answer as string[])
      : []

    const toggle = (opt: string) => {
      const next = selected.includes(opt)
        ? selected.filter((s) => s !== opt)
        : [...selected, opt]
      onAnswer({ answer: next })
    }

    return (
      <div className='space-y-3'>
        <div className='space-y-1'>
          <p className='text-[16px] font-bold text-slate-900'>{question.order}</p>
          {questionText && (
            <p className='text-[15px] font-[500] leading-6 text-slate-900'>{questionText}</p>
          )}
          <p className='text-[13px] text-slate-500'>
            Choose the correct letters. More than one answer may be correct.
          </p>
        </div>
        <div className='space-y-2'>
          {options.map((opt, i) => {
            const id = `${question.id}-ms-${i}`
            const checked = selected.includes(opt)
            return (
              <div
                key={i}
                className={cn(
                  'flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 text-[15px] transition-colors',
                  checked
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-slate-200 hover:bg-slate-50',
                )}
                onClick={() => toggle(opt)}
              >
                <Checkbox
                  id={id}
                  checked={checked}
                  onCheckedChange={() => toggle(opt)}
                />
                <Label htmlFor={id} className='cursor-pointer font-normal text-slate-800'>
                  <span className='mr-1 font-semibold'>{String.fromCharCode(65 + i)}.</span>{' '}
                  {opt}
                </Label>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className='text-sm text-slate-400'>
      Question type "{qType}" (#{question.order})
    </div>
  )
}

// ── Matching Headings compound renderer ──────────────────────────────────────
// Group-level: left = paragraph labels (content.question), right = headings list
// (from group.options_shared). Headings always visible on right.

export function MatchingHeadingsRenderer({
  questions,
  options,
  answers,
  onAnswer,
}: {
  questions: Question[]
  options: string[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
}) {
  const prefixes = options.map((opt) => {
    const dot = opt.indexOf('.')
    return dot > 0 ? opt.slice(0, dot).trim() : opt.trim()
  })

  return (
    <div className='space-y-4'>
      {/* Always-visible headings list */}
      {options.length > 0 && (
        <div className='rounded border border-slate-200 bg-slate-50 p-3'>
          <p className='mb-2 text-[12px] font-semibold uppercase tracking-wide text-slate-500'>
            List of Headings
          </p>
          <ol className='space-y-1'>
            {options.map((opt, i) => (
              <li key={i} className='text-[13px] text-slate-700'>
                {opt}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Paragraph rows */}
      <div className='space-y-3'>
        {questions.map((q) => {
          const label = (q.content.question as string) ?? `Question ${q.order}`
          const currentVal = (answers[q.id]?.answer as string) ?? ''
          return (
            <div key={q.id} className='flex items-center gap-3'>
              <span className={chip}>{q.order}</span>
              <span className='w-36 shrink-0 text-[13px] font-medium text-slate-800'>{label}</span>
              <select
                value={currentVal}
                onChange={(e) => onAnswer(q.id, { answer: e.target.value })}
                className='flex-1 rounded border border-slate-300 bg-white px-2 py-1 text-[13px] text-slate-800 focus:border-blue-500 focus:outline-none'
              >
                <option value=''>— select —</option>
                {options.map((opt, i) => (
                  <option key={i} value={prefixes[i]}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Matching Information / Features compound renderer ─────────────────────────
// Shows a "List of Sections/People" plate with all options, then one statement
// per row with a letter/prefix dropdown.

export function MatchingLetterRenderer({
  questions,
  options,
  answers,
  onAnswer,
  listTitle = 'List of Options',
  repeatable = true,
}: {
  questions: Question[]
  options: string[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  listTitle?: string
  repeatable?: boolean
}) {
  const prefixes = options.map((opt) => {
    const dot = opt.indexOf('.')
    return dot > 0 ? opt.slice(0, dot).trim() : opt.trim()
  })

  return (
    <div className='space-y-4'>
      {/* Options plate */}
      {options.length > 0 && (
        <div className='rounded border border-slate-200 bg-slate-50 p-3'>
          <p className='mb-2 text-[12px] font-semibold uppercase tracking-wide text-slate-500'>
            {listTitle}
          </p>
          <div className='flex flex-wrap gap-x-6 gap-y-1'>
            {options.map((opt, i) => (
              <span key={i} className='text-[13px] text-slate-700'>
                {opt}
              </span>
            ))}
          </div>
          {repeatable && (
            <p className='mt-2 text-[11px] italic text-slate-500'>
              NB: You may use any letter more than once.
            </p>
          )}
        </div>
      )}

      {/* Statement rows */}
      <div className='space-y-3'>
        {questions.map((q) => {
          const statement = (q.content.question as string) ?? `Question ${q.order}`
          const currentVal = (answers[q.id]?.answer as string) ?? ''
          return (
            <div key={q.id} className='flex items-start gap-3'>
              <span className={`${chip} mt-0.5`}>{q.order}</span>
              <span className='flex-1 text-[14px] text-slate-800'>{statement}</span>
              <select
                value={currentVal}
                onChange={(e) => onAnswer(q.id, { answer: e.target.value })}
                className='rounded border border-slate-300 bg-white px-2 py-1 text-[13px] text-slate-800 focus:border-blue-500 focus:outline-none'
              >
                <option value=''>—</option>
                {prefixes.map((prefix, i) => (
                  <option key={i} value={prefix}>
                    {prefix}
                  </option>
                ))}
              </select>
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
  const { onToggleFlag, flagged } = props
  return (
    <div className='relative'>
      {onToggleFlag && (
        <button
          type='button'
          onClick={onToggleFlag}
          title={flagged ? 'Remove flag' : 'Flag for review'}
          className={cn(
            'absolute right-0 top-0 z-10 rounded p-1 transition-colors',
            flagged
              ? 'text-amber-500 hover:text-amber-600'
              : 'text-slate-300 hover:text-amber-400',
          )}
        >
          <Flag className='size-4' />
        </button>
      )}
      <QuestionRenderer {...props} />
    </div>
  )
}
