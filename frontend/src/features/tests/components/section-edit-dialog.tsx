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
      audio_url: '',
      passage: '',
    },
  })

  useEffect(() => {
    if (open && section) {
      form.reset({
        audio_url: section.audio_url ?? '',
        passage: section.passage ?? '',
      })
    }
  }, [open, section, form])

  const mutation = useMutation({
    mutationFn: (values: SectionForm) => {
      if (!section) throw new Error('No section')
      return updateSection(section.id, {
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
            Update the section content
            {isListening ? ' and audio URL' : ''}
            {isReading ? ' and passage text' : ''}. Timing is set per section
            type in the test editor.
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
