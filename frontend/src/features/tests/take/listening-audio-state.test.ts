import { afterEach, describe, expect, it } from 'vitest'
import { PREVIEW_ATTEMPT_ID } from './constants'
import {
  advance,
  emptyListeningAudioState,
  readState,
  resolveTarget,
  storageKey,
  writeState,
  type ListeningAudioSection,
  type ListeningAudioState,
} from './listening-audio-state'

const ATTEMPT = 'attempt-audio-1'

function part(
  id: string,
  audio_url: string | null = `/media/${id}.mp3`,
): ListeningAudioSection {
  return { id, audio_url }
}

function state(
  patch: Partial<ListeningAudioState> = {},
): ListeningAudioState {
  return {
    ...emptyListeningAudioState(),
    updatedAt: 1,
    ...patch,
  }
}

afterEach(() => {
  localStorage.clear()
})

describe('storageKey', () => {
  it('uses the attempt-scoped listening-audio key', () => {
    expect(storageKey(ATTEMPT)).toBe(`attempt:${ATTEMPT}:listening-audio`)
  })
})

describe('readState / writeState', () => {
  it('round-trips a valid snapshot', () => {
    const saved = state({
      sectionId: 'p2',
      position: 42.5,
      completed: ['p1'],
      volume: 0.4,
    })
    expect(writeState(ATTEMPT, saved)).toBe(true)
    expect(readState(ATTEMPT)).toEqual(saved)
  })

  it('returns null for a missing key', () => {
    expect(readState(ATTEMPT)).toBeNull()
  })

  it('returns null for corrupt JSON', () => {
    localStorage.setItem(storageKey(ATTEMPT), '{not-json')
    expect(readState(ATTEMPT)).toBeNull()
  })

  it('returns null for an outdated version', () => {
    localStorage.setItem(
      storageKey(ATTEMPT),
      JSON.stringify({ ...state(), v: 2 }),
    )
    expect(readState(ATTEMPT)).toBeNull()
  })

  it('returns null when required fields are missing', () => {
    localStorage.setItem(
      storageKey(ATTEMPT),
      JSON.stringify({ v: 1, sectionId: 'p1' }),
    )
    expect(readState(ATTEMPT)).toBeNull()
  })

  it('does not read or write without an attempt id', () => {
    expect(readState(null)).toBeNull()
    expect(readState(undefined)).toBeNull()
    expect(writeState(null, state())).toBe(false)
    expect(writeState('', state())).toBe(false)
    expect(localStorage.length).toBe(0)
  })

  it('does not persist preview attempts', () => {
    expect(writeState(PREVIEW_ATTEMPT_ID, state({ sectionId: 'p1' }))).toBe(
      false,
    )
    expect(readState(PREVIEW_ATTEMPT_ID)).toBeNull()
    expect(localStorage.length).toBe(0)
  })
})

describe('resolveTarget', () => {
  const parts = [part('p1'), part('p2'), part('p3'), part('p4')]

  it('returns null when there are no playable parts', () => {
    expect(resolveTarget([], emptyListeningAudioState())).toBeNull()
    expect(
      resolveTarget([part('p1', null)], emptyListeningAudioState()),
    ).toBeNull()
  })

  it('starts at the first playable part when nothing is saved', () => {
    expect(resolveTarget(parts, emptyListeningAudioState())).toEqual({
      section: parts[0],
      position: 0,
    })
  })

  it('restores the saved part and position when it is still playable', () => {
    expect(
      resolveTarget(
        parts,
        state({ sectionId: 'p2', position: 15, completed: ['p1'] }),
      ),
    ).toEqual({ section: parts[1], position: 15 })
  })

  it('skips a saved part that is already completed', () => {
    expect(
      resolveTarget(
        parts,
        state({ sectionId: 'p1', position: 99, completed: ['p1'] }),
      ),
    ).toEqual({ section: parts[1], position: 0 })
  })

  it('skips parts without audio', () => {
    const mixed = [part('p1', null), part('p2'), part('p3')]
    expect(resolveTarget(mixed, emptyListeningAudioState())).toEqual({
      section: mixed[1],
      position: 0,
    })
  })

  it('returns null when every playable part is completed', () => {
    expect(
      resolveTarget(
        parts,
        state({
          sectionId: 'p4',
          completed: ['p1', 'p2', 'p3', 'p4'],
        }),
      ),
    ).toBeNull()
  })
})

describe('advance', () => {
  const parts = [part('p1'), part('p2'), part('p3')]

  it('marks the current part completed and returns the next one', () => {
    const { next, state: nextState } = advance(
      parts,
      state({ sectionId: 'p1', position: 80 }),
    )
    expect(next).toEqual({ section: parts[1], position: 0 })
    expect(nextState.sectionId).toBe('p2')
    expect(nextState.position).toBe(0)
    expect(nextState.completed).toEqual(['p1'])
  })

  it('skips the next part when it has no audio', () => {
    const mixed = [part('p1'), part('p2', null), part('p3')]
    const { next, state: nextState } = advance(
      mixed,
      state({ sectionId: 'p1' }),
    )
    expect(next).toEqual({ section: mixed[2], position: 0 })
    expect(nextState.completed).toEqual(['p1'])
  })

  it('returns null after the last part and keeps every id completed', () => {
    const { next, state: nextState } = advance(
      parts,
      state({ sectionId: 'p3', completed: ['p1', 'p2'] }),
    )
    expect(next).toBeNull()
    expect(nextState.sectionId).toBeNull()
    expect(nextState.completed).toEqual(['p1', 'p2', 'p3'])
  })
})
