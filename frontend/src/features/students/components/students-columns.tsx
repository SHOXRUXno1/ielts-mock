import type { ColumnDef } from '@tanstack/react-table'
import { Link } from '@tanstack/react-router'
import {
  Eye,
  MoreHorizontal,
  Pencil,
  RefreshCw,
  Trash2,
  UserCheck,
} from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { updateStudent } from '@/lib/api/students'
import { apiErrorMessage } from '@/lib/api/error'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { Student } from '../data/schema'
import { useStudents } from './students-provider'

// eslint-disable-next-line react-refresh/only-export-components
function RowActions({ student }: { student: Student }) {
  const { setOpen, setCurrentRow } = useStudents()
  const qc = useQueryClient()

  const act = (action: Parameters<typeof setOpen>[0]) => {
    setCurrentRow(student)
    setOpen(action)
  }

  const activateMutation = useMutation({
    mutationFn: () => updateStudent(student.id, { is_active: true }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['students'] })
      void qc.invalidateQueries({ queryKey: ['student-results'] })
      toast.success('Student activated', {
        description: 'They can sign in again.',
      })
    },
    onError: (err) =>
      toast.error(apiErrorMessage(err, 'Could not activate this student.')),
  })

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant='ghost' size='icon' className='h-8 w-8'>
          <MoreHorizontal size={16} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align='end'>
        <DropdownMenuLabel>Actions</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link
            to='/students/$studentId'
            params={{ studentId: student.id }}
          >
            <Eye size={14} className='mr-2' /> View profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => act('edit')}>
          <Pencil size={14} className='mr-2' /> Edit
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => act('reset-password')}>
          <RefreshCw size={14} className='mr-2' /> Reset Password
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {student.is_active ? (
          <DropdownMenuItem onClick={() => act('delete')} className='text-destructive'>
            <Trash2 size={14} className='mr-2' /> Deactivate
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem
            onClick={() => activateMutation.mutate()}
            disabled={activateMutation.isPending}
            className='text-green-600'
          >
            <UserCheck size={14} className='mr-2' /> Activate
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function useStudentsColumns(): ColumnDef<Student>[] {
  return [
    {
      accessorKey: 'full_name',
      header: 'Name',
      cell: ({ row }) => (
        <div>
          <div className='font-medium text-foreground group-hover:text-primary'>
            {row.original.full_name}
          </div>
          <div className='text-xs text-muted-foreground'>{row.original.phone ?? ''}</div>
        </div>
      ),
    },
    {
      accessorKey: 'login',
      header: 'Login',
      cell: ({ row }) => (
        <code className='rounded bg-muted px-1.5 py-0.5 text-xs whitespace-nowrap'>
          {row.original.login}
        </code>
      ),
    },
    {
      accessorKey: 'group_name',
      header: 'Group',
      cell: ({ row }) => row.original.group_name ?? <span className='text-muted-foreground'>—</span>,
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) =>
        row.original.is_active ? (
          <Badge variant='outline' className='text-green-600 border-green-300'>Active</Badge>
        ) : (
          <Badge variant='outline' className='text-muted-foreground'>Inactive</Badge>
        ),
    },
    {
      id: 'actions',
      cell: ({ row }) => <RowActions student={row.original} />,
    },
  ]
}
