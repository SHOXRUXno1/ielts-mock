import { memo, type ReactNode } from 'react'
import { Maximize2, Minimize2, Volume2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useFullscreen } from '../hooks/use-fullscreen'
import type { Phase } from '../types/phase'
import { transcriptHistorySignature } from '../lib/transcript-history'
import {
  ExaminerLoadingOverlay,
  type ExaminerLoadingStage,
} from './examiner-loading-screen'
import { LiveTranscriptPanel } from './live-transcript-panel'
import { PartIndicator } from './part-indicator'
import { SimliAvatar } from './simli-avatar'
import { UserCameraPreview } from './user-camera-preview'

const PIP_BASE =
  'pointer-events-none absolute right-3 z-20 aspect-[4/3] w-[26%] min-w-[128px] max-w-[240px]'

type VideoStageProps = {
  phase: Phase
  statusLabel: string
  showSimli: boolean
  showUserCamera: boolean
  isRecording: boolean
  showStatus: boolean
  isLoading: boolean
  loadingStage?: ExaminerLoadingStage
  loadingAction?: ReactNode
  simliReady?: boolean
  simliMountKey: number
  simliToken: string
  simliFaceId: string
  simliIceServers: RTCIceServer[] | null | undefined
  pendingAudioB64: string | null
  onSimliDone: () => void
  onSimliReady: (ready: boolean) => void
  onSimliFallback: () => void
  onSimliConnectionLost?: () => void
  controlsOverlay?: ReactNode
  centerOverlay?: ReactNode
  expanded?: boolean
  currentPart?: number
  questionNumber?: number
  showPartIndicator?: boolean
  transcriptHistory?: { role: 'examiner' | 'candidate'; text: string }[]
  showLiveTranscript?: boolean
}

export function VideoStageInner({
  phase,
  statusLabel,
  showSimli,
  showUserCamera,
  isRecording,
  showStatus,
  isLoading,
  loadingStage,
  loadingAction,
  simliReady = false,
  simliMountKey,
  simliToken,
  simliFaceId,
  simliIceServers,
  pendingAudioB64,
  onSimliDone,
  onSimliReady,
  onSimliFallback,
  onSimliConnectionLost,
  controlsOverlay,
  centerOverlay,
  expanded = false,
  currentPart = 1,
  questionNumber = 1,
  showPartIndicator = false,
  transcriptHistory = [],
  showLiveTranscript = false,
}: VideoStageProps) {
  const { ref: frameRef, isFullscreen, toggle: toggleFullscreen } = useFullscreen()

  if (!showSimli && !showUserCamera) return null

  const hasControls = Boolean(controlsOverlay)

  return (
    <div className={cn('flex w-full flex-col', expanded ? 'min-h-0 w-full' : 'gap-2')}>
      <div
        ref={frameRef}
        className={cn(
          'relative w-full overflow-hidden border [contain:layout_style]',
          showSimli ? 'bg-black' : 'bg-muted',
          isFullscreen
            ? 'h-full w-full rounded-none'
            : cn(
                'rounded-xl',
                expanded
                  ? 'aspect-video max-h-[min(78vh,720px)]'
                  : 'aspect-video max-h-[min(62vh,680px)]',
              ),
        )}
      >
        {showSimli && (
          <SimliAvatar
            key={simliMountKey}
            sessionToken={simliToken}
            faceId={simliFaceId}
            iceServers={simliIceServers}
            audioBase64={pendingAudioB64}
            isSpeaking={phase === 'playing'}
            isListening={phase === 'recording'}
            onSpeakingDone={onSimliDone}
            onReady={onSimliReady}
            onFallback={onSimliFallback}
            onConnectionLost={onSimliConnectionLost}
            suppressConnectingUI={isLoading}
            className='h-full w-full'
          />
        )}

        {showUserCamera && (
          <UserCameraPreview
            enabled={showUserCamera}
            isRecording={isRecording}
            className={cn(
              showSimli && PIP_BASE,
              showSimli && (hasControls ? 'bottom-28 sm:bottom-24' : 'bottom-3'),
            )}
            variant={showSimli ? 'pip' : 'standalone'}
          />
        )}

        <button
          type='button'
          aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          className='absolute right-3 top-3 z-40 rounded-md bg-black/50 p-2 text-white backdrop-blur-sm hover:bg-black/70'
          onClick={() => {
            void toggleFullscreen()
          }}
        >
          {isFullscreen ? (
            <Minimize2 className='size-4' />
          ) : (
            <Maximize2 className='size-4' />
          )}
        </button>

        {showStatus && (
          <div className='pointer-events-none absolute left-3 top-3 z-20 rounded-md bg-black/50 px-2.5 py-1.5 text-left backdrop-blur-sm'>
            <p className='text-xs font-semibold text-white'>James Harrison</p>
            <p
              className={cn(
                'text-[11px]',
                phase === 'playing'
                  ? 'text-blue-300'
                  : phase === 'recording'
                    ? 'text-red-300'
                    : 'text-white/70',
              )}
              aria-live='polite'
              aria-busy={
                phase === 'playing' ||
                phase === 'thinking' ||
                phase === 'transcribing' ||
                phase === 'scoring'
              }
            >
              {phase === 'playing' && (
                <Volume2 className='mr-1 inline size-3 animate-pulse' />
              )}
              {statusLabel}
            </p>
          </div>
        )}

        {showPartIndicator && (
          <div className='pointer-events-none absolute right-14 top-3 z-20 max-w-[min(220px,45%)]'>
            <PartIndicator
              currentPart={currentPart}
              questionNumber={questionNumber}
              compact
            />
          </div>
        )}

        {showLiveTranscript && transcriptHistory.length > 0 && (
          <LiveTranscriptPanel
            history={transcriptHistory}
            className={hasControls ? 'bottom-28 sm:bottom-24' : 'bottom-3'}
          />
        )}

        {centerOverlay && (
          <div className='absolute inset-0 z-[25] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm'>
            {centerOverlay}
          </div>
        )}

        {controlsOverlay && (
          <div className='absolute inset-x-0 bottom-0 z-30'>{controlsOverlay}</div>
        )}

        {isLoading && (
          <ExaminerLoadingOverlay
            stage={
              loadingStage ??
              (showSimli && !simliReady ? 'video' : 'examiner')
            }
            action={loadingAction}
          />
        )}
      </div>
    </div>
  )
}

function videoStagePropsEqual(prev: VideoStageProps, next: VideoStageProps): boolean {
  const keysToCompare: (keyof VideoStageProps)[] = [
    'phase',
    'statusLabel',
    'showSimli',
    'showUserCamera',
    'isRecording',
    'showStatus',
    'isLoading',
    'loadingStage',
    'loadingAction',
    'simliReady',
    'simliMountKey',
    'simliToken',
    'simliFaceId',
    'simliIceServers',
    'pendingAudioB64',
    'expanded',
    'currentPart',
    'questionNumber',
    'showPartIndicator',
    'showLiveTranscript',
    'controlsOverlay',
    'centerOverlay',
    'onSimliDone',
    'onSimliReady',
    'onSimliFallback',
    'onSimliConnectionLost',
  ]

  for (const key of keysToCompare) {
    if (prev[key] !== next[key]) return false
  }

  return (
    transcriptHistorySignature(prev.transcriptHistory ?? []) ===
    transcriptHistorySignature(next.transcriptHistory ?? [])
  )
}

export const VideoStage = memo(VideoStageInner, videoStagePropsEqual)

VideoStage.displayName = 'VideoStage'
