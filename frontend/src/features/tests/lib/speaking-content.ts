import type { Question, Section } from '../data/schema'

/** Questions attached to a speaking section (groups first, then fetched map). */
export function questionsForSection(
  section: Section,
  questionsMap: Record<string, Question[]>,
): Question[] {
  const fromMap = questionsMap[section.id] ?? []
  if (fromMap.length > 0) return fromMap
  return (section.question_groups ?? []).flatMap((g) => g.questions ?? [])
}

/** True when a part has examiner prompts or a Part 2 cue card topic. */
export function speakingPartHasContent(questions: Question[]): boolean {
  for (const q of questions) {
    const c = q.content ?? {}
    if (Array.isArray(c.questions)) {
      if (c.questions.some((p) => typeof p === 'string' && p.trim())) return true
    }
    const cue = c.cue_card
    if (cue && typeof cue === 'object') {
      const topic = (cue as { topic?: unknown }).topic
      if (typeof topic === 'string' && topic.trim()) return true
    }
    if (typeof c.prompt === 'string' && c.prompt.trim()) return true
    if (typeof c.topic === 'string' && c.topic.trim()) return true
  }
  return false
}

export function countAuthoredSpeakingParts(
  sections: Section[],
  questionsMap: Record<string, Question[]>,
): number {
  return sections
    .filter((s) => s.type === 'speaking')
    .sort((a, b) => a.order - b.order)
    .filter((s) => speakingPartHasContent(questionsForSection(s, questionsMap)))
    .length
}
