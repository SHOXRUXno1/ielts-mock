import type { QuestionType } from './schema'

export const COMPOUND_TYPES = [
  'table_completion',
  'note_completion',
  'form_completion',
  'summary_completion',
  'flow_chart_completion',
  'diagram_labeling',
] as const

export type CompoundQuestionType = (typeof COMPOUND_TYPES)[number]

export type CompoundVariant = 'table' | 'notes' | 'form' | 'summary' | 'flow'

export type CompoundStructureBase = {
  instruction_words: string
  max_words_per_gap: number
  /** Optional diagram/illustration shown above the completion card */
  image_url?: string
}

/** Shared segment model for table cells, note items, form gap lines, summary. */
export type CellSegment =
  | { type: 'text'; value: string }
  | { type: 'gap'; gap_id: string }

export type SummarySegment = CellSegment

export type BulletItem = {
  segments: CellSegment[]
}

export type TableCell =
  | { variant: 'plain'; segments: CellSegment[] }
  | { variant: 'bullets'; bullets: BulletItem[] }

export type TableStructure = CompoundStructureBase & {
  variant: 'table'
  title?: string
  headers: string[]
  rows: TableCell[][]
}

export type NoteItem = {
  segments: CellSegment[]
}

export type NoteSection = {
  heading?: string
  items: NoteItem[]
}

export type NoteStructure = CompoundStructureBase & {
  variant: 'notes'
  title?: string
  /** When false, render items as plain lines (no bullet markers). Default true. */
  bullets?: boolean
  sections: NoteSection[]
}

export type FormField =
  | { type: 'static'; label: string; value: string }
  | { type: 'gap_line'; label: string; segments: CellSegment[] }

export type FormStructure = CompoundStructureBase & {
  variant: 'form'
  form_title: string
  fields: FormField[]
}

export type SummaryParagraph = {
  segments: CellSegment[]
}

export type SummaryStructure = CompoundStructureBase & {
  variant: 'summary'
  /** Optional boxed title above the summary paragraph (e.g. "Art and the Brain") */
  title?: string
  /** Optional word bank shown above the summary (lettered A, B, C…) */
  options?: string[]
  paragraphs: SummaryParagraph[]
}

export type FlowStep = {
  segments: CellSegment[]
}

export type FlowStructure = CompoundStructureBase & {
  variant: 'flow'
  title?: string
  steps: FlowStep[]
}

export type CompoundStructure =
  | TableStructure
  | NoteStructure
  | FormStructure
  | SummaryStructure
  | FlowStructure

export function isCompoundType(
  type: string | null | undefined,
): type is CompoundQuestionType {
  return (
    type === 'table_completion' ||
    type === 'note_completion' ||
    type === 'form_completion' ||
    type === 'summary_completion' ||
    type === 'flow_chart_completion' ||
    type === 'diagram_labeling'
  )
}

export function instructionWordsFromMax(maxWords: number): string {
  if (maxWords <= 1) return 'ONE WORD ONLY'
  if (maxWords === 2) return 'ONE WORD AND/OR A NUMBER'
  return `NO MORE THAN ${maxWords - 1} WORDS AND/OR A NUMBER`
}

/** Numeric max_words_per_gap value for a given instruction-words label. */
export const WORD_LIMIT_OPTIONS: { value: number; label: string }[] = [
  { value: 1, label: 'ONE WORD ONLY' },
  { value: 2, label: 'ONE WORD AND/OR A NUMBER' },
  { value: 3, label: 'NO MORE THAN TWO WORDS AND/OR A NUMBER' },
  { value: 4, label: 'NO MORE THAN THREE WORDS AND/OR A NUMBER' },
]

