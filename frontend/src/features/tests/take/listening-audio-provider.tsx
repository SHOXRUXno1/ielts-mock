import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { mediaUrl } from '@/lib/api/attempts'
import { sectionsOfType } from '../lib/part-resolver'
import { isPreviewAttemptId } from './constants'
import {
  ListeningAudioContext,
  type ListeningAudioContextValue,
} from './listening-audio-context'
import {
  advance,
  emptyListeningAudioState,
  readState,
  resolveTarget,
  writeState,
  type ListeningAudioState,
} from './listening-audio-state'
import { useTakeTest } from './take-test-context'
import { useTestNavigation } from './use-test-navigation'

const PERSIST_MS = 1000

function isNotAllowedError(err: unknown): boolean {
  return (
    (err instanceof DOMException || err instanceof Error) &&
    err.name === 'NotAllowedError'
  )
}

function clampVolume(value: number): number {
  if (!Number.isFinite(value)) return 1
  return Math.min(1, Math.max(0, value))
}

export function ListeningAudioProvider({ children }: { children: ReactNode }) {
  const ctx = useTakeTest()
  const nav = useTestNavigation()
  const audioRef = useRef<HTMLAudioElement>(null)

  const listeningSections = useMemo(
    () => sectionsOfType(ctx.sortedSections, 'listening'),
    [ctx.sortedSections],
  )

  const persistable =
    !ctx.isPreview && !!ctx.attemptId && !isPreviewAttemptId(ctx.attemptId)

  const [initial] = useState(() =>
    persistable
      ? (readState(ctx.attemptId) ?? emptyListeningAudioState())
      : emptyListeningAudioState(),
  )

  const [playingSectionId, setPlayingSectionId] = useState<string | null>(
    initial.sectionId,
  )
  const [position, setPosition] = useState(initial.position)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [blocked, setBlocked] = useState(false)
  const [completed, setCompleted] = useState<Set<string>>(
    () => new Set(initial.completed),
  )
  const [volume, setVolumeState] = useState(initial.volume)

  const snapshotRef = useRef<ListeningAudioState>(initial)
  const completedRef = useRef<Set<string>>(new Set(initial.completed))
  const volumeRef = useRef(initial.volume)
  const playingSectionIdRef = useRef<string | null>(initial.sectionId)
  const pendingSeekRef = useRef<number | null>(null)
  const loadedSrcRef = useRef<string | null>(null)
  const wantPlayRef = useRef(false)
  const lastPersistAtRef = useRef(0)
  const listeningSectionsRef = useRef(listeningSections)
  const goToPartRef = useRef(nav.goToPart)
  const isPreviewRef = useRef(ctx.isPreview)
  const practiceScopeRef = useRef(ctx.practiceScope)
  const persistableRef = useRef(persistable)
  const attemptIdRef = useRef(ctx.attemptId)

  useEffect(() => {
    completedRef.current = completed
    volumeRef.current = volume
    playingSectionIdRef.current = playingSectionId
    listeningSectionsRef.current = listeningSections
    goToPartRef.current = nav.goToPart
    isPreviewRef.current = ctx.isPreview
    practiceScopeRef.current = ctx.practiceScope
    persistableRef.current = persistable
    attemptIdRef.current = ctx.attemptId
  }, [
    completed,
    volume,
    playingSectionId,
    listeningSections,
    nav.goToPart,
    ctx.isPreview,
    ctx.practiceScope,
    persistable,
    ctx.attemptId,
  ])

  const captureState = useCallback((): ListeningAudioState => {
    const el = audioRef.current
    const pendingSeek = pendingSeekRef.current
    const position =
      pendingSeek != null
        ? pendingSeek
        : (el?.currentTime ?? snapshotRef.current.position)
    const next: ListeningAudioState = {
      v: 1,
      sectionId: playingSectionIdRef.current,
      position,
      completed: [...completedRef.current],
      volume: volumeRef.current,
      updatedAt: Date.now(),
    }
    snapshotRef.current = next
    return next
  }, [])

  const persist = useCallback(
    (force = false) => {
      if (!persistableRef.current) return
      const now = Date.now()
      if (!force && now - lastPersistAtRef.current < PERSIST_MS) return
      lastPersistAtRef.current = now
      writeState(attemptIdRef.current, captureState())
    },
    [captureState],
  )

  const tryPlay = useCallback(async () => {
    const el = audioRef.current
    if (!el || !el.src) return
    try {
      await el.play()
      setBlocked(false)
    } catch (err) {
      if (isNotAllowedError(err)) setBlocked(true)
    }
  }, [])

  const loadSource = useCallback((sectionId: string, src: string, seekTo: number) => {
    const el = audioRef.current
    if (!el) return
    pendingSeekRef.current = seekTo
    playingSectionIdRef.current = sectionId
    setPlayingSectionId(sectionId)
    snapshotRef.current = {
      ...snapshotRef.current,
      sectionId,
      position: seekTo,
      updatedAt: Date.now(),
    }
    if (loadedSrcRef.current !== src || !el.src) {
      loadedSrcRef.current = src
      el.src = src
      el.load()
      return
    }
    if (el.readyState >= 1) {
      applyPendingSeek(el, pendingSeekRef)
      setDuration(el.duration || 0)
      if (wantPlayRef.current) void tryPlay()
    }
  }, [tryPlay])

  const loadSection = useCallback(
    (sectionId: string, seekTo: number) => {
      const section = listeningSectionsRef.current.find((s) => s.id === sectionId)
      if (!section?.audio_url) return
      loadSource(sectionId, mediaUrl(section.audio_url), seekTo)
    },
    [loadSource],
  )

  const applyAutostartTarget = useCallback(() => {
    const target = resolveTarget(listeningSectionsRef.current, snapshotRef.current)
    if (!target) return
    loadSection(target.section.id, target.position)
  }, [loadSection])

  const listeningActive =
    ctx.stateOf('listening') === 'active' && !ctx.sealedTypes.has('listening')
  const shouldAutostart =
    !ctx.isPreview &&
    nav.currentType === 'listening' &&
    listeningActive &&
    !ctx.inputsLocked &&
    !ctx.finished

  useEffect(() => {
    wantPlayRef.current = shouldAutostart
    if (!shouldAutostart) {
      const el = audioRef.current
      if (el && !el.paused) {
        el.pause()
        persist(true)
      }
      return
    }
    if (playingSectionIdRef.current && audioRef.current?.src) {
      void tryPlay()
      return
    }
    applyAutostartTarget()
  }, [shouldAutostart, applyAutostartTarget, persist, tryPlay])

  useEffect(() => {
    if (nav.currentType === 'listening') return
    const el = audioRef.current
    if (el && !el.paused) {
      el.pause()
      persist(true)
    }
  }, [nav.currentType, persist])

  useEffect(() => {
    const el = audioRef.current
    if (el) el.volume = volume
  }, [volume])

  useEffect(() => {
    const el = audioRef.current
    if (!el) return

    const onLoaded = () => {
      applyPendingSeek(el, pendingSeekRef)
      setDuration(el.duration || 0)
      setPosition(el.currentTime)
      if (wantPlayRef.current) void tryPlay()
    }
    const onTime = () => {
      setPosition(el.currentTime)
      persist(false)
    }
    const onPlay = () => setIsPlaying(true)
    const onPause = () => {
      setIsPlaying(false)
      persist(true)
    }
    const onEnded = () => {
      setIsPlaying(false)
      const currentId = playingSectionIdRef.current
      if (!currentId) return
      if (isPreviewRef.current) {
        persist(true)
        return
      }
      const { next, state } = advance(listeningSectionsRef.current, {
        ...snapshotRef.current,
        sectionId: currentId,
      })
      snapshotRef.current = state
      completedRef.current = new Set(state.completed)
      setCompleted(new Set(state.completed))
      persist(true)

      if (!next?.section.audio_url) {
        playingSectionIdRef.current = null
        setPlayingSectionId(null)
        setPosition(0)
        return
      }

      wantPlayRef.current = !isPreviewRef.current
      loadSection(next.section.id, 0)

      if (isPreviewRef.current || practiceScopeRef.current === 'part') return
      const partNumber =
        listeningSectionsRef.current.findIndex((s) => s.id === next.section.id) +
        1
      if (partNumber > 0) void goToPartRef.current(partNumber)
    }

    el.addEventListener('loadedmetadata', onLoaded)
    el.addEventListener('timeupdate', onTime)
    el.addEventListener('play', onPlay)
    el.addEventListener('pause', onPause)
    el.addEventListener('ended', onEnded)
    return () => {
      el.removeEventListener('loadedmetadata', onLoaded)
      el.removeEventListener('timeupdate', onTime)
      el.removeEventListener('play', onPlay)
      el.removeEventListener('pause', onPause)
      el.removeEventListener('ended', onEnded)
    }
  }, [loadSection, persist, tryPlay])

  useEffect(() => {
    const flush = () => persist(true)
    const onVisibility = () => {
      if (document.visibilityState === 'hidden') flush()
    }
    window.addEventListener('pagehide', flush)
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      window.removeEventListener('pagehide', flush)
      document.removeEventListener('visibilitychange', onVisibility)
      flush()
    }
  }, [persist])

  const resume = useCallback(() => {
    wantPlayRef.current = true
    setBlocked(false)
    if (!audioRef.current?.src) {
      applyAutostartTarget()
      return
    }
    void tryPlay()
  }, [applyAutostartTarget, tryPlay])

  const togglePlay = useCallback(
    (sectionId: string) => {
      const el = audioRef.current
      if (!el) return
      const done = completedRef.current.has(sectionId)
      if (done && !isPreviewRef.current) return

      if (blocked) {
        resume()
        return
      }

      if (playingSectionIdRef.current === sectionId && el.src) {
        if (el.paused) {
          wantPlayRef.current = true
          void tryPlay()
        } else {
          el.pause()
        }
        return
      }

      if (!isPreviewRef.current) return
      wantPlayRef.current = true
      loadSection(sectionId, 0)
    },
    [blocked, loadSection, resume, tryPlay],
  )

  const setVolume = useCallback(
    (next: number) => {
      const clamped = clampVolume(next)
      setVolumeState(clamped)
      volumeRef.current = clamped
      if (audioRef.current) audioRef.current.volume = clamped
      persist(true)
    },
    [persist],
  )

  const playingPartNumber = useMemo(() => {
    if (!playingSectionId) return null
    const idx = listeningSections.findIndex((s) => s.id === playingSectionId)
    return idx >= 0 ? idx + 1 : null
  }, [listeningSections, playingSectionId])

  const value = useMemo<ListeningAudioContextValue>(
    () => ({
      playingSectionId,
      playingPartNumber,
      position,
      duration,
      isPlaying,
      blocked,
      completed,
      volume,
      allowReplay: ctx.isPreview,
      resume,
      togglePlay,
      setVolume,
    }),
    [
      playingSectionId,
      playingPartNumber,
      position,
      duration,
      isPlaying,
      blocked,
      completed,
      volume,
      ctx.isPreview,
      resume,
      togglePlay,
      setVolume,
    ],
  )

  return (
    <ListeningAudioContext.Provider value={value}>
      <audio ref={audioRef} preload='auto' className='hidden' />
      {children}
    </ListeningAudioContext.Provider>
  )
}

function applyPendingSeek(
  el: HTMLAudioElement,
  pendingSeekRef: { current: number | null },
) {
  const seek = pendingSeekRef.current
  pendingSeekRef.current = null
  if (seek == null || !Number.isFinite(el.duration) || el.duration <= 0) return
  el.currentTime = Math.min(Math.max(0, seek), Math.max(0, el.duration - 0.05))
}
