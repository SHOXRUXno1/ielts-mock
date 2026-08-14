import { Clock, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SectionType } from '../../data/schema'
import {
  SectionProgress,
  type SectionTabState,
} from './section-progress'

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

type Props = {
  title: string
  isPreview: boolean
  isPractice: boolean
  presentTypes: SectionType[]
  currentType: SectionType
  sectionStates?: Partial<Record<SectionType, SectionTabState>>
  unlockableType?: SectionType | null
  onSwitchType: (type: SectionType) => void
  showAiPaced: boolean
  showCountdown: boolean
  remainingSec: number
  totalAnswered: number
  totalQuestions: number
  onFinishSection?: () => void
  finishDisabled?: boolean
  showFinishSection: boolean
  onSubmit: () => void
  isSubmitting: boolean
}

export function ExamHeader({
  title,
  isPreview,
  isPractice,
  presentTypes,
  currentType,
  sectionStates,
  unlockableType = null,
  onSwitchType,
  showAiPaced,
  showCountdown,
  remainingSec,
  totalAnswered,
  totalQuestions,
  onFinishSection,
  finishDisabled,
  showFinishSection,
  onSubmit,
  isSubmitting,
}: Props) {
  const tabs = !isPractice ? (
    <SectionProgress
      presentTypes={presentTypes}
      currentType={currentType}
      sectionStates={isPreview ? undefined : sectionStates}
      unlockableType={isPreview ? null : unlockableType}
      onSwitchType={onSwitchType}
    />
  ) : null

  return (
    <>
      <header className='grid h-14 shrink-0 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2 border-b border-slate-200 bg-white px-3 sm:px-5'>
        <div className='flex min-w-0 items-center gap-3'>
          <span className='min-w-0 max-w-[22ch] truncate text-sm font-medium text-slate-900 lg:max-w-[28ch] xl:max-w-none'>
            {title}
          </span>
          {!isPractice && (
            <>
              <div className='hidden h-5 w-px shrink-0 bg-slate-200 lg:block' />
              <SectionProgress
                variant='inline'
                className='hidden min-w-0 lg:flex'
                presentTypes={presentTypes}
                currentType={currentType}
                sectionStates={isPreview ? undefined : sectionStates}
                unlockableType={isPreview ? null : unlockableType}
                onSwitchType={onSwitchType}
              />
            </>
          )}
        </div>

        <div className='flex items-center gap-2 sm:gap-3'>
          {showAiPaced && (
            <span className='rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-medium text-slate-600'>
              AI-paced
            </span>
          )}
          {showCountdown && (
            <span
              className={cn(
                'inline-flex items-center gap-1.5 tabular-nums text-[13px]',
                remainingSec < 60
                  ? 'animate-pulse font-semibold text-red-600'
                  : remainingSec <= 300
                    ? 'font-medium text-amber-600'
                    : 'font-medium text-slate-800',
              )}
            >
              <Clock className='size-3.5 stroke-[1.75]' aria-hidden />
              <span>{formatTime(remainingSec)}</span>
            </span>
          )}
        </div>

        <div className='flex items-center justify-end gap-2 sm:gap-3'>
          <span className='hidden tabular-nums text-[13px] text-slate-500 sm:inline'>
            <span className='font-medium text-slate-700'>
              {totalAnswered}/{totalQuestions}
            </span>{' '}
            answered
          </span>
          {showFinishSection && (
            <button
              type='button'
              onClick={onFinishSection}
              disabled={finishDisabled}
              className='hidden h-9 items-center rounded-lg border border-slate-200 bg-white px-3 text-[13px] font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60 sm:inline-flex'
            >
              Finish section
            </button>
          )}
          <button
            type='button'
            onClick={onSubmit}
            disabled={!isPreview && isSubmitting}
            className={cn(
              'inline-flex h-9 items-center gap-1.5 rounded-lg px-4 text-[13px] font-medium text-white transition-colors disabled:opacity-60',
              isPreview
                ? 'bg-orange-600 hover:bg-orange-700'
                : 'bg-blue-600 hover:bg-blue-700',
            )}
          >
            {!isPreview && isSubmitting && (
              <Loader2 className='size-3.5 animate-spin' />
            )}
            {isPreview
              ? 'Close Preview'
              : isPractice
                ? 'Finish practice'
                : 'Submit'}
          </button>
        </div>
      </header>
      {tabs && (
        <div className='lg:hidden'>
          {tabs}
        </div>
      )}
    </>
  )
}
