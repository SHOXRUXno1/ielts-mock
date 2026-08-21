/** Split a stored "leaves and bark" answer across N visual blanks. */
export function splitJoinedGapAnswer(value: string, parts: number): string[] {
  if (parts <= 1) return [value]
  const empty = Array.from({ length: parts }, () => '')
  const trimmed = value.trim()
  if (!trimmed) return empty

  const andPieces = trimmed.split(/\s+and\s+/i).map((p) => p.trim())
  if (andPieces.length === parts) return andPieces

  const words = trimmed.split(/\s+/).filter(Boolean)
  if (words.length === parts) return words
  if (words.length > parts) {
    return [...words.slice(0, parts - 1), words.slice(parts - 1).join(' ')]
  }
  return [...words, ...empty.slice(words.length)]
}

/** Join visual blanks back to one IELTS answer ("leaves and bark"). */
export function joinGapAnswerParts(parts: string[]): string {
  const filled = parts.map((p) => p.trim()).filter(Boolean)
  if (filled.length === 0) return ''
  if (filled.length === 1) return filled[0]
  return filled.join(' and ')
}
