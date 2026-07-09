import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import {
  AlertCircle,
  BookOpen,
  Clock,
  Headphones,
  LayoutGrid,
  Loader2,
  Mic,
  PenLine,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  finishAttempt,
  startAttempt,
  submitAnswers,
} from '@/lib/api/attempts'
import { fetchQuestions } from '@/lib/api/questions'
import { fetchTest } from '@/lib/api/tests'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ListeningSection } from './components/take/listening-section'
import { QuestionPalette } from './components/take/question-palette'
import { ReadingSection } from './components/take/reading-section'
import { SectionProgress } from './components/take/section-progress'
import { WritingSection } from './components/take/writing-section'
import type { Question, Section, SectionType } from './data/schema'

type SectionAnswers = Record<string, Record<string, unknown>>

const SECTION_ICONS: Record<SectionType, React.ReactNode> = {
  listening: <Headphones className='size-4' />,
  reading:   <BookOpen className='size-4' />,
  writing:   <PenLine className='size-4' />,
  speaking:  <Mic className='size-4' />,
}

const SECTION_LABELS: Record<SectionType, string> = {
  listening: 'Listening',
  reading:   'Reading',
  writing:   'Writing',
  speaking:  'Speaking',
}

const TYPE_ORDER: SectionType[] = ['listening', 'reading', 'writing', 'speaking']

// ── Helpers ───────────────────────────────────────────────────────────────

