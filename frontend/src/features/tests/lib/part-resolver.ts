import type { Question, Section, SectionType } from '../data/schema'

export type ResolvedPart = {
  /** Section UUID for listening/reading/speaking; writing section UUID for writing */
  sectionId: string
  /** 0-based task index for writing; null for other types */
  writingTaskIdx: number | null
  /** 1-based part index as used in the URL */
  partIndex: number
}

/** Sections of a type, sorted by order ascending. */
export function sectionsOfType(
  sections: Section[],
  type: SectionType,
): Section[] {
  return sections
    .filter((s) => s.type === type)
    .sort((a, b) => a.order - b.order)
}

function writingTasks(
  sections: Section[],
  writingQuestions?: Question[],
): Question[] {
  const writingSec = sectionsOfType(sections, 'writing')[0]
  if (!writingSec) return []
  const qs =
    writingQuestions ??
    writingSec.question_groups.flatMap((g) => g.questions)
  const essays = qs.filter(
    (q) => q.question_type === 'essay' || q.task_number != null,
  )
  return [...essays].sort((a, b) => {
    const aN = a.task_number ?? a.order
    const bN = b.task_number ?? b.order
    return aN - bN
  })
}

/**
 * How many parts/passages/tasks a skill has.
 * Listening/Reading/Speaking = number of Section rows.
 * Writing = number of essay questions (task_number), default 2 when empty.
 */
export function partCount(
  sections: Section[],
  type: SectionType,
  writingQuestions?: Question[],
): number {
  if (type === 'writing') {
    const tasks = writingTasks(sections, writingQuestions)
    return tasks.length > 0 ? tasks.length : sectionsOfType(sections, 'writing').length > 0 ? 2 : 0
  }
  return sectionsOfType(sections, type).length
}

/**
 * Resolve a 1-based part index to a section (and writing task).
 * Returns null if the type is missing or partIndex is out of range.
 */
export function resolvePart(
  sections: Section[],
  type: SectionType,
  partIndex: number,
  writingQuestions?: Question[],
): ResolvedPart | null {
  if (!Number.isFinite(partIndex) || partIndex < 1) return null

  if (type === 'writing') {
    const writingSec = sectionsOfType(sections, 'writing')[0]
    if (!writingSec) return null
    const count = partCount(sections, 'writing', writingQuestions)
    if (partIndex > count) return null
    return {
      sectionId: writingSec.id,
      writingTaskIdx: partIndex - 1,
      partIndex,
    }
  }

  const siblings = sectionsOfType(sections, type)
  const section = siblings[partIndex - 1]
  if (!section) return null
  return {
    sectionId: section.id,
    writingTaskIdx: null,
    partIndex,
  }
}

/** 1-based part index for a section id, or null if not found. */
export function partIndexForSection(
  sections: Section[],
  sectionId: string,
): number | null {
  const section = sections.find((s) => s.id === sectionId)
  if (!section) return null
  if (section.type === 'writing') return 1
  const siblings = sectionsOfType(sections, section.type as SectionType)
  const idx = siblings.findIndex((s) => s.id === sectionId)
  return idx >= 0 ? idx + 1 : null
}

/**
 * 1-based part index for a question (writing uses task_number; others use section).
 */
export function partIndexForQuestion(
  sections: Section[],
  sectionQuestions: Record<string, Question[]>,
  sectionId: string,
  questionId: string,
): number | null {
  const section = sections.find((s) => s.id === sectionId)
  if (!section) return null

  if (section.type === 'writing') {
    const qs = sectionQuestions[sectionId] ?? []
    const q = qs.find((item) => item.id === questionId)
    if (!q) return null
    const tasks = writingTasks(sections, qs)
    const taskIdx = tasks.findIndex((t) => t.id === questionId)
    if (taskIdx >= 0) return taskIdx + 1
    const tn = q.task_number ?? q.order
    return tn >= 1 ? tn : 1
  }

  return partIndexForSection(sections, sectionId)
}

/** Clamp a 1-based part index into [1, partCount]. Returns 1 if type missing. */
export function clampPart(
  sections: Section[],
  type: SectionType,
  partIndex: number,
  writingQuestions?: Question[],
): number {
  const count = partCount(sections, type, writingQuestions)
  if (count <= 0) return 1
  if (!Number.isFinite(partIndex) || partIndex < 1) return 1
  if (partIndex > count) return count
  return Math.floor(partIndex)
}

export const SECTION_TYPES: SectionType[] = [
  'listening',
  'reading',
  'writing',
  'speaking',
]

export function isSectionType(value: string): value is SectionType {
  return (SECTION_TYPES as string[]).includes(value)
}
