import { BookOpen, Check, Headphones, Lock, Mic, PenLine } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { SectionType } from '../../data/schema'
import type { SectionState } from '@/lib/api/section-progress'

const TYPE_META: Record<SectionType, { label: string; icon: typeof Headphones }> = {
  listening: { label: 'Listening', icon: Headphones },
  reading: { label: 'Reading', icon: BookOpen },
  writing: { label: 'Writing', icon: PenLine },
  speaking: { label: 'Speaking', icon: Mic },
}

export type TabVisualState = 'sealed' | 'active' | 'available' | 'locked'

function formatSealedAt(iso: string | null | undefined): string | null {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export type SectionTabState = {
  state: SectionState | string
  sealedAt?: string | null
}

function getTabVisual(
  progress: SectionTabState | undefined,
  isCurrent: boolean,
  freeNav: boolean,
  /** Only this not_started section may be clicked (sequential exam). */
  unlockable: SectionType | null,
  type: SectionType,
): TabVisualState {
  if (freeNav) return isCurrent ? 'active' : 'available'
  if (progress?.state === 'sealed') return 'sealed'
  if (isCurrent || progress?.state === 'active') return 'active'
  if (progress?.state === 'not_started' && type === unlockable) return 'available'
  return 'locked'
}

type Props = {
  presentTypes: SectionType[]
  currentType: SectionType
  /** Per-type progress state (exam mode). When omitted, falls back to free navigation. */
  sectionStates?: Partial<Record<SectionType, SectionTabState>>
  /** Only next section in order is clickable (exam mode). */
  unlockableType?: SectionType | null
  /** Legacy positional completed set (preview). */
  completedTypes?: Set<SectionType>
  onSwitchType?: (type: SectionType) => void
  /** `bar` = own row with connectors. `inline` = compact pills for the exam header. */
  variant?: 'bar' | 'inline'
  className?: string
}

export function SectionProgress({
  presentTypes,
  currentType,
  sectionStates,
  unlockableType = null,
  completedTypes = new Set(),
  onSwitchType,
  variant = 'bar',
  className,
}: Props) {
  const freeNav = !sectionStates
  const inline = variant === 'inline'

  return (
    <div
      className={cn(
        'flex items-center gap-0 bg-white',
        inline
          ? 'justify-start'
          : 'justify-center border-b border-slate-200 px-4 py-2 sm:px-6 sm:py-2.5',
        className,
      )}
    >
      {presentTypes.map((type, i) => {
        const { label, icon: Icon } = TYPE_META[type]
        const progress = sectionStates?.[type]
        const isCurrent = type === currentType
        const visual = getTabVisual(
          progress,
          isCurrent,
          freeNav,
          unlockableType,
          type,
        )
        const sealedLabel = formatSealedAt(progress?.sealedAt)
        const clickable =
          !!onSwitchType &&
          !isCurrent &&
          (visual === 'available' || (freeNav && visual !== 'sealed'))

        const button = (
          <button
            type='button'
            disabled={!clickable}
            onClick={() => onSwitchType?.(type)}
            className={cn(
              'flex items-center gap-1.5 rounded-full font-medium transition-colors',
              inline
                ? 'px-2.5 py-1 text-[12px]'
                : 'px-3 py-1.5 text-[13px]',
              visual === 'sealed' && 'cursor-not-allowed text-emerald-600',
              visual === 'active' && 'cursor-default text-blue-600',
              visual === 'available' &&
                'cursor-pointer text-slate-500 hover:bg-slate-100 hover:text-slate-700',
              visual === 'locked' && 'cursor-not-allowed text-slate-300',
            )}
          >
            {visual === 'sealed' ? (
              <Check className='size-3.5 text-emerald-500' />
            ) : visual === 'locked' ? (
              <Lock className='size-3.5 text-slate-300' />
            ) : completedTypes.has(type) && freeNav ? (
              <Check className='size-3.5 text-emerald-500' />
            ) : (
              <Icon className='size-3.5' />
            )}
            <span>{label}</span>
            {visual === 'active' && (
              <span className='size-1.5 rounded-full bg-blue-600' />
            )}
          </button>
        )

        return (
          <div key={type} className='flex items-center'>
            {i > 0 && !inline && (
              <div
                className={cn(
                  'mx-2 h-px w-6 sm:mx-3 sm:w-8',
                  visual === 'sealed' || progress?.state === 'sealed'
                    ? 'bg-emerald-400'
                    : 'bg-slate-200',
                )}
              />
            )}
            {visual === 'sealed' ? (
              <Tooltip>
                <TooltipTrigger asChild>{button}</TooltipTrigger>
                <TooltipContent>
                  {sealedLabel
                    ? `Completed at ${sealedLabel}`
                    : 'Section completed'}
                </TooltipContent>
              </Tooltip>
            ) : visual === 'locked' ? (
              <Tooltip>
                <TooltipTrigger asChild>{button}</TooltipTrigger>
                <TooltipContent>Not available yet</TooltipContent>
              </Tooltip>
            ) : (
              button
            )}
          </div>
        )
      })}
    </div>
  )
}
