/**
 * Build a keepalive fetch init for flushing answers on pagehide.
 * sendBeacon cannot set Authorization, so we use fetch({ keepalive: true }).
 */
export function buildPagehideFlushInit(opts: {
  baseUrl: string
  attemptId: string
  token: string | null | undefined
  answers: { question_id: string; response: Record<string, unknown> }[]
}): { url: string; init: RequestInit } | null {
  if (!opts.attemptId || opts.answers.length === 0) return null
  const base = opts.baseUrl.replace(/\/$/, '')
  return {
    url: `${base}/attempts/${opts.attemptId}/answers`,
    init: {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(opts.token ? { Authorization: `Bearer ${opts.token}` } : {}),
      },
      body: JSON.stringify({ answers: opts.answers }),
      keepalive: true,
    },
  }
}
