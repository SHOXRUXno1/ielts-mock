import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  createQuestion,
  deleteQuestion,
  fetchQuestions,
  updateQuestion,
  type QuestionCreatePayload,
} from '@/lib/api/questions'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/confirm-dialog'
import {
  QUESTION_TYPE_LABELS,
  SECTION_QUESTION_TYPES,
  type Question,
  type SectionType,
} from '../data/schema'
import { multiSelectValidationError } from '../data/multi-select'
import { QuestionEditor, type QuestionDraft } from '../wizard/question-editor'

/** Strip legacy writing fields that now live as DB columns. */
function stripWritingContentFields(content: Record<string, unknown>): Record<string, unknown> {
  const {
    task_type: _taskType,
    min_words: _minWords,
    image_url: _imageUrl,
    ...rest
  } = content
  return rest
}

function inferTaskNumber(q: Question): number | null {
  if (q.task_number != null) return q.task_number
  const taskType = q.content.task_type
  if (taskType === 'task_2') return 2
  if (taskType === 'task_1') return 1
  return null
}

function inferMinWords(q: Question, taskNumber: number | null): number | null {
  if (q.min_words != null) return q.min_words
  if (typeof q.content.min_words === 'number') return q.content.min_words
  if (taskNumber === 1) return 150
  if (taskNumber === 2) return 250
  return null
}

function questionToDraft(q: Question): QuestionDraft {
  const taskNumber = inferTaskNumber(q)
  return {
    id: q.id,
    order: q.order,
    question_type: q.question_type,
    content: q.content,
    answer_key: q.answer_key,
    task_number: taskNumber,
    min_words: inferMinWords(q, taskNumber),
    image_url: q.image_url ?? (q.content?.image_url as string | undefined) ?? null,
    essay_type: q.essay_type ?? null,
  }
}

function draftToPayload(draft: QuestionDraft): QuestionCreatePayload {
  return {
    order: draft.order,
    question_type: draft.question_type,
    content: stripWritingContentFields(draft.content),
    answer_key: draft.answer_key ?? undefined,
    task_number: draft.task_number ?? null,
    min_words: draft.min_words ?? null,
    image_url: draft.image_url ?? null,
    essay_type: draft.task_number === 2 ? (draft.essay_type ?? null) : null,
  }
}

function getPreview(q: Question): string | null {
  const c = q.content
  if (c.statement) return String(c.statement)
  if (c.question) return String(c.question)
  if (c.text) return String(c.text)
  if (c.prompt) return String(c.prompt)
  if (c.cue_card && typeof c.cue_card === 'object') {
    const cc = c.cue_card as Record<string, unknown>
    if (cc.topic) return String(cc.topic)
  }
  if (c.cue_card) return String(c.cue_card)
  if (Array.isArray(c.questions) && c.questions.length > 0) return String(c.questions[0])
  return null
}

function isFixedWritingEssay(q: Question | QuestionDraft): boolean {
  const n = 'task_number' in q ? q.task_number : null
  return n === 1 || n === 2
}

type Props = {
  sectionId: string
  sectionType: SectionType
  testId: string
}

