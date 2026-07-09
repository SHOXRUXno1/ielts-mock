import { cn } from '@/lib/utils'

type CueCardContentProps = {
  text: string
  className?: string
}

export function CueCardContent({ text, className }: CueCardContentProps) {
  const lines = text
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)

  return (
    <div className={cn('space-y-2 text-sm', className)}>
      {lines.map((line, i) => {
        const isBullet = /^[-•*]\s/.test(line)
        return (
          <p
            key={i}
            className={
              isBullet ? 'ms-2 text-muted-foreground' : 'font-medium text-foreground'
            }
          >
            {isBullet ? line.replace(/^[-•*]\s*/, '• ') : line}
          </p>
        )
      })}
    </div>
  )
}
