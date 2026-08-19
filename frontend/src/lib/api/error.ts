import type { AxiosError } from 'axios'

type FastApiDetail =
  | string
  | { msg: string }[]
  | { errors: unknown[] }
  | Record<string, unknown>

/**
 * Extracts a human-readable error message from an Axios error response.
 * FastAPI returns `{ detail: string }`, `{ detail: [{msg}] }`, or
 * `{ detail: { errors: string[] } }` (publish validation).
 */
function isTimeoutError(err: AxiosError): boolean {
  return (
    err.code === 'ECONNABORTED' ||
    err.code === 'ETIMEDOUT' ||
    /timeout/i.test(err.message ?? '')
  )
}

export function apiErrorMessage(err: unknown, fallback = 'Something went wrong.'): string {
  const axiosErr = err as AxiosError<{ detail?: FastApiDetail }>
  if (axiosErr?.isAxiosError && isTimeoutError(axiosErr)) {
    return 'Request timed out. Please try again.'
  }
  if (axiosErr?.isAxiosError && !axiosErr.response) {
    return 'Network error. Check your connection and try again.'
  }
  const detail = axiosErr?.response?.data?.detail
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  if (
    typeof detail === 'object' &&
    !Array.isArray(detail) &&
    'errors' in detail &&
    Array.isArray(detail.errors) &&
    detail.errors.length > 0
  ) {
    return detail.errors.map(String).join('\n')
  }
  return fallback
}

/** All publish / validation error strings from a FastAPI 422 response. */
export function apiErrorMessages(err: unknown, fallback = 'Something went wrong.'): string[] {
  const axiosErr = err as AxiosError<{ detail?: FastApiDetail }>
  const detail = axiosErr?.response?.data?.detail
  if (!detail) return [fallback]
  if (typeof detail === 'string') return [detail]
  if (Array.isArray(detail)) {
    return detail.map((d) =>
      typeof d === 'object' && d && 'msg' in d ? String(d.msg) : String(d),
    )
  }
  if (
    typeof detail === 'object' &&
    'errors' in detail &&
    Array.isArray(detail.errors) &&
    detail.errors.length > 0
  ) {
    return detail.errors.map(String)
  }
  return [fallback]
}

/** Timeout / network copy for media uploads (listening audio, images). */
export function apiUploadErrorMessage(
  err: unknown,
  fallback = 'Failed to upload file.',
): string {
  const axiosErr = err as AxiosError
  if (axiosErr?.isAxiosError && isTimeoutError(axiosErr)) {
    return 'Upload timed out. The file may be large — please try again.'
  }
  if (axiosErr?.isAxiosError && !axiosErr.response) {
    return 'Connection lost during upload. Please try again.'
  }
  return apiErrorMessage(err, fallback)
}