function isAttemptDone(err: unknown): boolean {
  const detail = (err as { response?: { data?: { detail?: string } } })
    ?.response?.data?.detail
  return detail === 'Attempt already finished'
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h}h ${m}m` : `${h}h`
}

// ── Sub-section pill bar ───────────────────────────────────────────────────

function SubSectionBar({
  sortedSections,
  sectionQuestions,
  currentType,
  activeSectionId,
  activeWritingTask,
  onSwitchSection,
  onSwitchWritingTask,
}: {
  sortedSections: Section[]
  sectionQuestions: Record<string, Question[]>
  currentType: SectionType
  activeSectionId: string | null
  activeWritingTask: number
  onSwitchSection: (id: string) => void
  onSwitchWritingTask: (idx: number) => void
}) {
  const pillInactive =
    'min-w-[36px] rounded-md border border-slate-300 bg-white px-4 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50'
  const pillActive =
    'min-w-[36px] rounded-md border border-slate-900 bg-slate-900 px-4 py-1.5 text-sm font-medium text-white'

  const bar = 'flex shrink-0 items-center gap-2 border-b border-slate-100 bg-slate-50 px-6 py-2'

  // Listening, Reading, Writing tabs are now rendered inside their section components
  if (currentType === 'listening' || currentType === 'reading' || currentType === 'writing') {
    return null
  }

  return null
}

// ── Main TakeTest component ────────────────────────────────────────────────

export function TakeTest({ testId, resume, initialSection }: { testId: string; resume?: string; initialSection?: string }) {
  const navigate = useNavigate()

  const [attemptId, setAttemptId] = useState<string | null>(resume ?? null)
  const [finished, setFinished] = useState(false)

  // Section navigation — seed from URL :section param if provided
  const [currentTypeIdx, setCurrentTypeIdx] = useState(() => {
    if (!initialSection) return 0
    const idx = TYPE_ORDER.indexOf(initialSection as typeof TYPE_ORDER[number])
    return idx >= 0 ? idx : 0
  })

  // Sub-section tracking
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null)
  const [activeWritingTask, setActiveWritingTask] = useState(0)
  const [activeListeningPart, setActiveListeningPart] = useState(0)

  const [answers, setAnswers] = useState<Record<string, SectionAnswers>>({})
  const [timeLeft, setTimeLeft] = useState<Record<string, number>>({})
  const [sectionQuestions, setSectionQuestions] = useState<Record<string, Question[]>>({})
  const [showSubmitDialog, setShowSubmitDialog] = useState(false)
  const [flagged, setFlagged] = useState<Set<string>>(new Set())
  const [showPalette, setShowPalette] = useState(false)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const currentTypeRef = useRef<SectionType | null>(null)
  const finishMutationRef = useRef<(() => void) | null>(null)
  const isFinishingRef = useRef(false)
  const hasTimedOutRef = useRef<Set<string>>(new Set())
  const autoSaveRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const answersRef = useRef(answers)

  useEffect(() => { answersRef.current = answers }, [answers])

  // beforeunload guard
  useEffect(() => {
    if (!attemptId || finished) return
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault() }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [attemptId, finished])

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: test, isLoading: testLoading } = useQuery({
    queryKey: ['tests', testId],
    queryFn: () => fetchTest(testId),
  })

  const sortedSections = test
    ? [...test.sections].sort((a, b) => a.order - b.order)
    : []

  const presentTypes = TYPE_ORDER.filter((t) =>
    sortedSections.some((s) => s.type === t),
  )
  const currentType: SectionType = presentTypes[currentTypeIdx] ?? 'listening'
  const isLastType = currentTypeIdx === presentTypes.length - 1
  const nextType = isLastType ? null : presentTypes[currentTypeIdx + 1]

  // Sync currentType into ref for timer callback (cannot be done during render)
  useEffect(() => { currentTypeRef.current = currentType }, [currentType])

  // Load questions
  useEffect(() => {
    if (!test) return
    const load = async () => {
      const result: Record<string, Question[]> = {}
      for (const section of test.sections) {
        result[section.id] = await fetchQuestions(section.id)
      }
      setSectionQuestions(result)
    }
    load()
  }, [test])

  // ── localStorage persist & restore ───────────────────────────────────────
  const LS_KEY = attemptId ? `attempt:${attemptId}:state` : null

  useEffect(() => {
    if (!LS_KEY) return
    try {
      const raw = localStorage.getItem(LS_KEY)
      if (!raw) return
      const saved = JSON.parse(raw) as {
        answers: Record<string, SectionAnswers>
        snapshotAt: number
        timeLeftSnapshot: Record<string, number>
        currentTypeIdx: number
        activeSectionId: string | null
      }
      const elapsedSec = Math.floor((Date.now() - saved.snapshotAt) / 1000)
      const restored: Record<string, number> = {}
      for (const [type, left] of Object.entries(saved.timeLeftSnapshot)) {
        restored[type] = Math.max(0, left - elapsedSec)
      }
      setTimeout(() => {
        setAnswers(saved.answers)
        setTimeLeft(restored)
        setCurrentTypeIdx(saved.currentTypeIdx ?? 0)
        if (saved.activeSectionId) setActiveSectionId(saved.activeSectionId)
      }, 0)
    } catch {
      // ignore corrupt
    }
  }, [LS_KEY])

  useEffect(() => {
    if (!LS_KEY || !attemptId || finished) return
    if (autoSaveRef.current) clearTimeout(autoSaveRef.current)
    autoSaveRef.current = setTimeout(() => {
      try {
        localStorage.setItem(
          LS_KEY,
          JSON.stringify({
            answers: answersRef.current,
            snapshotAt: Date.now(),
            timeLeftSnapshot: timeLeft,
            currentTypeIdx,
            activeSectionId,
          }),
        )
      } catch {
        // quota
      }
    }, 2000)
  }, [answers, timeLeft, currentTypeIdx, activeSectionId, LS_KEY, attemptId, finished])

  // ── Backend autosave every 15s ────────────────────────────────────────────
  useEffect(() => {
    if (!attemptId || finished) return
    const interval = setInterval(async () => {
      const allAnswers: { question_id: string; response: Record<string, unknown> }[] = []
      for (const sectionAnswers of Object.values(answersRef.current)) {
        for (const [questionId, response] of Object.entries(sectionAnswers)) {
          if (Object.keys(response).length > 0) {
            allAnswers.push({ question_id: questionId, response })
          }
        }
      }
      if (allAnswers.length > 0) {
        try { await submitAnswers(attemptId, allAnswers) } catch { /* silent */ }
      }
    }, 15000)
    return () => clearInterval(interval)
  }, [attemptId, finished])

  // ── Timer ─────────────────────────────────────────────────────────────────
  const startTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      const ct = currentTypeRef.current
      if (!ct || ct === 'speaking') return
      setTimeLeft((prev) => {
        const val = prev[ct] ?? 0
        if (val <= 1) return { ...prev, [ct]: 0 }
        return { ...prev, [ct]: val - 1 }
      })
    }, 1000)
  }, [])

  useEffect(() => {
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [])

  // ── Advance to next section ───────────────────────────────────────────────

  // When currentTypeIdx changes, reset to first section of new type
  useEffect(() => {
    if (sortedSections.length === 0) return
    const first = sortedSections.find((s) => s.type === currentType)
    if (first) setTimeout(() => setActiveSectionId(first.id), 0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentTypeIdx])

  const switchType = useCallback((type: SectionType) => {
    const idx = presentTypes.indexOf(type)
    if (idx === -1) return
    setCurrentTypeIdx(idx)
    setActiveListeningPart(0)
  }, [presentTypes])

  // ── Timer auto-advance ────────────────────────────────────────────────────
  useEffect(() => {
    if (!attemptId || !test || currentType === 'speaking') return
    const remaining = timeLeft[currentType] ?? Infinity
    if (remaining > 0) return
    if (hasTimedOutRef.current.has(currentType)) return
    hasTimedOutRef.current.add(currentType)

    setTimeout(() => {
      if (isLastType) {
        toast.error("Time is up! Submitting your test…")
        finishMutationRef.current?.()
      } else {
        toast.warning(`Time's up for ${SECTION_LABELS[currentType]}. Moving to ${SECTION_LABELS[nextType!]}.`)
        switchType(nextType!)
      }
    }, 0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeLeft, currentType])

  // ── Mutations ─────────────────────────────────────────────────────────────
  const startMutation = useMutation({
    mutationFn: () => startAttempt(testId),
    onSuccess: (data) => {
      setAttemptId(data.id)
      if (test) {
        const timers: Record<string, number> = {}
        for (const section of sortedSections) {
          if (section.duration_minutes > 0) {
            timers[section.type] = Math.max(
              timers[section.type] ?? 0,
              section.duration_minutes * 60,
            )
          }
        }
        setTimeLeft(timers)
        const first = sortedSections[0]
        if (first) {
          setCurrentTypeIdx(0)
          setActiveSectionId(first.id)
        }
        startTimer()
      }
      toast.success('Test started')
    },
  })

  const finishMutation = useMutation({
    mutationFn: async () => {
      if (!attemptId || !test) throw new Error('No attempt')
      const allAnswers: { question_id: string; response: Record<string, unknown> }[] = []
      for (const sectionAnswers of Object.values(answersRef.current)) {
        for (const [questionId, response] of Object.entries(sectionAnswers)) {
          allAnswers.push({ question_id: questionId, response })
        }
      }
      if (allAnswers.length > 0) {
        try {
          await submitAnswers(attemptId, allAnswers)
        } catch (err) {
          if (isAttemptDone(err)) {
            navigate({ to: '/results/$attemptId', params: { attemptId } })
            return null as unknown as ReturnType<typeof finishAttempt> extends Promise<infer T> ? T : never
          }
          throw err
        }
      }
      return finishAttempt(attemptId)
    },
    onSuccess: (result) => {
      isFinishingRef.current = false
      if (!result) return
      if (timerRef.current) clearInterval(timerRef.current)
      setFinished(true)
      try {
        const keysToRemove: string[] = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key && (key.startsWith(`writing:${attemptId}:`) || key === `attempt:${attemptId}:state`)) {
            keysToRemove.push(key)
          }
        }
        keysToRemove.forEach((k) => localStorage.removeItem(k))
      } catch { /* unavailable */ }
      toast.success('Test submitted!')
      navigate({ to: '/results/$attemptId', params: { attemptId: result.id } })
    },
    onError: (err: unknown) => {
      isFinishingRef.current = false
      if (isAttemptDone(err)) {
        if (attemptId) navigate({ to: '/results/$attemptId', params: { attemptId } })
        return
      }
      toast.error('Failed to submit test. Please try again.')
    },
  })

  const { mutate: finishMutate, isPending: finishIsPending } = finishMutation
  useEffect(() => {
    finishMutationRef.current = () => {
      if (!finishIsPending && !isFinishingRef.current) {
        isFinishingRef.current = true
        finishMutate()
      }
    }
  }, [finishMutate, finishIsPending])

  // ── Handlers ──────────────────────────────────────────────────────────────
  const switchSection = useCallback((id: string) => {
    setActiveSectionId(id)
    setActiveListeningPart(0)
  }, [])

  const updateAnswer = useCallback((sectionId: string, questionId: string, response: Record<string, unknown>) => {
    setAnswers((prev) => ({
      ...prev,
      [sectionId]: { ...prev[sectionId], [questionId]: response },
    }))
  }, [])

  const toggleFlag = useCallback((questionId: string) => {
    setFlagged((prev) => {
      const next = new Set(prev)
      if (next.has(questionId)) next.delete(questionId)
      else next.add(questionId)
      return next
    })
  }, [])

  const handleSubmit = useCallback(() => {
    setShowSubmitDialog(true)
  }, [])

  // ── Derived ───────────────────────────────────────────────────────────────
  const activeSection =
    sortedSections.find((s) => s.id === activeSectionId) ??
    sortedSections.find((s) => s.type === currentType)

  const getAnsweredCount = (section: Section) =>
    Object.values(answers[section.id] ?? {}).filter((resp) => {
      const vals = Object.values(resp)
      return vals.some((v) => {
        if (v === '' || v === null || v === undefined) return false
        if (Array.isArray(v)) return (v as unknown[]).length > 0
        if (typeof v === 'object' && v !== null) return Object.keys(v).length > 0
        return true
      })
    }).length

  const totalQuestions = sortedSections.reduce((sum, s) => sum + (sectionQuestions[s.id]?.length ?? 0), 0)
  const totalAnswered = sortedSections.reduce((sum, s) => sum + getAnsweredCount(s), 0)

  // ── Render guards ─────────────────────────────────────────────────────────
  if (testLoading) {
    return (
      <div className='flex h-screen items-center justify-center bg-white'>
        <Loader2 className='size-8 animate-spin text-slate-400' />
      </div>
    )
  }

  if (!test) {
    return (
      <div className='flex h-screen items-center justify-center bg-white'>
        <Alert variant='destructive' className='max-w-md'>
          <AlertCircle className='size-4' />
          <AlertDescription>Test not found.</AlertDescription>
        </Alert>
      </div>
    )
  }

  // ── Intro screen ──────────────────────────────────────────────────────────
  if (!attemptId) {
    const uniqueTypes = presentTypes
    const totalMinutes = uniqueTypes.reduce((sum, t) => {
      const sec = sortedSections.find((s) => s.type === t)
      return sum + (sec?.duration_minutes ?? 0)
    }, 0)

    return (
      <div className='flex h-screen flex-col items-center justify-center gap-6 bg-white px-4'>
        <div className='w-full max-w-lg text-center'>
          <div className='mx-auto mb-4 flex size-16 items-center justify-center rounded-2xl bg-blue-600'>
            <BookOpen className='size-8 text-white' />
          </div>
          <h1 className='text-3xl font-bold text-slate-900'>{test.title}</h1>
          {test.description && (
            <p className='mt-2 text-base text-slate-500'>{test.description}</p>
          )}
        </div>

        <div className='w-full max-w-lg rounded-xl border border-slate-200 bg-slate-50 p-6'>
          <h2 className='mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500'>
            This test has {uniqueTypes.length} sections:
          </h2>
          <div className='space-y-2'>
            {uniqueTypes.map((t, i) => {
              const sec = sortedSections.find((s) => s.type === t)
              const isSpeaking = t === 'speaking'
              return (
                <div
                  key={t}
                  className='flex items-center justify-between rounded-lg bg-white px-4 py-3 shadow-sm'
                >
                  <div className='flex items-center gap-3'>
                    <span className='flex size-6 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-600'>
                      {i + 1}
                    </span>
                    <span className='text-slate-400'>{SECTION_ICONS[t]}</span>
                    <span className='font-medium text-slate-800'>{SECTION_LABELS[t]}</span>
                    {isSpeaking && (
                      <span className='rounded bg-violet-100 px-1.5 py-0.5 text-[11px] font-medium text-violet-700'>
                        AI Examiner
                      </span>
                    )}
                  </div>
                  <span className='text-sm text-slate-500'>
                    {isSpeaking ? 'Separate session' : `${sec?.duration_minutes ?? '—'} min`}
                  </span>
                </div>
              )
            })}
          </div>
          <div className='mt-4 flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5'>
            <Clock className='size-4 text-slate-400' />
            <span className='text-sm text-slate-600'>
              Total time: <span className='font-semibold'>{formatDuration(totalMinutes)}</span>
            </span>
            <span className='ml-auto text-xs text-slate-400'>You can switch between sections freely.</span>
          </div>
        </div>

        <div className='text-center'>
          <p className='mb-4 text-sm text-slate-500'>
            You can freely switch between sections at any time. Timers run per section.
          </p>
          <Button
            size='lg'
            className='bg-blue-600 px-10 text-base hover:bg-blue-700'
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
          >
            {startMutation.isPending && <Loader2 className='animate-spin' />}
            Start Test
          </Button>
        </div>
      </div>
    )
  }

  // ── Active test ────────────────────────────────────────────────────────────
  return (
    <>
      <div className='flex h-svh flex-col bg-white'>
        {/* ── Header ──────────────────────────────────────────────────── */}
        <header className='flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6'>
          <span className='text-[15px] font-semibold text-slate-900'>
            {test.title}
          </span>
          <div className='flex items-center gap-5'>
            {/* Timer — only shown when section has a timer */}
            {currentType !== 'speaking' && (
              <span
                className={`font-mono text-sm ${
                  (timeLeft[currentType] ?? 0) < 60
                    ? 'font-bold text-red-600'
                    : (timeLeft[currentType] ?? 0) < 300
                      ? 'font-semibold text-amber-500'
                      : 'text-slate-500'
                }`}
              >
                {formatTime(timeLeft[currentType] ?? 0)}
              </span>
            )}
            <span className='text-sm text-slate-400'>
              {totalAnswered}/{totalQuestions} answered
            </span>
            <button
              type='button'
              onClick={() => setShowPalette(true)}
              title='Question navigator'
              className='flex items-center gap-1.5 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-600 transition-colors hover:bg-slate-50'
            >
              <LayoutGrid className='size-4' />
            </button>
            <button
              type='button'
              onClick={handleSubmit}
              disabled={finishIsPending}
              className='flex items-center gap-1.5 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-60'
            >
              {finishIsPending && <Loader2 className='size-3.5 animate-spin' />}
              Submit
            </button>
          </div>
        </header>

        {/* ── Section tabs ──────────────────────────────────────────────── */}
        <SectionProgress
          presentTypes={presentTypes}
          currentType={currentType}
          onSwitchType={switchType}
        />

        {/* ── Sub-section pills (only when >1 sub-section exists) ─────── */}
        <SubSectionBar
          sortedSections={sortedSections}
          sectionQuestions={sectionQuestions}
          currentType={currentType}
          activeSectionId={activeSectionId}
          activeWritingTask={activeWritingTask}
          onSwitchSection={switchSection}
          onSwitchWritingTask={setActiveWritingTask}
        />

        {/* ── Section content ───────────────────────────────────────────── */}
        <main className='relative min-h-0 flex-1 overflow-hidden'>
          {activeSection && (
            <SectionRenderer
              key={activeSection.id}
              section={activeSection}
              questions={sectionQuestions[activeSection.id] ?? []}
              answers={answers[activeSection.id] ?? {}}
              onAnswer={(qId, resp) => updateAnswer(activeSection.id, qId, resp)}
              attemptId={attemptId}
              activeWritingTask={activeWritingTask}
              activeListeningPart={activeListeningPart}
              sortedSections={sortedSections}
              onSwitchSection={switchSection}
              onSwitchWritingTask={setActiveWritingTask}
              flagged={flagged}
              onToggleFlag={toggleFlag}
            />
          )}
        </main>
      </div>

      {/* ── Question palette ───────────────────────────────────────────── */}
      {showPalette && (
        <QuestionPalette
          sortedSections={sortedSections}
          sectionQuestions={sectionQuestions}
          answers={answers}
          flagged={flagged}
          currentType={currentType}
          onClose={() => setShowPalette(false)}
          onJump={(sectionId) => {
            const target = sortedSections.find((s) => s.id === sectionId)
            if (!target) return
            switchType(target.type as SectionType)
            setActiveSectionId(sectionId)
            setActiveListeningPart(0)
          }}
        />
      )}

      {/* ── Submit Test confirm dialog ────────────────────────────────── */}
      <AlertDialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit Test?</AlertDialogTitle>
            <AlertDialogDescription>
              You have answered {totalAnswered} of {totalQuestions} questions.
              Once submitted, you cannot make changes.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Continue test</AlertDialogCancel>
            <AlertDialogAction
              className='bg-red-600 hover:bg-red-700'
              onClick={() => {
                setShowSubmitDialog(false)
                finishMutate()
              }}
            >
              Yes, submit
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

// ── SectionRenderer ────────────────────────────────────────────────────────

function SectionRenderer({
  section,
  questions,
  answers,
  onAnswer,
  attemptId,
  activeWritingTask,
  activeListeningPart,
  sortedSections,
  onSwitchSection,
  onSwitchWritingTask,
  flagged,
  onToggleFlag,
}: {
  section: Section
  questions: Question[]
  answers: SectionAnswers
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  attemptId: string | null
  activeWritingTask: number
  activeListeningPart: number
  sortedSections: Section[]
  onSwitchSection: (id: string) => void
  onSwitchWritingTask: (idx: number) => void
  flagged: Set<string>
  onToggleFlag: (id: string) => void
}) {
  switch (section.type) {
    case 'listening': {
      const listeningSections = sortedSections.filter((s) => s.type === 'listening')
      return (
        <ListeningSection
          section={section}
          questions={questions}
          answers={answers}
          onAnswer={onAnswer}
          activePart={activeListeningPart}
          allSections={listeningSections.length > 1 ? listeningSections : undefined}
          onSwitchSection={onSwitchSection}
          flagged={flagged}
          onToggleFlag={onToggleFlag}
        />
      )
    }
    case 'reading': {
      const readingSiblings = sortedSections.filter((s) => s.type === 'reading')
      const passageIndex = readingSiblings.findIndex((s) => s.id === section.id)
      return (
        <ReadingSection
          section={section}
          passage={section.passage}
          questions={questions}
          answers={answers}
          onAnswer={onAnswer}
          passageIndex={passageIndex >= 0 ? passageIndex : 0}
          totalPassages={readingSiblings.length}
          allSections={readingSiblings.length > 1 ? readingSiblings : undefined}
          onSwitchSection={onSwitchSection}
          flagged={flagged}
          onToggleFlag={onToggleFlag}
        />
      )
    }
    case 'writing':
      return (
        <WritingSection
          questions={questions}
          answers={answers}
          onAnswer={onAnswer}
          attemptId={attemptId}
          activeTaskIdx={activeWritingTask}
          onSwitchTask={onSwitchWritingTask}
        />
      )
    case 'speaking':
      return <SpeakingCta attemptId={attemptId} />
    default:
      return null
  }
}

function SpeakingCta({ attemptId }: { attemptId: string | null }) {
  return (
    <div className='flex h-full flex-col items-center justify-center gap-6 px-4 py-16'>
      <div className='flex size-20 items-center justify-center rounded-2xl bg-violet-100'>
        <Mic className='size-9 text-violet-600' />
      </div>
      <div className='max-w-md text-center'>
        <h2 className='text-2xl font-bold text-slate-900'>Speaking Section</h2>
        <p className='mt-2 text-slate-500'>
          The Speaking section is conducted with an AI examiner in a separate session.
          Your score will be automatically linked to this test attempt.
        </p>
      </div>
      <Button size='lg' className='bg-violet-600 px-8 hover:bg-violet-700' asChild>
        <Link
          to='/speaking-examiner'
          search={attemptId ? { attemptId } : {}}
        >
          Open AI Examiner
        </Link>
      </Button>
      <p className='text-xs text-slate-400'>
        After the speaking test, return here and submit your test.
      </p>
    </div>
  )
}
