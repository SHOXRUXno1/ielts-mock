import type { AxiosError } from 'axios'

/**
 * Extracts a human-readable error message from an Axios error response.
 * FastAPI returns `{ detail: string }` for 4xx/5xx errors.
 */
export function apiErrorMessage(err: unknown, fallback = 'Something went wrong.'): string {
  const axiosErr = err as AxiosError<{ detail?: string | { msg: string }[] }>
  const detail = axiosErr?.response?.data?.detail
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return fallback
}
