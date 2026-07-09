export type SectionType = 'listening' | 'reading' | 'writing' | 'speaking'

export type QuestionType =
  | 'mcq'
  | 'gap_fill'
  | 'matching'
  | 'map_labeling'
  | 'true_false_ng'
  | 'multi_select'
  | 'essay'
  | 'speaking_part'
  | 'matching_headings'
  | 'matching_information'
  | 'matching_features'
  | 'yes_no_ng'
  | 'sentence_completion'
  | 'short_answer'

export type Question = {
  id: string
  section_id: string
  question_group_id: string | null
  order: number
  question_type: QuestionType
  content: Record<string, unknown>
  answer_key: Record<string, unknown> | null
  // Writing-task specific (null for all other question types)
  task_number: number | null
  min_words: number | null
  image_url: string | null
  created_at: string
  updated_at: string
}

export type QuestionGroup = {
  id: string
  section_id: string
  order: number
  question_type: QuestionType
  instruction: string
  options_shared: Record<string, unknown> | null
  questions: Question[]
  created_at: string
  updated_at: string
}

export type Section = {
  id: string
  test_id: string
  type: SectionType
  order: number
  duration_minutes: number
  audio_url: string | null
  passage: string | null
  audioscript: string | null
  title: string | null
  question_count: number
  question_groups: QuestionGroup[]
  created_at: string
  updated_at: string
}

export type Test = {
  id: string
  title: string
  description: string | null
  is_published: boolean
  type: string
  book_name: string | null
  book_slug: string
  test_number: number
  created_at: string
  updated_at: string
}

export type TestDetail = Test & {
  sections: Section[]
}

export const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  mcq: 'Multiple Choice',
  gap_fill: 'Gap Fill',
  matching: 'Matching',
  map_labeling: 'Map Labeling',
  true_false_ng: 'True / False / Not Given',
  multi_select: 'Multiple Select',
  essay: 'Essay',
  speaking_part: 'Speaking Part',
  matching_headings: 'Matching Headings',
  matching_information: 'Matching Information',
  matching_features: 'Matching Features',
  yes_no_ng: 'Yes / No / Not Given',
  sentence_completion: 'Sentence Completion',
  short_answer: 'Short Answer',
}

/**
 * Extract the prefix from a matching option string.
 * "iii. Some heading"  → "iii"
 * "A. Matt Elliot"     → "A"
 * "A"                  → "A"
 */
export function optionPrefix(opt: string): string {
  const dot = opt.indexOf('.')
  if (dot > 0) return opt.slice(0, dot).trim()
  return opt.trim()
}
