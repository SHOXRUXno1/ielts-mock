import { CheckCircle2, Headphones, Info, Pause, Play, Volume2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Section } from '../../data/schema'
import { useListeningAudio } from '../../take/listening-audio-context'

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function otherPartPlayingCopy(
  playingPart: number,
  viewedPart: number,
): string {
  return `Part ${playingPart} is still playing. Part ${viewedPart} starts automatically when the recording reaches it.`
}

type Props = {
  section: Section
  partNumber: number
}

export function ListeningAudioPlayer({ section, partNumber }: Props) {
  const audio = useListeningAudio()
  const isViewedPlaying = audio.playingSectionId === section.id
  const isCompleted = audio.completed.has(section.id) && !audio.allowReplay
  const isOtherPlaying =
    !!audio.playingSectionId && audio.playingSectionId !== section.id

  const displayTime = isViewedPlaying ? audio.position : 0
  const displayDuration = isViewedPlaying ? audio.duration : 0
  const progress = isCompleted
    ? 100
    : isViewedPlaying && displayDuration > 0
      ? (displayTime / displayDuration) * 100
      : 0

  const canToggle =
    !isCompleted &&
    (audio.blocked ||
      isViewedPlaying ||
      audio.allowReplay)

  const title = isCompleted
    ? 'Audio already played'
    : audio.blocked
      ? 'Resume audio'
      : audio.isPlaying && isViewedPlaying
        ? 'Pause'
        : 'Play'

  return (
    <div
      className={cn(
        'group/player rounded-xl border border-slate-200/70 bg-white p-4 shadow-sm ring-1 ring-slate-900/[0.02]',
        'sm:p-5',
      )}
      aria-label={`Part ${partNumber} audio`}
    >
      <div className='mb-3 flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          <div className='flex size-7 items-center justify-center rounded-md bg-blue-50 text-blue-600'>
            <Headphones className='size-3.5' />
          </div>
          <div className='flex flex-col'>
            <span className='text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500'>
              Part {partNumber}
            </span>
            <span className='text-[13px] font-medium text-slate-900'>
              Listening audio
            </span>
          </div>
        </div>

        {isCompleted ? (
          <span className='inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700'>
            <CheckCircle2 className='size-3' />
            Played
          </span>
        ) : isOtherPlaying && audio.playingPartNumber != null ? (
          <span className='inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700'>
            Part {audio.playingPartNumber} playing
          </span>
        ) : isViewedPlaying && audio.isPlaying ? (
          <span className='inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700'>
            <span className='size-1.5 animate-pulse rounded-full bg-blue-500' />
            Playing
          </span>
        ) : null}
      </div>

      <div
        className={cn(
          'flex items-center gap-3 sm:gap-4',
          isOtherPlaying && 'opacity-60',
        )}
      >
        <button
          type='button'
          onClick={() => audio.togglePlay(section.id)}
          disabled={!canToggle}
          title={title}
          aria-label={title}
          className={cn(
            'group/btn flex size-11 shrink-0 items-center justify-center rounded-full transition-all',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
            isCompleted || !canToggle
              ? 'cursor-not-allowed bg-slate-100 text-slate-400'
              : 'bg-blue-600 text-white shadow-sm hover:bg-blue-700 hover:shadow-md active:scale-95',
          )}
        >
          {audio.isPlaying && isViewedPlaying ? (
            <Pause className='size-4' />
          ) : (
            <Play className='size-4 translate-x-0.5' />
          )}
        </button>

        <div className='flex flex-1 flex-col gap-2'>
          <div
            className='relative h-1.5 w-full overflow-hidden rounded-full bg-slate-200/80'
            role='progressbar'
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(progress)}
          >
            <div
              className={cn(
                'h-full rounded-full transition-all duration-300 ease-out',
                isCompleted ? 'bg-slate-400' : 'bg-blue-600',
              )}
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className='flex justify-between text-xs font-medium tabular-nums text-slate-600'>
            <span>{isViewedPlaying ? formatTime(displayTime) : '--:--'}</span>
            <span className='text-slate-500'>
              {isViewedPlaying && displayDuration > 0
                ? formatTime(displayDuration)
                : '--:--'}
            </span>
          </div>
        </div>

        <div className='flex items-center gap-2'>
          <Volume2 className='size-4 shrink-0 text-slate-500' />
          <input
            type='range'
            min={0}
            max={1}
            step={0.05}
            value={audio.volume}
            onChange={(e) => audio.setVolume(Number(e.target.value))}
            aria-label='Volume'
            className='h-1 w-16 accent-blue-600 sm:w-20'
          />
        </div>
      </div>

      {audio.blocked && (
        <button
          type='button'
          onClick={() => audio.resume()}
          className='mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-blue-700 hover:shadow-md active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2'
        >
          <Play className='size-4 translate-x-0.5' />
          Resume audio
        </button>
      )}

      {isCompleted && (
        <div className='mt-3 flex items-start gap-2 rounded-lg bg-amber-50/70 px-3 py-2 text-xs text-amber-800 ring-1 ring-amber-200/70'>
          <Info className='mt-0.5 size-3.5 shrink-0' />
          <span>Audio has been played. Replay is not available in a real exam.</span>
        </div>
      )}

      {!isCompleted && isOtherPlaying && audio.playingPartNumber != null && (
        <p className='mt-3 flex items-start gap-2 text-xs text-slate-600'>
          <Info className='mt-0.5 size-3.5 shrink-0 text-slate-400' />
          <span>{otherPartPlayingCopy(audio.playingPartNumber, partNumber)}</span>
        </p>
      )}

      {!isCompleted &&
        !isViewedPlaying &&
        !isOtherPlaying &&
        !audio.blocked && (
          <p className='mt-3 flex items-start gap-2 text-xs text-slate-500'>
            <Info className='mt-0.5 size-3.5 shrink-0 text-slate-400' />
            <span>Audio for this part will start automatically.</span>
          </p>
        )}
    </div>
  )
}
