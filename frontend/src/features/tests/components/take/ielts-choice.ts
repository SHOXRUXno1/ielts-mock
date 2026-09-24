/**
 * Values persisted for IELTS three-choice questions.
 *
 * They are deliberately uppercase: this is the canonical spelling used in
 * answer keys and in the official IELTS instructions.  Keeping the displayed
 * label and the submitted value identical avoids case-sensitive scorer
 * implementations turning a correct answer into an incorrect one.
 */
export type IeltsChoice = {
  value: string
  label: string
}

export const TRUE_FALSE_NG_CHOICES: readonly IeltsChoice[] = [
  { value: 'TRUE', label: 'TRUE' },
  { value: 'FALSE', label: 'FALSE' },
  { value: 'NOT GIVEN', label: 'NOT GIVEN' },
]

export const YES_NO_NG_CHOICES: readonly IeltsChoice[] = [
  { value: 'YES', label: 'YES' },
  { value: 'NO', label: 'NO' },
  { value: 'NOT GIVEN', label: 'NOT GIVEN' },
]

/** Make answers saved by older clients select the equivalent canonical radio. */
export function canonicalIeltsChoice(value: unknown): string {
  return typeof value === 'string' ? value.trim().toUpperCase() : ''
}
