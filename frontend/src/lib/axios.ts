import axios from 'axios'
import { useAuthStore } from '@/stores/auth-store'

export const api = axios.create({
  // Empty = same origin. Nginx already proxies /auth, /admin, /tests, etc.
  baseURL: import.meta.env.VITE_API_URL || '',
  // Speaking / TTS calls set their own longer timeout.
  timeout: 20_000,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().auth.accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
