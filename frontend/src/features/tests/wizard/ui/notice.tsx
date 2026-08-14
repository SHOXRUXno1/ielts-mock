import { AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

type Variant = 'info' | 'warning' | 'error'

type Props = {
  variant?: Variant
  children: React.ReactNode
  className?: string
}

const config: Record<Variant, { icon: typeof Info; container: string; text: string }> = {
  info: {
    icon: Info,
    container: 'border-border bg-muted/50',
    text: 'text-muted-foreground',
  },
  warning: {
    icon: AlertTriangle,
    container: 'border-warning/40 bg-warning/10',
    text: 'text-warning-foreground',
  },
  error: {
    icon: AlertCircle,
    container: 'border-destructive/30 bg-destructive/5',
    text: 'text-destructive',
  },
}

export function Notice({ variant = 'info', children, className }: Props) {
  const { icon: Icon, container, text } = config[variant]
  return (
    <div
      className={cn(
        'flex items-start gap-2 rounded-md border px-3 py-2 text-xs',
        container,
        text,
        className,
      )}
    >
      <Icon className='mt-0.5 size-3.5 shrink-0' />
      <div className='flex-1'>{children}</div>
    </div>
  )
}
