import type { SectionType } from '../data/schema'
import { isSectionType } from '../lib/part-resolver'

export function asSectionType(
  raw: string | null | undefined,
): SectionType | null {
  return raw && isSectionType(raw) ? raw : null
}

/** Immediate neighbour after `from`, or null at the end of the exam. */
export function nextTypeAfter(
  presentTypes: SectionType[],
  from: SectionType,
): SectionType | null {
  const i = presentTypes.indexOf(from)
  if (i < 0 || i >= presentTypes.length - 1) return null
  return presentTypes[i + 1]!
}

/** True when `to` is the immediate next section after `from` in exam order. */
export function isNextSection(
  from: SectionType,
  to: SectionType,
  presentTypes: SectionType[],
): boolean {
  const i = presentTypes.indexOf(from)
  const j = presentTypes.indexOf(to)
  return i >= 0 && j === i + 1
}

/**
 * The only section the candidate may advance into from the current active one.
 * Later not_started sections stay locked (no skipping Listening → Writing).
 */
export function nextUnlockableType(
  presentTypes: SectionType[],
  stateOf: (type: string) => string | null,
  activeType: SectionType | null,
): SectionType | null {
  if (activeType) {
    const i = presentTypes.indexOf(activeType)
    if (i < 0 || i >= presentTypes.length - 1) return null
    const next = presentTypes[i + 1]!
    return stateOf(next) === 'not_started' ? next : null
  }
  return presentTypes.find((t) => stateOf(t) === 'not_started') ?? null
}