export function autoCompoundInstruction(
  type: string,
  maxWords: number,
): string {
  if (type === 'diagram_labeling') {
    return (
      `Label the diagram below. Choose ${instructionWordsFromMax(maxWords)} ` +
      `from the passage for each answer.`
    )
  }
  const kind =
    type === 'note_completion'
      ? 'notes'
      : type === 'form_completion'
        ? 'form'
        : type === 'summary_completion'
          ? 'summary'
          : type === 'flow_chart_completion'
            ? 'flow-chart'
            : 'table'
  return `Complete the ${kind} below. Write ${instructionWordsFromMax(maxWords)} for each answer.`
}

/** Draft snapshot for live student preview in the wizard. */
export type CompoundGroupDraft = {
  groupId: string
  questionType: string
  instruction: string
  /** Optional context heading between instruction and questions */
  subtitle?: string | null
  /** Present for compound types; omitted for meta-only (MCQ etc.) drafts */
  structure?: CompoundStructure
  gapDrafts?: Array<{
    id?: string
    order: number
    content: Record<string, unknown>
    answer_key: Record<string, unknown> | null
  }>
  /**
   * Live question rows for section-wide Q numbering (non-compound + compound gaps).
   * Parent merges these over saved group.questions when computing display numbers.
   */
  questions?: Array<{
    id?: string
    order: number
    content: Record<string, unknown>
    answer_key: Record<string, unknown> | null
  }>
  /** Editor cell focus — used to highlight matching preview cell */
  focusedCell?: { row: number; col: number } | null
  /** Live options for matching subtypes (used for admin preview before save) */
  optionsShared?: string[]
  /** Map image URL for map_labeling (live preview before/after save) */
  mapImageUrl?: string | null
  /** Live questions heading for matching subtypes */
  questionsHeading?: string
}

export function variantFromType(type: QuestionType | string): CompoundVariant {
  switch (type) {
    case 'table_completion':
      return 'table'
    case 'note_completion':
    case 'diagram_labeling':
      return 'notes'
    case 'form_completion':
      return 'form'
    case 'summary_completion':
      return 'summary'
    case 'flow_chart_completion':
      return 'flow'
    default:
      return 'table'
  }
}

function gapsFromSegments(segments: CellSegment[] | undefined): string[] {
  if (!segments) return []
  const gaps: string[] = []
  for (const seg of segments) {
    if (seg.type === 'gap') gaps.push(seg.gap_id)
  }
  return gaps
}

export function defaultStructureForType(
  type: QuestionType | string,
): CompoundStructure {
  const base = {
    instruction_words: 'ONE WORD AND/OR A NUMBER',
    max_words_per_gap: 2,
  }
  switch (variantFromType(type)) {
    case 'table':
      return {
        ...base,
        variant: 'table',
        headers: ['Column 1', 'Column 2'],
        rows: [
          [
            { variant: 'plain', segments: [{ type: 'text', value: '' }] },
            { variant: 'plain', segments: [{ type: 'gap', gap_id: 'g1' }] },
          ],
        ],
      }
    case 'notes':
      return {
        ...base,
        variant: 'notes',
        title: '',
        sections: [
          {
            heading: '',
            items: [{ segments: [{ type: 'gap', gap_id: 'g1' }] }],
          },
        ],
      }
    case 'form':
      return {
        ...base,
        variant: 'form',
        form_title: 'APPLICATION FORM',
        fields: [
          {
            type: 'gap_line',
            label: 'Field',
            segments: [{ type: 'gap', gap_id: 'g1' }],
          },
        ],
      }
    case 'summary':
      return {
        ...base,
        variant: 'summary',
        paragraphs: [
          {
            segments: [
              { type: 'text', value: 'Complete the summary. ' },
              { type: 'gap', gap_id: 'g1' },
              { type: 'text', value: '.' },
            ],
          },
        ],
      }
    case 'flow':
      return {
        ...base,
        variant: 'flow',
        title: '',
        steps: [{ segments: [{ type: 'gap', gap_id: 'g1' }] }],
      }
  }
}

