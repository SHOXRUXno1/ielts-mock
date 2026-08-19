import { Link } from '@tanstack/react-router'
import { Award, BookOpen, ChevronRight } from 'lucide-react'
import { Panel, SectionLabel } from '@/components/report'
import { ENTER } from '@/features/results/lib/motion'
import { cn } from '@/lib/utils'

const LINKS = [
  {
    to: '/student/results' as const,
    title: 'View results',
    description: 'See all your test scores',
    icon: Award,
    surface: 'bg-skill-writing-soft',
    accent: 'text-skill-writing',
  },
  {
    to: '/student/tests' as const,
    title: 'Browse tests',
    description: 'Start a new practice session',
    icon: BookOpen,
    surface: 'bg-skill-reading-soft',
    accent: 'text-skill-reading',
  },
]

export function QuickLinks() {
  return (
    <div className={ENTER}>
      <SectionLabel className='mb-3'>Quick links</SectionLabel>
      <Panel padding='none' className='divide-y divide-border overflow-hidden'>
        {LINKS.map(({ to, title, description, icon: Icon, surface, accent }) => (
          <Link
            key={to}
            to={to}
            className={cn(
              'flex w-full items-center gap-3 px-5 py-4 text-left transition-colors',
              'hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
            )}
          >
            <div
              className={cn(
                'flex size-9 items-center justify-center rounded-lg',
                surface,
              )}
            >
              <Icon className={cn('size-4', accent)} />
            </div>
            <div className='min-w-0 flex-1'>
              <p className='text-sm font-medium text-foreground'>{title}</p>
              <p className='text-xs text-muted-foreground'>{description}</p>
            </div>
            <ChevronRight className='size-4 text-muted-foreground' />
          </Link>
        ))}
      </Panel>
    </div>
  )
}
