import { useEffect } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { updateSection } from '@/lib/api/sections'
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
import { Textarea } from '@/components/ui/textarea'
import { type Section } from '../data/schema'

const formSchema = z.object({
  duration_minutes: z
    .number()
    .int()
    .min(1, 'Must be at least 1 minute.')
    .max(180, 'Must be 180 minutes or less.'),
  audio_url: z.string().optional(),
  passage: z.string().optional(),
})

type SectionForm = z.infer<typeof formSchema>

type SectionEditDialogProps = {
  section: Section | null
  testId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SectionEditDialog({
  section,
  testId,
  open,
  onOpenChange,
}: SectionEditDialogProps) {
  const queryClient = useQueryClient()
  const isListening = section?.type === 'listening'
  const isReading = section?.type === 'reading'

  const form = useForm<SectionForm>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      duration_minutes: 30,
      audio_url: '',
      passage: '',
    },
  })

  useEffect(() => {
    if (open && section) {
      form.reset({
        duration_minutes: section.duration_minutes,
        audio_url: section.audio_url ?? '',
        passage: section.passage ?? '',
      })
    }
  }, [open, section, form])

  const mutation = useMutation({
    mutationFn: (values: SectionForm) => {
      if (!section) throw new Error('No section')
      return updateSection(section.id, {
        duration_minutes: values.duration_minutes,
        audio_url: values.audio_url?.trim() || null,
        passage: isReading ? (values.passage?.trim() || null) : undefined,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests', testId] })
      toast.success('Section updated')
      onOpenChange(false)
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='sm:max-w-lg'>
        <DialogHeader>
          <DialogTitle className='capitalize'>
            Edit {section?.type ?? 'section'}
          </DialogTitle>
          <DialogDescription>
            Update the section settings
            {isListening ? ' and audio URL' : ''}
            {isReading ? ' and passage text' : ''}.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            id='section-form'
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
            className='grid gap-4'
          >
            <FormField
              control={form.control}
              name='duration_minutes'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Duration (minutes)</FormLabel>
                  <FormControl>
                    <Input
                      type='number'
                      min={1}
                      max={180}
                      value={field.value ?? ''}
                      onChange={(e) =>
                        field.onChange(
                          e.target.value === '' ? undefined : e.target.valueAsNumber
                        )
                      }
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name='audio_url'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Audio URL</FormLabel>
                  <FormControl>
                    <Input
                      placeholder='https://...'
                      disabled={!isListening}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {isListening
                      ? 'Direct URL to the Listening audio file (mp3).'
                      : 'Only applicable for the Listening section.'}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            {isReading && (
              <FormField
                control={form.control}
                name='passage'
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Passage Text</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder='Paste the reading passage here...'
                        className='min-h-[200px]'
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      The reading passage students will see alongside the
                      questions.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
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
          <Button
            type='submit'
            form='section-form'
            disabled={mutation.isPending}
          >
            {mutation.isPending && <Loader2 className='animate-spin' />}
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
