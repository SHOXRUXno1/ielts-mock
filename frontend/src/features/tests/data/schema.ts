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
  | 'table_completion'
  | 'note_completion'
  | 'form_completion'
  | 'summary_completion'
  | 'flow_chart_completion'
  | 'diagram_labeling'

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
  essay_type: string | null
  /** IELTS display number from backend (start of range for multi_select) */
  computed_number?: number | null
  /** Inclusive end when multi_select spans multiple slots */
  computed_number_end?: number | null
  created_at: string
  updated_at: string
}

export type QuestionGroup = {
  id: string
  section_id: string
  order: number
  question_type: QuestionType
  instruction: string
  /** Optional context heading shown between instruction and questions */
  subtitle?: string | null
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
  audio_url: string | null
  passage: string | null
  audioscript: string | null
  title: string | null
  passage_subtitle: string | null
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

export type DurationMode = 'standard' | 'custom'

/** Per-test timing, one row per section type. `null` duration means untimed. */
export type SectionSettings = {
  id: string
  test_id: string
  section_type: SectionType
  duration_minutes: number | null
  duration_mode: DurationMode
}

export type TestDetail = Test & {
  sections: Section[]
  section_settings: SectionSettings[]
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
  table_completion: 'Table Completion',
  note_completion: 'Note Completion',
  form_completion: 'Form Completion',
  summary_completion: 'Summary Completion',
  flow_chart_completion: 'Flow-chart Completion',
  diagram_labeling: 'Diagram Labeling',
}

export const READING_TYPES: QuestionType[] = [
  'mcq', 'multi_select', 'matching', 'matching_information', 'matching_features',
  'matching_headings', 'true_false_ng', 'yes_no_ng', 'sentence_completion',
  'short_answer', 'summary_completion', 'gap_fill', 'note_completion', 'table_completion',
  'diagram_labeling',
]

export const LISTENING_TYPES: QuestionType[] = [
  'mcq', 'multi_select', 'matching', 'matching_features', 'map_labeling',
  'form_completion', 'note_completion', 'table_completion', 'summary_completion',
  'sentence_completion', 'short_answer', 'gap_fill', 'flow_chart_completion',
  'diagram_labeling',
]

export const SECTION_QUESTION_TYPES: Record<SectionType, QuestionType[]> = {
  reading: READING_TYPES,
  listening: LISTENING_TYPES,
  writing: ['essay'],
  speaking: ['speaking_part'],
}

export const QUESTION_TYPE_CATEGORIES: { label: string; types: QuestionType[] }[] = [
  { label: 'Choice', types: ['mcq', 'multi_select'] },
  { label: 'Matching', types: ['matching', 'matching_features', 'matching_information', 'matching_headings'] },
  { label: 'Labeling', types: ['map_labeling', 'diagram_labeling'] },
  { label: 'Completion', types: ['gap_fill', 'sentence_completion', 'short_answer', 'summary_completion', 'note_completion', 'table_completion', 'form_completion', 'flow_chart_completion'] },
  { label: 'True / False', types: ['true_false_ng', 'yes_no_ng'] },
]

export const LEGACY_TYPE_MAP: Record<string, QuestionType> = {
  table: 'table_completion',
  notes: 'note_completion',
  notes_completion: 'note_completion',
  form: 'form_completion',
  flow: 'flow_chart_completion',
}

export function normaliseQuestionType(raw: string): QuestionType {
  return (LEGACY_TYPE_MAP[raw] as QuestionType) ?? (raw as QuestionType)
}

export function groupAllowedTypes(
  allowed: QuestionType[],
): { label: string; types: QuestionType[] }[] {
  const set = new Set(allowed)
  const groups = QUESTION_TYPE_CATEGORIES
    .map((g) => ({ label: g.label, types: g.types.filter((t) => set.has(t)) }))
    .filter((g) => g.types.length > 0)
  const covered = new Set(QUESTION_TYPE_CATEGORIES.flatMap((g) => g.types))
  const other = allowed.filter((t) => !covered.has(t))
  if (other.length > 0) groups.push({ label: 'Other', types: other })
  return groups
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

/** How many IELTS marks / display numbers one Question row contributes. */
export function scoringSlotsForQuestion(
  q: Pick<Question, 'question_type' | 'content' | 'answer_key'> | {
    question_type: string
    content?: Record<string, unknown> | null
    answer_key?: Record<string, unknown> | null
  },
): number {
  if (q.question_type !== 'multi_select') return 1
  // Prefer students_choose (choose_n) — canonical span; correct[] must match on save.
  const chooseN = q.content?.choose_n
  if (typeof chooseN === 'number' && chooseN >= 1) return chooseN
  const key = q.answer_key ?? {}
  const correct =
    'correct' in key ? key.correct : (key as { answer?: unknown }).answer
  if (Array.isArray(correct) && correct.length > 0) return correct.length
  return 1
}

export function countScoringSlots(
  questions: Array<Pick<Question, 'question_type' | 'content' | 'answer_key'>>,
): number {
  return questions.reduce((sum, q) => sum + scoringSlotsForQuestion(q), 0)
}

export type SlotRange = { start: number; end: number }

/** Minimal group shape for section-wide IELTS display numbering. */
export type SlotNumberingGroup = {
  id: string
  order: number
  question_type?: string
  questions: Array<{
    id: string
    order: number
    question_type?: string
    content?: Record<string, unknown> | null
    answer_key?: Record<string, unknown> | null
  }>
}

/**
 * Assign inclusive IELTS display numbers across all groups in a section.
 * Groups are sorted by group.order; questions within a group by question.order.
 * Multi_select spans choose_n / correct-list slots.
 *
 * First question starts at `baseOffset + 1`.
 */
export function assignGroupsSlotNumbers(
  groups: SlotNumberingGroup[],
  baseOffset: number,
): Map<string, SlotRange> {
  const map = new Map<string, SlotRange>()
  let cursor = 1
  const sortedGroups = [...groups].sort((a, b) => a.order - b.order)
  for (const group of sortedGroups) {
    const qs = [...group.questions].sort((a, b) => a.order - b.order)
    for (const q of qs) {
      const slots = scoringSlotsForQuestion({
        question_type: q.question_type ?? group.question_type ?? 'mcq',
        content: q.content,
        answer_key: q.answer_key,
      })
      map.set(q.id, {
        start: baseOffset + cursor,
        end: baseOffset + cursor + slots - 1,
      })
      cursor += slots
    }
  }
  return map
}

/**
 * Assign inclusive display numbers from cumulative scoring slots.
 * First question starts at `baseOffset + 1`.
 */
export function assignSlotNumbers(
  questions: Question[],
  baseOffset: number,
): Map<string, SlotRange> {
  const sorted = [...questions].sort((a, b) => a.order - b.order)
  const map = new Map<string, SlotRange>()
  let cursor = 1
  for (const q of sorted) {
    const slots = scoringSlotsForQuestion(q)
    const start = baseOffset + cursor
    const end = baseOffset + cursor + slots - 1
    map.set(q.id, { start, end })
    cursor += slots
  }
  return map
}

/**
 * Listening Parts use section.order 1–4 → offsets 0, 10, 20, 30.
 * Prefer this only for listening; Reading must pass an explicit baseOffset
 * (sum of prior passages' slots) because section.order is 10/11/12.
 */
export function listeningSlotNumbers(
  sectionOrder: number,
  questions: Question[],
): Map<string, SlotRange> {
  return assignSlotNumbers(questions, (sectionOrder - 1) * 10)
}

/**
 * Remap question.order for display using cumulative scoring slots.
 * Multi-slot questions also get content.display_slot_end for range labels.
 *
 * When section.question_groups is available, questions are sequenced
 * group-by-group (sorted by group.order), then by local order within each
 * group. This prevents interleaving when different groups share the same
 * local order values (1, 2, 3…).
 *
 * @param baseOffset - questions start at baseOffset+1.
 *   Listening default: (section.order - 1) * 10.
 *   Reading: sum of scoring slots in previous passages (required for global Q#).
 */
export function withDisplayOrders(
  section: Pick<Section, 'type' | 'order'> & { question_groups?: Pick<QuestionGroup, 'id' | 'order'>[] },
  questions: Question[],
  baseOffset?: number,
): Question[] {
  // Prefer backend-computed IELTS numbers when present (hybrid model).
  const allHaveComputed = questions.every(
    (q) => typeof q.computed_number === 'number' && q.computed_number >= 1,
  )
  if (allHaveComputed) {
    return questions.map((q) => {
      const start = q.computed_number as number
      const end =
        typeof q.computed_number_end === 'number' ? q.computed_number_end : start
      if (end !== start) {
        return {
          ...q,
          order: start,
          content: { ...q.content, display_slot_end: end },
        }
      }
      return { ...q, order: start }
    })
  }

  const offset =
    baseOffset ??
    (section.type === 'listening' ? (section.order - 1) * 10 : 0)

  const groups = section.question_groups
  let ranges: Map<string, SlotRange>

  if (groups && groups.length > 0) {
    const byGroup = new Map<string, Question[]>()
    for (const q of questions) {
      const gid = q.question_group_id ?? '__ungrouped__'
      const list = byGroup.get(gid) ?? []
      list.push(q)
      byGroup.set(gid, list)
    }
    const numberingGroups: SlotNumberingGroup[] = groups.map((g) => ({
      id: g.id,
      order: g.order,
      questions: (byGroup.get(g.id) ?? []).map((q) => ({
        id: q.id,
        order: q.order,
        question_type: q.question_type,
        content: q.content,
        answer_key: q.answer_key,
      })),
    }))
    // Orphan questions without a group still get numbers after known groups
    const known = new Set(groups.map((g) => g.id))
    for (const [gid, qs] of byGroup) {
      if (gid !== '__ungrouped__' && known.has(gid)) continue
      numberingGroups.push({
        id: gid,
        order: Number.MAX_SAFE_INTEGER,
        questions: qs.map((q) => ({
          id: q.id,
          order: q.order,
          question_type: q.question_type,
          content: q.content,
          answer_key: q.answer_key,
        })),
      })
    }
    ranges = assignGroupsSlotNumbers(numberingGroups, offset)
  } else {
    ranges = assignSlotNumbers(questions, offset)
  }

  return questions.map((q) => {
    const range = ranges.get(q.id)
    if (!range) return q
    if (range.end !== range.start) {
      return {
        ...q,
        order: range.start,
        content: { ...q.content, display_slot_end: range.end },
      }
    }
    return { ...q, order: range.start }
  })
}

/** @deprecated Prefer assignSlotNumbers / listeningSlotNumbers. */
export function displayQuestionNumber(
  sectionType: SectionType,
  sectionOrder: number,
  localOrder: number,
): number {
  if (sectionType === 'listening') {
    return (sectionOrder - 1) * 10 + localOrder
  }
  return localOrder
}
