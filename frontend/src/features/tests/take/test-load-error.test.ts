import { describe, expect, it } from 'vitest'
import { testLoadError } from './test-load-error'

describe('testLoadError', () => {
  it('does not mislabel an expired session as a missing test', () => {
    expect(testLoadError({ response: { status: 401 } }, true)).toEqual({
      message: 'Your session has expired. Please sign in again.',
      action: 'login',
    })
  })

  it('uses the saved-attempt message only for a real 404', () => {
    expect(testLoadError({ response: { status: 404 } }, true)).toEqual({
      message: 'This saved attempt is no longer available.',
      action: 'tests',
    })
  })

  it('offers a retry for a network failure', () => {
    expect(testLoadError(new Error('Network Error'), false)).toEqual({
      message: 'Cannot reach the server. Check your connection and try again.',
      action: 'retry',
    })
  })
})
