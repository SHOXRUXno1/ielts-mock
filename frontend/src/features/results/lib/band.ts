export const BAND_MAX = 9

export type BandTone = 'strong' | 'fair' | 'weak' | 'empty'

export function formatBand(band: number | null | undefined): string {
  if (band == null) return '—'
  return band.toFixed(1)
}

export function bandPercent(band: number | null | undefined): number {
  if (band == null) return 0
  return Math.max(0, Math.min(100, (band / BAND_MAX) * 100))
}

export function bandTone(band: number | null | undefined): BandTone {
  if (band == null) return 'empty'
  if (band >= 7) return 'strong'
  if (band >= 5.5) return 'fair'
  return 'weak'
}

export function bandToneClasses(tone: BandTone): { text: string; bg: string } {
  switch (tone) {
    case 'strong':
      return { text: 'text-success-foreground', bg: 'bg-success' }
    case 'fair':
      return { text: 'text-warning-foreground', bg: 'bg-warning' }
    case 'weak':
      return { text: 'text-destructive', bg: 'bg-destructive/10' }
    default:
      return { text: 'text-muted-foreground', bg: 'bg-muted' }
  }
}
