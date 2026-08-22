import { useCallback, useRef, useState } from 'react'
import { Eye, ImageIcon, Loader2, PenLine, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { uploadImage } from '@/lib/api/attempts'
import { apiErrorMessage } from '@/lib/api/error'
import { createQuestion, updateQuestion } from '@/lib/api/questions'
import { createSection } from '@/lib/api/sections'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { Question, Section, SectionSettings, Test } from '../data/schema'
import { getDefaultInstruction, getDefaultQuestion } from '../data/writing-presets'
import { SectionDurationField } from './section-duration-field'
import { EmptyState } from './ui/empty-state'

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

const DEFAULT_CUSTOM_OPTIONS = [
  { value: 'default', label: 'Default (IELTS standard)' },
  { value: 'custom', label: 'Custom' },
] as const

type Props = {
  test: Test | null
  sections: Section[]
  sectionSettings: SectionSettings[]
  questionsMap: Record<string, Question[]>
  onRefresh: () => void
}

type TaskDraft = {
  id?: string
  order: number
  taskDescription: string
  taskInstruction: string
  useCustomInstruction: boolean
  taskStatement: string
  taskQuestion: string
  useCustomQuestion: boolean
  imageUrl: string | null
  essayType: string | null
}

function loadDraft(q: Question | undefined, taskNum: number): TaskDraft {
  const content = q?.content ?? {}
  const desc =
    (content.task_description as string | undefined) ??
    (content.prompt as string | undefined) ??
    ''
  const instr = (content.task_instruction as string | undefined) ?? ''
  const instrPreset = getDefaultInstruction(taskNum, q?.essay_type)
  const isCustomInstr = !!instr && instr !== instrPreset

  const statement = (content.task_statement as string | undefined) ?? ''
  const question = (content.task_question as string | undefined) ?? ''
  const questionPreset = getDefaultQuestion(q?.essay_type) ?? ''
  const isCustomQuestion =
    (content.use_custom_question as boolean | undefined) ??
    (!!question && !!questionPreset && question !== questionPreset)

  return {
    id: q?.id,
    order: taskNum,
    taskDescription: taskNum === 2 && statement ? statement : desc,
    taskInstruction: instr || instrPreset,
    useCustomInstruction: isCustomInstr,
    taskStatement: statement || (taskNum === 2 ? desc : ''),
    taskQuestion: question || questionPreset,
    useCustomQuestion: isCustomQuestion,
    imageUrl:
      taskNum === 1
        ? (q?.image_url ?? (q?.content?.image_url as string | undefined) ?? null)
        : null,
    essayType: q?.essay_type ?? null,
  }
}

export function StepWriting({
  test,
  sections,
  sectionSettings,
  questionsMap,
  onRefresh,
}: Props) {
  const writingSection = sections.find((s) => s.type === 'writing')
  const [adding, setAdding] = useState(false)

  const handleAddWriting = useCallback(async () => {
    if (!test?.id) {
      toast.error('Test not loaded yet')
      return
    }
    setAdding(true)
    try {
      await createSection(test.id, { type: 'writing' })
      onRefresh()
      toast.success('Writing section added')
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Failed to add writing section'))
    } finally {
      setAdding(false)
    }
  }, [test?.id, onRefresh])

  if (!writingSection) {
    return (
      <EmptyState
        icon={PenLine}
        headline='No writing section yet'
        description='Add a Writing section to configure Task 1 and Task 2.'
        action={
          <Button onClick={() => void handleAddWriting()} disabled={adding || !test?.id}>
            {adding ? (
              <Loader2 className='mr-1.5 size-4 animate-spin' />
            ) : (
              <Plus className='mr-1.5 size-4' />
            )}
            Add Writing Section
          </Button>
        }
      />
    )
  }

  return (
    <WritingEditor
      section={writingSection}
      sectionSettings={sectionSettings}
      questionsMap={questionsMap}
      testType={test?.type ?? 'academic'}
      onRefresh={onRefresh}
    />
  )
}

function WritingEditor({
  section,
  sectionSettings,
  questionsMap,
  testType,
  onRefresh,
}: {
  section: Section
  sectionSettings: SectionSettings[]
  questionsMap: Record<string, Question[]>
  testType: string
  onRefresh: () => void
}) {
  const existing = questionsMap[section.id] ?? []
  const isAcademic = testType.toLowerCase() === 'academic'

  const findTask = (num: number): Question | undefined =>
    existing.find((q) => q.task_number === num) ??
    existing.find((q) => q.order === num)

  const [tasks, setTasks] = useState<TaskDraft[]>(() => [
    loadDraft(findTask(1), 1),
    loadDraft(findTask(2), 2),
  ])

  const [saving, setSaving] = useState([false, false])

  const handleSave = async (taskIdx: number) => {
    const draft = tasks[taskIdx]
    const taskNumber = taskIdx + 1
    setSaving((prev) => prev.map((v, i) => (i === taskIdx ? true : v)))
    try {
      const content: Record<string, unknown> = {}

      if (taskNumber === 2) {
        const fullDesc = draft.taskQuestion
          ? `${draft.taskStatement}\n\n${draft.taskQuestion}`
          : draft.taskStatement
        content.task_statement = draft.taskStatement
        content.task_question = draft.taskQuestion
        content.use_custom_question = draft.useCustomQuestion
        content.task_description = fullDesc
        content.task_instruction = draft.taskInstruction
        content.prompt = `${fullDesc}\n\n${draft.taskInstruction}`.trim()
      } else {
        content.task_description = draft.taskDescription
        content.task_instruction = draft.taskInstruction
        content.prompt = `${draft.taskDescription}\n\n${draft.taskInstruction}`.trim()
      }

      const payload = {
        order: draft.order,
        question_type: 'essay' as const,
        content,
        answer_key: null,
        task_number: taskNumber,
        min_words: taskNumber === 1 ? 150 : 250,
        image_url: taskIdx === 0 ? (draft.imageUrl ?? null) : null,
        essay_type: taskNumber === 2 ? (draft.essayType ?? null) : null,
      }

      let saved: Question
      if (draft.id) {
        saved = await updateQuestion(section.id, draft.id, payload)
      } else {
        saved = await createQuestion(section.id, payload)
      }

      setTasks((prev) =>
        prev.map((t, i) =>
          i === taskIdx
            ? {
                ...t,
                id: saved.id,
                imageUrl: saved.image_url ?? null,
                essayType: saved.essay_type ?? null,
              }
            : t
        )
      )
      toast.success(`Task ${taskNumber} saved`)
      onRefresh()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Failed to save task')
    } finally {
      setSaving((prev) => prev.map((v, i) => (i === taskIdx ? false : v)))
    }
  }

  const task1Label = isAcademic ? 'Task 1 — Report' : 'Task 1 — Letter'
  const task2Label = 'Task 2 — Essay'

  return (
    <Tabs defaultValue='task1'>
      <SectionDurationField
        testId={section.test_id}
        sectionType='writing'
        settings={sectionSettings}
        onSaved={onRefresh}
      />

      <TabsList className='mt-4'>
        <TabsTrigger value='task1'>Task 1</TabsTrigger>
        <TabsTrigger value='task2'>Task 2</TabsTrigger>
      </TabsList>

      <TabsContent value='task1' className='space-y-5'>
        <TaskEditor
          taskIdx={0}
          label={task1Label}
          minWords={150}
          showImageUpload={isAcademic}
          showEssayType={false}
          draft={tasks[0]}
          saving={saving[0]}
          onChange={(updated) =>
            setTasks((prev) => prev.map((t, i) => (i === 0 ? updated : t)))
          }
          onSave={() => void handleSave(0)}
        />
      </TabsContent>

      <TabsContent value='task2' className='space-y-5'>
        <TaskEditor
          taskIdx={1}
          label={task2Label}
          minWords={250}
          showImageUpload={false}
          showEssayType
          draft={tasks[1]}
          saving={saving[1]}
          onChange={(updated) =>
            setTasks((prev) => prev.map((t, i) => (i === 1 ? updated : t)))
          }
          onSave={() => void handleSave(1)}
        />
      </TabsContent>
    </Tabs>
  )
}

function TaskEditor({
  taskIdx,
  label,
  minWords,
  showImageUpload,
  showEssayType,
  draft,
  saving,
  onChange,
  onSave,
}: {
  taskIdx: number
  label: string
  minWords: number
  showImageUpload: boolean
  showEssayType: boolean
  draft: TaskDraft
  saving: boolean
  onChange: (d: TaskDraft) => void
  onSave: () => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const taskNumber = taskIdx + 1
  const isTask2 = taskNumber === 2

  const displayImageUrl = draft.imageUrl?.startsWith('/')
    ? `${import.meta.env.VITE_API_URL}${draft.imageUrl}`
    : draft.imageUrl

  const essaySelectValue = draft.essayType ?? '__none__'
  const essayHint =
    ESSAY_TYPE_OPTIONS.find((o) => o.value === essaySelectValue)?.hint ??
    ESSAY_TYPE_OPTIONS[0].hint

  const handleImageUpload = async (file: File) => {
    setUploading(true)
    try {
      const url = await uploadImage(file)
      onChange({ ...draft, imageUrl: url })
      toast.success('Image uploaded')
    } catch {
      toast.error('Failed to upload image')
    } finally {
      setUploading(false)
    }
  }

  const handleEssayTypeChange = (v: string) => {
    const newType = v === '__none__' ? null : v
    const updated = { ...draft, essayType: newType }
    if (!draft.useCustomInstruction) {
      updated.taskInstruction = getDefaultInstruction(taskNumber, newType)
    }
    if (!draft.useCustomQuestion) {
      updated.taskQuestion = getDefaultQuestion(newType) ?? ''
    }
    onChange(updated)
  }

  const handleInstructionModeChange = (mode: string) => {
    if (mode === 'default') {
      onChange({
        ...draft,
        useCustomInstruction: false,
        taskInstruction: getDefaultInstruction(taskNumber, draft.essayType),
      })
    } else {
      onChange({ ...draft, useCustomInstruction: true })
    }
  }

  const handleQuestionModeChange = (mode: string) => {
    if (mode === 'default') {
      onChange({
        ...draft,
        useCustomQuestion: false,
        taskQuestion: getDefaultQuestion(draft.essayType) ?? '',
      })
    } else {
      onChange({ ...draft, useCustomQuestion: true })
    }
  }

  const descPlaceholder = isTask2
    ? 'The most important aim of science should be to improve people\'s lives.'
    : 'The chart below shows the percentage of households in...'

  return (
    <div className='space-y-4'>
      <div className='flex items-center justify-between'>
        <div>
          <h3 className='font-medium text-foreground'>{label}</h3>
          <p className='mt-0.5 text-xs text-muted-foreground'>
            Minimum {minWords} words &nbsp;·&nbsp; Required task
          </p>
        </div>
        <span className='rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground'>
          min {minWords} words
        </span>
      </div>

      {showEssayType && (
        <div className='space-y-1.5'>
          <Label className='text-sm font-medium'>Essay Type</Label>
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
        <Label className='text-sm font-medium'>
          {isTask2 ? 'Statement' : 'Task Description'}
        </Label>
        <Textarea
          rows={isTask2 ? 3 : 5}
          value={isTask2 ? draft.taskStatement : draft.taskDescription}
          onChange={(e) =>
            isTask2
              ? onChange({ ...draft, taskStatement: e.target.value })
              : onChange({ ...draft, taskDescription: e.target.value })
          }
          placeholder={descPlaceholder}
        />
      </div>

      {isTask2 && (
        <div className='space-y-1.5'>
          <div className='flex items-center justify-between'>
            <Label className='text-sm font-medium'>Question</Label>
            <Select
              value={draft.useCustomQuestion ? 'custom' : 'default'}
              onValueChange={handleQuestionModeChange}
            >
              <SelectTrigger className='h-7 w-[200px] text-xs'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DEFAULT_CUSTOM_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value} className='text-xs'>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Textarea
            rows={2}
            value={draft.taskQuestion}
            onChange={(e) => onChange({ ...draft, taskQuestion: e.target.value })}
            readOnly={!draft.useCustomQuestion}
            className={!draft.useCustomQuestion ? 'cursor-default bg-muted text-muted-foreground' : ''}
          />
          {!draft.useCustomQuestion && !draft.essayType && (
            <p className='text-xs text-muted-foreground'>
              Select an essay type above to auto-fill the question.
            </p>
          )}
        </div>
      )}

      <div className='space-y-1.5'>
        <div className='flex items-center justify-between'>
          <Label className='text-sm font-medium'>Instruction</Label>
          <Select
            value={draft.useCustomInstruction ? 'custom' : 'default'}
            onValueChange={handleInstructionModeChange}
          >
            <SelectTrigger className='h-7 w-[200px] text-xs'>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DEFAULT_CUSTOM_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value} className='text-xs'>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Textarea
          rows={2}
          value={draft.taskInstruction}
          onChange={(e) => onChange({ ...draft, taskInstruction: e.target.value })}
          readOnly={!draft.useCustomInstruction}
            className={!draft.useCustomInstruction ? 'cursor-default bg-muted text-muted-foreground' : ''}
          />
          {!draft.useCustomInstruction && (
            <p className='text-xs text-muted-foreground'>
            Standard IELTS instruction. Switch to Custom to edit.
          </p>
        )}
      </div>

      {showImageUpload && (
        <div className='space-y-1.5'>
          <Label className='text-sm font-medium'>Chart / Diagram</Label>
          <input
            ref={fileRef}
            type='file'
            accept='image/*'
            className='hidden'
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) void handleImageUpload(f)
            }}
          />
          {draft.imageUrl ? (
            <div className='group relative w-full overflow-hidden rounded-lg border border-border bg-muted'>
              <img
                src={displayImageUrl ?? ''}
                alt='Chart / Diagram'
                className='mx-auto block max-h-64 w-full object-contain p-2'
              />
              <div className='absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 transition-opacity group-hover:opacity-100'>
                <Button
                  type='button'
                  size='sm'
                  variant='secondary'
                  onClick={() => window.open(displayImageUrl ?? '', '_blank')}
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
                  {uploading
                    ? <Loader2 className='mr-1 size-3.5 animate-spin' />
                    : <ImageIcon className='mr-1 size-3.5' />}
                  Replace
                </Button>
                <Button
                  type='button'
                  size='sm'
                  variant='destructive'
                  onClick={() => onChange({ ...draft, imageUrl: null })}
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
                {uploading ? 'Uploading…' : 'Upload chart or diagram'}
              </span>
              <span className='text-xs'>PNG, JPG, GIF up to 10MB</span>
            </button>
          )}
        </div>
      )}

      <div className='flex justify-end'>
        <Button onClick={onSave} disabled={saving}>
          {saving && <Loader2 className='mr-1 size-4 animate-spin' />}
          Save {label.split(' — ')[0]}
        </Button>
      </div>
    </div>
  )
}
