import {
  BarChart3,
  BookOpen,
  HelpCircle,
  LayoutDashboard,
  Mic,
  Settings,
  UserCog,
  Palette,
  Users,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'Admin',
    email: 'admin@ielts-mock.com',
    avatar: '/avatars/shadcn.jpg',
  },
  teams: [],
  navGroups: [
    {
      title: 'General',
      items: [
        {
          title: 'Dashboard',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Tests',
          url: '/tests',
          icon: BookOpen,
        },
        {
          title: 'Results',
          url: '/results',
          icon: BarChart3,
        },
        {
          title: 'Students',
          url: '/students',
          icon: Users,
        },
        {
          title: 'AI Examiner',
          url: '/speaking-examiner',
          icon: Mic,
        },
      ],
    },
    {
      title: 'Other',
      items: [
        {
          title: 'Settings',
          icon: Settings,
          items: [
            {
              title: 'Account',
              url: '/settings',
              icon: UserCog,
            },
            {
              title: 'Appearance',
              url: '/settings/appearance',
              icon: Palette,
            },
          ],
        },
        {
          title: 'Help Center',
          url: '/help-center',
          icon: HelpCircle,
        },
      ],
    },
  ],
}
