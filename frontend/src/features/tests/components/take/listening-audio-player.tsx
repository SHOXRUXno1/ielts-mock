import { Pause, Play, Volume2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Section } from '../../data/schema'
import { useListeningAudio } from '../../take/listening-audio-context'

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
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
    : displayDuration > 0
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
      className='rounded-lg border-[0.5px] border-slate-200 bg-slate-50 p-4'
      aria-label={`Part ${partNumber} audio`}
    >
      <div className='flex items-center gap-4'>
        <button
          type='button'
          onClick={() => audio.togglePlay(section.id)}
          disabled={!canToggle}
          title={title}
          className={cn(
            'flex size-10 shrink-0 items-center justify-center rounded-full transition-colors',
            isCompleted || !canToggle
              ? 'cursor-not-allowed bg-slate-200 text-slate-400'
              : 'bg-blue-600 text-white hover:bg-blue-700',
          )}
        >
          {audio.isPlaying && isViewedPlaying ? (
            <Pause className='size-4' />
          ) : (
            <Play className='size-4 translate-x-0.5' />
          )}
        </button>

        <div className='flex flex-1 flex-col gap-1.5'>
          <div className='relative h-1 w-full overflow-hidden rounded-full bg-slate-200'>
            <div
              className='h-full rounded-full bg-blue-600 transition-all'
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className='flex justify-between text-[13px] tabular-nums text-slate-500'>
            <span>{formatTime(displayTime)}</span>
            <span>{displayDuration > 0 ? formatTime(displayDuration) : '--:--'}</span>
          </div>
        </div>

        <div className='flex items-center gap-1.5'>
          <Volume2 className='size-4 shrink-0 text-slate-400' />
          <input
            type='range'
            min={0}
            max={1}
            step={0.05}
            value={audio.volume}
            onChange={(e) => audio.setVolume(Number(e.target.value))}
            className='w-16 accent-blue-600'
          />
        </div>
      </div>

      {audio.blocked && (
        <button
          type='button'
          onClick={() => audio.resume()}
          className='mt-3 w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700'
        >
          Resume audio
        </button>
      )}

      {isCompleted && (
        <p className='mt-3 text-xs text-amber-600'>
          Audio has been played. You cannot replay it in a real exam.
        </p>
      )}

      {!isCompleted && isOtherPlaying && audio.playingPartNumber != null && (
        <p className='mt-3 text-xs text-slate-500'>
          Now playing: Part {audio.playingPartNumber}
        </p>
      )}

      {!isCompleted &&
        !isViewedPlaying &&
        !isOtherPlaying &&
        !audio.blocked && (
          <p className='mt-3 text-xs text-slate-500'>
            Audio for this part will start automatically.
          </p>
        )}
    </div>
  )
}