export function extractGapIds(structure: CompoundStructure | null | undefined): string[] {
  if (!structure) return []
  const gaps: string[] = []

  if (structure.variant === 'table') {
    for (const row of structure.rows) {
      for (const cell of row) {
        if (cell.variant === 'bullets') {
          for (const bullet of cell.bullets) {
            gaps.push(...gapsFromSegments(bullet.segments))
          }
        } else {
          gaps.push(...gapsFromSegments(cell.segments))
        }
      }
    }
  } else if (structure.variant === 'notes') {
    for (const section of structure.sections) {
      for (const item of section.items) {
        gaps.push(...gapsFromSegments(item.segments))
      }
    }
  } else if (structure.variant === 'form') {
    for (const field of structure.fields) {
      if (field.type === 'gap_line') {
        gaps.push(...gapsFromSegments(field.segments))
      }
    }
  } else if (structure.variant === 'summary') {
    for (const paragraph of structure.paragraphs) {
      gaps.push(...gapsFromSegments(paragraph.segments))
    }
  } else if (structure.variant === 'flow') {
    for (const step of structure.steps) {
      gaps.push(...gapsFromSegments(step.segments))
    }
  }

  const seen = new Set<string>()
  const unique: string[] = []
  for (const id of gaps) {
    if (seen.has(id)) continue
    seen.add(id)
    unique.push(id)
  }
  return unique
}

export function nextGapId(existing: string[]): string {
  let n = 1
  const set = new Set(existing)
  while (set.has(`g${n}`)) n += 1
  return `g${n}`
}

/**
 * Parse editable text with `{gap}`, `{gap1}`, `{gap2}` (and legacy `[GAP1]` /
 * `[g1]`) into CellSegment[]. Numbered tokens keep stable gap_ids; bare
 * `{gap}` allocates the next free id via `allocId`.
 */
export function parseSegments(
  text: string,
  allocId: () => string = () => 'g1',
): CellSegment[] {
  const segments: CellSegment[] = []
  // Match {gap}, {gapN}, [GAPN], [gN]
  const re = /\{gap(\d*)\}|\[(?:GAP|g)(\d+)\]/gi
  let last = 0
  let match: RegExpExecArray | null
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) {
      segments.push({ type: 'text', value: text.slice(last, match.index) })
    }
    const numbered = match[1] !== undefined && match[1] !== ''
      ? match[1]
      : match[2]
    if (numbered) {
      segments.push({ type: 'gap', gap_id: `g${numbered}` })
    } else {
      // bare {gap}
      segments.push({ type: 'gap', gap_id: allocId() })
    }
    last = match.index + match[0].length
  }
  if (last < text.length) {
    segments.push({ type: 'text', value: text.slice(last) })
  }
  if (segments.length === 0) {
    segments.push({ type: 'text', value: text })
  }
  return segments
}

/** Serialize segments to editable text using stable `{gapN}` tokens. */
export function segmentsToText(segments: CellSegment[]): string {
  return segments
    .map((s) =>
      s.type === 'text' ? s.value : `{gap${s.gap_id.replace(/^g/i, '')}}`,
    )
    .join('')
}

/**
 * Parse a multi-paragraph summary. Gap ids are allocated globally across
 * paragraphs so bare `{gap}` tokens stay unique.
 */
export function parseSummaryGaps(
  text: string,
  base?: Pick<CompoundStructureBase, 'instruction_words' | 'max_words_per_gap'>,
): SummaryStructure {
  const used = new Set<string>()
  const allocId = () => {
    const id = nextGapId([...used])
    used.add(id)
    return id
  }

  const paragraphs = text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((paragraphText) => {
      const segments = parseSegments(paragraphText, allocId)
      for (const s of segments) {
        if (s.type === 'gap') used.add(s.gap_id)
      }
      return { segments }
    })

  return {
    variant: 'summary',
    instruction_words: base?.instruction_words ?? 'ONE WORD AND/OR A NUMBER',
    max_words_per_gap: base?.max_words_per_gap ?? 2,
    paragraphs:
      paragraphs.length > 0
        ? paragraphs
        : [{ segments: [{ type: 'text', value: '' }] }],
  }
}

