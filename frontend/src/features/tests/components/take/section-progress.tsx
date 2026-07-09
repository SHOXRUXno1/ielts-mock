import { BookOpen, CheckCircle2, Circle, Headphones, Mic, PenLine } from 'lucide-react'
import type { SectionType } from '../../data/schema'

const TYPE_META: Record<SectionType, { label: string; icon: typeof Headphones }> = {
  listening: { label: 'Listening', icon: Headphones },
  reading:   { label: 'Reading',   icon: BookOpen },
  writing:   { label: 'Writing',   icon: PenLine },
  speaking:  { label: 'Speaking',  icon: Mic },
}

type Props = {
  presentTypes: SectionType[]
  currentType: SectionType
  completedTypes?: Set<SectionType>
  onSwitchType?: (type: SectionType) => void
}

export function SectionProgress({ presentTypes, currentType, completedTypes = new Set(), onSwitchType }: Props) {
  return (
    <div className='flex items-center justify-center gap-0 border-b border-slate-200 bg-white px-6 py-2'>
      {presentTypes.map((type, i) => {
        const { label, icon: Icon } = TYPE_META[type]
        const isCompleted = completedTypes.has(type)
        const isCurrent = type === currentType
        const isFuture = !isCompleted && !isCurrent
        const clickable = !!onSwitchType && !isCurrent

        return (
          <div key={type} className='flex items-center'>
            {i > 0 && (
              <div
                className={`mx-2 h-px w-8 ${isCompleted ? 'bg-emerald-400' : 'bg-slate-200'}`}
              />
            )}
            <button
              type='button'
              disabled={!clickable}
              onClick={() => onSwitchType?.(type)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                isCompleted
                  ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 cursor-pointer'
                  : isCurrent
                    ? 'bg-slate-900 text-white cursor-default'
                    : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600 cursor-pointer'
              }`}
            >
              {isCompleted ? (
                <CheckCircle2 className='size-3.5' />
              ) : (
                <Icon className={`size-3.5 ${isFuture ? 'opacity-40' : ''}`} />
              )}
              <span className={isFuture ? 'opacity-40' : ''}>{label}</span>
              {isCompleted && <span className='text-emerald-500'>✓</span>}
              {isCurrent && <Circle className='size-2 fill-white opacity-80' />}
            </button>
          </div>
        )
      })}
    </div>
  )
}
