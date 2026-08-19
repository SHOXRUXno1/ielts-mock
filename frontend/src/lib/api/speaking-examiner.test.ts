import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { getSpeakingApiErrorDetail } from './speaking-examiner'

describe('getSpeakingApiErrorDetail', () => {
  it('surfaces FastAPI detail on 502 instead of a generic 5xx toast', () => {
    const err = new AxiosError('Request failed')
    err.response = {
      status: 502,
      statusText: 'Bad Gateway',
      headers: {},
      config: err.config!,
      data: { detail: 'Transcription failed (HTTP 403)' },
    }
    expect(getSpeakingApiErrorDetail(err)).toBe('Transcription failed (HTTP 403)')
  })

  it('falls back to the generic speaking toast when 5xx has no detail', () => {
    const err = new AxiosError('Request failed')
    err.response = {
      status: 500,
      statusText: 'Internal Server Error',
      headers: {},
      config: err.config!,
      data: {},
    }
    expect(getSpeakingApiErrorDetail(err)).toMatch(/Speaking service had an error/)
  })
})
