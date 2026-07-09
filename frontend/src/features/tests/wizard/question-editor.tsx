import { useRef, useState } from 'react'
import { ImageIcon, Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { uploadImage } from '@/lib/api/attempts'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { AlertTriangle } from 'lucide-react'
import { QUESTION_TYPE_LABELS, optionPrefix, type QuestionType } from '../data/schema'

export type QuestionDraft = {
  /** undefined = new question not yet saved */
  id?: string
  order: number
  question_type: QuestionType
  content: Record<string, unknown>
  answer_key: Record<string, unknown> | null
}

type Props = {
  question: QuestionDraft
  questionNumber: number
  allowedTypes: QuestionType[]
  /** Parsed options array from the parent group (for matching subtypes) */
  sharedOptions?: string[]
  /**
   * When set, the component is inside a QuestionGroup.
   * The Type dropdown is hidden and fields are rendered according to this type,
   * not question.question_type.
   */
  groupType?: QuestionType | null
  onChange: (q: QuestionDraft) => void
  onDelete: () => void
}

export function QuestionEditor({
  question,
  questionNumber,
  allowedTypes,
  sharedOptions,
  groupType,
  onChange,
  onDelete,
}: Props) {
  const handleTypeChange = (type: QuestionType) => {
    onChange({ ...question, question_type: type, content: {}, answer_key: null })
  }

  // When inside a group, fields are driven by groupType regardless of the stored question type
  const effectiveType: QuestionType = groupType ?? question.question_type
  const hasMismatch = groupType != null && question.question_type !== groupType

  // Show Type dropdown only when NOT in a group and more than one option available
  const showTypeDropdown = groupType == null && allowedTypes.length > 1
  // Always show Order input so teachers can reorder; hide only Type Select inside groups
  const showOrderInput = groupType != null || allowedTypes.length > 1

  return (
    <div className='rounded-lg border border-slate-200 bg-white p-4'>
      <div className='mb-3 flex items-center justify-between gap-3'>
        <span className='flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white'>
          {questionNumber}
        </span>
        {showTypeDropdown && (
          <div className='flex-1'>
            <Select value={question.question_type} onValueChange={handleTypeChange}>
              <SelectTrigger className='h-8 w-44 text-sm'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {allowedTypes.map((t) => (
                  <SelectItem key={t} value={t}>
                    {QUESTION_TYPE_LABELS[t]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        {showOrderInput && (
          <div className='flex items-center gap-1.5'>
            <Label className='text-xs text-slate-500'>Order</Label>
            <Input
              type='number'
              min={1}
              value={question.order}
              onChange={(e) => onChange({ ...question, order: Number(e.target.value) })}
              className='h-8 w-16 text-sm [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
            />
          </div>
        )}
        <Button variant='ghost' size='icon' className='size-8 text-destructive' onClick={onDelete}>
          <Trash2 className='size-4' />
        </Button>
      </div>

      {hasMismatch && (
        <div className='mb-3 flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800'>
          <AlertTriangle className='mt-0.5 size-3.5 shrink-0' />
          <span>
            Type mismatch — stored as <strong>{QUESTION_TYPE_LABELS[question.question_type] ?? question.question_type}</strong>,
            will be normalised to group type <strong>{QUESTION_TYPE_LABELS[groupType!]}</strong> on save.
          </span>
        </div>
      )}

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
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
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
    case 'map_labeling':
      return (
        <MatchingFields
          content={question.content}
          answerKey={question.answer_key}
          onContentChange={setContent}
          onAnswerKeyChange={setAnswer}
          isMapLabeling={question.question_type === 'map_labeling'}
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
      return <EssayFields content={question.content} onContentChange={setContent} />
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

      {sharedOptions.length > 0 ? (
        <div className='space-y-1.5'>
          <Label className='text-xs'>Correct answer</Label>
          <Select value={correctPrefix} onValueChange={(v) => onAnswerKeyChange({ correct: v })}>
            <SelectTrigger className='w-full text-sm'>
              <SelectValue placeholder='Select answer...' />
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
      ) : (
        <div className='space-y-1.5'>
          <Label className='text-xs'>Correct answer (prefix)</Label>
          <Input
            value={correctPrefix}
            onChange={(e) => onAnswerKeyChange({ correct: e.target.value })}
            placeholder={questionType === 'matching_headings' ? 'e.g. iii' : 'e.g. A'}
          />
          <p className='text-[11px] text-slate-400'>Save Group Settings first to load options dropdown.</p>
        </div>
      )}
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

/* ── MCQ ── */
function McqFields({ content, answerKey, onContentChange, onAnswerKeyChange }: FieldProps) {
  const rawOpts = content.options
  const options: string[] = Array.isArray(rawOpts) ? rawOpts : ['', '', '', '']
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
          value={(answerKey?.correct as string) ?? ''}
          onValueChange={(v) => onAnswerKeyChange({ correct: v })}
        >
          <SelectTrigger className='w-full'>
            <SelectValue placeholder='Select correct option...' />
          </SelectTrigger>
          <SelectContent>
            {options.filter((o: string) => o.trim()).map((opt: string) => (
              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

/* ── Multi Select ── */
function MultiSelectFields({ content, answerKey, onContentChange, onAnswerKeyChange }: FieldProps) {
  const rawOpts = content.options
  const options: string[] = Array.isArray(rawOpts) ? rawOpts : ['', '', '', '', '']
  const rawCorrect = answerKey?.correct
  const correct: string[] = Array.isArray(rawCorrect) ? rawCorrect : rawCorrect ? [String(rawCorrect)] : []
  const chooseN = (content.choose_n as number) ?? 2

  const toggleCorrect = (opt: string) => {
    const next = correct.includes(opt) ? correct.filter((c) => c !== opt) : [...correct, opt]
    onAnswerKeyChange({ correct: next })
  }

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Question / Instruction</Label>
        <Textarea
          rows={2}
          value={(content.question as string) ?? ''}
          onChange={(e) => onContentChange({ ...content, question: e.target.value })}
          placeholder='Which THREE items are mentioned in the passage?'
        />
      </div>
      <div className='flex items-center gap-3'>
        <Label className='text-xs'>Students choose</Label>
        <Input
          type='number'
          min={2}
          max={5}
          value={chooseN}
          onChange={(e) => onContentChange({ ...content, choose_n: Number(e.target.value) })}
          className='h-8 w-16 text-sm'
        />
        <span className='text-xs text-slate-500'>answers</span>
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Options (tick correct ones)</Label>
        {options.map((opt: string, i: number) => (
          <div key={i} className='flex items-center gap-2'>
            <Checkbox
              checked={correct.includes(opt) && opt.trim() !== ''}
              onCheckedChange={() => opt.trim() && toggleCorrect(opt)}
            />
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

/* ── Matching / Map Labeling ── */
function MatchingFields({
  content, answerKey, onContentChange, onAnswerKeyChange, isMapLabeling,
}: FieldProps & { isMapLabeling: boolean }) {
  const rawLeft = content.left
  const left: string[] = Array.isArray(rawLeft) ? rawLeft : ['']
  const rawRight = content.right
  const right: string[] = Array.isArray(rawRight) ? rawRight : ['']
  const pairs = (answerKey?.correct as Record<string, string>) ?? {}

  return (
    <div className='space-y-3'>
      {isMapLabeling && (
        <div className='space-y-1.5'>
          <Label className='text-xs'>Image URL</Label>
          <Input
            value={(content.image_url as string) ?? ''}
            onChange={(e) => onContentChange({ ...content, image_url: e.target.value })}
            placeholder='https://...'
          />
        </div>
      )}
      <div className='grid grid-cols-2 gap-3'>
        <div className='space-y-1.5'>
          <Label className='text-xs'>{isMapLabeling ? 'Labels' : 'Left column'}</Label>
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
          <Label className='text-xs'>{isMapLabeling ? 'Locations' : 'Right column'}</Label>
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
            <span className='text-slate-400'>→</span>
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
          <p className='text-[11px] text-slate-400'>Use ____ to mark the blank that students must fill.</p>
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
        <span className='text-xs text-slate-500'>words</span>
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
  onContentChange,
}: {
  content: Record<string, unknown>
  onContentChange: (c: Record<string, unknown>) => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const taskType = (content.task_type as string) ?? 'task_1'
  const imageUrl = content.image_url as string | undefined
  // Backend serves /media/... files; prefix with the API origin for the browser
  const displayImageUrl = imageUrl?.startsWith('/')
    ? `${import.meta.env.VITE_API_URL}${imageUrl}`
    : imageUrl

  const handleImage = async (file: File) => {
    setUploading(true)
    try {
      const url = await uploadImage(file)
      onContentChange({ ...content, image_url: url })
      toast.success('Image uploaded')
    } catch {
      toast.error('Failed to upload image')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Task type</Label>
        <Select
          value={taskType}
          onValueChange={(v) =>
            onContentChange({ ...content, task_type: v, min_words: v === 'task_1' ? 150 : 250 })
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='task_1'>Task 1 — Report / Letter (min 150 words)</SelectItem>
            <SelectItem value='task_2'>Task 2 — Essay (min 250 words)</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs'>Prompt</Label>
        <Textarea
          rows={5}
          value={(content.prompt as string) ?? ''}
          onChange={(e) => onContentChange({ ...content, prompt: e.target.value })}
          placeholder={taskType === 'task_1'
            ? 'The chart below shows the percentage of...'
            : 'Some people think that governments should spend more money on public transport...'}
        />
      </div>
      {taskType === 'task_1' && (
        <div className='space-y-1.5'>
          <Label className='text-xs'>Chart / Diagram</Label>
          <input
            ref={fileRef}
            type='file'
            accept='image/*'
            className='hidden'
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleImage(f) }}
          />
          {imageUrl ? (
            <div className='group relative w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-50'>
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
                  onClick={() => onContentChange({ ...content, image_url: undefined })}
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
              className='flex w-full cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-slate-400 transition-colors hover:border-slate-400 hover:bg-slate-100 hover:text-slate-600 disabled:cursor-not-allowed disabled:opacity-60'
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
      <div className='flex items-center gap-3'>
        <Label className='text-xs'>Min words</Label>
        <Input
          type='number'
          min={50}
          value={(content.min_words as number) ?? (taskType === 'task_1' ? 150 : 250)}
          onChange={(e) => onContentChange({ ...content, min_words: Number(e.target.value) })}
          className='h-8 w-20 text-sm [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
        />
      </div>
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
