import { Link } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatBand } from '@/features/results/lib/band'
import { ENTER } from '@/features/results/lib/motion'
import { cn } from '@/lib/utils'

export type AttemptRowItem = {
  id: string
  title: string
  subtitle: string
  band: number | null
  fallback?: string
}

type AttemptListProps = {
  title: string
  icon?: ReactNode
  rows: AttemptRowItem[]
  viewAllTo?: '/student/results' | '/student/tests'
  viewAllLabel?: string
}

export function AttemptList({
  title,
  icon,
  rows,
  viewAllTo,
  viewAllLabel = 'View all',
}: AttemptListProps) {
  if (rows.length === 0) return null

  return (
    <div className={ENTER}>
      <div className='mb-3 flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          {icon}
          <h3 className='text-sm font-medium text-muted-foreground'>{title}</h3>
        </div>
        {viewAllTo && (
          <Button
            asChild
            variant='ghost'
            size='sm'
            className='h-7 text-xs text-muted-foreground hover:text-foreground'
          >
            <Link to={viewAllTo}>
              {viewAllLabel}
              <ChevronRight className='ml-0.5 size-3.5' />
            </Link>
          </Button>
        )}
      </div>
      <div className='space-y-2'>
        {rows.map((row) => (
          <AttemptRow key={row.id} row={row} />
        ))}
      </div>
    </div>
  )
}

function AttemptRow({ row }: { row: AttemptRowItem }) {
  return (
    <Link
      to='/student/results/$attemptId'
      params={{ attemptId: row.id }}
      className={cn(
        'group flex items-center justify-between rounded-xl border border-border/60 bg-card px-4 py-3.5 shadow-sm transition-colors',
        'hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
      )}
    >
      <div className='min-w-0'>
        <p className='truncate text-sm font-medium text-foreground'>{row.title}</p>
        <p className='mt-0.5 text-xs text-muted-foreground'>{row.subtitle}</p>
      </div>
      <div className='flex items-center gap-2'>
        {row.band != null ? (
          <span className='rounded-lg bg-muted px-2.5 py-1 font-manrope text-xs font-semibold tabular-nums text-foreground'>
            Band {formatBand(row.band)}
          </span>
        ) : row.fallback ? (
          <Badge variant='secondary' className='text-xs'>
            {row.fallback}
          </Badge>
        ) : null}
        <ChevronRight className='size-4 text-muted-foreground/50 transition-colors group-hover:text-foreground' />
      </div>
    </Link>
  )
}
