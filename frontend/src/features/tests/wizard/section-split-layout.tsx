import { useState } from 'react'
import { Eye, ExternalLink, Pencil } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

type Props = {
  testId: string
  sectionType?: string
  editor: React.ReactNode
  preview: React.ReactNode
}

export function SectionSplitLayout({ testId, sectionType, editor, preview }: Props) {
  const previewSection = sectionType || 'listening'
  const [modalOpen, setModalOpen] = useState(false)
  const [mobileMode, setMobileMode] = useState<'edit' | 'preview'>('edit')

  const previewLink =
    previewSection === 'speaking'
      ? ({
          to: '/tests/$testId/preview/$section' as const,
          params: { testId, section: 'speaking' },
        })
      : ({
          to: '/tests/$testId/preview/$section/$part' as const,
          params: { testId, section: previewSection, part: '1' },
        })

  return (
    <div className='space-y-3'>
      {/* Tablet / narrow: Edit | Preview toggle */}
      <div className='flex items-center justify-between gap-2 xl:hidden'>
        <div className='inline-flex rounded-md border border-border p-0.5'>
          <button
            type='button'
            onClick={() => setMobileMode('edit')}
            className={cn(
              'inline-flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium',
              mobileMode === 'edit'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted/50',
            )}
          >
            <Pencil className='size-3' />
            Edit
          </button>
          <button
            type='button'
            onClick={() => setMobileMode('preview')}
            className={cn(
              'inline-flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium',
              mobileMode === 'preview'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted/50',
            )}
          >
            <Eye className='size-3' />
            Preview
          </button>
        </div>
        <div className='flex gap-1'>
          <Button
            type='button'
            variant='ghost'
            size='sm'
            className='h-7 px-2 text-xs md:hidden'
            onClick={() => setModalOpen(true)}
          >
            <Eye className='mr-1 size-3' />
            Full preview
          </Button>
          <Button type='button' variant='ghost' size='sm' className='h-7 px-2 text-xs' asChild>
            <Link {...previewLink} target='_blank'>
              <ExternalLink className='mr-1 size-3' />
              Fullscreen
            </Link>
          </Button>
        </div>
      </div>

      <div className='flex flex-col gap-4 xl:flex-row xl:items-stretch'>
        <div
          className={cn(
            'min-w-0 flex-1 xl:w-1/2',
            mobileMode === 'preview' && 'hidden xl:block',
          )}
        >
          {editor}
        </div>

        {/* Desktop sticky preview — keeps a light surface to match student view */}
        <aside className='hidden xl:sticky xl:top-4 xl:flex xl:w-1/2 xl:max-h-[calc(100vh-8rem)] xl:shrink-0 xl:flex-col xl:overflow-hidden'>
          <div className='flex min-h-0 flex-1 flex-col rounded-lg border border-border bg-card'>
            <div className='flex shrink-0 items-center justify-between border-b border-border px-3 py-2'>
              <span className='text-xs font-semibold uppercase tracking-wide text-muted-foreground'>
                Student preview
              </span>
              <Button
                type='button'
                variant='ghost'
                size='sm'
                className='h-7 px-2 text-xs'
                asChild
              >
                <Link {...previewLink} target='_blank'>
                  <ExternalLink className='mr-1 size-3' />
                  Fullscreen
                </Link>
              </Button>
            </div>
            <div className='min-h-0 flex-1 overflow-y-auto p-4'>{preview}</div>
          </div>
        </aside>

        {/* Tablet preview pane (toggle) */}
        <div
          className={cn(
            'min-w-0 flex-1 xl:hidden',
            mobileMode === 'edit' && 'hidden',
          )}
        >
          <div className='rounded-lg border border-border bg-card p-4'>
            <p className='mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground'>
              Student preview
            </p>
            {preview}
          </div>
        </div>
      </div>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className='max-h-[90vh] max-w-2xl overflow-y-auto'>
          <DialogHeader>
            <DialogTitle>Student preview</DialogTitle>
          </DialogHeader>
          {preview}
        </DialogContent>
      </Dialog>
    </div>
  )
}
