import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Eraser, Info, Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { useIsDesktop } from '@/hooks/use-mobile'
import { mediaUrl } from '@/lib/api/attempts'
import {
  requestWritingFeedback,
  type WritingFeedbackResult,
} from '@/lib/api/feedback'
import { cn } from '@/lib/utils'
import type { Question } from '../../data/schema'
import { getDefaultInstruction, getDefaultQuestion } from '../../data/writing-presets'
import { WritingFeedbackView } from './writing-feedback-view'

// ── Types & helpers ──────────────────────────────────────────────────────────

type Props = {
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  attemptId: string | null
  /** Controlled from parent. 0 = Task 1, 1 = Task 2. */
  activeTaskIdx?: number
  previewMode?: boolean
  /** Instant AI feedback. Off in a full mock so the exam stays closed-book. */
  showInstantFeedback?: boolean
}

function countWords(text: string): number {
  return text
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length
}

const DRAFT_KEY = (attemptId: string, questionId: string) =>
  `writing:${attemptId}:${questionId}`

function formatSavedTime(d: Date): string {
  return d.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

// ── Single task editor ───────────────────────────────────────────────────────

function TaskEditor({
  question,
  index,
  text,
  onTextChange,
  attemptId,
  showInstantFeedback,
}: {
  question: Question
  index: number
  text: string
  onTextChange: (val: string) => void
  attemptId: string | null
  showInstantFeedback: boolean
}) {
  // task_number from DB column takes priority; fallback to index for old data
  const taskNumber = question.task_number ?? (index === 0 ? 1 : 2)
  const isTask1 = taskNumber === 1
  // min_words from DB column takes priority; fallback to content JSON then hardcoded default
  const minWords =
    question.min_words ??
    (question.content.min_words as number | undefined) ??
    (isTask1 ? 150 : 250)
  const taskStatement =
    (question.content.task_statement as string) ?? ''
  const taskDescription =
    (question.content.task_description as string) ??
    (question.content.prompt as string) ?? ''
  const taskQuestion =
    (question.content.task_question as string) ??
    (!isTask1 ? (getDefaultQuestion(question.essay_type) ?? '') : '')
  const taskInstruction =
    (question.content.task_instruction as string) ??
    (question.content.instruction as string) ??
    getDefaultInstruction(taskNumber, question.essay_type)
  const displayStatement = !isTask1 && taskStatement ? taskStatement : taskDescription
  // image_url from DB column takes priority; fallback to content JSON
  const imageUrl =
    question.image_url ??
    (question.content.image_url as string | undefined)
  // Only Task 1 ever shows an image (Task 2 is always essay, no charts)
  const hasImage = isTask1 && !!imageUrl

  const wordCount = countWords(text)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)
  const [savedRecently, setSavedRecently] = useState(false)
  const savedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [feedback, setFeedback] = useState<WritingFeedbackResult | null>(null)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const isDesktop = useIsDesktop()

  const markSaved = () => {
    setLastSavedAt(new Date())
    setSavedRecently(true)
    if (savedTimerRef.current) clearTimeout(savedTimerRef.current)
    savedTimerRef.current = setTimeout(() => setSavedRecently(false), 2000)
  }

  // Hydrate from localStorage on mount
  useEffect(() => {
    if (!attemptId || text !== '') return
    try {
      const draft = localStorage.getItem(DRAFT_KEY(attemptId, question.id))
      if (draft) {
        onTextChange(draft)
        setTimeout(() => markSaved(), 0)
      }
    } catch {
      // unavailable
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attemptId, question.id])

  // 30-second autosave interval
  useEffect(() => {
    if (!attemptId) return
    intervalRef.current = setInterval(() => {
      try {
        const currentText = textareaRef.current?.value ?? ''
        localStorage.setItem(DRAFT_KEY(attemptId, question.id), currentText)
        markSaved()
      } catch {
        // unavailable
      }
    }, 30_000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [attemptId, question.id])

  // Debounced save on every change (500ms)
  const handleChange = (val: string) => {
    onTextChange(val)
    if (!attemptId) return
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(DRAFT_KEY(attemptId, question.id), val)
        markSaved()
      } catch {
        // unavailable
      }
    }, 500)
  }

  useEffect(() => {
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      if (savedTimerRef.current) clearTimeout(savedTimerRef.current)
    }
  }, [])

  const handleClear = () => {
    onTextChange('')
    if (attemptId) {
      try {
        localStorage.removeItem(DRAFT_KEY(attemptId, question.id))
      } catch {
        // unavailable
      }
    }
    setLastSavedAt(null)
    setShowClearConfirm(false)
    textareaRef.current?.focus()
  }

  const feedbackMutation = useMutation({
    mutationFn: () =>
      requestWritingFeedback({
        task: taskNumber as 1 | 2,
        task_description: taskDescription,
        task_statement: taskStatement || undefined,
        task_question: taskQuestion || undefined,
        task_instruction: taskInstruction,
        text,
        image_url: hasImage ? imageUrl : null,
        essay_type: question.essay_type,
        attempt_id: attemptId,
      }),
    onSuccess: (data) => {
      setFeedback(data)
      setFeedbackOpen(true)
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to get feedback. Please try again.'
      toast.error(msg)
    },
  })

  const wordCountColor =
    wordCount === 0
      ? 'text-slate-400'
      : wordCount < minWords
        ? 'text-amber-500'
        : 'text-emerald-500'

  // ── Left pane ──────────────────────────────────────────────────────────────
  const leftPane = (
    <div className='h-full overflow-y-auto px-10 py-8'>
      <h2 className='text-lg font-medium text-slate-900'>
        Task {taskNumber}
      </h2>
      <p className='mt-1 text-[13px] text-slate-400'>
        You should spend about {isTask1 ? '20' : '40'} minutes on this task.
      </p>

      {!isTask1 && (
        <p className='mt-6 text-[13px] text-slate-500'>
          Write about the following topic:
        </p>
      )}

      <div
        className={cn(
          'rounded-lg border-l-[3px] border-blue-500 bg-slate-50 p-6',
          isTask1 ? 'mt-6' : 'mt-2',
        )}
      >
        <div
          className='text-[15px] leading-[1.9] text-slate-800'
          style={!isTask1 ? { fontFamily: 'Georgia, serif' } : undefined}
        >
          {displayStatement.split('\n').map((line, i) =>
            line.trim() ? (
              <p key={i} className={i > 0 ? 'mt-3' : undefined}>
                {line}
              </p>
            ) : null,
          )}
          {!isTask1 && taskQuestion && (
            <p className='mt-4 font-medium'>{taskQuestion}</p>
          )}
        </div>
      </div>

      {taskInstruction && (
        <p className='mt-3 text-sm italic leading-relaxed text-slate-500'>
          {taskInstruction}
        </p>
      )}

      {hasImage && (
        <img
          src={mediaUrl(imageUrl)}
          alt='Task 1 chart'
          className='mt-5 max-w-full rounded-lg'
        />
      )}

      <div className='mt-6 flex items-center gap-1.5 text-[13px] text-slate-400'>
        <Info className='size-3.5 shrink-0' />
        <span>Write at least {minWords} words</span>
      </div>
    </div>
  )

  // ── Right pane ─────────────────────────────────────────────────────────────
  const rightPane = (
    <div className='flex h-full min-h-0 flex-col overflow-y-auto border-t border-slate-200 lg:border-t-0'>
      {/* Autosave + clear row */}
      <div className='flex shrink-0 items-center justify-between px-5 py-3'>
        {lastSavedAt ? (
          <span
            className='text-xs transition-colors duration-500'
            style={{ color: savedRecently ? '#22c55e' : '#9ca3af' }}
          >
            Saved · {formatSavedTime(lastSavedAt)}
          </span>
        ) : (
          <span />
        )}

        {showClearConfirm ? (
          <div className='flex items-center gap-2 text-xs'>
            <span className='text-slate-500'>Clear all?</span>
            <button
              type='button'
              onClick={handleClear}
              className='font-medium text-red-600 hover:underline'
            >
              Yes
            </button>
            <button
              type='button'
              onClick={() => setShowClearConfirm(false)}
              className='text-slate-400 hover:underline'
            >
              No
            </button>
          </div>
        ) : (
          <button
            type='button'
            title='Clear answer'
            onClick={() => setShowClearConfirm(true)}
            className='rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600'
          >
            <Eraser className='size-4' />
          </button>
        )}
      </div>

      {/* Textarea */}
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => handleChange(e.target.value)}
        placeholder='Start writing your response...'
        spellCheck={false}
        autoCorrect='off'
        autoCapitalize='off'
        autoComplete='off'
        data-gramm='false'
        data-gramm_editor='false'
        data-enable-grammarly='false'
        className='mx-5 h-[min(42vh,360px)] min-h-[200px] shrink-0 resize-y rounded-lg border-[0.5px] border-slate-200 bg-white px-5 py-5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-[3px] focus:ring-blue-500/10'
        style={{ fontFamily: 'Georgia, serif', lineHeight: '1.8' }}
      />

      {/* Word count + Get Feedback */}
      <div className='flex shrink-0 items-center justify-between px-5 py-4'>
        <span className={cn('text-[13px] font-medium tabular-nums', wordCountColor)}>
          {wordCount} / {minWords}+ words
        </span>
        {showInstantFeedback && (
          <button
            type='button'
            disabled={feedbackMutation.isPending || wordCount < 10}
            onClick={() => feedbackMutation.mutate()}
            className='flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2 text-[13px] font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500'
          >
            {feedbackMutation.isPending ? (
              <Loader2 className='size-4 animate-spin' />
            ) : (
              <Sparkles className='size-4' />
            )}
            Get Feedback
          </button>
        )}
      </div>

      {showInstantFeedback && (
        <div className='mx-5 mb-5 shrink-0 overflow-hidden rounded-lg border border-blue-200'>
          <button
            type='button'
            onClick={() => setFeedbackOpen((v) => !v)}
            className='flex w-full items-center justify-between bg-blue-50 px-4 py-3 text-left text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100'
          >
            <div className='flex items-center gap-2'>
              <Sparkles className='size-4' />
              <span>AI Feedback</span>
            </div>
            <div className='flex items-center gap-2'>
              {feedback && (
                <span className='rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700'>
                  Band {feedback.overall_band.toFixed(1)}
                </span>
              )}
              <span className='text-xs text-blue-400'>
                {feedbackOpen ? '▲' : '▼'}
              </span>
            </div>
          </button>
          {feedbackOpen && (
            <div className='p-4'>
              {feedback ? (
                <WritingFeedbackView
                  feedback={feedback}
                  essayText={text}
                  taskNumber={taskNumber === 2 ? 2 : 1}
                />
              ) : (
                <div className='flex items-center gap-2 rounded-lg bg-slate-50 p-4'>
                  <Sparkles className='size-4 shrink-0 text-slate-400' />
                  <p className='text-[13px] text-slate-400'>
                    Submit your essay to receive AI feedback
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )

  if (!isDesktop) {
    return (
      <div className='flex h-full min-h-0 flex-col'>
        <div className='min-h-0 flex-1 overflow-y-auto'>{leftPane}</div>
        <div className='min-h-0 flex-1 overflow-y-auto'>{rightPane}</div>
      </div>
    )
  }

  return (
    <ResizablePanelGroup orientation='horizontal' className='h-full min-h-0'>
      <ResizablePanel defaultSize='50%' minSize='25%'>
        <div className='h-full min-h-0 overflow-y-auto overflow-x-hidden'>{leftPane}</div>
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize='50%' minSize='25%'>
        <div className='h-full min-h-0 overflow-y-auto overflow-x-hidden'>{rightPane}</div>
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}

// ── Main exported component ──────────────────────────────────────────────────

export function WritingSection({
  questions,
  answers,
  onAnswer,
  attemptId,
  activeTaskIdx = 0,
  previewMode: _previewMode = false,
  showInstantFeedback = true,
}: Props) {
  const sortedQuestions = useMemo(
    () => [...questions].sort((a, b) => a.order - b.order),
    [questions],
  )

  // Full mock / whole-section practice: 2 tasks. Single-part practice: 1 task.
  if (sortedQuestions.length === 0 || sortedQuestions.length > 2) {
    return (
      <div className='flex h-full items-center justify-center'>
        <p className='text-sm text-slate-500'>
          Writing section misconfigured
        </p>
      </div>
    )
  }

  // Practice may pass only Task 2 while URL still says part=2 → clamp to 0.
  const safeTaskIdx = Math.min(
    Math.max(0, activeTaskIdx),
    sortedQuestions.length - 1,
  )

  return (
    <div className='flex h-full min-h-0 flex-col bg-white'>
      <div className='min-h-0 flex-1'>
        {sortedQuestions.map((q, i) => {
          if (i !== safeTaskIdx) return null
          const text = (answers[q.id]?.answer as string) ?? ''
          return (
            <TaskEditor
              key={q.id}
              question={q}
              index={i}
              text={text}
              onTextChange={(val) => onAnswer(q.id, { answer: val })}
              attemptId={attemptId}
              showInstantFeedback={showInstantFeedback}
            />
          )
        })}
      </div>
    </div>
  )
}
