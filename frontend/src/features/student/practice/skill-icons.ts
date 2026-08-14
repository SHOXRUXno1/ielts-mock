import type { SectionType } from '@/features/tests/data/schema'
import listeningIcon from './icons/listening.png'
import readingIcon from './icons/reading.png'
import writingIcon from './icons/writing.png'
import speakingIcon from './icons/speaking.png'

/**
 * Shared soft-3D skill icons used across student surfaces.
 * Icons8 3D Fluency (free with attribution): airpods-pro-max, book, pencil, mic.
 * https://icons8.com
 */
export const SKILL_ICONS: Record<SectionType, string> = {
  listening: listeningIcon,
  reading: readingIcon,
  writing: writingIcon,
  speaking: speakingIcon,
}

export const SKILL_ORDER: SectionType[] = [
  'listening',
  'reading',
  'writing',
  'speaking',
]
