import { cn } from '@/lib/utils'

type MicLevelMeterProps = {
  levels: number[]
  className?: string
}

export function MicLevelMeter({ levels, className }: MicLevelMeterProps) {
  const average =
    levels.length > 0
      ? Math.round(levels.reduce((sum, level) => sum + level, 0) / levels.length)
      : 0

  return (
    <div
      role='meter'
      aria-label='Microphone level'
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={average}
      className={cn('flex items-end justify-center gap-1', className)}
    >
      {levels.map((level, i) => (
        <div
          key={i}
          className='w-2 rounded-sm bg-green-500 transition-all duration-75 dark:bg-green-400'
          style={{ height: `${Math.max(4, level * 0.32)}px` }}
        />
      ))}
    </div>
  )
}
