import type { AnswerRead } from '@/lib/api/attempts'
import {
  assignSlotNumbers,
  countScoringSlots,
  scoringSlotsForQuestion,
  type Question,
} from '@/features/tests/data/schema'

export const OBJECTIVE_QUESTION_TOTAL = 40

export type AnswerOutcome = 'correct' | 'partial' | 'incorrect' | 'skipped'

export type AnswerMarks = { earned: number; total: number }

/**
 * Marks the question is worth, and how many the candidate earned.
 *
 * "Choose TWO letters" fills two question numbers and is worth two marks, so
 * one right letter earns one of them. The server already scores it that way —
 * `score` is the fraction earned, and the raw total includes it — but the
 * report used to collapse the pair into a single row and call it wrong, which
 * read as though the right letter had counted for nothing.
 *
 * Only questions that span several numbers are split. Elsewhere `is_correct`
 * stays the single source of truth, so nothing that scores one mark today can
 * start reporting a fraction of one.
 */
export function answerMarks(answer: AnswerRead): AnswerMarks {
  const question = answer.question
  const total = question
    ? scoringSlotsForQuestion({
        question_type: question.question_type,
        content: question.content,
        answer_key: question.answer_key,
      })
    : 1

  if (total <= 1) {
    return { earned: answer.is_correct === true ? 1 : 0, total: 1 }
  }
  if (answer.is_correct === true) return { earned: total, total }

  const fraction = answer.score ?? 0
  const earned = Math.round(fraction * total)
  return { earned: Math.max(0, Math.min(total - 1, earned)), total }
}

export function formatStudentAnswer(response: Record<string, unknown>): string {
  const val = response.answer
  if (val == null || val === '') return '(no answer)'
  if (Array.isArray(val)) return val.join(', ')
  if (typeof val === 'object' && val !== null) {
    return Object.entries(val as Record<string, unknown>)
      .map(([k, v]) => `${k} → ${v}`)
      .join('; ')
  }
  return String(val)
}

/** A–J option letters, as matching / multiple-choice keys are written. */
const CHOICE_LETTER = /^[A-Ja-j]$/

/**
 * Split a formatted answer into option letters, or null if it is ordinary text.
 *
 * Single letters must stay readable: a strikethrough through "B" sits on the
 * middle bar and the glyph reads as "D". Callers render these as marks, not
 * struck-through text.
 */
export function splitChoiceLetters(value: string): string[] | null {
  const parts = value
    .trim()
    .split(/\s*[|,]\s*|\s+/)
    .filter(Boolean)
  if (parts.length === 0) return null
  if (!parts.every((part) => CHOICE_LETTER.test(part))) return null
  return parts.map((part) => part.toUpperCase())
}

export function formatCorrectAnswer(
  answerKey: Record<string, unknown> | null,
): string {
  if (!answerKey) return ''
  const accepted = answerKey.accepted_answers
  if (Array.isArray(accepted) && accepted.length > 0) {
    return accepted.join(' | ')
  }
  const correct = answerKey.correct ?? answerKey.answer
  if (correct == null) {
    const legacy = answerKey.answers
    if (Array.isArray(legacy) && legacy.length > 0) {
      return legacy.join(' | ')
    }
    return ''
  }
  if (Array.isArray(correct)) {
    const sorted = [...correct].sort()
    return sorted.length > 0 ? sorted.join(' | ') : ''
  }
  if (typeof correct === 'object' && correct !== null) {
    return Object.entries(correct as Record<string, unknown>)
      .map(([_k, v]) => String(v))
      .join(' | ')
  }
  return String(correct)
}

export function answerOutcome(answer: AnswerRead): AnswerOutcome {
  const student = formatStudentAnswer(answer.response)
  if (student === '(no answer)') return 'skipped'
  if (answer.is_correct === true) return 'correct'
  return answerMarks(answer).earned > 0 ? 'partial' : 'incorrect'
}

/**
 * Split a question's marks across the report's three buckets.
 *
 * Counted in marks rather than rows so the totals agree with the raw score in
 * the header: a half-right pair adds one mark to each side instead of one row
 * to "incorrect".
 */
export function tallyMarks(answers: AnswerRead[]): {
  correct: number
  incorrect: number
  skipped: number
} {
  let correct = 0
  let incorrect = 0
  let skipped = 0
  for (const answer of answers) {
    const { earned, total } = answerMarks(answer)
    correct += earned
    if (answerOutcome(answer) === 'skipped') skipped += total - earned
    else incorrect += total - earned
  }
  return { correct, incorrect, skipped }
}

