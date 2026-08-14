import { useMemo, useState } from 'react'
import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { LogOut } from 'lucide-react'
import { toast } from 'sonner'
import type { AdminSession } from '@/lib/api/devices'
import { revokeSession } from '@/lib/api/devices'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { DataTablePagination } from '@/components/data-table'
import { cn } from '@/lib/utils'
import { formatAbsolute, formatDuration } from '../lib/format'
import { DeviceIcon } from './device-icon'

type DevicesHistoryTableProps = {
  data: AdminSession[]
  isLoading?: boolean
}

function RevokeButton({
  sessionId,
  queryClient,
}: {
  sessionId: string
  queryClient: ReturnType<typeof useQueryClient>
}) {
  const mutation = useMutation({
    mutationFn: () => revokeSession(sessionId),
    onSuccess: () => {
      toast.success('Session revoked')
      void queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
    onError: () => toast.error('Failed to revoke session'),
  })

  return (
    <Button
      variant='ghost'
      size='sm'
      className='h-7 px-2 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive'
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
    >
      <LogOut size={12} className='mr-1' />
      {mutation.isPending ? '…' : 'Sign out'}
    </Button>
  )
}

function EndReasonBadge({ reason }: { reason: string | null }) {
  if (!reason) {
    return (
      <Badge variant='outline' className='font-normal text-muted-foreground'>
        —
      </Badge>
    )
  }
  const map: Record<string, { label: string; className: string }> = {
    logout: {
      label: 'Signed out',
      className:
        'border-transparent bg-slate-500/10 text-slate-700 dark:text-slate-300',
    },
    timeout: {
      label: 'Timed out',
      className:
        'border-transparent bg-amber-500/10 text-amber-700 dark:text-amber-400',
    },
    expired: {
      label: 'Expired',
      className:
        'border-transparent bg-rose-500/10 text-rose-700 dark:text-rose-400',
    },
  }
  const style = map[reason] ?? {
    label: reason,
    className: 'font-normal',
  }
  return (
    <Badge variant='outline' className={cn('font-normal', style.className)}>
      {style.label}
    </Badge>
  )
}

export function DevicesHistoryTable({
  data,
  isLoading,
}: DevicesHistoryTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'login_at', desc: true },
  ])
  const queryClient = useQueryClient()

  const columns = useMemo<ColumnDef<AdminSession>[]>(
    () => [
      {
        id: 'device',
        header: 'Device',
        accessorFn: (row) =>
          [row.browser, row.os_name].filter(Boolean).join(' · '),
        cell: ({ row }) => {
          const s = row.original
          const title =
            [s.browser, s.os_name].filter(Boolean).join(' · ') ||
            'Unknown device'
          return (
            <div className='flex items-center gap-3'>
              <div className='flex size-9 items-center justify-center rounded-lg bg-muted text-muted-foreground'>
                <DeviceIcon deviceType={s.device_type} size={18} />
              </div>
              <div className='min-w-0'>
                <p className='truncate font-medium'>{title}</p>
                <p className='truncate text-xs text-muted-foreground capitalize'>
                  {s.device_type}
                  {s.is_current ? ' · this device' : ''}
                </p>
              </div>
            </div>
          )
        },
      },
      {
        accessorKey: 'ip_address',
        header: 'IP',
        cell: ({ row }) => (
          <span className='font-mono text-xs tabular-nums'>
            {row.original.ip_address || '—'}
          </span>
        ),
      },
      {
        accessorKey: 'login_at',
        header: 'Signed in',
        cell: ({ row }) => (
          <span className='text-sm tabular-nums'>
            {formatAbsolute(row.original.login_at)}
          </span>
        ),
      },
      {
        accessorKey: 'ended_at',
        header: 'Signed out',
        cell: ({ row }) => {
          const s = row.original
          if (s.is_online) {
            return (
              <span className='inline-flex items-center gap-1.5 text-sm text-emerald-600 dark:text-emerald-400'>
                <span className='size-1.5 rounded-full bg-emerald-500' />
                Online
              </span>
            )
          }
          return (
            <span className='text-sm tabular-nums'>
              {formatAbsolute(s.ended_at ?? s.last_seen_at)}
            </span>
          )
        },
      },
      {
        accessorKey: 'duration_seconds',
        header: 'Duration',
        cell: ({ row }) => (
          <span className='text-sm tabular-nums'>
            {formatDuration(row.original.duration_seconds)}
          </span>
        ),
      },
      {
        accessorKey: 'end_reason',
        header: 'Status',
        cell: ({ row }) =>
          row.original.is_online ? (
            <Badge
              variant='outline'
              className='border-transparent bg-emerald-500/10 font-normal text-emerald-700 dark:text-emerald-400'
            >
              Online
            </Badge>
          ) : (
            <EndReasonBadge reason={row.original.end_reason} />
          ),
      },
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => {
          const s = row.original
          if (!s.is_online || s.is_current) return null
          return <RevokeButton sessionId={s.id} queryClient={queryClient} />
        },
      },
    ],
    [queryClient]
  )

  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  })

  return (
    <div className='flex flex-1 flex-col gap-4'>
      <div className='overflow-hidden rounded-xl border bg-card'>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className='bg-muted/40'>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className='h-28 text-center text-muted-foreground'
                >
                  Loading sessions…
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  className={cn(row.original.is_current && 'bg-primary/5')}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className='h-28 text-center text-muted-foreground'
                >
                  No sessions yet. Sign in again to start tracking devices.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination table={table} className='mt-auto' />
    </div>
  )
}
