import { create } from 'zustand'
import { getCookie, setCookie, removeCookie } from '@/lib/cookies'

const ACCESS_TOKEN = 'thisisjustarandomstring'
const USER_SNAPSHOT = 'auth_user'

export interface AuthUser {
  id: string | null
  login: string
  name: string
  full_name?: string
  role: 'admin' | 'student'
  exp: number
}

interface AuthState {
  auth: {
    user: AuthUser | null
    setUser: (user: AuthUser | null) => void
    accessToken: string
    setAccessToken: (accessToken: string) => void
    resetAccessToken: () => void
    reset: () => void
  }
}

function loadUser(): AuthUser | null {
  try {
    const raw = getCookie(USER_SNAPSHOT)
    if (!raw) return null
    return JSON.parse(decodeURIComponent(raw)) as AuthUser
  } catch {
    return null
  }
}

function persistUser(user: AuthUser | null) {
  if (user) {
    setCookie(USER_SNAPSHOT, encodeURIComponent(JSON.stringify(user)))
  } else {
    removeCookie(USER_SNAPSHOT)
  }
}

export const useAuthStore = create<AuthState>()((set) => {
  const cookieState = getCookie(ACCESS_TOKEN)
  const initToken = cookieState ? JSON.parse(cookieState) : ''
  const initUser = initToken ? loadUser() : null
  return {
    auth: {
      user: initUser,
      setUser: (user) =>
        set((state) => {
          persistUser(user)
          return { ...state, auth: { ...state.auth, user } }
        }),
      accessToken: initToken,
      setAccessToken: (accessToken) =>
        set((state) => {
          setCookie(ACCESS_TOKEN, JSON.stringify(accessToken))
          return { ...state, auth: { ...state.auth, accessToken } }
        }),
      resetAccessToken: () =>
        set((state) => {
          removeCookie(ACCESS_TOKEN)
          return { ...state, auth: { ...state.auth, accessToken: '' } }
        }),
      reset: () =>
        set((state) => {
          removeCookie(ACCESS_TOKEN)
          removeCookie(USER_SNAPSHOT)
          return {
            ...state,
            auth: { ...state.auth, user: null, accessToken: '' },
          }
        }),
    },
  }
})
