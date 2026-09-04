import { type ReactNode, useState } from 'react'
import {
  type SortingState,
  type Table as TableInstance,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { useNavigate } from '@tanstack/react-router'
import { FileText, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { DataTablePagination } from '@/components/data-table'
import { DataTableViewOptions } from '@/components/data-table/view-options'
import { type Test } from '../data/schema'
import { testsColumns as columns } from './tests-columns'

type TestsTableProps = {
  /** Rows after filtering + search, ready to render. */
  data: Test[]
  isLoading?: boolean
  /**
   * Renders in the header row above the table (search input, pill filters,
   * chip strip, etc.). Toolbar shrinks left; view-options button sticks right.
   */
  toolbar?: ReactNode
  /** Total rows before filtering — used only for the empty-state copy so
   * "no matches" vs "no tests at all" say different things. */
  totalUnfiltered?: number
}

export function TestsTable({
  data,
  isLoading,
  toolbar,
  totalUnfiltered,
}: TestsTableProps) {
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [sorting, setSorting] = useState<SortingState>([])

  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnVisibility },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  })

  return (
    <div className='flex flex-1 flex-col gap-4'>
      {(toolbar || true) && (
        <div className='flex flex-wrap items-center gap-2'>
          <div className='flex flex-1 flex-wrap items-center gap-2'>
            {toolbar}
          </div>
          <DataTableViewOptions table={table} />
        </div>
      )}

      <div className='overflow-hidden rounded-lg border bg-card'>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow
                key={headerGroup.id}
                className='hover:bg-transparent border-b'
              >
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    colSpan={header.colSpan}
                    className={cn(
                      'bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground',
                      header.column.columnDef.meta?.className,
                    )}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>

          <TableBody>
            {isLoading ? (
              <SkeletonRows table={table} />
            ) : table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <ClickableRow key={row.id} testId={row.original.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell
                      key={cell.id}
                      className={cn(cell.column.columnDef.meta?.className)}
                    >
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </TableCell>
                  ))}
                </ClickableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className='p-0'
                >
                  <EmptyState
                    kind={
                      (totalUnfiltered ?? data.length) === 0
                        ? 'empty'
                        : 'no-matches'
                    }
                  />
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

/**
 * Click anywhere on the row navigates to the detail page — except when the
 * click starts on an interactive descendant (button, link, dropdown menu).
 * This keeps the "…" menu, sortable header, and pagination controls working.
 */
function ClickableRow({
  testId,
  children,
}: {
  testId: string
  children: ReactNode
}) {
  const navigate = useNavigate()
  return (
    <TableRow
      className='group/row cursor-pointer transition-colors hover:bg-muted/40'
      onClick={(e) => {
        const target = e.target as HTMLElement
        if (target.closest('button, a, [role="menuitem"], [role="menu"]')) {
          return
        }
        void navigate({ to: '/tests/$testId', params: { testId } })
      }}
    >
      {children}
    </TableRow>
  )
}

function SkeletonRows({ table }: { table: TableInstance<Test> }) {
  const cols = table.getAllLeafColumns().filter((c) => c.getIsVisible())
  return (
    <>
      {Array.from({ length: 6 }).map((_, rowIdx) => (
        <TableRow key={rowIdx} className='hover:bg-transparent'>
          {cols.map((col, cellIdx) => (
            <TableCell
              key={col.id}
              className={cn(col.columnDef.meta?.className)}
            >
              {cellIdx === 0 ? (
                <div className='space-y-1.5'>
                  <Skeleton className='h-4 w-52' />
                  <Skeleton className='h-3 w-32' />
                </div>
              ) : cellIdx === cols.length - 1 ? (
                <Skeleton className='h-6 w-6 rounded-md' />
              ) : (
                <Skeleton className='h-4 w-20' />
              )}
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  )
}

function EmptyState({ kind }: { kind: 'empty' | 'no-matches' }) {
  return (
    <div className='flex flex-col items-center justify-center gap-3 py-16 px-6 text-center'>
      <div className='flex h-12 w-12 items-center justify-center rounded-full bg-muted'>
        <FileText className='h-5 w-5 text-muted-foreground' aria-hidden />
      </div>
      {kind === 'empty' ? (
        <>
          <div>
            <h3 className='text-base font-semibold'>No tests yet</h3>
            <p className='mt-1 text-sm text-muted-foreground'>
              Import from an Excel template or start a new test from scratch.
            </p>
          </div>
          <Button size='sm' asChild>
            <a href='/tests/create'>
              <Plus className='h-4 w-4' />
              New Test
            </a>
          </Button>
        </>
      ) : (
        <div>
          <h3 className='text-base font-semibold'>No matches</h3>
          <p className='mt-1 text-sm text-muted-foreground'>
            Try clearing the search or switching the filters.
          </p>
        </div>
      )}
    </div>
  )
}
