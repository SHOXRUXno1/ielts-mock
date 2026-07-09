import { useEffect } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { createTest, updateTest } from '@/lib/api/tests'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { type Test } from '../data/schema'

const formSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required.')
    .max(255, 'Title must be 255 characters or less.'),
  description: z.string().optional(),
  is_published: z.boolean(),
})

type TestForm = z.infer<typeof formSchema>

type TestsActionDialogProps = {
  currentRow?: Test | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TestsActionDialog({
  currentRow,
  open,
  onOpenChange,
}: TestsActionDialogProps) {
  const queryClient = useQueryClient()
  const isEdit = !!currentRow

  const form = useForm<TestForm>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: '',
      description: '',
      is_published: false,
    },
  })

  // Sync form when opening / switching rows
  useEffect(() => {
    if (open) {
      form.reset({
        title: currentRow?.title ?? '',
        description: currentRow?.description ?? '',
        is_published: currentRow?.is_published ?? false,
      })
    }
  }, [open, currentRow, form])

  const mutation = useMutation({
    mutationFn: async (values: TestForm) => {
      const payload = {
        title: values.title,
        description: values.description?.trim() || null,
        is_published: values.is_published,
      }
      return isEdit && currentRow
        ? updateTest(currentRow.id, payload)
        : createTest(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      toast.success(isEdit ? 'Test updated' : 'Test created')
      onOpenChange(false)
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='sm:max-w-lg'>
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit test' : 'New test'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update the test details below.'
              : 'Create a new IELTS mock test.'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            id='test-form'
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
            className='grid gap-4'
          >
            <FormField
              control={form.control}
              name='title'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input placeholder='IELTS Mock Test #1' {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name='description'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder='Optional description for admins.'
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name='is_published'
              render={({ field }) => (
                <FormItem className='flex flex-row items-center justify-between rounded-md border p-3'>
                  <div className='space-y-0.5'>
                    <FormLabel>Published</FormLabel>
                    <FormDescription>
                      Students can see this test only when published.
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </form>
        </Form>

        <DialogFooter>
          <Button
            type='button'
            variant='outline'
            onClick={() => onOpenChange(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button type='submit' form='test-form' disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className='animate-spin' />}
            {isEdit ? 'Save' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