export function summaryToEditableText(structure: SummaryStructure): string {
  return structure.paragraphs.map((p) => segmentsToText(p.segments)).join('\n\n')
}

/**
 * Parse a single-line/cell text into segments, preserving existing gap ids
 * from `knownIds` when allocating bare `{gap}`.
 */
export function parseCellText(
  text: string,
  knownIds: string[] = [],
): CellSegment[] {
  const used = new Set(knownIds)
  return parseSegments(text, () => {
    const id = nextGapId([...used])
    used.add(id)
    return id
  })
}

/** Convert a plain cell into a single-bullet bullets cell. */
export function plainToBullets(
  cell: Extract<TableCell, { variant: 'plain' }>,
): Extract<TableCell, { variant: 'bullets' }> {
  return {
    variant: 'bullets',
    bullets: [{ segments: cell.segments.length ? cell.segments : [{ type: 'text', value: '' }] }],
  }
}

/**
 * Flatten bullets into a plain cell, joining bullet texts with " / ".
 * Gap ids from the joined text are preserved via numbered `{gapN}` tokens.
 */
export function bulletsToPlain(
  cell: Extract<TableCell, { variant: 'bullets' }>,
  knownIds: string[] = [],
): Extract<TableCell, { variant: 'plain' }> {
  const joined = cell.bullets
    .map((b) => segmentsToText(b.segments))
    .filter((t) => t.length > 0)
    .join(' / ')
  return {
    variant: 'plain',
    segments: parseCellText(joined, knownIds),
  }
}

export function emptyPlainCell(): Extract<TableCell, { variant: 'plain' }> {
  return { variant: 'plain', segments: [{ type: 'text', value: '' }] }
}

export function emptyBulletsCell(): Extract<TableCell, { variant: 'bullets' }> {
  return {
    variant: 'bullets',
    bullets: [{ segments: [{ type: 'text', value: '' }] }],
  }
}

/** Insert a new gap after the last segment (plus trailing empty text). */
export function appendGap(
  segments: CellSegment[],
  gapId: string,
): CellSegment[] {
  const next = [...segments]
  if (next.length === 0) {
    return [
      { type: 'text', value: '' },
      { type: 'gap', gap_id: gapId },
      { type: 'text', value: '' },
    ]
  }
  next.push({ type: 'gap', gap_id: gapId })
  next.push({ type: 'text', value: '' })
  return next
}

export function removeGapFromSegments(
  segments: CellSegment[],
  gapId: string,
): CellSegment[] {
  const next = segments.filter(
    (s) => !(s.type === 'gap' && s.gap_id === gapId),
  )
  const merged: CellSegment[] = []
  for (const s of next) {
    const last = merged[merged.length - 1]
    if (s.type === 'text' && last?.type === 'text') {
      merged[merged.length - 1] = {
        type: 'text',
        value: last.value + s.value,
      }
    } else {
      merged.push(s)
    }
  }
  return merged.length > 0 ? merged : [{ type: 'text', value: '' }]
}

// ─── Legacy → segments normalization ─────────────────────────────────────────

function normalizeTableCell(cell: Record<string, unknown>): TableCell {
  if (cell.variant === 'bullets' || (Array.isArray(cell.bullets) && cell.variant !== 'plain')) {
    const bulletsRaw = Array.isArray(cell.bullets) ? (cell.bullets as unknown[]) : []
    const bullets: BulletItem[] = bulletsRaw.map((b) => {
      const bullet =
        b && typeof b === 'object' ? (b as Record<string, unknown>) : {}
      return {
        segments: Array.isArray(bullet.segments)
          ? (bullet.segments as CellSegment[])
          : [{ type: 'text' as const, value: '' }],
      }
    })
    return {
      variant: 'bullets',
      bullets:
        bullets.length > 0
          ? bullets
          : [{ segments: [{ type: 'text', value: '' }] }],
    }
  }

  if (Array.isArray(cell.segments)) {
    return {
      variant: 'plain',
      segments: cell.segments as CellSegment[],
    }
  }
  if (cell.type === 'gap' && typeof cell.gap_id === 'string') {
    return {
      variant: 'plain',
      segments: [{ type: 'gap', gap_id: cell.gap_id }],
    }
  }
  if (cell.type === 'text') {
    return {
      variant: 'plain',
      segments: [
        {
          type: 'text',
          value: typeof cell.value === 'string' ? cell.value : '',
        },
      ],
    }
  }
  return emptyPlainCell()
}