/** Partial answers belong under "incorrect": a mark was lost there. */
export function matchesOutcomeFilter(
  outcome: AnswerOutcome,
  filter: AnswerOutcome,
): boolean {
  if (filter === 'incorrect') return outcome === 'incorrect' || outcome === 'partial'
  return outcome === filter
}

function snapshotAsQuestion(q: NonNullable<AnswerRead['question']>): Question {
  return {
    id: q.id,
    section_id: q.section_id,
    question_group_id: q.question_group_id ?? null,
    order: q.order,
    question_type: q.question_type as Question['question_type'],
    content: q.content,
    answer_key: q.answer_key,
    task_number: q.task_number ?? null,
    min_words: null,
    image_url: null,
    essay_type: null,
    computed_number: q.computed_number ?? null,
    computed_number_end: q.computed_number_end ?? null,
    created_at: '',
    updated_at: '',
  }
}

/** IELTS display numbers (Listening 1–40, Reading cumulative across passages). */
export function buildDisplayNumbers(answers: AnswerRead[]): Map<string, string> {
  const map = new Map<string, string>()
  const bySection = new Map<string, AnswerRead[]>()
  for (const a of answers) {
    if (a.is_correct === null || !a.section || !a.question) continue
    const list = bySection.get(a.section.id) ?? []
    list.push(a)
    bySection.set(a.section.id, list)
  }

  const sections = Array.from(bySection.entries()).sort(([, a], [, b]) => {
    const ao = a[0]?.section?.order ?? 999
    const bo = b[0]?.section?.order ?? 999
    return ao - bo
  })

  let readingOffset = 0
  for (const [, sectionAnswers] of sections) {
    const sec = sectionAnswers[0]?.section
    if (!sec) continue
    const qs = sectionAnswers
      .map((a) => a.question)
      .filter((q): q is NonNullable<typeof q> => q != null)
      .map(snapshotAsQuestion)
      .sort((a, b) => {
        const aN = a.computed_number ?? a.order
        const bN = b.computed_number ?? b.order
        return aN - bN
      })

    const seen = new Set<string>()
    const uniqueQs = qs.filter((q) => {
      if (seen.has(q.id)) return false
      seen.add(q.id)
      return true
    })

    const useComputed = uniqueQs.every(
      (q) => typeof q.computed_number === 'number' && q.computed_number >= 1,
    )

    let ranges: Map<string, { start: number; end: number }>
    if (useComputed) {
      ranges = new Map(
        uniqueQs.map((q) => {
          const start = q.computed_number as number
          const end =
            typeof q.computed_number_end === 'number'
              ? q.computed_number_end
              : start
          return [q.id, { start, end }]
        }),
      )
      if (sec.type === 'reading') {
        readingOffset += countScoringSlots(uniqueQs)
      }
    } else if (sec.type === 'listening') {
      ranges = assignSlotNumbers(uniqueQs, (sec.order - 1) * 10)
    } else if (sec.type === 'reading') {
      ranges = assignSlotNumbers(uniqueQs, readingOffset)
      readingOffset += countScoringSlots(uniqueQs)
    } else {
      ranges = new Map(
        uniqueQs.map((q) => [q.id, { start: q.order, end: q.order }]),
      )
    }

    for (const a of sectionAnswers) {
      const qid = a.question?.id
      if (!qid) continue
      const range = ranges.get(qid)
      if (!range) {
        map.set(a.id, String(a.question?.order ?? '?'))
        continue
      }
      map.set(
        a.id,
        range.end !== range.start
          ? `${range.start}–${range.end}`
          : String(range.start),
      )
    }
  }
  return map
}

export type AnswerGroup = {
  key: string
  label: string
  answers: AnswerRead[]
}

export function groupAnswersByPart(
  answers: AnswerRead[],
  skill: 'listening' | 'reading',
): AnswerGroup[] {
  const bySection = new Map<string, AnswerRead[]>()
  for (const answer of answers) {
    const key = answer.section?.id ?? 'unknown'
    const list = bySection.get(key) ?? []
    list.push(answer)
    bySection.set(key, list)
  }

  const groups = Array.from(bySection.entries()).map(([key, rows]) => {
    const order = rows[0]?.section?.order ?? 999
    const label =
      skill === 'listening' ? `Part ${order}` : `Passage ${order}`
    return { key, label, order, answers: rows }
  })

  groups.sort((a, b) => a.order - b.order)
  return groups.map(({ key, label, answers: rows }) => ({ key, label, answers: rows }))
}
