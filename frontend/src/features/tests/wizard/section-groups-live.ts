import type { CompoundGroupDraft } from '../data/compound'
import type { QuestionGroup, SlotNumberingGroup } from '../data/schema'

/** Merge live draft question rows over saved group.questions for Q numbering. */
export function buildLiveSectionGroups(
  sortedGroups: QuestionGroup[],
  drafts: Record<string, CompoundGroupDraft>,
): SlotNumberingGroup[] {
  return sortedGroups.map((g) => {
    const draft = drafts[g.id]
    const qType = draft?.questionType ?? g.question_type
    if (draft?.questions && draft.questions.length > 0) {
      return {
        id: g.id,
        order: g.order,
        question_type: qType,
        questions: draft.questions.map((d, i) => ({
          id: d.id ?? `__draft-${g.id}-${i}`,
          order: d.order,
          question_type: qType,
          content: d.content,
          answer_key: d.answer_key,
        })),
      }
    }
    return {
      id: g.id,
      order: g.order,
      question_type: g.question_type,
      questions: g.questions.map((q) => ({
        id: q.id,
        order: q.order,
        question_type: q.question_type,
        content: q.content,
        answer_key: q.answer_key,
      })),
    }
  })
}