function normalizeNoteItem(item: Record<string, unknown>): NoteItem {
  if (Array.isArray(item.segments) && item.type !== 'text' && item.type !== 'gap_line') {
    return { segments: item.segments as CellSegment[] }
  }
  if (Array.isArray(item.segments) && !item.type) {
    return { segments: item.segments as CellSegment[] }
  }
  if (item.type === 'text') {
    return {
      segments: [
        {
          type: 'text',
          value: typeof item.value === 'string' ? item.value : '',
        },
      ],
    }
  }
  if (item.type === 'gap_line' && typeof item.gap_id === 'string') {
    const segments: CellSegment[] = []
    if (typeof item.prefix === 'string' && item.prefix) {
      segments.push({ type: 'text', value: item.prefix })
    }
    segments.push({ type: 'gap', gap_id: item.gap_id })
    if (typeof item.suffix === 'string' && item.suffix) {
      segments.push({ type: 'text', value: item.suffix })
    }
    return { segments }
  }
  if (Array.isArray(item.segments)) {
    return { segments: item.segments as CellSegment[] }
  }
  return { segments: [{ type: 'text', value: '' }] }
}

function normalizeFormField(field: Record<string, unknown>): FormField {
  if (field.type === 'static') {
    return {
      type: 'static',
      label: typeof field.label === 'string' ? field.label : '',
      value: typeof field.value === 'string' ? field.value : '',
    }
  }
  if (field.type === 'gap_line' && Array.isArray(field.segments)) {
    return {
      type: 'gap_line',
      label: typeof field.label === 'string' ? field.label : '',
      segments: field.segments as CellSegment[],
    }
  }
  if (field.type === 'gap' && typeof field.gap_id === 'string') {
    const segments: CellSegment[] = []
    if (typeof field.prefix === 'string' && field.prefix) {
      segments.push({ type: 'text', value: field.prefix })
    }
    segments.push({ type: 'gap', gap_id: field.gap_id })
    if (typeof field.suffix === 'string' && field.suffix) {
      segments.push({ type: 'text', value: field.suffix })
    }
    return {
      type: 'gap_line',
      label: typeof field.label === 'string' ? field.label : '',
      segments,
    }
  }
  return {
    type: 'static',
    label: typeof field.label === 'string' ? field.label : '',
    value: '',
  }
}

