import { type ColumnDef } from '@tanstack/react-table'
import { Link } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { DataTableColumnHeader } from '@/components/data-table'
import { LongText } from '@/components/long-text'
import { type Test } from '../data/schema'
import { DataTableRowActions } from './data-table-row-actions'

export const testsColumns: ColumnDef<Test>[] = [
  {
    accessorKey: 'title',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Title' />
    ),
    cell: ({ row }) => (
      <Link
        to='/tests/$testId'
        params={{ testId: row.original.id }}
        className='font-medium hover:underline'
      >
        <LongText className='max-w-60'>{row.getValue('title')}</LongText>
      </Link>
    ),
    meta: { className: 'min-w-48' },
    enableHiding: false,
  },
  {
    accessorKey: 'description',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Description' />
    ),
    cell: ({ row }) => {
      const description = row.getValue<string | null>('description')
      return (
        <LongText className='max-w-96 text-muted-foreground'>
          {description ?? '—'}
        </LongText>
      )
    },
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
