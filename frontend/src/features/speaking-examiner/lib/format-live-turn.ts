export const LIVE_TURN_TRUNCATE_LENGTH = 180
export const LIVE_TURN_PREVIEW_LENGTH = 160

export function isCueCardTurn(text: string): boolean {
  return /you should say:/i.test(text)
}

export function shouldTruncateLiveTurn(text: string): boolean {
  return text.length > LIVE_TURN_TRUNCATE_LENGTH || isCueCardTurn(text)
}

export function previewLiveTurnText(text: string): string {
  if (text.length <= LIVE_TURN_PREVIEW_LENGTH) return text
  return `${text.slice(0, LIVE_TURN_PREVIEW_LENGTH).trimEnd()}…`
}

export function liveTurnLabel(role: 'examiner' | 'candidate', text: string): string {
  if (role === 'examiner' && isCueCardTurn(text)) {
    return 'Cue card'
  }
  return role === 'examiner' ? 'Examiner' : 'You'
}
