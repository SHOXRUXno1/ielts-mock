import type { SectionSettings, SectionType } from './schema'

export type DurationRule = {
  min: number | null
  max: number | null
  recommended: number | null
  /** Soft band around recommended — within this, no warning toast. */
  tolerance: number
  hint: string
}

/**
 * Mirrors backend `services/section_duration.DURATION_RULES` for input bounds
 * and inline hints. The backend always has the final say.
 */
export const DURATION_RULES: Record<SectionType, DurationRule> = {
  listening: {
    min: 20,
    max: 45,
    recommended: 30,
    tolerance: 3,
    hint: 'Recommended: 30 min (computer-delivered). Paper-based: 40 min.',
  },
  reading: {
    min: 45,
    max: 75,
    recommended: 60,
    tolerance: 5,
    hint: 'Recommended: 60 min for all three passages.',
  },
  writing: {
    min: 45,
    max: 75,
    recommended: 60,
    tolerance: 5,
    hint: 'Recommended: 60 min for Task 1 and Task 2 combined.',
  },
  speaking: {
    min: 1,
    max: 20,
    recommended: null,
    tolerance: 0,
    hint: 'Speaking section is untimed — AI controls pacing. An optional cap (max 20 min) guards against stuck sessions.',
  },
}

/** Typical speaking length, used only to estimate the total test duration. */
export const SPEAKING_TYPICAL_MINUTES = 12

export const SECTION_TYPE_ORDER: SectionType[] = [
  'listening',
  'reading',
  'writing',
  'speaking',
]

export function durationByType(
  settings: SectionSettings[] | undefined
): Record<SectionType, number | null> {
  const map: Record<SectionType, number | null> = {
    listening: null,
    reading: null,
    writing: null,
    speaking: null,
  }
  for (const row of settings ?? []) {
    map[row.section_type] = row.duration_minutes
  }
  return map
}

export function modeByType(
  settings: SectionSettings[] | undefined
): Record<SectionType, SectionSettings['duration_mode']> {
  const map: Record<SectionType, SectionSettings['duration_mode']> = {
    listening: 'standard',
    reading: 'standard',
    writing: 'standard',
    speaking: 'standard',
  }
  for (const row of settings ?? []) {
    // Legacy audio_length rows are treated as custom (value kept as-is).
    const raw = (row.duration_mode as string | undefined) ?? 'standard'
    map[row.section_type] = raw === 'standard' ? 'standard' : 'custom'
  }
  return map
}

/** Estimated total, counting untimed speaking as its typical length. */
export function estimatedTotalMinutes(
  settings: SectionSettings[] | undefined
): number {
  const map = durationByType(settings)
  return SECTION_TYPE_ORDER.reduce((sum, type) => {
    const minutes = map[type]
    if (minutes != null) return sum + minutes
    return type === 'speaking' ? sum + SPEAKING_TYPICAL_MINUTES : sum
  }, 0)
}

export function formatMinutes(total: number): string {
  const hours = Math.floor(total / 60)
  const minutes = total % 60
  if (hours === 0) return `${minutes} min`
  if (minutes === 0) return `${hours}h`
  return `${hours}h ${minutes}min`
}

/** Client-side pre-check; the backend returns the authoritative message. */
export function durationRangeError(
  type: SectionType,
  minutes: number | null
): string | null {
  const rule = DURATION_RULES[type]
  if (minutes == null) {
    if (type === 'speaking') return null
    return `${label(type)} duration cannot be null. Recommended: ${rule.recommended}.`
  }
  if (!Number.isInteger(minutes) || minutes <= 0) {
    return `${label(type)} duration must be a positive number of minutes.`
  }
  const { min, max } = rule
  if ((min != null && minutes < min) || (max != null && minutes > max)) {
    const span = min != null && max != null ? `${min}-${max}` : `at most ${max}`
    const suffix =
      rule.recommended != null ? ` Recommended: ${rule.recommended}.` : ''
    return `${label(type)} duration must be ${span} min.${suffix}`
  }
  return null
}

function label(type: SectionType): string {
  return type.charAt(0).toUpperCase() + type.slice(1)
}
