const key = (attemptId: string) => `score-reveal:${attemptId}`

export function markScoreReveal(attemptId: string): void {
  try {
    sessionStorage.setItem(key(attemptId), '1')
  } catch {
    /* private mode */
  }
}

export function hasScoreReveal(attemptId: string): boolean {
  try {
    return sessionStorage.getItem(key(attemptId)) === '1'
  } catch {
    return false
  }
}

export function clearScoreReveal(attemptId: string): void {
  try {
    sessionStorage.removeItem(key(attemptId))
  } catch {
    /* private mode */
  }
}
