export type CefrLevel = 'C2' | 'C1' | 'B2' | 'B1' | 'A2'

const DESCRIPTORS: { min: number; label: string }[] = [
  { min: 9, label: 'Expert' },
  { min: 8, label: 'Very good' },
  { min: 7, label: 'Good' },
  { min: 6, label: 'Competent' },
  { min: 5, label: 'Modest' },
  { min: 4, label: 'Limited' },
]

export function bandDescriptor(band: number | null | undefined): string | null {
  if (band == null) return null
  for (const row of DESCRIPTORS) {
    if (band >= row.min) return row.label
  }
  return 'Limited'
}

export function cefrLevel(band: number | null | undefined): CefrLevel | null {
  if (band == null) return null
  if (band >= 8.5) return 'C2'
  if (band >= 7) return 'C1'
  if (band >= 5.5) return 'B2'
  if (band >= 4) return 'B1'
  return 'A2'
}
