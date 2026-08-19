import axios from 'axios'
import { useAuthStore } from '@/stores/auth-store'

/** Listening MP3s are often 5–15 MB; 20s aborts the POST (nginx 499). */
export const MEDIA_UPLOAD_TIMEOUT_MS = 180_000

export const api = axios.create({
  // Empty = same origin. Nginx already proxies /auth, /admin, /tests, etc.
  baseURL: import.meta.env.VITE_API_URL || '',
  // Speaking / TTS / media uploads set their own longer timeout.
  timeout: 20_000,
  headers: {
    Accept: 'application/json',
    // /student/tests and other API paths also serve the SPA. Without this,
    // Chrome reuses the cached HTML document for the XHR and the page crashes.
    'Cache-Control': 'no-store',
    Pragma: 'no-cache',
  },
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().auth.accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
