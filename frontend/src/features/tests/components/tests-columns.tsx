import { type ColumnDef } from '@tanstack/react-table'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { DataTableColumnHeader } from '@/components/data-table'
import { cn } from '@/lib/utils'
import { type SectionCounts, type Test } from '../data/schema'
import { DataTableRowActions } from './data-table-row-actions'

const RELATIVE_TIME = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
const RELATIVE_UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 60 * 60 * 24 * 365],
  ['month', 60 * 60 * 24 * 30],
  ['week', 60 * 60 * 24 * 7],
  ['day', 60 * 60 * 24],
  ['hour', 60 * 60],
  ['minute', 60],
]

function relativeTime(iso: string): string {
  const diffSec = (Date.now() - new Date(iso).getTime()) / 1000
  if (diffSec < 60) return 'just now'
  for (const [unit, sec] of RELATIVE_UNITS) {
    if (diffSec >= sec) return RELATIVE_TIME.format(-Math.round(diffSec / sec), unit)
  }
  return 'just now'
}

// Deterministic dot color per book slug — keeps books visually distinct across
// rows without a hard-coded map, so a new book/set picks up a colour on its
// own. Palette values are Tailwind class strings that work in both themes.
const BOOK_DOT_PALETTE = [
  'bg-teal-500',
  'bg-amber-500',
  'bg-violet-500',
  'bg-rose-500',
  'bg-sky-500',
  'bg-emerald-500',
  'bg-indigo-500',
  'bg-orange-500',
]

function bookDotClass(slug: string | null | undefined): string {
  if (!slug) return 'bg-muted-foreground/40'
  let hash = 0
  for (let i = 0; i < slug.length; i++) hash = (hash * 31 + slug.charCodeAt(i)) | 0
  return BOOK_DOT_PALETTE[Math.abs(hash) % BOOK_DOT_PALETTE.length]
}

function SectionsPill({ counts }: { counts: SectionCounts | null | undefined }) {
  if (!counts) {
    return <span className='text-muted-foreground text-sm'>—</span>
  }
  const parts: [string, number][] = [
    ['L', counts.listening],
    ['R', counts.reading],
    ['W', counts.writing],
    ['S', counts.speaking],
  ]
  return (
    <div className='flex items-center gap-1.5 font-mono text-xs tabular-nums'>
      {parts.map(([label, n]) => (
        <span
          key={label}
          className={cn(
            'inline-flex items-center gap-1 rounded-md px-1.5 py-0.5',
            n > 0
              ? 'bg-muted text-foreground'
              : 'bg-transparent text-muted-foreground/50',
          )}
          title={`${label === 'L' ? 'Listening' : label === 'R' ? 'Reading' : label === 'W' ? 'Writing' : 'Speaking'}: ${n}`}
        >
          <span className='font-semibold'>{label}</span>
          {n}
        </span>
      ))}
    </div>
  )
}

export const testsColumns: ColumnDef<Test>[] = [
  {
    accessorKey: 'title',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Test' />
    ),
    cell: ({ row }) => {
      const test = row.original
      const subtitle = [test.book_name, `Test ${test.test_number}`]
        .filter(Boolean)
        .join(' · ')
      return (
        <div className='min-w-0'>
          <div className='font-medium truncate'>{test.title}</div>
          {subtitle && (
            <div className='mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground'>
              <span
                className={cn('h-1.5 w-1.5 rounded-full shrink-0', bookDotClass(test.book_slug))}
                aria-hidden
              />
              <span className='truncate'>{subtitle}</span>
            </div>
          )}
        </div>
      )
    },
    meta: { className: 'min-w-56' },
    enableHiding: false,
  },
  {
    id: 'sections',
    header: 'Sections',
    cell: ({ row }) => <SectionsPill counts={row.original.section_counts} />,
    enableSorting: false,
    meta: { className: 'w-56' },
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => {
      const t = row.getValue<string>('type')
      const label = t.charAt(0).toUpperCase() + t.slice(1)
      return (
        <Badge
          variant={t === 'academic' ? 'default' : 'secondary'}
          className='text-xs font-medium'
        >
          {label}
        </Badge>
      )
    },
    meta: { className: 'w-28' },
  },
  {
    accessorKey: 'is_published',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Status' />
    ),
    cell: ({ row }) => {
      const published = row.getValue<boolean>('is_published')
      return (
        <div className='flex items-center gap-2'>
          <span
            className={cn(
              'h-2 w-2 rounded-full',
              published ? 'bg-emerald-500' : 'bg-muted-foreground/40',
            )}
            aria-hidden
          />
          <span
            className={cn(
              'text-sm',
              published ? 'font-medium text-foreground' : 'text-muted-foreground',
            )}
          >
            {published ? 'Published' : 'Draft'}
          </span>
        </div>
      )
    },
    meta: { className: 'w-28' },
  },
  {
    accessorKey: 'created_at',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Created' />
    ),
    cell: ({ row }) => {
      const value = row.getValue<string>('created_at')
      const absolute = new Date(value).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            <span className='text-muted-foreground text-nowrap text-sm cursor-help'>
              {relativeTime(value)}
            </span>
          </TooltipTrigger>
          <TooltipContent>{absolute}</TooltipContent>
        </Tooltip>
      )
    },
    meta: { className: 'w-32' },
  },
  {
    id: 'actions',
    cell: DataTableRowActions,
    meta: { className: 'w-12' },
  },
]
