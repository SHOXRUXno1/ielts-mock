export type Student = {
  id: string
  login: string
  full_name: string
  phone: string | null
  group_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

export type StudentDialogAction =
  | 'add'
  | 'edit'
  | 'delete'
  | 'reset-password'
  | 'show-credentials'
  | null
