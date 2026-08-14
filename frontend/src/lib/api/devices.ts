import { api } from '@/lib/axios'

export type AdminSession = {
  id: string
  actor_login: string
  actor_name: string | null
  ip_address: string | null
  device_type: string
  browser: string | null
  os_name: string | null
  login_at: string
  last_seen_at: string
  ended_at: string | null
  end_reason: string | null
  is_online: boolean
  is_current: boolean
  duration_seconds: number
}

export type DevicesSummary = {
  online_now: number
  logins_today: number
  unique_devices_7d: number
  last_login_at: string | null
}

export type DevicesStatusFilter = 'all' | 'online' | 'ended'

export async function fetchDevices(params?: {
  status?: DevicesStatusFilter
  days?: number
  limit?: number
}): Promise<AdminSession[]> {
  const { data } = await api.get<AdminSession[]>('/admin/devices/', { params })
  return data
}

export async function fetchDevicesSummary(): Promise<DevicesSummary> {
  const { data } = await api.get<DevicesSummary>('/admin/devices/summary')
  return data
}

export async function revokeSession(sessionId: string): Promise<void> {
  await api.delete(`/admin/devices/${sessionId}`)
}

export async function revokeAllSessions(): Promise<{ revoked: number }> {
  const { data } = await api.post<{ revoked: number }>('/admin/devices/revoke-all')
  return data
}
