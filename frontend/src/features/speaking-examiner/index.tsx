import { useCallback, useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getRouteApi } from '@tanstack/react-router'
import { Mic, Square } from 'lucide-react'
import { toast } from 'sonner'
import {
  getPart2BeginPhrase,
  getSpeakingApiErrorDetail,
  isSpeakingAbortError,
  NO_SPEECH_TRANSCRIPT,
  startExaminerWithRetry,
  transcribeAndRespondWithRetry,
  type ConversationTurn,
  type ExaminerTurnResponse,
  type PhraseResponse,
} from '@/lib/api/speaking-examiner'
import { Button } from '@/components/ui/button'
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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { cn } from '@/lib/utils'
import { Part2PrepCard } from './components/part2-prep-card'
import { RecordingActionDock } from './components/recording-action-dock'
import { ScoreCard } from './components/score-card'
import { SpeakingSessionShell } from './components/speaking-session-shell'
import { VideoStage } from './components/video-stage'
import { PART2_BEGIN_SPEAKING } from './constants/part2'
import { useExaminerAudio } from './hooks/use-examiner-audio'
import { useMicCheck } from './hooks/use-mic-check'
import {
  fetchSimliTokenQuery,
  useSpeakingInit,
} from './hooks/use-speaking-init'
import {
  useSpeakingFlow,
  type AudioDoneContext,
} from './hooks/use-speaking-flow'
import { useSpeakingRecorder } from './hooks/use-speaking-recorder'
import { useSpeakingSounds } from './hooks/use-speaking-sounds'

function applyExaminerMeta(
  resp: ExaminerTurnResponse,
  setCurrentPart: (p: number) => void,
  setQuestionNumber: (n: number) => void,
  setCueCard: (c: string | null) => void,
): number {
  setCurrentPart(resp.part)
  setQuestionNumber(resp.question_number)
  if (resp.cue_card) {
    setCueCard(resp.cue_card)
  } else if (resp.part !== 2) {
    setCueCard(null)
  }
  return resp.part
}

const route = getRouteApi('/_authenticated/speaking-examiner')

