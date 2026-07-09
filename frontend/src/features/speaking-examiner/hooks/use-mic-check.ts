import { useCallback, useState } from 'react'
import { toast } from 'sonner'

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
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true },
        })
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
