import type { ComponentProps } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const panelVariants = cva(
  'rounded-2xl border border-border/60 bg-card text-card-foreground',
  {
    variants: {
      tone: {
        default: 'shadow-sm',
        raised: 'bg-surface-raised shadow-sm',
        flat: '',
      },
      padding: {
        none: '',
        sm: 'p-5',
        md: 'p-6',
      },
    },
    defaultVariants: {
      tone: 'default',
      padding: 'md',
    },
  },
)

type PanelProps = ComponentProps<'div'> & VariantProps<typeof panelVariants>

export function Panel({ className, tone, padding, ...props }: PanelProps) {
  return (
    <div
      data-slot='panel'
      className={cn(panelVariants({ tone, padding }), className)}
      {...props}
    />
  )
}

export function PanelHeader({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot='panel-header'
      className={cn('flex flex-wrap items-start justify-between gap-4', className)}
      {...props}
    />
  )
}

export function PanelTitle({ className, ...props }: ComponentProps<'h3'>) {
  return (
    <h3
      data-slot='panel-title'
      className={cn('text-base font-semibold text-foreground', className)}
      {...props}
    />
  )
}

export function PanelToolbar({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot='panel-toolbar'
      className={cn('flex flex-wrap items-center gap-2', className)}
      {...props}
    />
  )
}

export function PanelBody({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div data-slot='panel-body' className={cn('mt-5', className)} {...props} />
  )
}
