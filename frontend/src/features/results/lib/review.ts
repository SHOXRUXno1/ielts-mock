import type { AnswerRead } from '@/lib/api/attempts'
import { formatCorrectAnswer, formatStudentAnswer } from './answers'

export type ReviewOption = {
  letter: string
  label: string
}

export type ReviewPair = {
  item: string
  student: string | null
  correct: string | null
}

const TFNG = ['True', 'False', 'Not Given']
const YNNG = ['Yes', 'No', 'Not Given']

const CHOICE_TYPES = new Set([
  'mcq',
  'multi_select',
  'true_false_ng',
  'yes_no_ng',
  'matching_headings',
  'matching_information',
  'matching_features',
  'map_labeling',
])

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return null
}

function stringField(
  content: Record<string, unknown> | undefined,
  ...keys: string[]
): string {
  if (!content) return ''
  for (const key of keys) {
    const value = content[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

export function questionStem(
  content: Record<string, unknown> | undefined,
  questionType?: string,
): string {
  if (questionType === 'true_false_ng' || questionType === 'yes_no_ng') {
    return stringField(content, 'statement', 'question', 'stem', 'prompt')
  }
  if (questionType === 'map_labeling') {
    return stringField(content, 'location', 'question', 'prompt', 'stem')
  }
  if (
    questionType === 'sentence_completion' ||
    questionType === 'short_answer' ||
    questionType === 'gap_fill'
  ) {
    return stringField(content, 'prompt', 'question', 'text', 'stem')
  }
  return stringField(
    content,
    'question',
    'prompt',
    'statement',
    'stem',
    'text',
    'location',
  )
}

function parseOption(raw: unknown, index: number): ReviewOption {
  const text = String(raw ?? '').trim()
  const prefixed = text.match(/^([A-Z])(?:[.)]|\s+)\s*(.+)$/i)
  if (prefixed) {
    const letter = prefixed[1].toUpperCase()
    return { letter, label: prefixed[2].trim() || letter }
  }
  if (/^[A-Z]$/i.test(text)) {
    const letter = text.toUpperCase()
    return { letter, label: letter }
  }
  return {
    letter: String.fromCharCode(65 + index),
    label: text,
  }
}

export function reviewOptions(
  content: Record<string, unknown> | undefined,
  questionType?: string,
): ReviewOption[] {
  if (questionType === 'true_false_ng') {
    return TFNG.map((label) => ({ letter: label, label }))
  }
  if (questionType === 'yes_no_ng') {
    return YNNG.map((label) => ({ letter: label, label }))
  }
  const raw = content?.options
  if (!Array.isArray(raw) || raw.length === 0) return []
  return raw.map((item, index) => parseOption(item, index))
}

export function isChoiceReview(
  questionType: string | undefined,
  options: ReviewOption[],
): boolean {
  if (!questionType) return options.length > 0
  if (questionType === 'matching') return false
  return CHOICE_TYPES.has(questionType) && options.length > 0
}

export function normalizeChoice(
  value: string,
  options: ReviewOption[],
): string {
  const trimmed = value.trim()
  if (!trimmed) return ''
  if (/^[A-Z]$/i.test(trimmed)) return trimmed.toUpperCase()
  const match = options.find(
    (opt) =>
      opt.letter.toLowerCase() === trimmed.toLowerCase() ||
      opt.label.toLowerCase() === trimmed.toLowerCase(),
  )
  return match?.letter ?? trimmed
}

function collectValues(value: unknown): string[] {
  if (value == null || value === '') return []
  if (Array.isArray(value)) return value.map(String).filter((item) => item.trim())
  if (typeof value === 'object') return []
  return [String(value)]
}

export function studentChoiceKeys(
  response: Record<string, unknown>,
  options: ReviewOption[],
): string[] {
  return collectValues(response.answer).map((item) =>
    normalizeChoice(item, options),
  )
}

export function correctChoiceKeys(
  answerKey: Record<string, unknown> | null | undefined,
  options: ReviewOption[],
): string[] {
  if (!answerKey) return []
  const raw = answerKey.correct ?? answerKey.answer ?? answerKey.answers
  return collectValues(raw).map((item) => normalizeChoice(item, options))
}

export function matchingPairs(
  content: Record<string, unknown> | undefined,
  response: Record<string, unknown>,
  answerKey: Record<string, unknown> | null | undefined,
): ReviewPair[] | null {
  const leftRaw = content?.left ?? content?.items
  const studentMap = asRecord(response.answer)
  const correctRaw = answerKey?.correct ?? answerKey?.answer
  const correctMap = asRecord(correctRaw)
  if (!Array.isArray(leftRaw) || leftRaw.length === 0) {
    if (!studentMap && !correctMap) return null
    const keys = new Set([
      ...Object.keys(studentMap ?? {}),
      ...Object.keys(correctMap ?? {}),
    ])
    if (keys.size === 0) return null
    return [...keys].map((item) => ({
      item,
      student: studentMap?.[item] != null ? String(studentMap[item]) : null,
      correct: correctMap?.[item] != null ? String(correctMap[item]) : null,
    }))
  }
  return leftRaw.map((item) => {
    const key = String(item)
    return {
      item: key,
      student: studentMap?.[key] != null ? String(studentMap[key]) : null,
      correct: correctMap?.[key] != null ? String(correctMap[key]) : null,
    }
  })
}

export function reviewFallback(answer: AnswerRead): {
  student: string
  correct: string
} {
  return {
    student: formatStudentAnswer(answer.response),
    correct: formatCorrectAnswer(answer.question?.answer_key ?? null),
  }
}
