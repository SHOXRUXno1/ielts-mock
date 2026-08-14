/** Helpers for multi_select question editing / validation. */

/** Normalize multi_select correct answers to letter codes A–Z (never empty strings). */
export function multiSelectCorrectLetters(
  answerKey: Record<string, unknown> | null | undefined,
  options: string[],
): string[] {
  const rawCorrect = answerKey?.correct
  const raw: string[] = Array.isArray(rawCorrect)
    ? rawCorrect.map(String)
    : rawCorrect
      ? [String(rawCorrect)]
      : []
  const letters: string[] = []
  for (const v of raw) {
    const trimmed = v.trim()
    if (!trimmed) continue
    if (/^[A-Z]$/i.test(trimmed)) {
      const letter = trimmed.toUpperCase()
      if (!letters.includes(letter)) letters.push(letter)
      continue
    }
    // Legacy full-text → letter; skip empty option slots (indexOf('') === 0 bug)
    const idx = options.findIndex((opt) => opt === v && opt.trim() !== '')
    if (idx >= 0) {
      const letter = String.fromCharCode(65 + idx)
      if (!letters.includes(letter)) letters.push(letter)
    }
  }
  return letters
}

/** null = valid; otherwise human-readable error for save UX / API. */
export function multiSelectValidationError(
  content: Record<string, unknown>,
  answerKey: Record<string, unknown> | null | undefined,
): string | null {
  const chooseN =
    typeof content.choose_n === 'number' && content.choose_n >= 1
      ? content.choose_n
      : 2
  const options: string[] = Array.isArray(content.options)
    ? (content.options as string[])
    : []
  const letters = multiSelectCorrectLetters(answerKey, options)
  if (letters.length !== chooseN) {
    return `Select exactly ${chooseN} correct answers`
  }
  return null
}
