import { useRef, useState } from 'react'
import { Eye, ImageIcon, Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { uploadImage } from '@/lib/api/attempts'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { QUESTION_TYPE_LABELS, groupAllowedTypes, optionPrefix, type QuestionType } from '../data/schema'
import {
  multiSelectCorrectLetters,
  multiSelectValidationError,
} from '../data/multi-select'
import { getDefaultInstruction, getDefaultQuestion } from '../data/writing-presets'

const ESSAY_TYPE_OPTIONS = [
  { value: '__none__', label: 'Not specified', hint: 'General essay evaluation criteria will be used.' },
  {
    value: 'opinion',
    label: 'Opinion (Agree/Disagree)',
    hint: 'Student must take a clear side (agree or disagree) and justify with reasons and examples.',
  },
  {
    value: 'discussion',
    label: 'Discussion (Both views + opinion)',
    hint: 'Student must discuss both views fairly, then give their own opinion with reasoning.',
  },
  {
    value: 'problem_solution',
    label: 'Problem & Solution',
    hint: 'Student must address both problems and practical solutions.',
  },
  {
    value: 'advantages_disadvantages',
    label: 'Advantages & Disadvantages',
    hint: 'Student must present both advantages and disadvantages; may need to give a verdict.',
  },
  {
    value: 'double_question',
    label: 'Double Question',
    hint: 'Student must directly answer both questions from the prompt with equal depth.',
  },
] as const

export type QuestionDraft = {
  /** undefined = new question not yet saved */
  id?: string
  order: number
  question_type: QuestionType
  content: Record<string, unknown>
  answer_key: Record<string, unknown> | null
  /** Writing essay columns (null/undefined for other types) */
  task_number?: number | null
  min_words?: number | null
  image_url?: string | null
  essay_type?: string | null
}

type Props = {
  question: QuestionDraft
  questionNumber: number
  /** Inclusive end for multi_select spanning multiple IELTS numbers */
  questionNumberEnd?: number
  allowedTypes: QuestionType[]
  /** Parsed options array from the parent group (for matching subtypes) */
  sharedOptions?: string[]
  /**
   * When set, the component is inside a QuestionGroup.
   * The Type dropdown is hidden and fields are rendered according to this type,
   * not question.question_type.
   */
  groupType?: QuestionType | null
  /** When false, the delete button is hidden (e.g. fixed writing tasks). */
  hideDelete?: boolean
  onChange: (q: QuestionDraft) => void
  onDelete: () => void
}

export function QuestionEditor({
  question,
  questionNumber,
  questionNumberEnd,
  allowedTypes,
  sharedOptions,
  groupType,
  hideDelete = false,
  onChange,
  onDelete,
}: Props) {
  const handleTypeChange = (type: QuestionType) => {
    if (type === 'multi_select') {
      onChange({
        ...question,
        question_type: type,
        content: { choose_n: 2, options: ['', '', '', '', ''] },
        answer_key: { correct: [] },
      })
      return
    }
    onChange({ ...question, question_type: type, content: {}, answer_key: null })
  }

  // When inside a group, fields are driven by groupType regardless of the stored question type
  const effectiveType: QuestionType = groupType ?? question.question_type

  // Show Type dropdown only when NOT in a group and more than one option available
  const showTypeDropdown = groupType == null && allowedTypes.length > 1
  const displayNumbers =
    questionNumberEnd != null && questionNumberEnd !== questionNumber
      ? `Q${questionNumber}–${questionNumberEnd}`
      : `Q${questionNumber}`

  return (
    <div className='rounded-lg border border-border bg-card p-4'>
      <div className='mb-3 flex items-center justify-between gap-3'>
        {/* Local order badge — never the IELTS display range */}
        <span className='flex h-7 min-w-7 shrink-0 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-semibold text-primary-foreground'>
          {question.order}
        </span>
        {showTypeDropdown && (
          <div className='flex-1'>
            <Select value={question.question_type} onValueChange={handleTypeChange}>
              <SelectTrigger className='h-8 w-44 text-sm'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {groupAllowedTypes(allowedTypes).map((g) => (
                  <SelectGroup key={g.label}>
                    <SelectLabel>{g.label}</SelectLabel>
                    {g.types.map((t) => (
                      <SelectItem key={t} value={t}>
                        {QUESTION_TYPE_LABELS[t]}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        {!hideDelete && (
          <Button variant='ghost' size='icon' className='size-8 text-destructive' onClick={onDelete}>
            <Trash2 className='size-4' />
          </Button>
        )}
      </div>

      <div className='mb-3 grid gap-3 sm:grid-cols-2'>
        <div className='space-y-1.5'>
          <Label className='text-xs'>Question order in group</Label>
          <Input
            type='number'
            min={1}
            className='h-8 w-24 text-sm'
            value={question.order}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (!Number.isFinite(n) || n < 1) return
              onChange({ ...question, order: Math.floor(n) })
            }}
          />
        </div>
        <div className='space-y-1.5'>
          <Label className='text-xs'>Question numbers</Label>
          <p className='flex h-8 items-center text-sm font-medium text-foreground'>
            {displayNumbers}
          </p>
          <p className='text-[11px] text-muted-foreground'>
            IELTS display number (section offset + cumulative slots across
            groups)
            {effectiveType === 'multi_select' ? '; multi_select spans N slots' : ''}
          </p>
        </div>
      </div>

      <QuestionTypeFields
        question={{ ...question, question_type: effectiveType }}
        sharedOptions={sharedOptions}
        onChange={onChange}
      />
    </div>
  )
}

/* ── per-type field dispatcher ── */

function QuestionTypeFields({
  question,
  sharedOptions,
  onChange,
}: {
  question: QuestionDraft
  sharedOptions?: string[]
  onChange: (q: QuestionDraft) => void
}) {
  const setContent = (content: Record<string, unknown>) => onChange({ ...question, content })
  const setAnswer = (answer_key: Record<string, unknown> | null) => onChange({ ...question, answer_key })

  switch (question.question_type) {
    case 'true_false_ng':
      return (
        <TrueFalseNgFields
          content={question.content}
          answerKey={question.answer_key}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'mcq':
      return (
        <McqFields
          content={question.content}
          answerKey={question.answer_key}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'multi_select':
      return (
        <MultiSelectFields
          content={question.content}
          answerKey={question.answer_key}
          onChange={(content, answer_key) =>
            onChange({ ...question, content, answer_key })
          }
        />
      )
    case 'gap_fill':
      return (
        <GapFillFields
          content={question.content}
          answerKey={question.answer_key}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'matching':
      return (
        <MatchingFields
          content={question.content}
          answerKey={question.answer_key}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'map_labeling':
      return (
        <MapLabelingFields
          content={question.content}
          answerKey={question.answer_key}
          sharedOptions={sharedOptions ?? []}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'matching_headings':
    case 'matching_information':
    case 'matching_features':
      return (
        <MatchingSubtypeFields
          content={question.content}
          answerKey={question.answer_key}
          sharedOptions={sharedOptions ?? []}
          questionType={question.question_type}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'yes_no_ng':
      return (
        <YesNoNgFields
          content={question.content}
          answerKey={question.answer_key}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'sentence_completion':
    case 'short_answer':
      return (
        <TextAnswerFields
          content={question.content}
          answerKey={question.answer_key}
          questionType={question.question_type}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
        />
      )
    case 'essay':
      return (
        <EssayFields
          content={question.content}
          taskNumber={question.task_number}
          imageUrl={question.image_url}
          essayType={question.essay_type}
          onContentChange={setContent}
          onImageUrlChange={(image_url) => onChange({ ...question, image_url })}
          onEssayTypeChange={(essay_type) => onChange({ ...question, essay_type })}
        />
      )
    case 'speaking_part':
      return <SpeakingFields content={question.content} onContentChange={setContent} />
    default:
      return null
  }
}

/* ── shared field props ── */
type FieldProps = {
  content: Record<string, unknown>
  answerKey: Record<string, unknown> | null
  onContentChange: (c: Record<string, unknown>) => void
  onAnswerKeyChange: (a: Record<string, unknown> | null) => void
}

/* ── Matching Headings / Information / Features ── */
function MatchingSubtypeFields({
  content,
  answerKey,
  sharedOptions,
  questionType,
  onContentChange,
  onAnswerKeyChange,
}: FieldProps & { sharedOptions: string[]; questionType: string }) {
  const questionLabel =
    questionType === 'matching_headings'
      ? 'Paragraph label (e.g. Paragraph A)'
      : 'Statement'

  const prefixes = sharedOptions.map(optionPrefix)
  const correctPrefix = (answerKey?.correct as string) ?? ''

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>{questionLabel}</Label>
        <Input
          value={(content.question as string) ?? ''}
          onChange={(e) => onContentChange({ ...content, question: e.target.value })}
          placeholder={questionType === 'matching_headings' ? 'Paragraph A' : 'The researcher who...'}
        />
      </div>

      <div className='space-y-1.5'>
        <Label className='text-xs'>Correct answer</Label>
        <Select
          value={correctPrefix}
          onValueChange={(v) => onAnswerKeyChange({ correct: v })}
          disabled={sharedOptions.length === 0}
        >
          <SelectTrigger className='w-full text-sm'>
            <SelectValue placeholder={sharedOptions.length === 0 ? 'Add options above first' : 'Select answer...'} />
          </SelectTrigger>
          <SelectContent>
            {sharedOptions.map((opt, i) => (
              <SelectItem key={i} value={prefixes[i]}>
                {opt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

/* ── True / False / Not Given ── */
function TrueFalseNgFields({ content, answerKey, onContentChange, onAnswerKeyChange }: FieldProps) {
  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Statement</Label>
        <Textarea
          rows={2}
          value={(content.statement as string) ?? ''}
          onChange={(e) =>
            onContentChange({ ...content, statement: e.target.value, options: ['True', 'False', 'Not Given'] })
          }
          placeholder='The author believes remote work is always better.'
        />
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Answer</Label>
        <Select
          value={(answerKey?.correct as string) ?? ''}
          onValueChange={(v) => onAnswerKeyChange({ correct: v })}
        >
          <SelectTrigger className='w-44'>
            <SelectValue placeholder='Select...' />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='True'>True</SelectItem>
            <SelectItem value='False'>False</SelectItem>
            <SelectItem value='Not Given'>Not Given</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

/** Return "A"–"Z" for a valid single-letter correct answer, or map legacy full-text to letter. */
function mcqCorrectLetter(raw: string, options: string[]): string {
  if (/^[A-Z]$/.test(raw)) return raw
  // Legacy: stored as full option text — find matching index
  const idx = options.findIndex((o) => o === raw)
  return idx >= 0 ? String.fromCharCode(65 + idx) : ''
}

/* ── MCQ ── */
function McqFields({ content, answerKey, onContentChange, onAnswerKeyChange }: FieldProps) {
  const rawOpts = content.options
  const options: string[] = Array.isArray(rawOpts) ? rawOpts : ['', '', '', '']
  const correctLetter = mcqCorrectLetter((answerKey?.correct as string) ?? '', options)

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Question</Label>
        <Textarea
          rows={2}
          value={(content.question as string) ?? ''}
          onChange={(e) => onContentChange({ ...content, question: e.target.value })}
          placeholder='What is the main topic?'
        />
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Options</Label>
        {options.map((opt: string, i: number) => (
          <div key={i} className='flex gap-2'>
            <span className='flex size-7 shrink-0 items-center justify-center rounded bg-muted text-xs font-medium'>
              {String.fromCharCode(65 + i)}
            </span>
            <Input
              value={opt}
              onChange={(e) => {
                const next = [...options]
                next[i] = e.target.value
                onContentChange({ ...content, options: next })
              }}
              placeholder={`Option ${String.fromCharCode(65 + i)}`}
            />
            {options.length > 2 && (
              <Button
                variant='ghost'
                size='icon'
                className='size-8'
                onClick={() =>
                  onContentChange({ ...content, options: options.filter((_: string, j: number) => j !== i) })
                }
              >
                <Trash2 className='size-3.5' />
              </Button>
            )}
          </div>
        ))}
        <Button
          variant='outline'
          size='sm'
          onClick={() => onContentChange({ ...content, options: [...options, ''] })}
        >
          <Plus className='size-3.5' /> Add Option
        </Button>
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Correct Answer</Label>
        <Select
          value={correctLetter}
          onValueChange={(v) => onAnswerKeyChange({ correct: v })}
        >
          <SelectTrigger className='w-full'>
            <SelectValue placeholder='Select correct option...' />
          </SelectTrigger>
          <SelectContent>
            {options.map((opt: string, i: number) => {
              if (!opt.trim()) return null
              const letter = String.fromCharCode(65 + i)
              return (
                <SelectItem key={letter} value={letter}>
                  <span className='font-semibold'>{letter}</span>
                  <span className='ml-1.5 text-muted-foreground'>— {opt}</span>
                </SelectItem>
              )
            })}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

/* ── Multi Select ── */

function MultiSelectFields({
  content,
  answerKey,
  onChange,
}: {
  content: Record<string, unknown>
  answerKey: Record<string, unknown> | null
  onChange: (
    content: Record<string, unknown>,
    answerKey: Record<string, unknown> | null,
  ) => void
}) {
  const rawOpts = content.options
  const options: string[] = Array.isArray(rawOpts)
    ? rawOpts
    : ['', '', '', '', '']
  const correctLetters = multiSelectCorrectLetters(answerKey, options)
  const chooseN =
    typeof content.choose_n === 'number' && content.choose_n >= 1
      ? content.choose_n
      : 2
  const validationError = multiSelectValidationError(
    { ...content, choose_n: chooseN, options },
    answerKey,
  )

  const toggleCorrect = (letter: string) => {
    const next = correctLetters.includes(letter)
      ? correctLetters.filter((c) => c !== letter)
      : [...correctLetters, letter]
    onChange({ ...content, options, choose_n: chooseN }, { correct: next })
  }

  const setChooseN = (n: number) => {
    const nextN = Math.min(5, Math.max(2, n))
    const nextCorrect =
      correctLetters.length > nextN
        ? correctLetters.slice(0, nextN)
        : correctLetters
    onChange(
      { ...content, options, choose_n: nextN },
      { correct: nextCorrect },
    )
  }

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Question / Instruction</Label>
        <Textarea
          rows={2}
          value={(content.question as string) ?? ''}
          onChange={(e) =>
            onChange(
              {
                ...content,
                options,
                choose_n: chooseN,
                question: e.target.value,
              },
              answerKey ?? { correct: [] },
            )
          }
          placeholder='Which TWO items are mentioned?'
        />
      </div>
      <div className='flex items-center gap-3'>
        <Label className='text-xs'>Students choose</Label>
        <Input
          type='number'
          min={2}
          max={5}
          value={chooseN}
          onChange={(e) => setChooseN(Number(e.target.value))}
          className='h-8 w-16 text-sm'
        />
        <span className='text-xs text-muted-foreground'>answers</span>
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Options (tick exactly {chooseN} correct)</Label>
        {options.map((opt: string, i: number) => {
          const letter = String.fromCharCode(65 + i)
          return (
            <div key={i} className='flex items-center gap-2'>
              <Checkbox
                checked={correctLetters.includes(letter)}
                onCheckedChange={() => toggleCorrect(letter)}
              />
              <span className='flex size-7 shrink-0 items-center justify-center rounded bg-muted text-xs font-medium'>
                {letter}
              </span>
              <Input
                value={opt}
                onChange={(e) => {
                  const next = [...options]
                  next[i] = e.target.value
                  onChange(
                    { ...content, choose_n: chooseN, options: next },
                    answerKey ?? { correct: [] },
                  )
                }}
                placeholder={`Option ${letter}`}
              />
              {options.length > 2 && (
                <Button
                  variant='ghost'
                  size='icon'
                  className='size-8'
                  onClick={() => {
                    const nextOpts = options.filter((_: string, j: number) => j !== i)
                    const nextCorrect = correctLetters
                      .filter((c) => c !== letter)
                      .map((c) => {
                        const code = c.charCodeAt(0) - 65
                        if (code > i) return String.fromCharCode(65 + code - 1)
                        return c
                      })
                    onChange(
                      { ...content, choose_n: chooseN, options: nextOpts },
                      { correct: nextCorrect },
                    )
                  }}
                >
                  <Trash2 className='size-3.5' />
                </Button>
              )}
            </div>
          )
        })}
        <Button
          variant='outline'
          size='sm'
          onClick={() =>
            onChange(
              {
                ...content,
                choose_n: chooseN,
                options: [...options, ''],
              },
              answerKey ?? { correct: [] },
            )
          }
        >
          <Plus className='size-3.5' /> Add Option
        </Button>
        {validationError && (
          <p className='text-xs text-destructive'>
            {validationError} (selected {correctLetters.length})
          </p>
        )}
      </div>
    </div>
  )
}

/* ── Gap Fill ── */
function GapFillFields({ content, answerKey, onContentChange, onAnswerKeyChange }: FieldProps) {
  const raw = answerKey?.correct
  const variants: string[] = Array.isArray(raw) ? raw : raw ? [String(raw)] : ['']
  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Text (use ___ for the blank)</Label>
        <Textarea
          rows={2}
          value={(content.text as string) ?? ''}
          onChange={(e) => onContentChange({ ...content, text: e.target.value })}
          placeholder='The meeting starts at ___ pm.'
        />
      </div>
      <div className='flex items-center gap-3'>
        <Label className='text-xs'>Max words</Label>
        <Input
          type='number'
          min={1}
          max={5}
          value={(content.max_words as number) ?? 1}
          onChange={(e) => onContentChange({ ...content, max_words: Number(e.target.value) })}
          className='h-8 w-16 text-sm'
        />
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Accepted answers</Label>
        {variants.map((v: string, i: number) => (
          <div key={i} className='flex gap-2'>
            <Input
              value={v}
              onChange={(e) => {
                const next = [...variants]
                next[i] = e.target.value
                onAnswerKeyChange({ correct: next })
              }}
              placeholder='Answer variant'
            />
            {variants.length > 1 && (
              <Button
                variant='ghost'
                size='icon'
                className='size-8'
                onClick={() => onAnswerKeyChange({ correct: variants.filter((_: string, j: number) => j !== i) })}
              >
                <Trash2 className='size-3.5' />
              </Button>
            )}
          </div>
        ))}
        <Button
          variant='outline'
          size='sm'
          onClick={() => onAnswerKeyChange({ correct: [...variants, ''] })}
        >
          <Plus className='size-3.5' /> Add Variant
        </Button>
      </div>
    </div>
  )
}

/* ── Matching ── */
function MatchingFields({
  content, answerKey, onContentChange, onAnswerKeyChange,
}: FieldProps) {
  const rawLeft = content.left
  const left: string[] = Array.isArray(rawLeft) ? rawLeft : ['']
  const rawRight = content.right
  const right: string[] = Array.isArray(rawRight) ? rawRight : ['']
  const pairs = (answerKey?.correct as Record<string, string>) ?? {}

  return (
    <div className='space-y-3'>
      <div className='grid grid-cols-2 gap-3'>
        <div className='space-y-1.5'>
          <Label className='text-xs'>Left column</Label>
          {left.map((item: string, i: number) => (
            <div key={i} className='flex gap-1.5'>
              <Input
                value={item}
                onChange={(e) => {
                  const next = [...left]; next[i] = e.target.value
                  onContentChange({ ...content, left: next })
                }}
              />
              {left.length > 1 && (
                <Button variant='ghost' size='icon' className='size-8'
                  onClick={() => onContentChange({ ...content, left: left.filter((_: string, j: number) => j !== i) })}>
                  <Trash2 className='size-3.5' />
                </Button>
              )}
            </div>
          ))}
          <Button variant='outline' size='sm' onClick={() => onContentChange({ ...content, left: [...left, ''] })}>
            <Plus className='size-3.5' /> Add
          </Button>
        </div>
        <div className='space-y-1.5'>
          <Label className='text-xs'>Right column</Label>
          {right.map((item: string, i: number) => (
            <div key={i} className='flex gap-1.5'>
              <Input
                value={item}
                onChange={(e) => {
                  const next = [...right]; next[i] = e.target.value
                  onContentChange({ ...content, right: next })
                }}
              />
              {right.length > 1 && (
                <Button variant='ghost' size='icon' className='size-8'
                  onClick={() => onContentChange({ ...content, right: right.filter((_: string, j: number) => j !== i) })}>
                  <Trash2 className='size-3.5' />
                </Button>
              )}
            </div>
          ))}
          <Button variant='outline' size='sm' onClick={() => onContentChange({ ...content, right: [...right, ''] })}>
            <Plus className='size-3.5' /> Add
          </Button>
        </div>
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Correct pairs (left → right)</Label>
        {left.filter((l: string) => l.trim()).map((l: string) => (
          <div key={l} className='flex items-center gap-2'>
            <span className='w-28 truncate text-xs font-medium'>{l}</span>
            <span className='text-muted-foreground'>→</span>
            <Select
              value={pairs[l] ?? ''}
              onValueChange={(v) => onAnswerKeyChange({ correct: { ...pairs, [l]: v } })}
            >
              <SelectTrigger className='flex-1 h-8 text-sm'>
                <SelectValue placeholder='Match to...' />
              </SelectTrigger>
              <SelectContent>
                {right.filter((r: string) => r.trim()).map((r: string) => (
                  <SelectItem key={r} value={r}>{r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── Map Labeling (per-question: location + correct letter) ── */
function MapLabelingFields({
  content, answerKey, sharedOptions, onContentChange, onAnswerKeyChange,
}: FieldProps & { sharedOptions: string[] }) {
  const location = (content.location as string) ?? ''
  const correct = (answerKey?.correct as string) ?? ''

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Location name</Label>
        <Input
          value={location}
          onChange={(e) => onContentChange({ ...content, location: e.target.value })}
          placeholder='e.g. School, Sports centre...'
        />
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Correct label</Label>
        <Select
          value={correct}
          onValueChange={(v) => onAnswerKeyChange({ correct: v })}
          disabled={sharedOptions.length === 0}
        >
          <SelectTrigger className='w-full text-sm'>
            <SelectValue placeholder={sharedOptions.length === 0 ? 'Add labels in group settings first' : 'Select label...'} />
          </SelectTrigger>
          <SelectContent>
            {sharedOptions.map((opt) => (
              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

/* ── Yes / No / Not Given ── */
function YesNoNgFields({ content, answerKey, onContentChange, onAnswerKeyChange }: FieldProps) {
  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Statement</Label>
        <Textarea
          rows={2}
          value={(content.statement as string) ?? ''}
          onChange={(e) =>
            onContentChange({ ...content, statement: e.target.value, options: ['Yes', 'No', 'Not Given'] })
          }
          placeholder='The company expanded its operations overseas.'
        />
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Answer</Label>
        <Select
          value={(answerKey?.correct as string) ?? ''}
          onValueChange={(v) => onAnswerKeyChange({ correct: v })}
        >
          <SelectTrigger className='w-44'>
            <SelectValue placeholder='Select...' />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='Yes'>Yes</SelectItem>
            <SelectItem value='No'>No</SelectItem>
            <SelectItem value='Not Given'>Not Given</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

/* ── Sentence Completion / Short Answer ── */
function TextAnswerFields({
  content,
  answerKey,
  questionType,
  onContentChange,
  onAnswerKeyChange,
}: FieldProps & { questionType: string }) {
  const raw = answerKey?.correct
  const variants: string[] = Array.isArray(raw) ? raw : raw ? [String(raw)] : ['']
  const isSentence = questionType === 'sentence_completion'

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>
          {isSentence ? 'Sentence (use ____ for the blank)' : 'Question'}
        </Label>
        <Textarea
          rows={2}
          value={(content.prompt as string) ?? ''}
          onChange={(e) => onContentChange({ ...content, prompt: e.target.value })}
          placeholder={
            isSentence
              ? 'The discovery was made in ____ by two researchers.'
              : 'Who was responsible for the discovery?'
          }
        />
        {isSentence && (
          <p className='text-[11px] text-muted-foreground'>Use ____ to mark the blank that students must fill.</p>
        )}
      </div>
      <div className='flex items-center gap-3'>
        <Label className='text-xs'>Max words</Label>
        <Input
          type='number'
          min={1}
          max={10}
          value={(content.max_words as number) ?? 3}
          onChange={(e) => onContentChange({ ...content, max_words: Number(e.target.value) })}
          className='h-8 w-16 text-sm [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
        />
        <span className='text-xs text-muted-foreground'>words</span>
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Accepted answers</Label>
        {variants.map((v: string, i: number) => (
          <div key={i} className='flex gap-2'>
            <Input
              value={v}
              onChange={(e) => {
                const next = [...variants]
                next[i] = e.target.value
                onAnswerKeyChange({ correct: next })
              }}
              placeholder='Answer variant'
            />
            {variants.length > 1 && (
              <Button
                variant='ghost'
                size='icon'
                className='size-8'
                onClick={() => onAnswerKeyChange({ correct: variants.filter((_: string, j: number) => j !== i) })}
              >
                <Trash2 className='size-3.5' />
              </Button>
            )}
          </div>
        ))}
        <Button
          variant='outline'
          size='sm'
          onClick={() => onAnswerKeyChange({ correct: [...variants, ''] })}
        >
          <Plus className='size-3.5' /> Add Variant
        </Button>
      </div>
    </div>
  )
}

/* ── Essay ── */
function EssayFields({
  content,
  taskNumber,
  imageUrl,
  essayType,
  onContentChange,
  onImageUrlChange,
  onEssayTypeChange,
}: {
  content: Record<string, unknown>
  taskNumber?: number | null
  imageUrl?: string | null
  essayType?: string | null
  onContentChange: (c: Record<string, unknown>) => void
  onImageUrlChange: (url: string | null) => void
  onEssayTypeChange: (essayType: string | null) => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const isTask1 = taskNumber !== 2
  const isTask2 = taskNumber === 2
  const tNum = taskNumber === 2 ? 2 : 1
  const minWords = isTask2 ? 250 : 150
  const essaySelectValue = essayType ?? '__none__'
  const essayHint =
    ESSAY_TYPE_OPTIONS.find((o) => o.value === essaySelectValue)?.hint ??
    ESSAY_TYPE_OPTIONS[0].hint
  const displayImageUrl = imageUrl?.startsWith('/')
    ? `${import.meta.env.VITE_API_URL}${imageUrl}`
    : imageUrl ?? undefined

  const desc = (content.task_description as string | undefined) ?? (content.prompt as string | undefined) ?? ''
  const instr = (content.task_instruction as string | undefined) ?? ''
  const instrPreset = getDefaultInstruction(tNum, essayType)
  const [useCustomInstr, setUseCustomInstr] = useState(!!instr && instr !== instrPreset)

  const statement = (content.task_statement as string | undefined) ?? ''
  const question = (content.task_question as string | undefined) ?? ''
  const questionPreset = getDefaultQuestion(essayType) ?? ''
  const [useCustomQuestion, setUseCustomQuestion] = useState(
    (content.use_custom_question as boolean | undefined) ??
    (!!question && !!questionPreset && question !== questionPreset)
  )

  const rebuildContent = (patch: Record<string, unknown>) => {
    const merged = { ...content, ...patch }
    const curDesc = (merged.task_description as string) ?? desc
    const curInstr = (merged.task_instruction as string) ?? instr
    const curStmt = (merged.task_statement as string) ?? statement
    const curQ = (merged.task_question as string) ?? question
    if (isTask2 && curStmt) {
      merged.task_description = curQ ? `${curStmt}\n\n${curQ}` : curStmt
    }
    merged.prompt = `${(merged.task_description as string) ?? curDesc}\n\n${curInstr}`.trim()
    onContentChange(merged)
  }

  const handleImage = async (file: File) => {
    setUploading(true)
    try {
      const url = await uploadImage(file)
      onImageUrlChange(url)
      toast.success('Image uploaded')
    } catch {
      toast.error('Failed to upload image')
    } finally {
      setUploading(false)
    }
  }

  const handleEssayTypeChange = (v: string) => {
    const newType = v === '__none__' ? null : v
    onEssayTypeChange(newType)
    const patch: Record<string, unknown> = {}
    if (!useCustomInstr) {
      patch.task_instruction = getDefaultInstruction(tNum, newType)
    }
    if (!useCustomQuestion) {
      patch.task_question = getDefaultQuestion(newType) ?? ''
    }
    rebuildContent(patch)
  }

  const handleInstructionModeChange = (mode: string) => {
    if (mode === 'default') {
      setUseCustomInstr(false)
      rebuildContent({ task_instruction: instrPreset })
    } else {
      setUseCustomInstr(true)
    }
  }

  const handleQuestionModeChange = (mode: string) => {
    if (mode === 'default') {
      setUseCustomQuestion(false)
      rebuildContent({ task_question: questionPreset, use_custom_question: false })
    } else {
      setUseCustomQuestion(true)
      rebuildContent({ use_custom_question: true })
    }
  }

  return (
    <div className='space-y-3'>
      <div className='flex items-center gap-2'>
        <span className='text-xs font-medium text-foreground'>
          Task {tNum}
        </span>
        <span className='rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground'>
          min {minWords} words
        </span>
      </div>
      {isTask2 && (
        <div className='space-y-1.5'>
          <Label className='text-xs'>Essay Type</Label>
          <Select value={essaySelectValue} onValueChange={handleEssayTypeChange}>
            <SelectTrigger className='w-full'>
              <SelectValue placeholder='Not specified' />
            </SelectTrigger>
            <SelectContent>
              {ESSAY_TYPE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className='text-xs text-muted-foreground'>{essayHint}</p>
        </div>
      )}
      <div className='space-y-1.5'>
        <Label className='text-xs'>{isTask2 ? 'Statement' : 'Task Description'}</Label>
        <Textarea
          rows={isTask2 ? 3 : 5}
          value={isTask2 ? (statement || desc) : desc}
          onChange={(e) =>
            isTask2
              ? rebuildContent({ task_statement: e.target.value })
              : rebuildContent({ task_description: e.target.value })
          }
          placeholder={isTask1
            ? 'The chart below shows the percentage of...'
            : 'The most important aim of science should be to improve people\'s lives.'}
        />
      </div>
      {isTask2 && (
        <div className='space-y-1.5'>
          <div className='flex items-center justify-between'>
            <Label className='text-xs'>Question</Label>
            <Select
              value={useCustomQuestion ? 'custom' : 'default'}
              onValueChange={handleQuestionModeChange}
            >
              <SelectTrigger className='h-6 w-[170px] text-xs'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='default' className='text-xs'>Default (IELTS standard)</SelectItem>
                <SelectItem value='custom' className='text-xs'>Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Textarea
            rows={2}
            value={question || questionPreset}
            onChange={(e) => rebuildContent({ task_question: e.target.value })}
            readOnly={!useCustomQuestion}
            className={!useCustomQuestion ? 'cursor-default bg-muted text-xs text-muted-foreground' : 'text-xs'}
          />
        </div>
      )}
      <div className='space-y-1.5'>
        <div className='flex items-center justify-between'>
          <Label className='text-xs'>Instruction</Label>
          <Select
            value={useCustomInstr ? 'custom' : 'default'}
            onValueChange={handleInstructionModeChange}
          >
            <SelectTrigger className='h-6 w-[170px] text-xs'>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='default' className='text-xs'>Default (IELTS standard)</SelectItem>
              <SelectItem value='custom' className='text-xs'>Custom</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Textarea
          rows={2}
          value={instr || instrPreset}
          onChange={(e) => rebuildContent({ task_instruction: e.target.value })}
          readOnly={!useCustomInstr}
          className={!useCustomInstr ? 'cursor-default bg-muted text-xs text-muted-foreground' : 'text-xs'}
        />
      </div>
      {isTask1 && (
        <div className='space-y-1.5'>
          <Label className='text-xs'>Chart / Diagram</Label>
          <input
            ref={fileRef}
            type='file'
            accept='image/*'
            className='hidden'
            onChange={(e) => { const f = e.target.files?.[0]; if (f) void handleImage(f) }}
          />
          {imageUrl ? (
            <div className='group relative w-full overflow-hidden rounded-lg border border-border bg-muted'>
              <img
                src={displayImageUrl}
                alt='Chart / Diagram'
                className='mx-auto block max-h-64 w-full object-contain p-2'
              />
              <div className='absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 transition-opacity group-hover:opacity-100'>
                <Button
                  type='button'
                  size='sm'
                  variant='secondary'
                  onClick={() => window.open(displayImageUrl, '_blank')}
                >
                  <Eye className='mr-1 size-3.5' />
                  View
                </Button>
                <Button
                  type='button'
                  size='sm'
                  variant='secondary'
                  onClick={() => fileRef.current?.click()}
                  disabled={uploading}
                >
                  {uploading ? <Loader2 className='mr-1 size-3.5 animate-spin' /> : <ImageIcon className='mr-1 size-3.5' />}
                  Replace
                </Button>
                <Button
                  type='button'
                  size='sm'
                  variant='destructive'
                  onClick={() => onImageUrlChange(null)}
                >
                  <Trash2 className='mr-1 size-3.5' />
                  Remove
                </Button>
              </div>
            </div>
          ) : (
            <button
              type='button'
              disabled={uploading}
              onClick={() => fileRef.current?.click()}
              className='flex w-full cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed border-border bg-muted/50 px-4 py-8 text-muted-foreground transition-colors hover:border-primary/40 hover:bg-muted hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60'
            >
              {uploading
                ? <Loader2 className='size-6 animate-spin' />
                : <ImageIcon className='size-6' />}
              <span className='text-sm font-medium'>
                {uploading ? 'Uploading…' : 'Click to upload chart or diagram'}
              </span>
              <span className='text-xs'>PNG, JPG, GIF up to 10 MB</span>
            </button>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Speaking Part ── */
function SpeakingFields({
  content,
  onContentChange,
}: {
  content: Record<string, unknown>
  onContentChange: (c: Record<string, unknown>) => void
}) {
  const rawQs = content.questions
  const questions: string[] = Array.isArray(rawQs) ? rawQs : ['']
  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Part number</Label>
        <Select
          value={String((content.part as number) ?? 1)}
          onValueChange={(v) => onContentChange({ ...content, part: Number(v) })}
        >
          <SelectTrigger className='w-52'>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='1'>Part 1 — Introduction</SelectItem>
            <SelectItem value='2'>Part 2 — Cue Card</SelectItem>
            <SelectItem value='3'>Part 3 — Discussion</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {(content.part as number) === 2 && (
        <div className='space-y-1.5'>
          <Label className='text-xs'>Cue card text</Label>
          <Textarea
            rows={3}
            value={(content.cue_card as string) ?? ''}
            onChange={(e) => onContentChange({ ...content, cue_card: e.target.value })}
            placeholder='Describe a place you have visited...'
          />
        </div>
      )}
      <div className='space-y-1.5'>
        <Label className='text-xs'>Questions / Prompts</Label>
        {questions.map((q: string, i: number) => (
          <div key={i} className='flex gap-2'>
            <Input
              value={q}
              onChange={(e) => {
                const next = [...questions]; next[i] = e.target.value
                onContentChange({ ...content, questions: next })
              }}
              placeholder={`Question ${i + 1}`}
            />
            {questions.length > 1 && (
              <Button variant='ghost' size='icon' className='size-8'
                onClick={() =>
                  onContentChange({ ...content, questions: questions.filter((_: string, j: number) => j !== i) })
                }>
                <Trash2 className='size-3.5' />
              </Button>
            )}
          </div>
        ))}
        <Button variant='outline' size='sm'
          onClick={() => onContentChange({ ...content, questions: [...questions, ''] })}>
          <Plus className='size-3.5' /> Add Question
        </Button>
      </div>
    </div>
  )
}