export function QuestionList({ sectionId, sectionType, testId }: Props) {
  const queryClient = useQueryClient()
  const allowedTypes = SECTION_QUESTION_TYPES[sectionType] ?? ['mcq']
  const isWriting = sectionType === 'writing'

  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [drafts, setDrafts] = useState<Record<string, QuestionDraft>>({})
  const [saving, setSaving] = useState<Record<string, boolean>>({})
  const [addingNew, setAddingNew] = useState(false)
  const [newDraft, setNewDraft] = useState<QuestionDraft | null>(null)
  const [savingNew, setSavingNew] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const { data: questions = [], isLoading } = useQuery({
    queryKey: ['questions', sectionId],
    queryFn: () => fetchQuestions(sectionId),
  })

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ['questions', sectionId] })
    void queryClient.invalidateQueries({ queryKey: ['tests', testId] })
  }

  const getDraft = (q: Question): QuestionDraft =>
    drafts[q.id] ?? questionToDraft(q)

  const handleSave = async (q: Question) => {
    const draft = getDraft(q)
    if (draft.question_type === 'multi_select') {
      const err = multiSelectValidationError(draft.content, draft.answer_key)
      if (err) {
        toast.error(err)
        return
      }
    }
    if (
      questions.some(
        (other) => other.id !== q.id && other.order === draft.order,
      )
    ) {
      toast.error('Order already exists')
      return
    }
    setSaving((prev) => ({ ...prev, [q.id]: true }))
    try {
      await updateQuestion(sectionId, q.id, draftToPayload(draft))
      toast.success('Question saved')
      setExpandedId(null)
      setDrafts((prev) => {
        const next = { ...prev }
        delete next[q.id]
        return next
      })
      refresh()
    } catch {
      toast.error('Failed to save question')
    } finally {
      setSaving((prev) => ({ ...prev, [q.id]: false }))
    }
  }

  const handleDelete = async () => {
    if (!deletingId) return
    setDeleting(true)
    try {
      await deleteQuestion(sectionId, deletingId)
      toast.success('Question deleted')
      setDeletingId(null)
      refresh()
    } catch {
      toast.error('Failed to delete question')
    } finally {
      setDeleting(false)
    }
  }

  const handleStartNew = () => {
    if (isWriting) {
      const hasTask1 = questions.some((q) => inferTaskNumber(q) === 1)
      const taskNumber = hasTask1 ? 2 : 1
      setNewDraft({
        order: taskNumber,
        question_type: 'essay',
        content: {},
        answer_key: null,
        task_number: taskNumber,
        min_words: taskNumber === 1 ? 150 : 250,
        image_url: null,
        essay_type: null,
      })
    } else {
      const maxOrder = questions.reduce((m, q) => Math.max(m, q.order), 0)
      setNewDraft({
        order: maxOrder + 1,
        question_type: allowedTypes[0],
        content: {},
        answer_key: null,
      })
    }
    setAddingNew(true)
  }

  const handleSaveNew = async () => {
    if (!newDraft) return
    if (newDraft.question_type === 'multi_select') {
      const err = multiSelectValidationError(newDraft.content, newDraft.answer_key)
      if (err) {
        toast.error(err)
        return
      }
    }
    if (questions.some((q) => q.order === newDraft.order)) {
      toast.error('Order already exists')
      return
    }
    setSavingNew(true)
    try {
      await createQuestion(sectionId, draftToPayload(newDraft))
      toast.success('Question added')
      setAddingNew(false)
      setNewDraft(null)
      refresh()
    } catch {
      toast.error('Failed to add question')
    } finally {
      setSavingNew(false)
    }
  }

  const canAddQuestion = !isWriting || questions.length < 2

  if (isLoading) {
    return <div className='py-4 text-sm text-muted-foreground'>Loading questions...</div>
  }

  return (
    <div className='space-y-3'>
      <div className='flex items-center justify-between'>
        <h4 className='text-sm font-medium'>Questions ({questions.length})</h4>
        {canAddQuestion && (
          <Button size='sm' onClick={handleStartNew} disabled={addingNew}>
            <Plus className='size-4' />
            Add Question
          </Button>
        )}
      </div>

      {questions.length === 0 && !addingNew && (
        <Card>
          <CardContent className='py-8 text-center text-sm text-muted-foreground'>
            No questions yet. Add one to get started.
          </CardContent>
        </Card>
      )}

      {questions.map((q) => {
        const isExpanded = expandedId === q.id
        const draft = getDraft(q)
        const hideDelete = isWriting && isFixedWritingEssay(draft)
        const preview = getPreview(q)
        return (
          <div key={q.id} className='rounded-lg border'>
            <div
              className='flex cursor-pointer items-center justify-between gap-2 rounded-lg px-4 py-3 transition-colors hover:bg-muted/40'
              onClick={() => setExpandedId(isExpanded ? null : q.id)}
            >
              <div className='flex items-center gap-3 min-w-0'>
                {isExpanded ? (
                  <ChevronDown className='size-4 shrink-0 text-muted-foreground' />
                ) : (
                  <ChevronRight className='size-4 shrink-0 text-muted-foreground' />
                )}
                <span className='flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary'>
                  {q.computed_number ?? q.order}
                </span>
                <div className='min-w-0'>
                  {preview ? (
                    <p className='truncate text-sm font-medium'>{preview}</p>
                  ) : (
                    <p className='truncate text-sm italic text-muted-foreground'>
                      {QUESTION_TYPE_LABELS[q.question_type]} — no preview text
                    </p>
                  )}
                  <Badge variant='secondary' className='mt-0.5 text-xs'>
                    {QUESTION_TYPE_LABELS[q.question_type]}
                    {draft.task_number != null ? ` · Task ${draft.task_number}` : ''}
                  </Badge>
                </div>
              </div>
              <div className='flex shrink-0 items-center gap-1'>
                {!hideDelete && (
                  <Button
                    variant='ghost'
                    size='icon'
                    className='size-8 text-destructive'
                    onClick={(e) => {
                      e.stopPropagation()
                      setDeletingId(q.id)
                    }}
                  >
                    <Trash2 className='size-3.5' />
                  </Button>
                )}
              </div>
            </div>

            {isExpanded && (
              <div className='border-t px-4 pb-4 pt-3'>
                <QuestionEditor
                  question={draft}
                  questionNumber={q.computed_number ?? draft.order}
                  questionNumberEnd={
                    q.computed_number_end != null &&
                    q.computed_number_end !== q.computed_number
                      ? q.computed_number_end
                      : undefined
                  }
                  allowedTypes={allowedTypes}
                  hideDelete={hideDelete}
                  onChange={(updated) =>
                    setDrafts((prev) => ({ ...prev, [q.id]: updated }))
                  }
                  onDelete={() => setDeletingId(q.id)}
                />
                <div className='mt-3 flex justify-end gap-2'>
                  <Button
                    size='sm'
                    variant='outline'
                    onClick={() => {
                      setExpandedId(null)
                      setDrafts((prev) => {
                        const next = { ...prev }
                        delete next[q.id]
                        return next
                      })
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size='sm'
                    onClick={() => void handleSave(q)}
                    disabled={
                      !!saving[q.id] ||
                      (getDraft(q).question_type === 'multi_select' &&
                        multiSelectValidationError(
                          getDraft(q).content,
                          getDraft(q).answer_key,
                        ) != null)
                    }
                  >
                    {saving[q.id] && <Loader2 className='mr-1 size-3.5 animate-spin' />}
                    Save Question
                  </Button>
                </div>
              </div>
            )}
          </div>
        )
      })}

      {/* New question editor */}
      {addingNew && newDraft && (
        <div className='rounded-lg border border-dashed p-4'>
          <p className='mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground'>
            New Question
          </p>
          <QuestionEditor
            question={newDraft}
            questionNumber={newDraft.order}
            allowedTypes={allowedTypes}
            hideDelete={isWriting && isFixedWritingEssay(newDraft)}
            onChange={setNewDraft}
            onDelete={() => {
              setAddingNew(false)
              setNewDraft(null)
            }}
          />
          <div className='mt-3 flex justify-end gap-2'>
            <Button
              size='sm'
              variant='outline'
              onClick={() => {
                setAddingNew(false)
                setNewDraft(null)
              }}
            >
              Cancel
            </Button>
            <Button
              size='sm'
              onClick={() => void handleSaveNew()}
              disabled={
                savingNew ||
                (newDraft.question_type === 'multi_select' &&
                  multiSelectValidationError(
                    newDraft.content,
                    newDraft.answer_key,
                  ) != null)
              }
            >
              {savingNew && <Loader2 className='mr-1 size-3.5 animate-spin' />}
              Save Question
            </Button>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={deletingId !== null}
        onOpenChange={(o) => { if (!o) setDeletingId(null) }}
        title='Delete Question'
        desc='This will permanently delete this question. Are you sure?'
        confirmText='Delete'
        destructive
        isLoading={deleting}
        handleConfirm={() => void handleDelete()}
      />
    </div>
  )
}
