import { memo } from 'react'
import type { ReactNode } from 'react'
import { ActionDock } from './action-dock'
import { useMicLevel } from '../hooks/use-mic-level'
import type { Phase } from '../types/phase'

type RecordingActionDockProps = {
  phase: Phase
  recordingStream: MediaStream | null
  recordingTime: number
  maxRecordingSeconds: number
  recordingProgress: number
  onStartRecording: () => void
  onStopRecording: () => void
  endTestButton: ReactNode
}

export const RecordingActionDock = memo(function RecordingActionDock({
  phase,
  recordingStream,
  recordingTime,
  maxRecordingSeconds,
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
      maxRecordingSeconds={maxRecordingSeconds}
      recordingProgress={recordingProgress}
      micLevels={micLevels}
      onStartRecording={onStartRecording}
      onStopRecording={onStopRecording}
      endTestButton={endTestButton}
    />
  )
})
