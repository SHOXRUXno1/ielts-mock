import { api } from '@/lib/axios'

export type StudentRead = {
  id: string
  login: string
  full_name: string
  phone: string | null
  group_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

export type StudentCreated = StudentRead & {
  password: string
}

export type StudentCreate = {
  full_name: string
  phone: string
  group_name?: string
}

export type StudentUpdate = {
  full_name?: string
  phone?: string
  group_name?: string
  is_active?: boolean
}

export type AttemptSummary = {
  id: string
  test_id: string
  status: string
  overall_band: number | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export type StudentDetail = StudentRead & {
  attempts: AttemptSummary[]
}

export async function fetchStudents(params?: {
  search?: string
  group?: string
  is_active?: boolean
}): Promise<StudentRead[]> {
  const { data } = await api.get<StudentRead[]>('/admin/students/', { params })
  return data
}

export async function createStudent(body: StudentCreate): Promise<StudentCreated> {
  const { data } = await api.post<StudentCreated>('/admin/students/', body)
  return data
}

export async function getStudent(id: string): Promise<StudentDetail> {
  const { data } = await api.get<StudentDetail>(`/admin/students/${id}`)
  return data
}

export async function updateStudent(id: string, body: StudentUpdate): Promise<StudentRead> {
  const { data } = await api.put<StudentRead>(`/admin/students/${id}`, body)
  return data
}

export async function resetStudentPassword(id: string): Promise<{ password: string }> {
  const { data } = await api.post<{ password: string }>(`/admin/students/${id}/reset-password`)
  return data
}

export async function deleteStudent(id: string): Promise<void> {
  await api.delete(`/admin/students/${id}`)
}
