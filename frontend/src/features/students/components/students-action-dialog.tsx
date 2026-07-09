import { useEffect } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { createStudent, updateStudent } from '@/lib/api/students'
import { apiErrorMessage } from '@/lib/api/error'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { useStudents } from './students-provider'

const schema = z.object({
  full_name: z.string().min(1, 'Full name is required'),
  phone: z.string().min(1, 'Phone is required — used as login and password'),
  group_name: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function StudentsActionDialog() {
  const { open, setOpen, currentRow, setCredentials } = useStudents()
  const qc = useQueryClient()
  const isAdd = open === 'add'
  const isEdit = open === 'edit'

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: '', phone: '', group_name: '' },
  })

  useEffect(() => {
    if (isEdit && currentRow) {
      form.reset({
        full_name: currentRow.full_name,
        phone: currentRow.phone ?? '',
        group_name: currentRow.group_name ?? '',
      })
    } else if (isAdd) {
      form.reset({ full_name: '', phone: '', group_name: '' })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, currentRow])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = { full_name: values.full_name, phone: values.phone, group_name: values.group_name }
      return isAdd ? createStudent(payload) : updateStudent(currentRow!.id, payload)
    },
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: ['students'] })
      setOpen(null)
      if (isAdd && 'password' in data) {
        setCredentials({ login: data.login, password: (data as { login: string; password: string }).password })
        setOpen('show-credentials')
      } else {
        toast.success(isAdd ? 'Student created.' : 'Student updated.')
      }
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  })

  return (
    <Dialog open={isAdd || isEdit} onOpenChange={(v) => !v && setOpen(null)}>
      <DialogContent className='max-w-sm'>
        <DialogHeader>
          <DialogTitle>{isAdd ? 'Add New Student' : 'Edit Student'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((d) => mutation.mutate(d))} className='space-y-4'>
            <FormField
              control={form.control}
              name='full_name'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full Name</FormLabel>
                  <FormControl><Input placeholder='Aziz Karimov' {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name='phone'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phone (login & password)</FormLabel>
                  <FormControl><Input placeholder='+998901234567' {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name='group_name'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Group</FormLabel>
                  <FormControl><Input placeholder='IELTS-7' {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button variant='outline' type='button' onClick={() => setOpen(null)}>
                Cancel
              </Button>
              <Button type='submit' disabled={mutation.isPending}>
                {mutation.isPending ? 'Saving…' : isAdd ? 'Create Student' : 'Save Changes'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
