import { Link } from '@tanstack/react-router'
import { AlertTriangle, ChevronRight } from 'lucide-react'
import type { DashboardAlert } from '@/lib/api/admin-dashboard'
import { cn } from '@/lib/utils'

export function AttentionAlert({ alerts }: { alerts: DashboardAlert[] }) {
  if (alerts.length === 0) return null

  const total = alerts.reduce((sum, a) => sum + a.count, 0)

  return (
    <div className='rounded-lg border border-l-4 border-l-red-500 bg-red-50 p-4 dark:bg-red-950/30'>
      <div className='flex items-center gap-2'>
        <AlertTriangle className='size-4 text-red-600 dark:text-red-400' />
        <p className='text-sm font-semibold text-red-800 dark:text-red-300'>
          {total} item{total !== 1 ? 's' : ''} need attention
        </p>
      </div>
      <ul className='mt-2 space-y-1'>
        {alerts.map((alert) => (
          <li key={alert.type}>
            <Link
              to={alert.action_url}
              className={cn(
                'group flex items-center gap-1.5 text-sm',
                'text-red-700 hover:underline dark:text-red-300',
              )}
            >
              <span className='text-red-400'>·</span>
              {alert.message}
              <ChevronRight className='size-3.5 opacity-0 transition-opacity group-hover:opacity-100' />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
