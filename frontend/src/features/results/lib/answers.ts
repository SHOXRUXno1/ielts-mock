import type { AnswerRead } from '@/lib/api/attempts'
import {
  assignSlotNumbers,
  countScoringSlots,
  type Question,
} from '@/features/tests/data/schema'

export const OBJECTIVE_QUESTION_TOTAL = 40

export type AnswerOutcome = 'correct' | 'incorrect' | 'skipped'

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
  return 'incorrect'
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
