import { cn } from '@/lib/utils'
import { getPartSubtitle, getQuestionsTotalForPart } from '../data/questions'

type Props = {
  currentPart: number
  questionNumber: number
  compact?: boolean
}

export function PartIndicator({ currentPart, questionNumber, compact = false }: Props) {
  const parts = [1, 2, 3] as const

  return (
    <div className={cn('flex flex-col', compact ? 'gap-1' : 'gap-2')}>
      <div className='flex items-center gap-1.5 overflow-x-auto pb-0.5'>
        {parts.map((num) => {
          const isActive = num === currentPart
          const label = isActive ? getPartSubtitle(num) : `Part ${num}`

          return (
            <div
              key={num}
              className={cn(
                'flex shrink-0 items-center rounded-full font-medium transition-colors',
                compact ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs',
                isActive
                  ? compact
                    ? 'bg-white/90 text-black'
                    : 'bg-primary text-primary-foreground'
                  : num < currentPart
                    ? compact
                      ? 'bg-white/25 text-white'
                      : 'bg-primary/20 text-primary'
                    : compact
                      ? 'bg-white/10 text-white/60'
                      : 'bg-muted text-muted-foreground',
              )}
            >
              {label}
            </div>
          )
        })}
      </div>
      <p
        className={cn(
          compact ? 'text-[10px] text-white/70' : 'text-center text-xs text-muted-foreground',
        )}
      >
        Question {questionNumber} of {getQuestionsTotalForPart(currentPart)}
      </p>
    </div>
  )
}
