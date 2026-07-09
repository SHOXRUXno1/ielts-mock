import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  createQuestion,
  deleteQuestion,
  fetchQuestions,
  updateQuestion,
} from '@/lib/api/questions'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/confirm-dialog'
import {
  QUESTION_TYPE_LABELS,
  type Question,
  type QuestionType,
  type SectionType,
} from '../data/schema'
import { QuestionEditor, type QuestionDraft } from '../wizard/question-editor'

const SECTION_ALLOWED_TYPES: Record<SectionType, QuestionType[]> = {
  listening: ['mcq', 'gap_fill', 'matching', 'map_labeling', 'true_false_ng', 'multi_select', 'matching_information', 'matching_features', 'sentence_completion', 'short_answer'],
  reading: ['mcq', 'gap_fill', 'matching', 'true_false_ng', 'multi_select', 'matching_headings', 'matching_information', 'matching_features', 'yes_no_ng', 'sentence_completion', 'short_answer'],
  writing: ['essay'],
  speaking: ['speaking_part'],
}

function getPreview(q: Question): string {
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
  return 'No preview'
}

type Props = {
  sectionId: string
  sectionType: SectionType
  testId: string
}

export function QuestionList({ sectionId, sectionType, testId }: Props) {
  const queryClient = useQueryClient()
  const allowedTypes = SECTION_ALLOWED_TYPES[sectionType] ?? ['mcq']

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
    drafts[q.id] ?? {
      id: q.id,
      order: q.order,
      question_type: q.question_type,
      content: q.content,
      answer_key: q.answer_key,
    }

  const handleSave = async (q: Question) => {
    const draft = getDraft(q)
    setSaving((prev) => ({ ...prev, [q.id]: true }))
    try {
      await updateQuestion(sectionId, q.id, {
        order: draft.order,
        question_type: draft.question_type,
        content: draft.content,
        answer_key: draft.answer_key ?? undefined,
      })
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
    setNewDraft({
      order: questions.length + 1,
      question_type: allowedTypes[0],
      content: {},
      answer_key: null,
    })
    setAddingNew(true)
  }

  const handleSaveNew = async () => {
    if (!newDraft) return
    setSavingNew(true)
    try {
      await createQuestion(sectionId, {
        order: newDraft.order,
        question_type: newDraft.question_type,
        content: newDraft.content,
        answer_key: newDraft.answer_key ?? undefined,
      })
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

  if (isLoading) {
    return <div className='py-4 text-sm text-muted-foreground'>Loading questions...</div>
  }

  return (
    <div className='space-y-3'>
      <div className='flex items-center justify-between'>
        <h4 className='text-sm font-medium'>Questions ({questions.length})</h4>
        <Button size='sm' onClick={handleStartNew} disabled={addingNew}>
          <Plus className='size-4' />
          Add Question
        </Button>
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
        return (
          <div key={q.id} className='rounded-lg border border-slate-200'>
            {/* Collapsed header */}
            <div
              className='flex cursor-pointer items-center justify-between gap-2 px-4 py-3'
              onClick={() => setExpandedId(isExpanded ? null : q.id)}
            >
              <div className='flex items-center gap-3 min-w-0'>
                <span className='flex size-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600'>
                  {q.order}
                </span>
                <div className='min-w-0'>
                  <p className='truncate text-sm font-medium text-slate-800'>{getPreview(q)}</p>
                  <Badge variant='secondary' className='mt-0.5 text-xs'>
                    {QUESTION_TYPE_LABELS[q.question_type]}
                  </Badge>
                </div>
              </div>
              <div className='flex shrink-0 items-center gap-1'>
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
              </div>
            </div>

            {/* Expanded inline editor */}
            {isExpanded && (
              <div className='border-t border-slate-100 px-4 pb-4 pt-3'>
                <QuestionEditor
                  question={draft}
                  questionNumber={draft.order}
                  allowedTypes={allowedTypes}
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
                    disabled={saving[q.id]}
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
        <div className='rounded-lg border border-dashed border-slate-300 p-4'>
          <p className='mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500'>
            New Question
          </p>
          <QuestionEditor
            question={newDraft}
            questionNumber={newDraft.order}
            allowedTypes={allowedTypes}
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
            <Button size='sm' onClick={() => void handleSaveNew()} disabled={savingNew}>
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
