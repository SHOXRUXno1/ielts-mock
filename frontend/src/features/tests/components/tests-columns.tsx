import { type ColumnDef } from '@tanstack/react-table'
import { Link } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { DataTableColumnHeader } from '@/components/data-table'
import { type Test } from '../data/schema'
import { DataTableRowActions } from './data-table-row-actions'

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
        .join(' \u00b7 ')
      return (
        <Link
          to='/tests/$testId'
          params={{ testId: test.id }}
          className='group block'
        >
          <span className='font-medium group-hover:underline'>
            {test.title}
          </span>
          {subtitle && (
            <span className='block text-xs text-muted-foreground'>
              {subtitle}
            </span>
          )}
        </Link>
      )
    },
    meta: { className: 'min-w-48' },
    enableHiding: false,
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => {
      const t = row.getValue<string>('type')
      return (
        <Badge variant='outline' className='text-xs capitalize'>
          {t}
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
        <Badge variant={published ? 'default' : 'secondary'}>
          {published ? 'Published' : 'Draft'}
        </Badge>
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
      return (
        <span className='text-muted-foreground text-nowrap'>
          {new Date(value).toLocaleDateString()}
        </span>
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
