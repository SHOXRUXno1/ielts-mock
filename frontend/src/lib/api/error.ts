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
export function apiErrorMessage(err: unknown, fallback = 'Something went wrong.'): string {
  const axiosErr = err as AxiosError<{ detail?: FastApiDetail }>
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
