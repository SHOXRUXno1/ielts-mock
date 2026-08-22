import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  Outlet,
  useBlocker,
  useNavigate,
  useRouterState,
} from '@tanstack/react-router'
import { AlertCircle, Clock, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  finishAttempt,
  getAttempt,
  getCurrentAttempt,
  startAttempt,
  submitAnswers,
  type AttemptDetailRead,
  type AttemptRead,
} from '@/lib/api/attempts'
import { markScoreReveal } from '@/features/results/lib/score-reveal-flag'
import { fetchQuestions } from '@/lib/api/questions'
import { fetchTest, fetchTestBySlug } from '@/lib/api/tests'
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
import { useAuthStore } from '@/stores/auth-store'
import { markSpeakingAutostartGesture } from '@/features/speaking-examiner/lib/user-activation'
import type { SpeakingSessionControls } from '@/features/speaking-examiner/speaking-examiner-session'
import { ExamHeader } from '../components/take/exam-header'
import { QuestionNavBar } from '../components/take/question-nav-bar'
import { TimeoutDialog } from '../components/take/timeout-dialog'
import { durationByType } from '../data/duration-rules'
import {
  countScoringSlots,
  scoringSlotsForQuestion,
  type Question,
  type Section,
  type SectionType,
} from '../data/schema'
import { isSectionType } from '../lib/part-resolver'
import {
  lsKeyForAttempt,
  PREVIEW_ATTEMPT_ID,
  SECTION_LABELS,
  TYPE_ORDER,
} from './constants'
import { IntroScreen } from './intro-screen'
import { ListeningAudioProvider } from './listening-audio-provider'
import {
  TakeTestProvider,
  useTakeTest,
  type SectionAnswers,
  type TakeTestContextValue,
} from './take-test-context'
import {
  collectAnswersForTypes,
} from './collect-answers'
import { buildPagehideFlushInit } from './pagehide-flush'
import { mergeAnswersServerWins } from './merge-answers'
import { isBenignSectionConflict } from './section-conflict'
import {
  parseSectionExpired,
  toExpiredInfo,
} from './section-expired'
import { asSectionType, nextTypeAfter, nextUnlockableType } from './section-order'
import {
  useSectionExpiryDialog,
  type TimeoutDialogInfo,
} from './use-section-expiry-dialog'
import { useSectionGuard } from './use-section-guard'
import { useSectionProgress } from './use-section-progress'
import { useSectionTimeWarnings } from './use-section-time-warnings'
import { useSectionTimeout } from './use-section-timeout'
import {
  TakeTestTimerProvider,
  useTakeTestTimer,
} from './take-test-timer-context'
import { useTestNavigation } from './use-test-navigation'
import { exitExamFullscreen } from './exam-fullscreen'

function isAttemptDone(err: unknown): boolean {
  const detail = (err as { response?: { data?: { detail?: string } } })
    ?.response?.data?.detail
  return detail === 'Attempt already finished'
}

type ShellProps = {
  mode: 'live' | 'preview' | 'practice'
  bookSlug?: string
  testSlug?: string
  testId?: string
  resume?: string
  /** Practice mode only: single target section type (e.g. 'listening') */
  practiceSectionType?: SectionType
  /** Practice mode only: 1-based part index inside the target section type */
  practicePartNumber?: number
  /** Practice mode only: 'part' (default) or whole 'section'. */
  practiceScope?: 'part' | 'section'
  /**
   * Override for the inner content. Full-mock and preview flows leave this
   * blank and rely on file-based Outlet routing; practice renders its content
   * inline because it isn't nested under a sub-route.
   */
  children?: ReactNode
}

