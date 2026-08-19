import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { apiErrorMessage, apiUploadErrorMessage } from './error'

function axiosTimeout(): AxiosError {
  const err = new AxiosError('timeout of 20000ms exceeded')
  err.code = 'ECONNABORTED'
  return err
}

describe('apiErrorMessage', () => {
  it('reads FastAPI string detail', () => {
    const err = new AxiosError('Request failed')
    err.response = {
      status: 422,
      statusText: 'Unprocessable Entity',
      headers: {},
      config: err.config!,
      data: { detail: 'Unsupported audio format' },
    }
    expect(apiErrorMessage(err)).toBe('Unsupported audio format')
  })

  it('maps a timeout to a retry hint', () => {
    expect(apiErrorMessage(axiosTimeout())).toMatch(/timed out/i)
  })
})

describe('apiUploadErrorMessage', () => {
  it('explains a timed-out media upload', () => {
    expect(apiUploadErrorMessage(axiosTimeout())).toMatch(/file may be large/i)
  })
})
