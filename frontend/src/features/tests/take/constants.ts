import type { SectionType } from '../data/schema'

/** Sentinel attempt id used in preview mode (no real DB attempt). */
export const PREVIEW_ATTEMPT_ID = 'preview'

export const TYPE_ORDER: SectionType[] = [
  'listening',
  'reading',
  'writing',
  'speaking',
]

export const SECTION_LABELS: Record<SectionType, string> = {
  listening: 'Listening',
  reading: 'Reading',
  writing: 'Writing',
  speaking: 'Speaking',
}

export function isPreviewAttemptId(id: string | null | undefined): boolean {
  return id === PREVIEW_ATTEMPT_ID
}

export function lsKeyForAttempt(attemptId: string): string {
  return `attempt:${attemptId}:state`
}

export function lsKeyForListeningAudio(attemptId: string): string {
  return `attempt:${attemptId}:listening-audio`
}
