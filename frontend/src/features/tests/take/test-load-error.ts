type ErrorResponse = {
  response?: {
    status?: number
  }
}

export type TestLoadError = {
  message: string
  action: 'login' | 'tests' | 'retry' | null
}

/**
 * Keep a failed test fetch truthful. A missing token, an unavailable server,
 * and a genuinely deleted test need different recovery actions.
 */
export function testLoadError(
  error: unknown,
  hasResumeAttempt: boolean,
): TestLoadError {
  const status = (error as ErrorResponse | undefined)?.response?.status

  if (status === 401) {
    return {
      message: 'Your session has expired. Please sign in again.',
      action: 'login',
    }
  }

  if (status === 403) {
    return {
      message: 'This test is not available for your account.',
      action: 'tests',
    }
  }

  if (status === 404 && hasResumeAttempt) {
    return {
      message: 'This saved attempt is no longer available.',
      action: 'tests',
    }
  }

  if (status === 404) {
    return {
      message: 'This test no longer exists.',
      action: 'tests',
    }
  }

  if (!status) {
    return {
      message: 'Cannot reach the server. Check your connection and try again.',
      action: 'retry',
    }
  }

  return {
    message: 'Could not load this test. Please try again.',
    action: 'retry',
  }
}
