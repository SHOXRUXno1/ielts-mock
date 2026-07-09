import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AlertTriangle } from 'lucide-react'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type { Test } from '../data/schema'

const schema = z.object({
  title: z.string().min(1, 'Title is required').max(255),
  book_name: z.string().optional(),
  test_number: z.number().int().min(1, 'Must be at least 1'),
  type: z.string().min(1),
  description: z.string().optional(),
})

export type StepInfoValues = z.infer<typeof schema>

type Props = {
  test: Test | null
  onFormReady: (getValues: () => StepInfoValues, isValid: () => Promise<boolean>) => void
}

export function StepInfo({ test, onFormReady }: Props) {
  const form = useForm<StepInfoValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: test?.title ?? '',
      book_name: test?.book_name ?? '',
      test_number: test?.test_number ?? 1,
      type: test?.type ?? 'academic',
      description: test?.description ?? '',
    },
  })

  useEffect(() => {
    onFormReady(
      () => form.getValues(),
      () => form.trigger(),
    )
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const isLegacyGeneral = test?.type === 'general'

  return (
    <Form {...form}>
      <div className='space-y-5'>
        {isLegacyGeneral && (
          <div className='flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800'>
            <AlertTriangle className='mt-0.5 size-4 shrink-0' />
            <span>
              This test is saved as <strong>General Training</strong>, which is temporarily
              unavailable. The test is preserved but new General Training tests cannot be created.
            </span>
          </div>
        )}

        <FormField
          control={form.control}
          name='title'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Test Name</FormLabel>
              <FormControl>
                <Input placeholder='Cambridge IELTS 7 Test 1' {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='book_name'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Book Name</FormLabel>
              <FormControl>
                <Input placeholder='Cambridge IELTS 7' {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='test_number'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Test Number</FormLabel>
              <FormControl>
                <Input
                  type='number'
                  min={1}
                  placeholder='1'
                  value={field.value}
                  onChange={(e) => field.onChange(parseInt(e.target.value, 10) || 1)}
                  onBlur={field.onBlur}
                  name={field.name}
                  ref={field.ref}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Type is fixed to Academic. Show read-only badge; keep hidden field. */}
        <FormField
          control={form.control}
          name='type'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Type</FormLabel>
              <div className='flex items-center gap-2'>
                <span className='inline-flex items-center rounded-md bg-blue-50 px-2.5 py-1 text-sm font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10'>
                  Academic
                </span>
                <span className='text-xs text-slate-400'>
                  General Training is temporarily unavailable.
                </span>
              </div>
              {/* Keep the hidden input so form value stays "academic" */}
              <input type='hidden' {...field} value='academic' />
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name='description'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description (optional)</FormLabel>
              <FormControl>
                <Textarea
                  rows={3}
                  placeholder='Full IELTS Academic test with all 4 sections.'
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    </Form>
  )
}
