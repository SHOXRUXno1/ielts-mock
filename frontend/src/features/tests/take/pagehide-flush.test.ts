import { describe, expect, it } from 'vitest'
import { buildPagehideFlushInit } from './pagehide-flush'

describe('buildPagehideFlushInit', () => {
  it('returns null when there is nothing to flush', () => {
    expect(
      buildPagehideFlushInit({
        baseUrl: 'http://localhost:8000',
        attemptId: 'a1',
        token: 'tok',
        answers: [],
      }),
    ).toBeNull()
  })

  it('builds keepalive POST with Authorization', () => {
    const req = buildPagehideFlushInit({
      baseUrl: 'http://localhost:8000/',
      attemptId: 'attempt-1',
      token: 'secret',
      answers: [{ question_id: 'q1', response: { answer: 'A' } }],
    })
    expect(req).not.toBeNull()
    expect(req!.url).toBe('http://localhost:8000/attempts/attempt-1/answers')
    expect(req!.init.method).toBe('POST')
    expect(req!.init.keepalive).toBe(true)
    const headers = req!.init.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer secret')
    expect(JSON.parse(String(req!.init.body))).toEqual({
      answers: [{ question_id: 'q1', response: { answer: 'A' } }],
    })
  })
})