function normalizeStructure(raw: Record<string, unknown>): CompoundStructure | null {
  const variant = raw.variant
  const instruction_words =
    typeof raw.instruction_words === 'string'
      ? raw.instruction_words
      : 'ONE WORD AND/OR A NUMBER'
  const max_words_per_gap =
    typeof raw.max_words_per_gap === 'number' && raw.max_words_per_gap >= 1
      ? raw.max_words_per_gap
      : typeof raw.max_words_per_gap === 'number' && raw.max_words_per_gap === 0
        ? 1  // legacy: 0 was "ONE WORD ONLY", now represented as 1
        : 2
  const image_url =
    typeof raw.image_url === 'string' && raw.image_url.trim()
      ? raw.image_url.trim()
      : undefined
  const base = {
    instruction_words,
    max_words_per_gap,
    ...(image_url ? { image_url } : {}),
  }

  if (variant === 'table') {
    const headers = Array.isArray(raw.headers)
      ? (raw.headers as unknown[]).map((h) => String(h ?? ''))
      : []
    const rowsRaw = Array.isArray(raw.rows) ? (raw.rows as unknown[]) : []
    const rows: TableCell[][] = rowsRaw.map((row) =>
      Array.isArray(row)
        ? row.map((cell) =>
            normalizeTableCell(
              cell && typeof cell === 'object'
                ? (cell as Record<string, unknown>)
                : {},
            ),
          )
        : [],
    )
    return { variant: 'table', ...base, ...(typeof raw.title === 'string' && raw.title.trim() ? { title: raw.title.trim() } : {}), headers, rows }
  }

  if (variant === 'notes') {
    const sectionsRaw = Array.isArray(raw.sections) ? (raw.sections as unknown[]) : []
    const sections: NoteSection[] = sectionsRaw.map((sec) => {
      const s =
        sec && typeof sec === 'object' ? (sec as Record<string, unknown>) : {}
      const itemsRaw = Array.isArray(s.items) ? (s.items as unknown[]) : []
      return {
        heading: typeof s.heading === 'string' ? s.heading : '',
        items: itemsRaw.map((it) =>
          normalizeNoteItem(
            it && typeof it === 'object' ? (it as Record<string, unknown>) : {},
          ),
        ),
      }
    })
    return {
      variant: 'notes',
      ...base,
      title: typeof raw.title === 'string' ? raw.title : '',
      bullets: raw.bullets === false ? false : true,
      sections,
    }
  }

  if (variant === 'form') {
    const fieldsRaw = Array.isArray(raw.fields) ? (raw.fields as unknown[]) : []
    const fields = fieldsRaw.map((f) =>
      normalizeFormField(
        f && typeof f === 'object' ? (f as Record<string, unknown>) : {},
      ),
    )
    return {
      variant: 'form',
      ...base,
      form_title: typeof raw.form_title === 'string' ? raw.form_title : '',
      fields,
    }
  }

  if (variant === 'summary') {
    const paragraphsRaw = Array.isArray(raw.paragraphs)
      ? (raw.paragraphs as unknown[])
      : []
    const paragraphs: SummaryParagraph[] = paragraphsRaw.map((p) => {
      const para =
        p && typeof p === 'object' ? (p as Record<string, unknown>) : {}
      return {
        segments: Array.isArray(para.segments)
          ? (para.segments as CellSegment[])
          : [{ type: 'text', value: '' }],
      }
    })
    const options = Array.isArray(raw.options)
      ? (raw.options as unknown[])
          .filter((o): o is string => typeof o === 'string')
          .map((o) => o.trim())
          .filter(Boolean)
      : undefined
    return {
      variant: 'summary',
      ...base,
      title: typeof raw.title === 'string' ? raw.title : '',
      ...(options && options.length > 0 ? { options } : {}),
      paragraphs,
    }
  }

  if (variant === 'flow') {
    const stepsRaw = Array.isArray(raw.steps) ? (raw.steps as unknown[]) : []
    const steps: FlowStep[] = stepsRaw.map((st) => {
      const step =
        st && typeof st === 'object' ? (st as Record<string, unknown>) : {}
      return normalizeNoteItem(step) as FlowStep
    })
    return {
      variant: 'flow',
      ...base,
      title: typeof raw.title === 'string' ? raw.title : '',
      steps,
    }
  }

  return null
}

/**
 * Coerce raw options_shared JSON into a CompoundStructure, normalizing any
 * legacy cell/item/field shapes into the segments model.
 */
export function asCompoundStructure(
  value: Record<string, unknown> | null | undefined,
): CompoundStructure | null {
  if (!value || typeof value !== 'object') return null
  const variant = value.variant
  if (
    variant !== 'table' &&
    variant !== 'notes' &&
    variant !== 'form' &&
    variant !== 'summary' &&
    variant !== 'flow'
  ) {
    return null
  }
  return normalizeStructure(value)
}
