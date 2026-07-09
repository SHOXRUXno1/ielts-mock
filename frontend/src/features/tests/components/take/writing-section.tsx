import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Eraser, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { mediaUrl } from '@/lib/api/attempts'
import {
  requestWritingFeedback,
  type WritingFeedbackResult,
} from '@/lib/api/feedback'
import { cn } from '@/lib/utils'
import type { Question } from '../../data/schema'
import { WritingFeedbackView } from './writing-feedback-view'

// ── Types & helpers ──────────────────────────────────────────────────────────

type Props = {
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  attemptId: string | null
  /** Controlled from parent. 0 = Task 1, 1 = Task 2. */
  activeTaskIdx?: number
  /** Callback to switch task — when provided, Task 1/2 tabs are shown inside content */
  onSwitchTask?: (idx: number) => void
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
}: {
  question: Question
  index: number
  text: string
  onTextChange: (val: string) => void
  attemptId: string | null
}) {
  // task_number from DB column takes priority; fallback to index for old data
  const taskNumber = question.task_number ?? (index === 0 ? 1 : 2)
  const isTask1 = taskNumber === 1
  // min_words from DB column takes priority; fallback to content JSON then hardcoded default
  const minWords =
    question.min_words ??
    (question.content.min_words as number | undefined) ??
    (isTask1 ? 150 : 250)
  const prompt = (question.content.prompt as string) ?? ''
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
        task: (index + 1) as 1 | 2,
        prompt,
        text,
        image_url: hasImage ? imageUrl : null,
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

  // Word count color: gray (0 words), red (below min), green (at or above min)
  const wordCountColor =
    wordCount === 0
      ? 'text-slate-500'
      : wordCount < minWords
        ? 'text-[#dc2626]'
        : 'text-[#22c55e]'

  // ── Left pane ──────────────────────────────────────────────────────────────
  const leftPane = (
    <div className='h-full overflow-y-auto px-10 py-8'>
      <h2
        style={{ fontSize: '28px', fontWeight: 800, letterSpacing: '-0.5px' }}
        className='text-slate-900'
      >
        TASK {index + 1}
      </h2>
      <p className='mt-1 text-sm text-slate-500'>
        You should spend about {isTask1 ? '20' : '40'} minutes on this task.
      </p>

      {!isTask1 && (
        <p className='mt-6 text-sm text-slate-600'>
          Write about the following topic:
        </p>
      )}

      <div
        className={cn(isTask1 ? 'mt-6' : 'mt-2')}
        style={{
          background: '#fefce8',
          borderLeft: '4px solid #111827',
          borderTop: 'none',
          borderRight: 'none',
          borderBottom: 'none',
          borderRadius: 0,
          padding: '32px 36px',
          fontFamily: "'Georgia', serif",
          fontSize: '19px',
          lineHeight: '2.0',
          fontWeight: 700,
          fontStyle: 'italic',
          color: '#000000',
          letterSpacing: '0.02em',
        }}
      >
        {prompt.split('\n').map((line, i) =>
          line.trim() ? (
            <p key={i} style={{ marginTop: i > 0 ? '14px' : 0 }}>
              {line}
            </p>
          ) : null,
        )}
      </div>

      {!isTask1 && (
        <p className='mt-3 text-sm italic text-slate-500'>
          Give reasons for your answer and include any relevant examples from
          your own knowledge or experience.
        </p>
      )}

      {hasImage && (
        <img
          src={mediaUrl(imageUrl)}
          alt='Task 1 chart'
          className='mt-5 max-w-full rounded'
        />
      )}
    </div>
  )

  // ── Right pane ─────────────────────────────────────────────────────────────
  const rightPane = (
    <div className='flex h-full flex-col border-l border-slate-200'>
      {/* Autosave row */}
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
              className='font-medium text-[#dc2626] hover:underline'
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
        className='mx-5 min-h-[60vh] flex-1 resize-y rounded-lg border border-slate-300 bg-white px-5 py-5 text-base text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-[3px] focus:ring-blue-500/10'
        style={{ fontFamily: 'Georgia, serif', lineHeight: '1.8' }}
      />

      {/* Word count + Submit for Feedback */}
      <div className='flex shrink-0 items-center justify-between px-5 py-4'>
        <span className={cn('text-sm font-medium', wordCountColor)}>
          Words: {wordCount}
        </span>
        <button
          type='button'
          disabled={feedbackMutation.isPending || wordCount === 0}
          onClick={() => feedbackMutation.mutate()}
          className='flex items-center gap-2 rounded-md bg-[#dc2626] px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#b91c1c] disabled:cursor-not-allowed disabled:opacity-50'
        >
          {feedbackMutation.isPending && (
            <Loader2 className='size-4 animate-spin' />
          )}
          Submit for Feedback
        </button>
      </div>

      {/* Writing Feedback collapsible */}
      <div className='mx-5 mb-5 overflow-hidden rounded-lg border border-slate-200'>
        <button
          type='button'
          onClick={() => setFeedbackOpen((v) => !v)}
          className='flex w-full items-center justify-between bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100'
        >
          <span>Writing Feedback</span>
          <div className='flex items-center gap-2'>
            {feedback && (
              <span className='rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700'>
                Band {feedback.overall_band.toFixed(1)}
              </span>
            )}
            <span className='text-xs text-slate-400'>
              {feedbackOpen ? '▲' : '▼'}
            </span>
          </div>
        </button>
        {feedbackOpen && (
          <div className='max-h-[50vh] overflow-y-auto p-4'>
            {feedback ? (
              <WritingFeedbackView feedback={feedback} essayText={text} />
            ) : (
              <p className='text-sm text-slate-400'>
                Submit your answer above to receive AI feedback.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className='flex h-full'>
      <div className='w-1/2'>{leftPane}</div>
      <div className='w-1/2'>{rightPane}</div>
    </div>
  )
}

// ── Main exported component ──────────────────────────────────────────────────

export function WritingSection({
  questions,
  answers,
  onAnswer,
  attemptId,
  activeTaskIdx = 0,
  onSwitchTask,
}: Props) {
  const sortedQuestions = useMemo(
    () => [...questions].sort((a, b) => a.order - b.order).slice(0, 2),
    [questions],
  )

  if (sortedQuestions.length === 0) {
    return (
      <div className='flex h-full items-center justify-center'>
        <p className='text-sm text-slate-400'>
          No writing tasks added to this section yet.
        </p>
      </div>
    )
  }

  return (
    <div className='flex h-full flex-col bg-white'>
      {/* Task switcher tabs — only shown when multiple tasks exist */}
      {sortedQuestions.length > 1 && onSwitchTask && (
        <div className='flex shrink-0 gap-2 border-b border-slate-200 bg-white px-8 py-3'>
          {sortedQuestions.map((_, i) => (
            <button
              key={i}
              type='button'
              onClick={() => onSwitchTask(i)}
              className={cn(
                'min-w-[52px] rounded-md border px-4 py-1.5 text-sm font-medium transition-colors',
                i === activeTaskIdx
                  ? 'border-slate-900 bg-slate-900 text-white'
                  : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
              )}
            >
              Task {i + 1}
            </button>
          ))}
        </div>
      )}
      {sortedQuestions.map((q, i) => {
        if (i !== activeTaskIdx) return null
        const text = (answers[q.id]?.answer as string) ?? ''
        return (
          <TaskEditor
            key={q.id}
            question={q}
            index={i}
            text={text}
            onTextChange={(val) => onAnswer(q.id, { answer: val })}
            attemptId={attemptId}
          />
        )
      })}
    </div>
  )
}
