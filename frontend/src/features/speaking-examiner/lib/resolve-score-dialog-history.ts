import type {
  ConversationTurn,
  ExaminerScore,
} from '@/lib/api/speaking-examiner'

export function resolveScoreDialogHistory(
  score: ExaminerScore,
  clientHistory?: ConversationTurn[],
): ConversationTurn[] {
  if (clientHistory?.length) return clientHistory
  if (score.conversation_history?.length) return score.conversation_history
  const t = score.transcript?.trim()
  if (t && t !== '(empty)' && t !== '(No speech detected)') {
    return t
      .split('\n\n')
      .filter(Boolean)
      .map((text) => ({ role: 'candidate' as const, text }))
  }
  return []
}
