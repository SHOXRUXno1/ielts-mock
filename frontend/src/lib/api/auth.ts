import { api } from '@/lib/axios'

export type LoginPayload = {
  login: string
  password: string
}

export type TokenUser = {
  id: string | null
  login: string
  full_name: string
  role: 'admin' | 'student'
}

export type LoginResponse = {
  access_token: string
  token_type: string
  user: TokenUser
}

export type MeResponse = {
  id: string | null
  login: string
  full_name: string | null
  name: string | null
  role: 'admin' | 'student'
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', payload)
  return data
}

export async function authMe(): Promise<MeResponse> {
  const { data } = await api.get<MeResponse>('/auth/me')
  return data
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