export function TakeTestShell({
  mode,
  bookSlug,
  testSlug,
  testId: testIdProp,
  resume,
  practiceSectionType,
  practicePartNumber,
  practiceScope = 'part',
  children,
}: ShellProps) {
  const navigate = useNavigate()
  const role = useAuthStore((s) => s.auth.user?.role)
  const isPreview = mode === 'preview'
  const isPractice = mode === 'practice'
  const isPracticePart = isPractice && practiceScope === 'part'
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  const testNumber = testSlug
    ? parseInt(testSlug.replace(/^test-/i, ''), 10)
    : NaN

  const slugQuery = useQuery({
    queryKey: ['test-by-slug', bookSlug, testNumber],
    queryFn: () => fetchTestBySlug(bookSlug!, testNumber),
    enabled: !isPreview && !!bookSlug && !isNaN(testNumber),
  })

  const idQuery = useQuery({
    queryKey: ['tests', testIdProp],
    queryFn: () => fetchTest(testIdProp!),
    enabled: isPreview && !!testIdProp,
  })

  const test = isPreview ? idQuery.data : slugQuery.data
  const testLoading = isPreview ? idQuery.isLoading : slugQuery.isLoading
  const testId = test ? String(test.id) : (testIdProp ?? '')

  const sortedSections = useMemo(() => {
    if (!test) return [] as Section[]
    const all = [...test.sections].sort((a, b) => a.order - b.order)
    if (isPractice && practiceSectionType) {
      const siblings = all.filter((s) => s.type === practiceSectionType)
      // Whole-section practice: keep every sibling of the skill.
      if (practiceScope === 'section' || practiceSectionType === 'writing') {
        return siblings
      }
      // Single-part practice: keep only the targeted part row.
      const idx = Math.max(1, practicePartNumber ?? 1) - 1
      return siblings[idx] ? [siblings[idx]] : siblings.slice(0, 1)
    }
    return all
  }, [test, isPractice, practiceSectionType, practicePartNumber, practiceScope])

  const presentTypes = useMemo(() => {
    // Practice runs a single skill in isolation — scoping presentTypes here
    // makes the whole existing machinery (stepper, timer, seal-on-finish,
    // sequential guard) behave as if the test contained just that one skill.
    if (isPractice && practiceSectionType) return [practiceSectionType]
    return TYPE_ORDER.filter((t) => sortedSections.some((s) => s.type === t))
  }, [sortedSections, isPractice, practiceSectionType])

  const isIntroRoute =
    !isPreview &&
    !isPractice &&
    !!bookSlug &&
    !!testSlug &&
    (pathname === `/take-test/${bookSlug}/${testSlug}` ||
      pathname === `/take-test/${bookSlug}/${testSlug}/`)

  const isReviewRoute =
    !isPreview &&
    !!bookSlug &&
    !!testSlug &&
    (pathname === `/take-test/${bookSlug}/${testSlug}/review` ||
      pathname.endsWith('/review'))

  const [localAttemptId, setLocalAttemptId] = useState<string | null>(null)
  const attemptId = isPreview
    ? PREVIEW_ATTEMPT_ID
    : (resume ?? localAttemptId)

  const [attempt, setAttempt] = useState<AttemptRead | AttemptDetailRead | null>(
    null,
  )
  const [attemptError, setAttemptError] = useState<
    'forbidden' | 'not_found' | null
  >(null)
  const [finished, setFinished] = useState(false)
  const [answers, setAnswers] = useState<Record<string, SectionAnswers>>({})
  const [sectionQuestions, setSectionQuestions] = useState<
    Record<string, Question[]>
  >({})
  const [flagged, setFlagged] = useState<Set<string>>(new Set())
  const [showSubmitDialog, setShowSubmitDialog] = useState(false)
  const [isFlushing, setIsFlushing] = useState(false)
  const [speakingActive, setSpeakingActive] = useState(false)

  const speakingControlsRef = useRef<SpeakingSessionControls | null>(null)
  const isFinishingRef = useRef(false)
  const autoSaveRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const answersRef = useRef(answers)
  const resumeNavDoneRef = useRef<string | null>(null)
  const activeTypeRef = useRef<SectionType | null>(null)

  useEffect(() => {
    answersRef.current = answers
  }, [answers])

  const sectionProgress = useSectionProgress({
    attemptId: isPreview ? null : attemptId,
    enabled: !isPreview && !!attemptId && !finished,
    presentTypes,
  })

  useEffect(() => {
    activeTypeRef.current = sectionProgress.activeType
  }, [sectionProgress.activeType])

  const {
    timeoutDialog,
    countdown: timeoutCountdown,
    inputsLocked,
    reportSectionExpired,
    clearTimeoutDialog,
    peekTimeoutNext,
    isExpiryHandled,
  } = useSectionExpiryDialog(sectionProgress.invalidate)

  // When all sections sealed → show submit dialog directly (no review page).
  useEffect(() => {
    if (isPreview || !attemptId || finished) return
    if (sectionProgress.allSealed && !showSubmitDialog) {
      setShowSubmitDialog(true)
    }
  }, [isPreview, attemptId, finished, sectionProgress.allSealed, showSubmitDialog, setShowSubmitDialog])

  /** Only the active section may receive answer writes (sealed → 409). */
  const collectWritableAnswers = useCallback(() => {
    const active = activeTypeRef.current
    if (!active) return []
    return collectAnswersForTypes(answersRef.current, sortedSections, [active])
  }, [sortedSections])

  const activeProgressRow = sectionProgress.activeType
    ? sectionProgress.byType[sectionProgress.activeType]
    : null

  const timerEnabled =
    !isPreview &&
    !!attemptId &&
    !finished &&
    !!activeProgressRow?.ends_at &&
    activeProgressRow.state === 'active'

  const handleExpiredAnswerError = useCallback(
    (err: unknown) => {
      const detail = parseSectionExpired(err)
      if (!detail) return false
      const from = activeTypeRef.current
      if (!from) {
        void sectionProgress.invalidate()
        return true
      }
      const info = toExpiredInfo(detail, from)
      reportSectionExpired({
        from: info.from ?? from,
        next: info.next,
      })
      return true
    },
    [reportSectionExpired, sectionProgress],
  )

  const goToResult = useCallback(
    (id: string, options?: { reveal?: boolean }) => {
      // Every finished-attempt path leaves through here — drop exam fullscreen.
      exitExamFullscreen()
      if (options?.reveal) markScoreReveal(id)
      const search = options?.reveal ? { reveal: true } : undefined
      if (role === 'student') {
        void navigate({
          to: '/student/results/$attemptId',
          params: { attemptId: id },
          search,
        })
      } else {
        void navigate({
          to: '/results/$attemptId',
          params: { attemptId: id },
          search,
        })
      }
    },
    [navigate, role],
  )

  // ── Load attempt (guards + hydrate answers) ──────────────────────────────
  useEffect(() => {
    if (isPreview || !attemptId || attemptId === PREVIEW_ATTEMPT_ID) return
    let cancelled = false
    ;(async () => {
      try {
        const detail = await getAttempt(attemptId)
        if (cancelled) return
        setAttemptError(null)

        if (detail.status !== 'in_progress') {
          goToResult(detail.id)
          return
        }

        setAttempt(detail)

        const fromServer: Record<string, SectionAnswers> = {}
        for (const ans of detail.answers ?? []) {
          const sid = ans.question?.section_id ?? ans.section?.id
          if (!sid) continue
          if (!fromServer[sid]) fromServer[sid] = {}
          fromServer[sid][ans.question_id] = ans.response
        }
        // Server wins; localStorage (prev) only fills question ids missing on server.
        setAnswers((prev) => mergeAnswersServerWins(prev, fromServer))
      } catch (err: unknown) {
        if (cancelled) return
        const status = (err as { response?: { status?: number } })?.response
          ?.status
        if (status === 403) setAttemptError('forbidden')
        else if (status === 404) setAttemptError('not_found')
        else toast.error('Failed to load attempt')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [attemptId, isPreview, goToResult])

  // ── Auto-resolve in-progress attempt when URL has no ?resume ─────────────
  // Practice mode always arrives with a fresh attempt id in the URL, so we
  // skip the "resume last mock" resolver here.
  const shouldResolveCurrent = !isPreview && !isPractice && !attemptId && !!testId
  const currentAttemptQuery = useQuery({
    queryKey: ['attempts', 'current', testId],
    queryFn: () => getCurrentAttempt(testId),
    enabled: shouldResolveCurrent,
    retry: false,
    staleTime: 0,
  })
  const resolvingAttempt =
    shouldResolveCurrent &&
    (currentAttemptQuery.isLoading || currentAttemptQuery.isFetching)

  useEffect(() => {
    if (!shouldResolveCurrent || !bookSlug || !testSlug) return
    if (currentAttemptQuery.isLoading || currentAttemptQuery.isFetching) return
    if (currentAttemptQuery.isError) return

    const current = currentAttemptQuery.data
    const navKey = `${testId}:${current?.id ?? 'none'}:${isIntroRoute ? 'intro' : pathname}`
    if (resumeNavDoneRef.current === navKey) return
    resumeNavDoneRef.current = navKey

    if (current) {
      if (isIntroRoute) {
        void navigate({
          to: '/take-test/$bookSlug/$testSlug/$section/$part',
          params: {
            bookSlug,
            testSlug,
            section: 'listening',
            part: '1',
          },
          search: { resume: current.id },
          replace: true,
        })
        return
      }
      if (pathname.includes('/review')) {
        void navigate({
          to: '/take-test/$bookSlug/$testSlug/review',
          params: { bookSlug, testSlug },
          search: { resume: current.id },
          replace: true,
        })
        return
      }
      const sectionMatch = pathname.match(
        /\/take-test\/[^/]+\/[^/]+\/([^/]+)/,
      )
      const section = sectionMatch?.[1]
      if (section && isSectionType(section)) {
        if (section === 'speaking') {
          void navigate({
            to: '/take-test/$bookSlug/$testSlug/$section',
            params: { bookSlug, testSlug, section: 'speaking' },
            search: { resume: current.id },
            replace: true,
          })
        } else {
          const partMatch = pathname.match(
            /\/take-test\/[^/]+\/[^/]+\/[^/]+\/(\d+)/,
          )
          const part = partMatch?.[1] ?? '1'
          void navigate({
            to: '/take-test/$bookSlug/$testSlug/$section/$part',
            params: { bookSlug, testSlug, section, part },
            search: { resume: current.id },
            replace: true,
          })
        }
      }
      return
    }

    if (!isIntroRoute && !attemptId) {
      void navigate({
        to: '/take-test/$bookSlug/$testSlug',
        params: { bookSlug, testSlug },
        replace: true,
      })
    }
  }, [
    shouldResolveCurrent,
    attemptId,
    currentAttemptQuery.isLoading,
    currentAttemptQuery.isFetching,
    currentAttemptQuery.isError,
    currentAttemptQuery.data,
    bookSlug,
    testSlug,
    testId,
    isIntroRoute,
    pathname,
    navigate,
  ])

  useEffect(() => {
    if (isPreview || !attemptId || finished) return
    const warnUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
    }
    // keepalive fetch survives tab close (sendBeacon can't set Authorization).
    const flushOnHide = () => {
      const req = buildPagehideFlushInit({
        baseUrl: (import.meta.env.VITE_API_URL as string) || '',
        attemptId,
        token: useAuthStore.getState().auth.accessToken,
        answers: collectWritableAnswers(),
      })
      if (!req) return
      void fetch(req.url, req.init).catch(() => {
        /* best-effort — localStorage backup remains */
      })
    }
    window.addEventListener('beforeunload', warnUnload)
    window.addEventListener('pagehide', flushOnHide)
    return () => {
      window.removeEventListener('beforeunload', warnUnload)
      window.removeEventListener('pagehide', flushOnHide)
    }
  }, [attemptId, finished, isPreview, collectWritableAnswers])

  const activeSectionFromPath = useMemo(() => {
    if (isReviewRoute) return sortedSections[0] ?? null
    // Single-part practice has only one section row — no URL part lookup.
    if (isPracticePart) return sortedSections[0] ?? null
    const m = pathname.match(/\/(listening|reading|writing|speaking)(?:\/(\d+))?/)
    if (!m) return sortedSections[0] ?? null
    const type = m[1] as SectionType
    const part = m[2] ? parseInt(m[2], 10) : 1
    const siblings = sortedSections.filter((s) => s.type === type)
    if (type === 'writing') return siblings[0] ?? null
    return siblings[Math.max(0, part - 1)] ?? siblings[0] ?? null
  }, [pathname, sortedSections, isReviewRoute, isPracticePart])

  useEffect(() => {
    if (!test) return
    let cancelled = false
    ;(async () => {
      const result: Record<string, Question[]> = { ...sectionQuestions }
      const loadOne = async (section: Section) => {
        if (result[section.id]?.length) return
        try {
          const questions = await fetchQuestions(section.id)
          // Practice writing: only surface the targeted task's essay so the
          // student can't accidentally answer the other one.
          if (
            isPracticePart &&
            practiceSectionType === 'writing' &&
            section.type === 'writing' &&
            practicePartNumber
          ) {
            result[section.id] = questions.filter((q) => {
              const task = q.task_number ?? q.order
              return task === practicePartNumber
            })
          } else {
            result[section.id] = questions
          }
        } catch {
          result[section.id] = []
        }
      }
      if (activeSectionFromPath) {
        await loadOne(activeSectionFromPath)
        if (!cancelled) setSectionQuestions({ ...result })
      }
      for (const section of sortedSections) {
        if (cancelled) return
        await loadOne(section)
      }
      if (!cancelled) setSectionQuestions({ ...result })
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [test?.id, activeSectionFromPath?.id, isReviewRoute, isPracticePart, practiceSectionType, practicePartNumber])

  const LS_KEY =
    !isPreview && attemptId && attemptId !== PREVIEW_ATTEMPT_ID
      ? lsKeyForAttempt(attemptId)
      : null

  const [hydratedLsKey, setHydratedLsKey] = useState<string | null>(null)
  if (LS_KEY && LS_KEY !== hydratedLsKey) {
    setHydratedLsKey(LS_KEY)
    try {
      const raw = localStorage.getItem(LS_KEY)
      if (raw) {
        const saved = JSON.parse(raw) as {
          answers?: Record<string, SectionAnswers>
          // Legacy cumulative-timer keys — ignored (startedAt, timeLeft*, deadlines)
        }
        if (saved.answers) {
          setAnswers((prev) => {
            const merged = { ...saved.answers }
            for (const [sid, qs] of Object.entries(prev)) {
              merged[sid] = { ...(merged[sid] ?? {}), ...qs }
            }
            return merged as Record<string, SectionAnswers>
          })
          // Rewrite without legacy timer fields if present
          localStorage.setItem(
            LS_KEY,
            JSON.stringify({ answers: saved.answers }),
          )
        }
      }
    } catch {
      // ignore corrupt
    }
  }

  const persistLocal = useCallback(() => {
    if (!LS_KEY) return
    try {
      localStorage.setItem(
        LS_KEY,
        JSON.stringify({
          answers: answersRef.current,
        }),
      )
    } catch {
      // quota
    }
  }, [LS_KEY])

  const cancelAutoSave = useCallback(() => {
    if (autoSaveRef.current) {
      clearTimeout(autoSaveRef.current)
      autoSaveRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!LS_KEY || !attemptId || finished) return
    if (autoSaveRef.current) clearTimeout(autoSaveRef.current)
    autoSaveRef.current = setTimeout(persistLocal, 2000)
    return () => {
      if (autoSaveRef.current) clearTimeout(autoSaveRef.current)
    }
  }, [answers, LS_KEY, attemptId, finished, persistLocal])

  useEffect(() => {
    if (isPreview || !attemptId || finished) return
    const interval = setInterval(async () => {
      if (inputsLocked || isExpiryHandled()) return
      const all = collectWritableAnswers()
      if (all.length > 0) {
        try {
          await submitAnswers(attemptId, all)
        } catch (err) {
          if (handleExpiredAnswerError(err)) return
          if (!isBenignSectionConflict(err) && import.meta.env.DEV) {
            console.warn('Autosave failed', err)
          }
        }
      }
    }, 15_000)
    return () => clearInterval(interval)
  }, [
    attemptId,
    finished,
    isPreview,
    inputsLocked,
    handleExpiredAnswerError,
    collectWritableAnswers,
    isExpiryHandled,
  ])

  /** Flush active-section answers. Returns true if SECTION_EXPIRED was handled. */
  const flushBeforeNavigate = useCallback(async (): Promise<boolean> => {
    if (isPreview || !attemptId || finished) {
      persistLocal()
      return false
    }
    if (autoSaveRef.current) {
      clearTimeout(autoSaveRef.current)
      autoSaveRef.current = null
    }
    persistLocal()
    const all = collectWritableAnswers()
    if (all.length === 0) return false
    setIsFlushing(true)
    let expired = false
    try {
      await submitAnswers(attemptId, all)
    } catch (err: unknown) {
      if (handleExpiredAnswerError(err)) expired = true
      else if (!isBenignSectionConflict(err) && import.meta.env.DEV) {
        console.warn('Flush failed', err)
      }
    } finally {
      setIsFlushing(false)
    }
    return expired
  }, [
    isPreview,
    attemptId,
    finished,
    persistLocal,
    handleExpiredAnswerError,
    collectWritableAnswers,
  ])

  const startMutation = useMutation({
    mutationFn: () => startAttempt(testId),
    onSuccess: (data) => {
      setLocalAttemptId(data.id)
      setAttempt(data)
      toast.success('Test started')
    },
    onError: () => toast.error('Failed to start test'),
  })

  useEffect(() => {
    if (isPreview || isPractice || !isIntroRoute || !attemptId || !bookSlug || !testSlug) {
      return
    }
    void navigate({
      to: '/take-test/$bookSlug/$testSlug/$section/$part',
      params: {
        bookSlug,
        testSlug,
        section: presentTypes[0] ?? 'listening',
        part: '1',
      },
      search: { resume: attemptId },
      replace: true,
    })
  }, [
    isPreview,
    isIntroRoute,
    attemptId,
    bookSlug,
    testSlug,
    presentTypes,
    navigate,
  ])

  // Redirect /review to active section (review page removed; submit is a modal now).
  useEffect(() => {
    if (!isReviewRoute || !attemptId || !bookSlug || !testSlug) return
    void navigate({
      to: '/take-test/$bookSlug/$testSlug/$section/$part',
      params: {
        bookSlug,
        testSlug,
        section: presentTypes[0] ?? 'listening',
        part: '1',
      },
      search: { resume: attemptId },
      replace: true,
    })
  }, [isReviewRoute, attemptId, bookSlug, testSlug, presentTypes, navigate])

  const finishMutation = useMutation({
    mutationFn: async () => {
      if (!attemptId) throw new Error('No attempt')
      setIsFlushing(true)
      try {
        // Only active-section answers are writable; sealed sections 409 the whole batch.
        const all = collectWritableAnswers()
        if (all.length > 0) {
          try {
            await submitAnswers(attemptId, all)
          } catch (err) {
            if (
              !handleExpiredAnswerError(err) &&
              !isBenignSectionConflict(err)
            ) {
              // Still finish — answers may already be on the server.
              if (import.meta.env.DEV) console.warn('Pre-finish flush failed', err)
            }
          }
        }
      } finally {
        setIsFlushing(false)
      }
      return finishAttempt(attemptId)
    },
    onSuccess: (result) => {
      setFinished(true)
      if (LS_KEY) {
        try {
          localStorage.removeItem(LS_KEY)
        } catch {
          /* ignore */
        }
      }
      try {
        const prefix = `writing:${attemptId}:`
        for (let i = localStorage.length - 1; i >= 0; i--) {
          const key = localStorage.key(i)
          if (key?.startsWith(prefix)) localStorage.removeItem(key)
        }
      } catch {
        /* ignore */
      }
      toast.success('Test submitted!')
      goToResult(result.id, { reveal: true })
    },
    onError: (err: unknown) => {
      isFinishingRef.current = false
      if (isAttemptDone(err)) {
        if (attemptId) goToResult(attemptId, { reveal: true })
        return
      }
      toast.error('Failed to submit test. Please try again.')
    },
  })

  const { mutate: finishMutate, isPending: finishIsPending } = finishMutation

  const updateAnswer = useCallback(
    (sectionId: string, questionId: string, response: Record<string, unknown>) => {
      if (inputsLocked) return
      setAnswers((prev) => ({
        ...prev,
        [sectionId]: { ...prev[sectionId], [questionId]: response },
      }))
    },
    [inputsLocked],
  )

  const toggleFlag = useCallback((questionId: string) => {
    setFlagged((prev) => {
      const next = new Set(prev)
      if (next.has(questionId)) next.delete(questionId)
      else next.add(questionId)
      return next
    })
  }, [])

  const handleSubmit = useCallback(() => {
    if (isPreview) {
      window.close()
      return
    }
    setShowSubmitDialog(true)
  }, [isPreview])

  const blocker = useBlocker({
    shouldBlockFn: ({ current, next }) => {
      if (!speakingActive) return false
      const cur = current.pathname
      const nxt = next.pathname
      const leavingSpeaking =
        cur.includes('/speaking') && !nxt.includes('/speaking')
      return leavingSpeaking
    },
    withResolver: true,
    enableBeforeUnload: speakingActive,
  })

  const switchGuardOpen = blocker.status === 'blocked'

  const confirmSpeakingLeave = useCallback(() => {
    speakingControlsRef.current?.stop()
    setSpeakingActive(false)
    if (blocker.status === 'blocked') {
      blocker.proceed()
    }
  }, [blocker])

  const cancelSpeakingLeave = useCallback(() => {
    if (blocker.status === 'blocked') {
      blocker.reset()
    }
  }, [blocker])

  const ctxValue: TakeTestContextValue | null = test
    ? {
        mode,
        isPreview,
        isPractice,
        practiceScope,
        isReviewRoute,
        test,
        testId,
        bookSlug,
        testSlug,
        attemptId,
        attempt,
        sortedSections,
        presentTypes,
        sectionQuestions,
        answers,
        updateAnswer,
        flagged,
        toggleFlag,
        speakingActive,
        setSpeakingActive,
        speakingControlsRef,
        flushBeforeNavigate,
        isFlushing,
        finished,
        startTest: () => startMutation.mutate(),
        isStarting: startMutation.isPending,
        submitTest: handleSubmit,
        isSubmitting: finishIsPending,
        showSubmitDialog,
        setShowSubmitDialog,
        attemptError,
        progress: sectionProgress.progress,
        sealedTypes: sectionProgress.sealedTypes,
        activeSectionType: sectionProgress.activeType,
        allSealed: sectionProgress.allSealed,
        stateOf: sectionProgress.stateOf,
        inputsLocked: inputsLocked || !!timeoutDialog,
        reportSectionExpired,
        enterSection: sectionProgress.enterSection,
        sealSection: sectionProgress.sealSection,
        isEntering: sectionProgress.isEntering,
        isSealing: sectionProgress.isSealing,
      }
    : null

  const testError = isPreview ? idQuery.isError : slugQuery.isError

  if (testLoading || resolvingAttempt) {
    return (
      <div className='flex h-screen items-center justify-center bg-white'>
        <Loader2 className='size-8 animate-spin text-slate-400' />
      </div>
    )
  }

  if (testError || !test || !ctxValue) {
    return (
      <div className='flex h-screen items-center justify-center bg-white'>
        <Alert variant='destructive' className='max-w-md'>
          <AlertCircle className='size-4' />
          <AlertDescription>Test not found.</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (attemptError === 'forbidden') {
    return (
      <div className='flex h-screen items-center justify-center bg-white px-4'>
        <Alert variant='destructive' className='max-w-md'>
          <AlertCircle className='size-4' />
          <AlertDescription>
            You do not have access to this attempt.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (attemptError === 'not_found') {
    return (
      <div className='flex h-screen items-center justify-center bg-white px-4'>
        <Alert variant='destructive' className='max-w-md'>
          <AlertCircle className='size-4' />
          <AlertDescription>Attempt not found.</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (isIntroRoute) {
    return attemptId ? (
      <div className='flex h-screen items-center justify-center bg-white'>
        <Loader2 className='size-8 animate-spin text-slate-400' />
      </div>
    ) : (
      <IntroScreen
        test={test}
        sortedSections={sortedSections}
        onStart={() => startMutation.mutate()}
        onCancel={() => {
          window.location.href = role === 'student'
            ? '/student/tests'
            : '/tests'
        }}
        isStarting={startMutation.isPending}
      />
    )
  }

  return (
    <TakeTestProvider value={ctxValue}>
      <TakeTestTimerProvider
        endsAt={activeProgressRow?.ends_at}
        skewMs={sectionProgress.skewMs}
        enabled={timerEnabled}
      >
        <ListeningAudioProvider>
          <ActiveChrome
            onConfirmSubmit={() => {
              setShowSubmitDialog(false)
              finishMutate()
            }}
            switchGuardOpen={switchGuardOpen}
            onConfirmSpeakingLeave={confirmSpeakingLeave}
            onCancelSpeakingLeave={cancelSpeakingLeave}
            timeoutDialog={timeoutDialog}
            timeoutCountdown={timeoutCountdown}
            clearTimeoutDialog={clearTimeoutDialog}
            peekTimeoutNext={peekTimeoutNext}
            persistLocal={persistLocal}
            cancelAutoSave={cancelAutoSave}
            setIsFlushing={setIsFlushing}
          >
            {children ?? <Outlet />}
          </ActiveChrome>
        </ListeningAudioProvider>
      </TakeTestTimerProvider>
    </TakeTestProvider>
  )
}

function ActiveChrome({
  children,
  onConfirmSubmit,
  switchGuardOpen,
  onConfirmSpeakingLeave,
  onCancelSpeakingLeave,
  timeoutDialog,
  timeoutCountdown,
  clearTimeoutDialog,
  peekTimeoutNext,
  persistLocal,
  cancelAutoSave,
  setIsFlushing,
}: {
  children: ReactNode
  onConfirmSubmit: () => void
  switchGuardOpen: boolean
  onConfirmSpeakingLeave: () => void
  onCancelSpeakingLeave: () => void
  timeoutDialog: TimeoutDialogInfo | null
  timeoutCountdown: number | null
  clearTimeoutDialog: () => void
  peekTimeoutNext: () => SectionType | null
  persistLocal: () => void
  cancelAutoSave: () => void
  setIsFlushing: (value: boolean) => void
}) {
  const ctx = useTakeTest()
  const { remainingMs, remainingSec, timerExpired } = useTakeTestTimer()
  const nav = useTestNavigation()
  const guard = useSectionGuard()

  const {
    test,
    isPreview,
    isPractice,
    presentTypes,
    answers,
    sectionQuestions,
    sortedSections,
    showSubmitDialog,
    setShowSubmitDialog,
    isFlushing,
    isSubmitting,
    submitTest,
    attemptId,
    sealedTypes,
    progress,
    flushBeforeNavigate,
    sealSection,
    enterSection,
    isSealing,
    bookSlug,
    testSlug,
    reportSectionExpired,
    activeSectionType,
    stateOf,
  } = ctx

  const currentType = nav.currentType
  const currentTypeIdx = nav.currentTypeIdx
  /** Progress-active section — not URL (URL can briefly point at a skipped tab). */
  const timedSectionType = activeSectionType ?? currentType
  const unlockableType = nextUnlockableType(
    presentTypes,
    stateOf,
    activeSectionType,
  )
  const [finishSectionOpen, setFinishSectionOpen] = useState(false)
  const [isFinishingSection, setIsFinishingSection] = useState(false)

  const onTimeoutExhausted = useCallback(() => {
    if (bookSlug && testSlug && attemptId) guard.triggerSubmit()
  }, [bookSlug, testSlug, attemptId, guard])

  useSectionTimeWarnings({
    remainingMs,
    sectionType: timedSectionType,
    enabled: !isPreview && !!attemptId,
    // Single-part practice is often ≤8 min — a "5 minutes remaining" toast
    // at the start is noise. Full mock + whole-section practice keep it.
    suppressFiveMin: isPractice && ctx.practiceScope === 'part',
  })

  const { handleContinue: handleTimeoutContinue } = useSectionTimeout({
    enabled: !isPreview && !!attemptId,
    timerExpired,
    deadlineType: activeSectionType,
    expiredType: timedSectionType,
    presentTypes,
    answers,
    sortedSections,
    timeoutDialog,
    countdown: timeoutCountdown,
    peekNext: peekTimeoutNext,
    reportSectionExpired,
    clearTimeoutDialog,
    flushBeforeNavigate,
    sealSection,
    enterSection,
    goToSection: nav.goToSection,
    onExhausted: onTimeoutExhausted,
  })

  const handleFinishSection = useCallback(async () => {
    if (isSealing || isFinishingSection) return
    const sealType = activeSectionType ?? currentType
    if (!sealType || sealedTypes.has(sealType)) return
    cancelAutoSave()
    persistLocal()
    setIsFinishingSection(true)
    setIsFlushing(true)
    try {
      // Seal persists answers — do not flush first (that was a second 40-row write).
      const all = collectAnswersForTypes(answers, sortedSections, [sealType])
      let next: SectionType | null = null
      try {
        const result = await sealSection({
          sectionType: sealType,
          answers: all,
          reason: 'manual',
        })
        next = asSectionType(result.next_section)
      } catch (err) {
        // Already sealed (double-click / confirm-switch race) — keep going.
        const detail = (err as { response?: { data?: { detail?: unknown } } })
          ?.response?.data?.detail
        if (detail !== 'Section not active') throw err
        next = nextTypeAfter(presentTypes, sealType)
      }
      setFinishSectionOpen(false)
      if (next) {
        if (next === 'speaking') markSpeakingAutostartGesture()
        try {
          await enterSection(next)
        } catch {
          /* may already be active */
        }
        await nav.goToSection(next)
      } else {
        guard.triggerSubmit()
      }
    } catch {
      toast.error('Failed to finish section')
    } finally {
      setIsFinishingSection(false)
      setIsFlushing(false)
    }
  }, [
    answers,
    persistLocal,
    cancelAutoSave,
    setIsFlushing,
    sealSection,
    activeSectionType,
    currentType,
    enterSection,
    nav,
    guard,
    presentTypes,
    sortedSections,
    isSealing,
    isFinishingSection,
    sealedTypes,
  ])

  const getAnsweredCount = (section: Section) => {
    const secAnswers = answers[section.id] ?? {}
    const qsMap = new Map(
      (sectionQuestions[section.id] ?? []).map((q) => [q.id, q]),
    )
    let count = 0
    for (const [qId, resp] of Object.entries(secAnswers)) {
      const vals = Object.values(resp)
      const hasAnswer = vals.some((v) => {
        if (v === '' || v === null || v === undefined) return false
        if (Array.isArray(v)) return (v as unknown[]).length > 0
        if (typeof v === 'object' && v !== null) return Object.keys(v).length > 0
        return true
      })
      if (!hasAnswer) continue
      const q = qsMap.get(qId)
      // multi_select: count selected options, not the full choose_n span
      if (q?.question_type === 'multi_select' && Array.isArray(resp.selected)) {
        const slots = scoringSlotsForQuestion(q)
        count += Math.min((resp.selected as unknown[]).length, slots)
      } else {
        count += 1
      }
    }
    return count
  }

  // Header counter: current skill only (not cumulative L+R+W).
  const currentSections = sortedSections.filter((s) => s.type === currentType)
  const totalQuestions = currentSections.reduce(
    (sum, s) => sum + countScoringSlots(sectionQuestions[s.id] ?? []),
    0,
  )
  const totalAnswered = currentSections.reduce(
    (sum, s) => sum + getAnsweredCount(s),
    0,
  )

  const sectionStates = useMemo(() => {
    const map: Partial<
      Record<SectionType, { state: string; sealedAt?: string | null }>
    > = {}
    for (const s of progress?.sections ?? []) {
      map[s.section_type as SectionType] = {
        state: s.state,
        sealedAt: s.sealed_at,
      }
    }
    for (const t of sealedTypes) {
      if (!map[t]) map[t] = { state: 'sealed' }
    }
    return map
  }, [progress, sealedTypes])

  const speakingActiveChrome = currentType === 'speaking' && !isPreview
  // Speaking is AI-paced; only surface the safety-cap countdown when <5 min left.
  const showAiPaced = speakingActiveChrome && remainingSec > 300
  const showCountdown =
    !isPreview &&
    !!attemptId &&
    !!progress &&
    remainingSec >= 0 &&
    (!speakingActiveChrome || remainingSec <= 300)

  const switchToDuration = guard.pendingSwitch
    ? durationByType(test.section_settings)[guard.pendingSwitch.to]
    : null

  return (
    <>
      <div className='flex h-svh flex-col bg-white'>
        {isPreview && (
          <div className='sticky top-0 z-50 flex items-center justify-between gap-3 bg-orange-500 px-3 py-2 text-sm font-medium text-white sm:px-6 sm:py-2.5'>
            <span>
              <span className='hidden sm:inline'>Preview Mode — </span>
              <span className='sm:hidden'>Preview — </span>
              Section {currentTypeIdx + 1} of {presentTypes.length} (
              {SECTION_LABELS[currentType]})
              <span className='hidden sm:inline'> — answers not saved</span>
            </span>
            <button
              type='button'
              onClick={() => window.close()}
              className='shrink-0 rounded-md border border-white/40 bg-white/15 px-3 py-1 text-xs font-semibold hover:bg-white/25'
            >
              Close Preview
            </button>
          </div>
        )}

        <ExamHeader
          title={test.title}
          isPreview={isPreview}
          isPractice={isPractice}
          presentTypes={presentTypes}
          currentType={currentType}
          sectionStates={isPreview ? undefined : sectionStates}
          unlockableType={isPreview ? null : unlockableType}
          onSwitchType={(type) =>
            isPreview ? void nav.goToSection(type) : guard.requestSwitch(type)
          }
          showAiPaced={showAiPaced}
          showCountdown={showCountdown}
          remainingSec={remainingSec}
          totalAnswered={totalAnswered}
          totalQuestions={totalQuestions}
          showFinishSection={!isPreview && !isPractice}
          onFinishSection={() => setFinishSectionOpen(true)}
          finishDisabled={
            isSealing ||
            isFinishingSection ||
            !activeSectionType ||
            sealedTypes.has(activeSectionType)
          }
          onSubmit={submitTest}
          isSubmitting={isSubmitting}
        />

        <main className='relative min-h-0 flex-1 overflow-hidden'>
          {children}
        </main>

        <QuestionNavBar />
      </div>

      {isFlushing && (
        <div className='fixed inset-0 z-[100] flex items-center justify-center bg-black/40'>
          <div className='flex items-center gap-3 rounded-xl bg-white px-8 py-5 shadow-lg'>
            <Loader2 className='size-5 animate-spin text-blue-600' />
            <span className='text-sm font-medium text-slate-700'>
              {isFinishingSection
                ? 'Finishing section…'
                : 'Saving your answers…'}
            </span>
          </div>
        </div>
      )}

      {!isPreview && (
        <AlertDialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                {isPractice ? 'Finish practice?' : 'All done! Submit your test?'}
              </AlertDialogTitle>
              <AlertDialogDescription>
                You have answered {totalAnswered} of {totalQuestions} questions
                {isPractice
                  ? '. Your practice run will be scored right away.'
                  : ' in this section. Once submitted, your test will be graded.'}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Go back</AlertDialogCancel>
              <AlertDialogAction
                className='bg-blue-600 hover:bg-blue-700'
                onClick={onConfirmSubmit}
              >
                {isPractice ? 'Finish practice' : 'Submit test'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      <AlertDialog
        open={switchGuardOpen}
        onOpenChange={(open) => {
          if (!open) onCancelSpeakingLeave()
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Leave speaking session?</AlertDialogTitle>
            <AlertDialogDescription>
              You have an active speaking session. Switching sections will end
              it. Continue?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={onCancelSpeakingLeave}>
              Stay
            </AlertDialogCancel>
            <AlertDialogAction
              className='bg-blue-600 hover:bg-blue-700'
              onClick={onConfirmSpeakingLeave}
            >
              Switch section
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={guard.confirmOpen}
        onOpenChange={(open) => {
          if (!open) void guard.cancelSwitch()
        }}
      >
        <AlertDialogContent className='max-w-sm'>
          <AlertDialogHeader className='items-center text-center'>
            <div className='mx-auto mb-2 flex size-12 items-center justify-center rounded-full bg-blue-50'>
              <AlertCircle className='size-6 text-blue-500' />
            </div>
            <AlertDialogTitle className='text-xl'>
              Start{' '}
              {guard.pendingSwitch
                ? SECTION_LABELS[guard.pendingSwitch.to]
                : 'section'}
              ?
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className='space-y-1 pt-1 text-center text-sm text-muted-foreground'>
                <p className='font-medium text-slate-700'>
                  {guard.pendingSwitch
                    ? `This will close ${SECTION_LABELS[guard.pendingSwitch.from]} and you cannot return to it.`
                    : 'This section will be sealed.'}
                </p>
                {switchToDuration != null && (
                  <p className='flex items-center justify-center gap-1.5 pt-1 text-slate-500'>
                    <Clock className='size-3.5' />
                    {guard.pendingSwitch
                      ? SECTION_LABELS[guard.pendingSwitch.to]
                      : 'Section'}{' '}
                    time: {switchToDuration} minutes
                  </p>
                )}
                {guard.pendingSwitch?.to === 'speaking' &&
                  switchToDuration == null && (
                    <p className='pt-1 text-slate-500'>
                      Speaking time: AI-paced (untimed)
                    </p>
                  )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className='mt-2 flex gap-2 sm:justify-center'>
            <AlertDialogCancel className='flex-1'>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className='flex-1 bg-blue-600 hover:bg-blue-700'
              onClick={() => void guard.confirmSwitch()}
            >
              Start{' '}
              {guard.pendingSwitch
                ? SECTION_LABELS[guard.pendingSwitch.to]
                : 'section'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <TimeoutDialog
        info={timeoutDialog}
        countdown={timeoutCountdown}
        onContinue={() => void handleTimeoutContinue()}
      />

      <AlertDialog open={finishSectionOpen} onOpenChange={setFinishSectionOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Finish{' '}
              {SECTION_LABELS[activeSectionType ?? currentType]}?
            </AlertDialogTitle>
            <AlertDialogDescription>
              You will not be able to return to this section. Next up:{' '}
              {unlockableType
                ? SECTION_LABELS[unlockableType]
                : 'review'}
              .
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isFinishingSection}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              className='bg-blue-600 hover:bg-blue-700'
              disabled={isFinishingSection}
              onClick={(e) => {
                e.preventDefault()
                void handleFinishSection()
              }}
            >
              {isFinishingSection && (
                <Loader2 className='mr-1.5 size-3.5 animate-spin' />
              )}
              Finish section
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
