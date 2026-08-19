import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import {
  apiErrorMessage,
  apiUploadErrorMessage,
  isRetryableUploadError,
} from './error'

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

  it('keeps a local validation message', () => {
    expect(apiUploadErrorMessage(new Error('Audio is too large (max 50 MB).'))).toBe(
      'Audio is too large (max 50 MB).',
    )
  })
})

describe('isRetryableUploadError', () => {
  it('retries timeouts and gateway failures, not validation', () => {
    expect(isRetryableUploadError(axiosTimeout())).toBe(true)
    const badGateway = new AxiosError('bad gateway')
    badGateway.response = {
      status: 502,
      statusText: 'Bad Gateway',
      headers: {},
      config: badGateway.config!,
      data: {},
    }
    expect(isRetryableUploadError(badGateway)).toBe(true)
    const unsupported = new AxiosError('unprocessable')
    unsupported.response = {
      status: 422,
      statusText: 'Unprocessable Entity',
      headers: {},
      config: unsupported.config!,
      data: { detail: 'Unsupported audio format' },
    }
    expect(isRetryableUploadError(unsupported)).toBe(false)
  })
})
