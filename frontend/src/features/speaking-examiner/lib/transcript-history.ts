import type { ConversationTurn } from '@/lib/api/speaking-examiner'

export function transcriptHistorySignature(history: ConversationTurn[]): string {
  if (history.length === 0) return '0'
  const last = history[history.length - 1]
  return `${history.length}:${last.role}:${last.text.length}:${last.text.slice(-24)}`
}
