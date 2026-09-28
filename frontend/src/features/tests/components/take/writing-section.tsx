import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ChevronDown, Eraser, Info, Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { mediaUrl } from '@/lib/api/attempts'
import {
  requestWritingFeedback,
  type WritingFeedbackResult,
} from '@/lib/api/feedback'
import { cn } from '@/lib/utils'
import { useIsDesktop } from '@/hooks/use-mobile'
import { Button } from '@/components/ui/button'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import type { Question } from '../../data/schema'
import {
  getDefaultInstruction,
  getDefaultQuestion,
} from '../../data/writing-presets'
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
  const taskStatement = (question.content.task_statement as string) ?? ''
  const taskDescription =
    (question.content.task_description as string) ??
    (question.content.prompt as string) ??
    ''
  const taskQuestion =
    (question.content.task_question as string) ??
    (!isTask1 ? (getDefaultQuestion(question.essay_type) ?? '') : '')
  const taskInstruction =
    (question.content.task_instruction as string) ??
    (question.content.instruction as string) ??
    getDefaultInstruction(taskNumber, question.essay_type)
  const promptBody =
    taskDescription.trim() ||
    [taskStatement, taskQuestion]
      .map((s) => s.trim())
      .filter(Boolean)
      .join('\n\n')
  // image_url from DB column takes priority; fallback to content JSON
  const imageUrl =
    question.image_url ?? (question.content.image_url as string | undefined)
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

  // ── Left pane ──────────────────────────────────────────────────────────────
  const leftPane = (
    <div className='min-h-full px-6 py-6 lg:px-8'>
      <h2 className='text-lg font-medium text-foreground'>Task {taskNumber}</h2>
      <p className='mt-2 text-sm text-muted-foreground'>
        You should spend about {isTask1 ? '20' : '40'} minutes on this task.
      </p>

      <div className='mt-6 rounded-md border border-border bg-muted/30 p-4 sm:p-6'>
        <div className='text-base leading-relaxed text-foreground'>
          {promptBody.split('\n').map((line, i) =>
            line.trim() ? (
              <p key={i} className={i > 0 ? 'mt-3' : undefined}>
                {line}
              </p>
            ) : null
          )}
        </div>
      </div>

      {taskInstruction && (
        <p className='mt-4 text-sm leading-relaxed text-muted-foreground italic'>
          {taskInstruction}
        </p>
      )}

      {hasImage && (
        <img
          src={mediaUrl(imageUrl)}
          alt='Task 1 chart'
          className='mx-auto mt-6 block max-h-[60vh] max-w-full rounded-md border border-border bg-background object-contain p-2'
        />
      )}

      <div className='mt-6 flex items-center gap-2 text-sm text-muted-foreground'>
        <Info aria-hidden='true' className='size-4 shrink-0' />
        <span>Write at least {minWords} words</span>
      </div>
    </div>
  )

  // ── Right pane ─────────────────────────────────────────────────────────────
  const rightPane = (
    <div className='flex min-h-full flex-col border-t border-border lg:border-t-0'>
      {/* Autosave + clear row */}
      <div className='flex shrink-0 items-center justify-between gap-4 px-4 py-3'>
        {lastSavedAt ? (
          <span
            className={cn(
              'text-sm transition-colors duration-200 ease-out',
              savedRecently ? 'text-foreground' : 'text-muted-foreground'
            )}
          >
            Saved · {formatSavedTime(lastSavedAt)}
          </span>
        ) : (
          <span />
        )}

        {showClearConfirm ? (
          <div className='flex items-center gap-2 text-xs'>
            <span className='text-muted-foreground'>Clear all?</span>
            <button
              type='button'
              onClick={handleClear}
              className='rounded-md px-2 py-1 font-medium text-foreground transition-colors duration-200 ease-out hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
            >
              Yes
            </button>
            <button
              type='button'
              onClick={() => setShowClearConfirm(false)}
              className='rounded-md px-2 py-1 text-muted-foreground transition-colors duration-200 ease-out hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
            >
              No
            </button>
          </div>
        ) : (
          <button
            type='button'
            title='Clear answer'
            aria-label='Clear answer'
            onClick={() => setShowClearConfirm(true)}
            className='inline-flex size-10 items-center justify-center rounded-md text-muted-foreground transition-colors duration-200 ease-out hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none active:bg-muted/70'
          >
            <Eraser aria-hidden='true' className='size-4' />
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
        className='mx-4 min-h-48 flex-1 resize-y rounded-md border border-input bg-background px-4 py-4 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30 focus-visible:outline-none'
      />

      {/* Word count + Get Feedback */}
      <div className='flex shrink-0 items-center justify-between gap-4 px-4 py-4'>
        <span className='text-sm font-medium text-muted-foreground tabular-nums'>
          {wordCount} / {minWords}+ words
        </span>
        {showInstantFeedback && (
          <Button
            type='button'
            size='sm'
            variant='outline'
            disabled={feedbackMutation.isPending || wordCount < 10}
            onClick={() => feedbackMutation.mutate()}
            className='shadow-none'
          >
            {feedbackMutation.isPending ? (
              <Loader2 aria-hidden='true' className='size-4 animate-spin' />
            ) : (
              <Sparkles aria-hidden='true' className='size-4' />
            )}
            Get Feedback
          </Button>
        )}
      </div>

      {showInstantFeedback && (
        <div className='mx-4 mb-4 shrink-0 overflow-hidden rounded-md border border-border'>
          <button
            type='button'
            onClick={() => setFeedbackOpen((v) => !v)}
            aria-expanded={feedbackOpen}
            className='flex w-full items-center justify-between bg-muted/30 px-4 py-3 text-left text-sm font-medium text-foreground transition-colors duration-200 ease-out hover:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none focus-visible:ring-inset'
          >
            <div className='flex items-center gap-2'>
              <Sparkles
                aria-hidden='true'
                className='size-4 text-muted-foreground'
              />
              <span>AI Feedback</span>
            </div>
            <div className='flex items-center gap-2'>
              {feedback && (
                <span className='rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground'>
                  Band {feedback.overall_band.toFixed(1)}
                </span>
              )}
              <ChevronDown
                aria-hidden='true'
                className={cn(
                  'size-4 text-muted-foreground transition-transform duration-200 ease-out',
                  feedbackOpen && 'rotate-180'
                )}
              />
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
                <div className='flex items-center gap-3 rounded-md bg-muted/30 p-4'>
                  <Sparkles
                    aria-hidden='true'
                    className='size-4 shrink-0 text-muted-foreground'
                  />
                  <p className='text-sm text-muted-foreground'>
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
        <div className='min-h-0 basis-2/5 overflow-y-auto'>{leftPane}</div>
        <div className='min-h-0 flex-1 overflow-y-auto'>{rightPane}</div>
      </div>
    )
  }

  return (
    <ResizablePanelGroup orientation='horizontal' className='h-full min-h-0'>
      <ResizablePanel defaultSize='50%' minSize='25%'>
        <div className='h-full min-h-0 overflow-x-hidden overflow-y-auto'>
          {leftPane}
        </div>
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize='50%' minSize='25%'>
        <div className='h-full min-h-0 overflow-x-hidden overflow-y-auto'>
          {rightPane}
        </div>
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
    [questions]
  )

  // Full mock / whole-section practice: 2 tasks. Single-part practice: 1 task.
  if (sortedQuestions.length === 0 || sortedQuestions.length > 2) {
    return (
      <div className='flex h-full items-center justify-center'>
        <p className='text-sm text-muted-foreground'>
          Writing section misconfigured
        </p>
      </div>
    )
  }

  // Practice may pass only Task 2 while URL still says part=2 → clamp to 0.
  const safeTaskIdx = Math.min(
    Math.max(0, activeTaskIdx),
    sortedQuestions.length - 1
  )

  return (
    <div className='flex h-full min-h-0 flex-col bg-background text-foreground'>
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
