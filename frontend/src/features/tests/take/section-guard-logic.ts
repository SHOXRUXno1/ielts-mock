import type { SectionType } from '../data/schema'

/**
 * Where to send the student after the current URL section is sealed.
 * `hold` is the Time's up dialog: do not enter or navigate yet, or the
 * next section's timer starts during the 5s countdown.
 */
export function resolveSealedRedirectTarget(opts: {
  hold: boolean
  sealedTypes: Set<SectionType>
  activeType: SectionType | null
  presentTypes: SectionType[]
  current: SectionType
}): SectionType | 'review' | null {
  if (opts.hold) return null
  if (
    opts.activeType &&
    opts.activeType !== opts.current &&
    !opts.sealedTypes.has(opts.activeType)
  ) {
    return opts.activeType
  }
  return opts.presentTypes.find((t) => !opts.sealedTypes.has(t)) ?? 'review'
}
