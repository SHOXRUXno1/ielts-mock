export const QUESTIONS_PER_PART: Record<number, number> = {
  1: 5,
  2: 1,
  3: 4,
}

export function getQuestionsTotalForPart(part: number): number {
  return QUESTIONS_PER_PART[part] ?? 1
}

export function getPartSubtitle(part: number): string {
  switch (part) {
    case 1:
      return 'Part 1 — Introduction'
    case 2:
      return 'Part 2 — Long Turn'
    case 3:
      return 'Part 3 — Discussion'
    default:
      return `Part ${part}`
  }
}
