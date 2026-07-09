import { useRef, useState } from 'react'
import { ImageIcon, Loader2, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { uploadImage } from '@/lib/api/attempts'
import { createQuestion, updateQuestion } from '@/lib/api/questions'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { Question, Section, Test } from '../data/schema'

type Props = {
  test: Test | null
  sections: Section[]
  questionsMap: Record<string, Question[]>
  onRefresh: () => void
}

type TaskDraft = {
  id?: string
  order: number
  prompt: string
  imageUrl: string | null
}

export function StepWriting({ test, sections, questionsMap, onRefresh }: Props) {
  const writingSection = sections.find((s) => s.type === 'writing')

  if (!writingSection) {
    return (
      <p className='py-12 text-center text-sm text-slate-400'>
        No writing section found. The test may not have been created yet.
      </p>
    )
  }

  return (
    <WritingEditor
      section={writingSection}
      questionsMap={questionsMap}
      testType={test?.type ?? 'academic'}
      onRefresh={onRefresh}
    />
  )
}

function WritingEditor({
  section,
  questionsMap,
  testType,
  onRefresh,
}: {
  section: Section
  questionsMap: Record<string, Question[]>
  testType: string
  onRefresh: () => void
}) {
  const existing = questionsMap[section.id] ?? []
  const isAcademic = testType.toLowerCase() === 'academic'

  const findTask = (num: number): Question | undefined =>
    existing.find((q) => q.task_number === num) ??
    existing.find((q) => q.order === num)

  const [tasks, setTasks] = useState<TaskDraft[]>(() => {
    const t1 = findTask(1)
    const t2 = findTask(2)
    return [
      {
        id: t1?.id,
        order: 1,
        prompt: String(t1?.content.prompt ?? ''),
        // Read image_url from new column first, fallback to content JSON
        imageUrl: t1?.image_url ?? (t1?.content.image_url as string | undefined) ?? null,
      },
      {
        id: t2?.id,
        order: 2,
        prompt: String(t2?.content.prompt ?? ''),
        imageUrl: null, // Task 2 never has an image
      },
    ]
  })

  const [saving, setSaving] = useState([false, false])

  const handleSave = async (taskIdx: number) => {
    const draft = tasks[taskIdx]
    const taskNumber = taskIdx + 1
    setSaving((prev) => prev.map((v, i) => (i === taskIdx ? true : v)))
    try {
      const payload = {
        order: draft.order,
        question_type: 'essay' as const,
        content: { prompt: draft.prompt },
        answer_key: null,
        task_number: taskNumber,
        // min_words is enforced by backend; send expected value for new creates
        min_words: taskNumber === 1 ? 150 : 250,
        image_url: taskIdx === 0 ? (draft.imageUrl ?? null) : null,
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
                prompt: String(saved.content.prompt ?? t.prompt),
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
      <TabsList>
        <TabsTrigger value='task1'>Task 1</TabsTrigger>
        <TabsTrigger value='task2'>Task 2</TabsTrigger>
      </TabsList>

      {/* Task 1 */}
      <TabsContent value='task1' className='space-y-5'>
        <TaskEditor
          taskIdx={0}
          label={task1Label}
          minWords={150}
          showImageUpload={isAcademic}
          draft={tasks[0]}
          saving={saving[0]}
          onChange={(updated) =>
            setTasks((prev) => prev.map((t, i) => (i === 0 ? updated : t)))
          }
          onSave={() => void handleSave(0)}
        />
      </TabsContent>

      {/* Task 2 */}
      <TabsContent value='task2' className='space-y-5'>
        <TaskEditor
          taskIdx={1}
          label={task2Label}
          minWords={250}
          showImageUpload={false}
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
  draft,
  saving,
  onChange,
  onSave,
}: {
  taskIdx: number
  label: string
  minWords: number
  showImageUpload: boolean
  draft: TaskDraft
  saving: boolean
  onChange: (d: TaskDraft) => void
  onSave: () => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)

  const displayImageUrl = draft.imageUrl?.startsWith('/')
    ? `${import.meta.env.VITE_API_URL}${draft.imageUrl}`
    : draft.imageUrl

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

  const promptPlaceholder =
    taskIdx === 0
      ? 'The chart below shows the percentage of households in...'
      : 'Some people think that governments should spend more money on public transport...'

  return (
    <div className='space-y-4'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h3 className='font-medium text-slate-900'>{label}</h3>
          <p className='mt-0.5 text-xs text-slate-500'>
            Minimum {minWords} words &nbsp;·&nbsp; Required task
          </p>
        </div>
        <span className='rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600'>
          min {minWords} words
        </span>
      </div>

      {/* Prompt */}
      <div className='space-y-1.5'>
        <Label className='text-sm font-medium'>Prompt</Label>
        <Textarea
          rows={5}
          value={draft.prompt}
          onChange={(e) => onChange({ ...draft, prompt: e.target.value })}
          placeholder={promptPlaceholder}
        />
      </div>

      {/* Chart/Diagram upload — Academic Task 1 only */}
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
            <div className='group relative w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-50'>
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
              className='flex w-full cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-slate-400 transition-colors hover:border-slate-400 hover:bg-slate-100 hover:text-slate-600 disabled:cursor-not-allowed disabled:opacity-60'
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

      {/* Save */}
      <div className='flex justify-end'>
        <Button onClick={onSave} disabled={saving}>
          {saving && <Loader2 className='mr-1 size-4 animate-spin' />}
          Save {label.split(' — ')[0]}
        </Button>
      </div>
    </div>
  )
}
