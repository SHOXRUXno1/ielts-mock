import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type MutableRefObject,
} from 'react'
import { toast } from 'sonner'
import {
  isSpeakingAbortError,
  scoreExaminerWithRetry,
  type ConversationTurn,
  type ExaminerScore,
} from '@/lib/api/speaking-examiner'
import { submitSpeakingScore } from '@/lib/api/attempts'
import { isLiveSpeakingPhase } from '../lib/is-live-phase'
import type { Phase } from '../types/phase'

export type AudioDoneContext = {
  isPart2CueCard: boolean
  afterBeginSpeaking: boolean
}

type UseSpeakingFlowOptions = {
  liveSessionId: string | null
  abortControllerRef?: MutableRefObject<AbortController | null>
  attemptId?: string | null
}

export function useSpeakingFlow({
  liveSessionId,
  abortControllerRef,
  attemptId,
}: UseSpeakingFlowOptions) {
  const [phase, setPhaseState] = useState<Phase>('idle')
  const [score, setScore] = useState<ExaminerScore | null>(null)
  const [scoredHistory, setScoredHistory] = useState<ConversationTurn[] | null>(
    null,
  )
  const [scoringFailed, setScoringFailed] = useState(false)
  const phaseRef = useRef<Phase>('idle')
  const pendingScoreHistoryRef = useRef<ConversationTurn[] | null>(null)
  const liveSessionIdRef = useRef(liveSessionId)

  useEffect(() => {
    phaseRef.current = phase
  }, [phase])

  useEffect(() => {
    liveSessionIdRef.current = liveSessionId
  }, [liveSessionId])

  const setPhase = useCallback((next: Phase) => {
    phaseRef.current = next
    setPhaseState(next)
  }, [])

  const runScoring = useCallback(
    async (history: ConversationTurn[]) => {
      setPhase('scoring')
      setScoringFailed(false)
      setScoredHistory([...history])
      const signal = abortControllerRef?.current?.signal

      try {
        const result = await scoreExaminerWithRetry(
          history,
          liveSessionIdRef.current,
          signal,
        )
        if (phaseRef.current !== 'scoring') return

        setScore(result)
        setPhase('done')

        // Post speaking score back to the test attempt if launched from one
        if (attemptId && result.overall_band != null) {
          try {
            await submitSpeakingScore(attemptId, {
              speaking_band: result.overall_band,
              score_json: result as unknown as Record<string, unknown>,
              session_id: liveSessionIdRef.current,
            })
            toast.success('Speaking score saved to your test attempt.')
          } catch {
            // Non-fatal — the score is displayed locally regardless
            if (import.meta.env.DEV) {
              // eslint-disable-next-line no-console
              console.warn('[SpeakingFlow] failed to save speaking score to attempt')
            }
          }
        }
      } catch (err) {
        if (phaseRef.current !== 'scoring') return
        if (isSpeakingAbortError(err)) return
        setScoringFailed(true)
        toast.error('Failed to compute score')
        setPhase('done')
      }
    },
    [setPhase, abortControllerRef, attemptId],
  )

  const retryScoring = useCallback(
    async (history: ConversationTurn[]) => {
      await runScoring(history)
    },
    [runScoring],
  )

  const onSimliLoadingComplete = useCallback(() => {
    if (isLiveSpeakingPhase(phaseRef.current)) return
    if (phaseRef.current === 'loading') setPhase('idle')
  }, [setPhase, phaseRef])

  const onStartSession = useCallback(() => {
    setPhase('thinking')
  }, [setPhase])

  const onExaminerTurnReady = useCallback(() => {
    setPhase('playing')
  }, [setPhase])

  const onRecordingStopped = useCallback(() => {
    if (phaseRef.current === 'recording') setPhase('transcribing')
  }, [setPhase])

  const onTranscriptReady = useCallback(() => {
    if (phaseRef.current === 'transcribing') setPhase('thinking')
  }, [setPhase])

  const onTranscriptFailed = useCallback(() => {
    if (phaseRef.current === 'transcribing') setPhase('ready')
  }, [setPhase])

  const scheduleScoringAfterSpeech = useCallback(
    (history: ConversationTurn[]) => {
      pendingScoreHistoryRef.current = history
    },
    [],
  )

  const onExaminerAudioDone = useCallback(
    (ctx: AudioDoneContext) => {
      if (phaseRef.current !== 'playing') return

      if (pendingScoreHistoryRef.current) {
        const h = pendingScoreHistoryRef.current
        pendingScoreHistoryRef.current = null
        void runScoring(h)
        return
      }

      if (ctx.afterBeginSpeaking) {
        setPhase('recording')
        return
      }

      if (ctx.isPart2CueCard) {
        setPhase('prep')
        return
      }

      setPhase('ready')
    },
    [setPhase, runScoring],
  )

  const onPrepTimerDone = useCallback(() => {
    if (phaseRef.current === 'prep') setPhase('playing')
  }, [setPhase])

  const resetFlow = useCallback(() => {
    pendingScoreHistoryRef.current = null
    setScoringFailed(false)
    setScoredHistory(null)
    setPhase('idle')
    setScore(null)
  }, [setPhase])

  const beginLoading = useCallback(() => {
    // Autostart / live turns must not be kicked back into the Simli loader.
    if (isLiveSpeakingPhase(phaseRef.current)) return
    setPhase('loading')
  }, [setPhase, phaseRef])

  return {
    phase,
    phaseRef,
    score,
    scoredHistory,
    scoringFailed,
    setPhase,
    beginLoading,
    onSimliLoadingComplete,
    onStartSession,
    onExaminerTurnReady,
    onRecordingStopped,
    onTranscriptReady,
    onTranscriptFailed,
    onExaminerAudioDone,
    onPrepTimerDone,
    scheduleScoringAfterSpeech,
    runScoring,
    retryScoring,
    resetFlow,
  }
}
