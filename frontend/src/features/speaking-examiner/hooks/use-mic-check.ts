import { useCallback, useState } from 'react'
import { toast } from 'sonner'
import { SPEAKING_AUDIO_CONSTRAINTS } from '../lib/mic-constraints'

export type MicCheckStatus = 'idle' | 'checking' | 'ok' | 'denied'

type CheckMicrophoneOptions = {
  silent?: boolean
}

export function useMicCheck() {
  const [micStatus, setMicStatus] = useState<MicCheckStatus>('idle')

  const checkMicrophone = useCallback(
    async (options?: CheckMicrophoneOptions): Promise<boolean> => {
      setMicStatus('checking')
      try {
        const stream = await navigator.mediaDevices.getUserMedia(
          SPEAKING_AUDIO_CONSTRAINTS,
        )
        stream.getTracks().forEach((t) => t.stop())
        setMicStatus('ok')
        if (!options?.silent) {
          toast.success('Microphone is working')
        }
        return true
      } catch {
        setMicStatus('denied')
        if (!options?.silent) {
          toast.error(
            'Microphone blocked — allow access in browser settings before starting',
          )
        }
        return false
      }
    },
    [],
  )

  const resetMicCheck = useCallback(() => {
    setMicStatus('idle')
  }, [])

  return { micStatus, checkMicrophone, resetMicCheck }
}
