import { BarChart3, BookOpen, Home, User, type LucideIcon } from 'lucide-react'

export type StudentNavItem = {
  to: '/student/dashboard' | '/student/tests' | '/student/results' | '/student/profile'
  label: string
  icon: LucideIcon
}

export const STUDENT_NAV: readonly StudentNavItem[] = [
  { to: '/student/dashboard', label: 'Dashboard', icon: Home },
  { to: '/student/tests', label: 'Tests', icon: BookOpen },
  { to: '/student/results', label: 'Results', icon: BarChart3 },
  { to: '/student/profile', label: 'Profile', icon: User },
] as const

export function isStudentNavActive(pathname: string, to: StudentNavItem['to']): boolean {
  if (to === '/student/dashboard') return pathname === '/student/dashboard'
  return pathname === to || pathname.startsWith(`${to}/`)
}