export function SpeakingExaminer() {
  const queryClient = useQueryClient()
  const { attemptId } = route.useSearch()
  const [history, setHistory] = useState<ConversationTurn[]>([])
  const [currentPart, setCurrentPart] = useState(1)
  const [questionNumber, setQuestionNumber] = useState(1)
  const [cueCard, setCueCard] = useState<string | null>(null)
  const [simliMountKey, setSimliMountKey] = useState(0)
  const [liveSessionId, setLiveSessionId] = useState<string | null>(null)
  const [endTestOpen, setEndTestOpen] = useState(false)

  const audioContextRef = useRef<AudioDoneContext>({
    isPart2CueCard: false,
    afterBeginSpeaking: false,
  })
  const startRecordingRef = useRef<() => Promise<boolean>>(async () => false)
  const prepCompleteRef = useRef(false)
  const part2PhraseRef = useRef<PhraseResponse | null>(null)
  const isStartingRef = useRef(false)
  const prevPartRef = useRef(1)
  const sessionIdRef = useRef(0)
  const abortControllerRef = useRef<AbortController | null>(null)

  const { playWarningBeep, playRecordStart, playRecordEnd, playPartTransition } =
    useSpeakingSounds()
  const { micStatus, checkMicrophone, resetMicCheck } = useMicCheck()

  const {
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
    onExaminerResponse,
    onExaminerAudioDone,
    onPrepTimerDone,
    scheduleScoringAfterSpeech,
    retryScoring,
    resetFlow,
  } = useSpeakingFlow({
    liveSessionId,
    abortControllerRef,
    attemptId,
  })

  const isSessionActive = useCallback(
    (sessionId: number) => sessionId === sessionIdRef.current,
    [],
  )

  const beginSessionAbort = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = new AbortController()
    sessionIdRef.current += 1
    return {
      sessionId: sessionIdRef.current,
      signal: abortControllerRef.current.signal,
    }
  }, [])

  const handleAudioComplete = useCallback(async () => {
    if (phaseRef.current === 'idle') return

    const ctx = { ...audioContextRef.current }
    audioContextRef.current = {
      isPart2CueCard: false,
      afterBeginSpeaking: false,
    }

    if (ctx.afterBeginSpeaking) {
      const ok = await startRecordingRef.current()
      if (!ok) {
        toast.info('Tap the button when you are ready to speak')
      }
      return
    }

    if (ctx.isPart2CueCard) {
      prepCompleteRef.current = false
    }

    onExaminerAudioDone(ctx)
  }, [onExaminerAudioDone, phaseRef])

  const {
    simliToken,
    setSimliToken,
    simliFaceId,
    setSimliFaceId,
    simliIceServers,
    setSimliIceServers,
    simliEnabled,
    setSimliEnabled,
    simliReady,
    simliFallback,
    pendingAudioB64,
    handleSimliReady,
    handleSimliFallback,
    handleSimliDone,
    playExaminerAudio,
    playExaminerPhrase,
    playSystemPhrase,
    resetAudioState,
    cancelBrowserSpeech,
    SIMLI_LOAD_TIMEOUT_MS,
  } = useExaminerAudio({
    phaseRef,
    onAudioComplete: handleAudioComplete,
  })

  const { simliBanner, isTokenPending, restartInit, applySimliTokenFromResponse } =
    useSpeakingInit({
    phase,
    phaseRef,
    simliEnabled,
    simliReady,
    simliFallback,
    beginLoading,
    onSimliLoadingComplete,
    handleSimliFallback,
    setSimliToken,
    setSimliFaceId,
    setSimliIceServers,
    setSimliEnabled,
    setPhase,
    simliLoadTimeoutMs: SIMLI_LOAD_TIMEOUT_MS,
  })

  const handleRecordStart = useCallback(() => {
    cancelBrowserSpeech()
    playRecordStart()
  }, [cancelBrowserSpeech, playRecordStart])

  const playExaminerTurn = useCallback(
    async (
      resp: ExaminerTurnResponse,
      ctx: AudioDoneContext,
      sessionId = sessionIdRef.current,
      signal?: AbortSignal,
    ) => {
      audioContextRef.current = ctx
      onExaminerTurnReady()
      const needsSynthesis = !resp.audio_base64?.trim()
      await playExaminerAudio(
        resp.text,
        resp.audio_base64,
        resp.tts_error,
        needsSynthesis
          ? {
              text: resp.text,
              part: resp.part,
              cue_card: resp.cue_card,
              signal,
            }
          : undefined,
      )
      if (!isSessionActive(sessionId)) return
    },
    [onExaminerTurnReady, playExaminerAudio, isSessionActive],
  )

  const reconnectSimli = useCallback(async (options?: { silent?: boolean; remount?: boolean }) => {
    try {
      const resp = await fetchSimliTokenQuery(queryClient)
      if (applySimliTokenFromResponse(resp)) {
        if (options?.remount) {
          setSimliMountKey((k) => k + 1)
        }
        if (!options?.silent) {
          toast.info('Reconnecting video avatar…')
        }
      }
    } catch {
      if (!options?.silent) {
        toast.warning('Video avatar reconnect failed — audio still works')
      }
    }
  }, [queryClient, applySimliTokenFromResponse])

  const processRecording = useCallback(
    async (blob: Blob) => {
      const sessionId = sessionIdRef.current
      const signal = abortControllerRef.current?.signal

      onRecordingStopped()
      try {
        if (blob.size < 1024) {
          toast.error('Recording too short — please speak for at least a few seconds')
          onTranscriptFailed()
          return
        }

        const resp = await transcribeAndRespondWithRetry(
          blob,
          liveSessionId,
          signal,
        )
        if (!isSessionActive(sessionId)) return

        if (
          !resp.transcript.trim() ||
          resp.transcript.trim().toLowerCase() === NO_SPEECH_TRANSCRIPT
        ) {
          toast.error(
            'No speech detected. Please speak clearly into the microphone.',
          )
          onTranscriptFailed()
          return
        }

        onTranscriptReady()

        const candidateTurn: ConversationTurn = {
          role: 'candidate',
          text: resp.transcript,
        }

        const newPart = applyExaminerMeta(
          resp,
          setCurrentPart,
          setQuestionNumber,
          setCueCard,
        )
        if (newPart !== prevPartRef.current) {
          playPartTransition(newPart)
          prevPartRef.current = newPart
        }
        if (resp.session_id) {
          setLiveSessionId(resp.session_id)
        }

        const examinerTurn: ConversationTurn = {
          role: 'examiner',
          text: resp.text,
        }
        const updatedHistory = [...history, candidateTurn, examinerTurn]
        setHistory(updatedHistory)

        onExaminerResponse()

        if (import.meta.env.DEV && resp.timings) {
          // eslint-disable-next-line no-console -- perf diagnostics
          console.debug('[Examiner] turn timings', resp.timings)
        }

        const isPart2CueCard = Boolean(resp.part === 2 && resp.cue_card)

        if (resp.is_end) {
          scheduleScoringAfterSpeech(updatedHistory)
          await playExaminerTurn(
            resp,
            { isPart2CueCard: false, afterBeginSpeaking: false },
            sessionId,
            signal,
          )
        } else {
          await playExaminerTurn(
            resp,
            { isPart2CueCard, afterBeginSpeaking: false },
            sessionId,
            signal,
          )
        }
      } catch (err) {
        if (!isSessionActive(sessionId) || isSpeakingAbortError(err)) return
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console -- surface API errors during development
          console.error('[Examiner] processRecording failed:', err)
        }
        toast.error(`Processing failed: ${getSpeakingApiErrorDetail(err)}`)
        onTranscriptFailed()
      }
    },
    [
      history,
      liveSessionId,
      onRecordingStopped,
      onTranscriptReady,
      onTranscriptFailed,
      onExaminerResponse,
      scheduleScoringAfterSpeech,
      playExaminerTurn,
      isSessionActive,
      playPartTransition,
    ],
  )

  const {
    recordingTime,
    maxRecordingSeconds,
    recordingProgress,
    recordingStream,
    startRecording,
    stopRecording,
    abortRecording,
    cleanupStream,
  } = useSpeakingRecorder({
    currentPart,
    onRecordingComplete: processRecording,
    setPhase,
    onRecordStart: handleRecordStart,
    onRecordEnd: playRecordEnd,
  })

  useEffect(() => {
    startRecordingRef.current = startRecording
  }, [startRecording])

  const handlePrepComplete = useCallback(async () => {
    if (prepCompleteRef.current) return
    const sessionId = sessionIdRef.current
    prepCompleteRef.current = true

    onPrepTimerDone()
    setHistory((h) => [
      ...h,
      { role: 'examiner', text: PART2_BEGIN_SPEAKING },
    ])

    audioContextRef.current = {
      isPart2CueCard: false,
      afterBeginSpeaking: true,
    }
    try {
      const cached = part2PhraseRef.current
      const phrase = cached ?? (await getPart2BeginPhrase())
      part2PhraseRef.current = phrase
      if (!isSessionActive(sessionId)) return
      await playExaminerPhrase(phrase.text, phrase.audio_base64, phrase.tts_error)
    } catch {
      if (!isSessionActive(sessionId)) return
      await playSystemPhrase(PART2_BEGIN_SPEAKING)
    }
    if (!isSessionActive(sessionId)) return
  }, [onPrepTimerDone, playExaminerPhrase, playSystemPhrase, isSessionActive])

  useEffect(() => {
    if (phase !== 'prep') {
      part2PhraseRef.current = null
      return
    }
    let cancelled = false
    getPart2BeginPhrase()
      .then((phrase) => {
        if (!cancelled) part2PhraseRef.current = phrase
      })
      .catch(() => {
        part2PhraseRef.current = null
      })
    return () => {
      cancelled = true
    }
  }, [phase])

  const handleStart = useCallback(async () => {
    if (isStartingRef.current || phaseRef.current !== 'idle') return

    if (micStatus !== 'ok') {
      const micOk = await checkMicrophone()
      if (!micOk) return
    }

    isStartingRef.current = true
    const { sessionId, signal } = beginSessionAbort()
    onStartSession()
    prepCompleteRef.current = false
    prevPartRef.current = 1
    setLiveSessionId(null)
    setHistory([])
    setCurrentPart(1)
    setQuestionNumber(1)
    setCueCard(null)

    try {
      const resp = await startExaminerWithRetry(signal)
      if (!isSessionActive(sessionId)) return

      applyExaminerMeta(resp, setCurrentPart, setQuestionNumber, setCueCard)
      if (resp.session_id) {
        setLiveSessionId(resp.session_id)
      }
      setHistory([{ role: 'examiner', text: resp.text }])
      onExaminerResponse()
      await playExaminerTurn(
        resp,
        { isPart2CueCard: false, afterBeginSpeaking: false },
        sessionId,
      )
    } catch (err) {
      if (!isSessionActive(sessionId) || isSpeakingAbortError(err)) return
      toast.error(`Failed to start session: ${getSpeakingApiErrorDetail(err)}`)
      setPhase('idle')
    } finally {
      isStartingRef.current = false
    }
  }, [
    beginSessionAbort,
    isSessionActive,
    onStartSession,
    onExaminerResponse,
    playExaminerTurn,
    setPhase,
    phaseRef,
    checkMicrophone,
    micStatus,
  ])

  const stopSession = useCallback(
    (options?: { notify?: boolean }) => {
      sessionIdRef.current += 1
      abortControllerRef.current?.abort()
      abortControllerRef.current = null
      isStartingRef.current = false

      if (phaseRef.current === 'recording') {
        abortRecording()
      } else {
        cleanupStream()
      }

      resetAudioState()
      resetFlow()
      setHistory([])
      setCurrentPart(1)
      setQuestionNumber(1)
      setCueCard(null)
      setLiveSessionId(null)
      prepCompleteRef.current = false
      prevPartRef.current = 1
      resetMicCheck()
      audioContextRef.current = {
        isPart2CueCard: false,
        afterBeginSpeaking: false,
      }
      setSimliMountKey((k) => k + 1)
      if (simliEnabled) {
        void restartInit()
      }
      if (options?.notify !== false) {
        toast.info('Test ended')
      }
    },
    [
      phaseRef,
      abortRecording,
      cleanupStream,
      resetAudioState,
      resetFlow,
      resetMicCheck,
      simliEnabled,
      restartInit,
    ],
  )

  const resetState = useCallback(() => {
    stopSession({ notify: false })
  }, [stopSession])

  const statusLabel =
    phase === 'playing'
      ? 'Speaking...'
      : phase === 'prep'
        ? 'Preparing...'
        : phase === 'recording'
          ? 'Listening...'
          : phase === 'thinking' || phase === 'transcribing'
            ? 'Processing...'
            : phase === 'scoring'
              ? 'Scoring...'
              : phase === 'loading'
                ? 'Loading...'
                : 'Waiting'

  const showLoading = phase === 'loading' || isTokenPending
  const canStart = phase === 'idle' && !score && !isTokenPending
  const showEndTest = phase !== 'idle' && phase !== 'done'
  const isActiveSession =
    phase !== 'idle' && phase !== 'loading' && phase !== 'done' && !isTokenPending
  const showPageHeader =
    phase === 'idle' || phase === 'done' || phase === 'loading' || isTokenPending

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code !== 'Space' || e.repeat) return
      const target = e.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return
      }
      if (phaseRef.current !== 'ready' && phaseRef.current !== 'recording') return
      e.preventDefault()
      if (phaseRef.current === 'ready') {
        cancelBrowserSpeech()
        void startRecording()
      } else if (phaseRef.current === 'recording') {
        stopRecording()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [phaseRef, startRecording, stopRecording, cancelBrowserSpeech])

  const showUserCamera = phase !== 'done'
  const showSimliAvatar =
    simliEnabled && simliToken && simliFaceId && phase !== 'done'

  const endTestButton = showEndTest ? (
    <Button
      variant='outline'
      size='sm'
      className={cn(
        'border-destructive/50 text-destructive hover:bg-destructive/10 hover:text-destructive',
        isActiveSession &&
          'border-red-400/50 bg-black/30 text-red-300 hover:bg-black/50 hover:text-red-200',
      )}
      onClick={() => setEndTestOpen(true)}
    >
      <Square className='mr-2 size-3.5 fill-current' />
      End Test
    </Button>
  ) : null

  const actionControlsOverlay = isActiveSession ? (
    <RecordingActionDock
      phase={phase}
      recordingStream={recordingStream}
      recordingTime={recordingTime}
      maxRecordingSeconds={maxRecordingSeconds}
      recordingProgress={recordingProgress}
      onStartRecording={() => {
        if (phase === 'ready') {
          cancelBrowserSpeech()
          void startRecording()
        }
      }}
      onStopRecording={stopRecording}
      endTestButton={endTestButton}
    />
  ) : null

  const centerOverlay =
    isActiveSession && phase === 'prep' && cueCard ? (
      <Part2PrepCard
        cueCardText={cueCard}
        onWarning={playWarningBeep}
        onComplete={() => {
          void handlePrepComplete()
        }}
      />
    ) : null

  const stage = (showSimliAvatar || showUserCamera) && (
    <VideoStage
      phase={phase}
      statusLabel={statusLabel}
      showSimli={Boolean(showSimliAvatar)}
      showUserCamera={showUserCamera}
      isRecording={phase === 'recording'}
      showStatus={phase !== 'idle' && phase !== 'loading'}
      isLoading={showLoading}
      simliReady={simliReady}
      simliMountKey={simliMountKey}
      simliToken={simliToken ?? ''}
      simliFaceId={simliFaceId ?? ''}
      simliIceServers={simliIceServers}
      pendingAudioB64={pendingAudioB64}
      onSimliDone={handleSimliDone}
      onSimliReady={handleSimliReady}
      onSimliFallback={handleSimliFallback}
      onSimliConnectionLost={() => {
        void reconnectSimli({ remount: true })
      }}
      controlsOverlay={actionControlsOverlay}
      centerOverlay={centerOverlay}
      expanded={isActiveSession}
      currentPart={currentPart}
      questionNumber={questionNumber}
      showPartIndicator={isActiveSession && phase !== 'prep'}
      transcriptHistory={history}
      showLiveTranscript={isActiveSession && phase !== 'prep'}
    />
  )

  const pageHeader = (
    <div>
      <h2 className='text-2xl font-bold tracking-tight'>AI Speaking Examiner</h2>
      <p className='text-muted-foreground'>
        Live conversational IELTS Speaking test with AI examiner
      </p>
    </div>
  )

  const banner =
    simliBanner && !showLoading ? (
      <div
        role='status'
        className='w-full rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100'
      >
        <p>{simliBanner}</p>
        {simliBanner.toLowerCase().includes('simli.com') ? (
          <a
            href='https://app.simli.com'
            target='_blank'
            rel='noreferrer'
            className='mt-2 inline-block font-medium underline underline-offset-2'
          >
            Open Simli billing
          </a>
        ) : null}
      </div>
    ) : null

  const idleContent = (
    <>
      {showLoading && endTestButton && (
        <div className='flex justify-center'>{endTestButton}</div>
      )}
      {canStart && (
        <Card className='w-full'>
          <CardHeader>
            <CardTitle>Ready to begin?</CardTitle>
            <CardDescription>
              {simliBanner
                ? 'Video avatar is unavailable, but the full speaking test works in audio-only mode with examiner voice (ElevenLabs).'
                : 'You will have a live conversation with AI examiner James Harrison. The test follows the official IELTS Speaking format: Part 1 (personal questions), Part 2 (long turn with cue card), and Part 3 (abstract discussion). Make sure your microphone is working.'}
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <Button
              variant='outline'
              className='w-full max-w-md'
              disabled={micStatus === 'checking'}
              onClick={() => {
                void checkMicrophone()
              }}
            >
              <Mic className='mr-2 size-4' />
              {micStatus === 'checking'
                ? 'Checking microphone…'
                : micStatus === 'ok'
                  ? 'Microphone OK'
                  : 'Check microphone'}
            </Button>
            <Button size='lg' className='min-h-14 w-full max-w-md' onClick={handleStart}>
              <Mic className='mr-2 size-4' />
              Start Speaking Test
            </Button>
          </CardContent>
        </Card>
      )}
    </>
  )

  const doneContent =
    phase === 'done' ? (
      score ? (
        <div className='w-full space-y-4'>
          <ScoreCard score={score} history={scoredHistory ?? history} />
          <Button variant='outline' className='w-full' onClick={resetState}>
            Take Another Test
          </Button>
        </div>
      ) : (
        <Card className='w-full'>
          <CardContent className='py-6 text-center'>
            <p className='text-muted-foreground'>
              Test completed but scoring was unavailable.
            </p>
            <div className='mt-4 flex flex-col gap-2 sm:flex-row sm:justify-center'>
              {scoringFailed && (
                <Button
                  onClick={() => {
                    void retryScoring(history)
                  }}
                >
                  Retry scoring
                </Button>
              )}
              <Button variant='outline' onClick={resetState}>
                Take Another Test
              </Button>
            </div>
          </CardContent>
        </Card>
      )
    ) : null

  return (
    <>
      <AlertDialog open={endTestOpen} onOpenChange={setEndTestOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>End speaking test?</AlertDialogTitle>
            <AlertDialogDescription>
              Your session will stop without a score. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Continue test</AlertDialogCancel>
            <AlertDialogAction
              className='bg-destructive text-destructive-foreground hover:bg-destructive/90'
              onClick={() => stopSession()}
            >
              End test
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <Header fixed>
        <Search className='me-auto' />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main
        fixed
        fluid
        className={cn(
          'flex min-h-0 flex-1 flex-col gap-4 md:gap-5',
          isActiveSession ? 'overflow-hidden px-1 py-2 sm:px-2' : 'overflow-y-auto',
        )}
      >
        <SpeakingSessionShell
          showPageHeader={showPageHeader}
          pageHeader={pageHeader}
          banner={banner}
          isActiveSession={isActiveSession}
          stage={stage}
          idleContent={idleContent}
          doneContent={doneContent}
        />
      </Main>
    </>
  )
}
