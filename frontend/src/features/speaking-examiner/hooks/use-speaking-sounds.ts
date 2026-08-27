import { useCallback, useRef } from 'react'

export function useSpeakingSounds() {
  const ctxRef = useRef<AudioContext | null>(null)

  const getCtx = useCallback(() => {
    if (!ctxRef.current) {
      ctxRef.current = new AudioContext()
    }
    if (ctxRef.current.state === 'suspended') {
      void ctxRef.current.resume()
    }
    return ctxRef.current
  }, [])

  const playTone = useCallback(
    (frequency: number, durationMs: number, volume = 0.15) => {
      try {
        const ctx = getCtx()
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.type = 'sine'
        osc.frequency.value = frequency
        gain.gain.value = volume
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.start()
        osc.stop(ctx.currentTime + durationMs / 1000)
      } catch {
        /* audio unavailable */
      }
    },
    [getCtx],
  )

  const playBeep = useCallback(() => playTone(880, 120), [playTone])

  const playWarningBeep = useCallback(() => playTone(660, 200, 0.2), [playTone])

  const playRecordEnd = useCallback(() => playTone(400, 150), [playTone])

  const playPartTransition = useCallback(
    (part: number) => {
      playTone(440 + part * 80, 100)
      window.setTimeout(() => playTone(540 + part * 80, 100), 150)
    },
    [playTone],
  )

  return {
    playBeep,
    playWarningBeep,
    playRecordEnd,
    playPartTransition,
  }
}
