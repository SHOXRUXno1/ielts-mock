import { memo, type ReactNode } from 'react'
import { ActionDock } from './action-dock'
import { useMicLevel } from '../hooks/use-mic-level'
import type { RecordingLimit } from '../constants/recording-limits'
import type { Phase } from '../types/phase'

type RecordingActionDockProps = {
  phase: Phase
  recordingStream: MediaStream | null
  recordingTime: number
  recordingLimit: RecordingLimit
  recordingProgress: number
  onStartRecording: () => void
  onStopRecording: () => void
  endTestButton: ReactNode
}

export const RecordingActionDock = memo(function RecordingActionDock({
  phase,
  recordingStream,
  recordingTime,
  recordingLimit,
  recordingProgress,
  onStartRecording,
  onStopRecording,
  endTestButton,
}: RecordingActionDockProps) {
  const micLevels = useMicLevel(recordingStream, phase === 'recording')

  return (
    <ActionDock
      variant='overlay'
      phase={phase}
      recordingTime={recordingTime}
      recordingLimit={recordingLimit}
      recordingProgress={recordingProgress}
      micLevels={micLevels}
      onStartRecording={onStartRecording}
      onStopRecording={onStopRecording}
      endTestButton={endTestButton}
    />
  )
})
