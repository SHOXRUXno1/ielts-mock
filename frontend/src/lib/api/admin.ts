import { api } from '@/lib/axios'

export type AdminLoginPayload = {
  email: string
  password: string
}

export type AdminTokenResponse = {
  access_token: string
  token_type: string
}

export type AdminMe = {
  login: string
  name: string
  role: string
}

export async function adminLogin(
  payload: AdminLoginPayload
): Promise<AdminTokenResponse> {
  const { data } = await api.post<AdminTokenResponse>(
    '/admin/auth/login',
    payload
  )
  return data
}

export async function adminMe(): Promise<AdminMe> {
  const { data } = await api.get<AdminMe>('/admin/auth/me')
  return data
}

export type JwtPayload = {
  sub: string
  role: string
  exp: number
}

export function decodeJwt(token: string): JwtPayload {
  const payload = token.split('.')[1]
  return JSON.parse(atob(payload))
}

export async function changePassword(body: {
  current_password: string
  new_password: string
}): Promise<{ ok: boolean }> {
  const { data } = await api.patch<{ ok: boolean }>('/admin/auth/password', body)
  return data
}

export async function changeName(body: {
  new_name: string
}): Promise<{ ok: boolean; new_name: string }> {
  const { data } = await api.patch<{ ok: boolean; new_name: string }>('/admin/auth/name', body)
  return data
}
