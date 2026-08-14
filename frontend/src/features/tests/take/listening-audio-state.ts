import { isPreviewAttemptId, lsKeyForListeningAudio } from './constants'

export type ListeningAudioState = {
  v: 1
  /** Part the tape is parked on. */
  sectionId: string | null
  /** Seconds inside that part. */
  position: number
  /** Parts that have played through to the end. */
  completed: string[]
  volume: number
  updatedAt: number
}

export type ListeningAudioSection = {
  id: string
  audio_url: string | null
}

export type ListeningAudioTarget = {
  section: ListeningAudioSection
  position: number
}

export function storageKey(attemptId: string): string {
  return lsKeyForListeningAudio(attemptId)
}

export function emptyListeningAudioState(): ListeningAudioState {
  return {
    v: 1,
    sectionId: null,
    position: 0,
    completed: [],
    volume: 1,
    updatedAt: 0,
  }
}

function isValidState(value: unknown): value is ListeningAudioState {
  if (!value || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  if (v.v !== 1) return false
  if (v.sectionId !== null && typeof v.sectionId !== 'string') return false
  if (typeof v.position !== 'number' || !Number.isFinite(v.position) || v.position < 0) {
    return false
  }
  if (
    !Array.isArray(v.completed) ||
    v.completed.some((id) => typeof id !== 'string')
  ) {
    return false
  }
  if (
    typeof v.volume !== 'number' ||
    !Number.isFinite(v.volume) ||
    v.volume < 0 ||
    v.volume > 1
  ) {
    return false
  }
  if (typeof v.updatedAt !== 'number' || !Number.isFinite(v.updatedAt)) {
    return false
  }
  return true
}

export function readState(
  attemptId: string | null | undefined,
): ListeningAudioState | null {
  if (!attemptId || isPreviewAttemptId(attemptId)) return null
  try {
    const raw = localStorage.getItem(storageKey(attemptId))
    if (!raw) return null
    const parsed: unknown = JSON.parse(raw)
    if (!isValidState(parsed)) return null
    return parsed
  } catch {
    return null
  }
}

export function writeState(
  attemptId: string | null | undefined,
  state: ListeningAudioState,
): boolean {
  if (!attemptId || isPreviewAttemptId(attemptId)) return false
  try {
    localStorage.setItem(storageKey(attemptId), JSON.stringify(state))
    return true
  } catch {
    return false
  }
}

function playableSections<T extends ListeningAudioSection>(sections: T[]): T[] {
  return sections.filter((s) => Boolean(s.audio_url))
}

/**
 * Where the tape should sit: the saved part if it is still playable,
 * otherwise the first part that has not finished.
 */
export function resolveTarget<T extends ListeningAudioSection>(
  sections: T[],
  state: ListeningAudioState,
): ListeningAudioTarget | null {
  const playable = playableSections(sections)
  if (playable.length === 0) return null
  const completed = new Set(state.completed)

  if (state.sectionId) {
    const current = playable.find((s) => s.id === state.sectionId)
    if (current && !completed.has(current.id)) {
      return { section: current, position: state.position }
    }
  }

  const firstIncomplete = playable.find((s) => !completed.has(s.id))
  if (!firstIncomplete) return null
  return { section: firstIncomplete, position: 0 }
}

/**
 * Mark the current part finished and move the tape to the next playable part.
 */
export function advance<T extends ListeningAudioSection>(
  sections: T[],
  state: ListeningAudioState,
): { next: ListeningAudioTarget | null; state: ListeningAudioState } {
  const completed = new Set(state.completed)
  if (state.sectionId) completed.add(state.sectionId)

  const playable = playableSections(sections)
  const currentIdx = state.sectionId
    ? playable.findIndex((s) => s.id === state.sectionId)
    : -1
  const nextSection =
    playable.find((s, i) => i > currentIdx && !completed.has(s.id)) ??
    playable.find((s) => !completed.has(s.id)) ??
    null

  const nextState: ListeningAudioState = {
    ...state,
    sectionId: nextSection?.id ?? null,
    position: 0,
    completed: [...completed],
    updatedAt: Date.now(),
  }

  return {
    next: nextSection ? { section: nextSection, position: 0 } : null,
    state: nextState,
  }
}
