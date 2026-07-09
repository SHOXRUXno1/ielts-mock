import { useState } from 'react'
import { AlertTriangle, Loader2, Plus, Trash2 } from 'lucide-react'
import type { AxiosError } from 'axios'
import { toast } from 'sonner'
import {
  createQuestionInGroup,
  deleteQuestionGroup,
  updateQuestionGroup,
} from '@/lib/api/question-groups'
import { deleteQuestion, updateQuestion } from '@/lib/api/questions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { QUESTION_TYPE_LABELS, type Question, type QuestionGroup, type QuestionType } from '../data/schema'
import { QuestionEditor, type QuestionDraft } from './question-editor'

const MATCHING_SUBTYPES = new Set(['matching_headings', 'matching_information', 'matching_features'])

function optionsPlaceholder(qtype: string): string {
  if (qtype === 'matching_headings') return 'i. First heading; ii. Second heading; iii. Third heading'
  if (qtype === 'matching_information') return 'A; B; C; D; E; F; G'
  if (qtype === 'matching_features') return 'A. Person One; B. Person Two; C. Person Three'
  return 'e.g. London; Paris; Berlin'
}

function instructionPlaceholder(qtype: string): string {
  if (qtype === 'true_false_ng') return 'Do the following statements agree with the information in the passage? Write TRUE, FALSE, or NOT GIVEN.'
  if (qtype === 'yes_no_ng') return 'Do the following statements agree with the views of the writer? Write YES, NO, or NOT GIVEN.'
  if (qtype === 'matching_headings') return 'The reading passage has several paragraphs. Choose the correct heading for each paragraph from the list of headings below.'
  if (qtype === 'matching_information') return 'The reading passage has several sections. Which section contains the following information?'
  if (qtype === 'matching_features') return 'Look at the following statements and the list of people below. Match each statement with the correct person.'
  if (qtype === 'sentence_completion') return 'Complete the sentences below. Choose NO MORE THAN THREE WORDS from the passage for each answer.'
  if (qtype === 'short_answer') return 'Answer the questions below. Choose NO MORE THAN THREE WORDS from the passage for each answer.'
  if (qtype === 'gap_fill') return 'Complete the notes below. Write NO MORE THAN TWO WORDS for each answer.'
  return 'e.g. Choose the correct letter A, B, or C...'
}

function optionsLabel(qtype: string): string {
  if (qtype === 'matching_headings') return 'Headings list (semicolon-separated)'
  if (qtype === 'matching_information') return 'Section letters (semicolon-separated)'
  if (qtype === 'matching_features') return 'Features / People list (semicolon-separated)'
  return 'Word Bank / Shared Options (semicolon-separated)'
}

type Props = {
  group: QuestionGroup
  groupNumber: number
  allowedTypes: QuestionType[]
  onRefresh: () => void
}

