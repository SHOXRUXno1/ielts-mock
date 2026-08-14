import {
  BarChart3,
  BookOpen,
  HelpCircle,
  LayoutDashboard,
  Mic,
  MonitorSmartphone,
  Settings,
  TrendingUp,
  UserCog,
  Palette,
  Users,
} from 'lucide-react'
import type { SidebarData } from '../types'

export function sidebarDataFor(
  role: 'admin' | 'student' | undefined,
  name?: string,
  login?: string
): SidebarData {
  const user =
    role === 'student'
      ? { name: name ?? 'Student', email: login ?? '', avatar: '/avatars/shadcn.jpg' }
      : { name: name ?? 'Admin', email: login ?? '', avatar: '/avatars/shadcn.jpg' }

  if (role === 'student') {
    return { user, teams: [], navGroups: [] }
  }

  return {
    user,
    teams: [],
    navGroups: [
      {
        title: 'General',
        items: [
          { title: 'Dashboard', url: '/', icon: LayoutDashboard },
          { title: 'Tests', url: '/tests', icon: BookOpen },
          { title: 'Results', url: '/results', icon: BarChart3 },
          { title: 'Students', url: '/students', icon: Users },
          { title: 'Analytics', url: '/analytics', icon: TrendingUp },
          { title: 'AI Examiner', url: '/speaking-examiner', icon: Mic },
        ],
      },
      {
        title: 'Other',
        items: [
          {
            title: 'Settings',
            icon: Settings,
            items: [
              { title: 'Account', url: '/settings', icon: UserCog },
              { title: 'Appearance', url: '/settings/appearance', icon: Palette },
              { title: 'Devices', url: '/devices', icon: MonitorSmartphone },
            ],
          },
          { title: 'Help Center', url: '/help-center', icon: HelpCircle },
        ],
      },
    ],
  }
}

export const sidebarData: SidebarData = sidebarDataFor('admin')