export function QuestionGroupEditor({ group, groupNumber, allowedTypes, onRefresh }: Props) {
  const [instruction, setInstruction] = useState(group.instruction ?? '')
  const [questionType, setQuestionType] = useState<string>(group.question_type)
  const [optionsShared, setOptionsShared] = useState<string>(
    Array.isArray((group.options_shared as { options?: unknown[] } | null)?.options)
      ? ((group.options_shared as { options: string[] }).options ?? []).join('; ')
      : ''
  )
  const [savingMeta, setSavingMeta] = useState(false)
  const [deletingGroup, setDeletingGroup] = useState(false)

  const [localQuestions, setLocalQuestions] = useState<QuestionDraft[]>(
    group.questions.map((q) => ({
      id: q.id,
      order: q.order,
      question_type: q.question_type,
      content: q.content,
      answer_key: q.answer_key,
    }))
  )

  const handleSaveMeta = async () => {
    const opts = optionsShared.trim()
      ? optionsShared.split(';').map((o) => o.trim()).filter(Boolean)
      : []

    // Subtype-specific validation
    if (questionType === 'matching_headings' && opts.length < 3) {
      toast.error('Matching Headings requires at least 3 headings.')
      return
    }
    if (questionType === 'matching_features' && opts.length < 2) {
      toast.error('Matching Features requires at least 2 options.')
      return
    }

    setSavingMeta(true)
    try {
      const shared = opts.length > 0 ? { options: opts } : null
      await updateQuestionGroup(group.id, {
        question_type: questionType,
        instruction: instruction,
        options_shared: shared,
      })
      toast.success('Group saved')
      onRefresh()
    } catch {
      toast.error('Failed to save group')
    } finally {
      setSavingMeta(false)
    }
  }

  const handleDeleteGroup = async () => {
    setDeletingGroup(true)
    try {
      await deleteQuestionGroup(group.id)
      toast.success('Group deleted')
      onRefresh()
    } catch {
      toast.error('Failed to delete group')
    } finally {
      setDeletingGroup(false)
    }
  }

  const handleAddQuestion = () => {
    const maxOrder = localQuestions.reduce((m, q) => Math.max(m, q.order), 0)
    setLocalQuestions((prev) => [
      ...prev,
      {
        order: maxOrder + 1,
        question_type: questionType as QuestionType,
        content: {},
        answer_key: null,
      },
    ])
  }

  const handleSaveQuestion = async (draft: QuestionDraft, idx: number) => {
    try {
      let saved: Question
      // Use the DB-persisted group type (group.question_type), NOT the local UI state
      // (questionType) which may be changed without clicking "Save Group Settings".
      const persistedGroupType = group.question_type
      if (draft.id) {
        saved = await updateQuestion(group.section_id, draft.id, {
          order: draft.order,
          question_type: persistedGroupType,
          content: draft.content,
          answer_key: draft.answer_key ?? undefined,
        })
      } else {
        saved = await createQuestionInGroup(group.id, {
          order: draft.order,
          question_type: persistedGroupType,
          content: draft.content,
          answer_key: draft.answer_key ?? undefined,
        })
      }
      setLocalQuestions((prev) =>
        prev.map((q, i) =>
          i === idx
            ? {
                id: saved.id,
                order: saved.order,
                question_type: saved.question_type,
                content: saved.content,
                answer_key: saved.answer_key,
              }
            : q
        )
      )
      toast.success('Question saved')
      onRefresh()
    } catch (err) {
      const axErr = err as AxiosError<{ detail?: string | { msg: string }[] }>
      const detail = axErr?.response?.data?.detail
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail[0]?.msg ?? 'Failed to save question'
            : 'Failed to save question'
      toast.error(msg)
    }
  }

  const handleDeleteQuestion = async (draft: QuestionDraft, idx: number) => {
    if (draft.id) {
      try {
        await deleteQuestion(group.section_id, draft.id)
        toast.success('Question deleted')
        onRefresh()
      } catch {
        toast.error('Failed to delete question')
        return
      }
    }
    setLocalQuestions((prev) => prev.filter((_, i) => i !== idx))
  }

  const parsedOptions = optionsShared.trim()
    ? optionsShared.split(';').map((o) => o.trim()).filter(Boolean)
    : []

  return (
    <div className='rounded-lg border border-slate-200 bg-slate-50/50 p-4 space-y-4'>
      {/* Group header */}
      <div className='flex items-center justify-between'>
        <span className='text-sm font-semibold text-slate-700'>
          Group {groupNumber} — {localQuestions.length} question{localQuestions.length !== 1 ? 's' : ''}
        </span>
        <Button
          variant='ghost'
          size='sm'
          className='text-destructive'
          onClick={handleDeleteGroup}
          disabled={deletingGroup}
        >
          {deletingGroup ? <Loader2 className='size-4 animate-spin' /> : <Trash2 className='size-4' />}
          Delete Group
        </Button>
      </div>

      {/* Legacy matching warning */}
      {group.question_type === 'matching' && !MATCHING_SUBTYPES.has(questionType) && (
        <div className='flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800'>
          <AlertTriangle className='mt-0.5 size-3.5 shrink-0' />
          <span>
            Consider specifying a subtype:{' '}
            <strong>Matching Headings</strong>, <strong>Matching Information</strong>, or{' '}
            <strong>Matching Features</strong>.
          </span>
        </div>
      )}

      {/* Group meta */}
      <div className='grid grid-cols-2 gap-3'>
        <div className='space-y-1.5'>
          <Label className='text-xs text-slate-600'>Question Type</Label>
          <Select
            value={questionType}
            onValueChange={setQuestionType}
          >
            <SelectTrigger className='h-8 text-sm'>
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

        <div className='space-y-1.5'>
          <Label className='text-xs text-slate-600'>{optionsLabel(questionType)}</Label>
          <Input
            className='h-8 text-sm'
            placeholder={optionsPlaceholder(questionType)}
            value={optionsShared}
            onChange={(e) => setOptionsShared(e.target.value)}
          />
        </div>
      </div>

      <div className='space-y-1.5'>
        <Label className='text-xs text-slate-600'>Group Instruction</Label>
        <Textarea
          rows={2}
          placeholder={instructionPlaceholder(questionType)}
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
        />
      </div>

      <div className='flex justify-end'>
        <Button variant='outline' size='sm' onClick={handleSaveMeta} disabled={savingMeta}>
          {savingMeta && <Loader2 className='mr-1 size-3.5 animate-spin' />}
          Save Group Settings
        </Button>
      </div>

      {/* Questions inside group */}
      <div className='space-y-3 pt-1'>
        {localQuestions.map((q, idx) => (
          <div key={idx}>
            <QuestionEditor
              question={q}
              questionNumber={q.order}
              allowedTypes={allowedTypes}
              groupType={questionType as QuestionType}
              sharedOptions={MATCHING_SUBTYPES.has(questionType) ? parsedOptions : undefined}
              onChange={(updated) =>
                setLocalQuestions((prev) => prev.map((x, i) => (i === idx ? updated : x)))
              }
              onDelete={() => handleDeleteQuestion(q, idx)}
            />
            <div className='mt-1 flex justify-end'>
              <Button size='sm' variant='outline' onClick={() => handleSaveQuestion(q, idx)}>
                Save question
              </Button>
            </div>
          </div>
        ))}

        <Button variant='outline' size='sm' onClick={handleAddQuestion}>
          <Plus className='mr-1 size-4' /> Add Question
        </Button>
      </div>
    </div>
  )
}
