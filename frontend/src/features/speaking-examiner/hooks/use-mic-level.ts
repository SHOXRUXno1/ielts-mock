import { useEffect, useRef, useState } from 'react'

const ZERO_LEVELS = [0, 0, 0, 0, 0, 0, 0, 0]
const THROTTLE_MS = 100

export function useMicLevel(stream: MediaStream | null, active: boolean) {
  const [levels, setLevels] = useState<number[]>(ZERO_LEVELS)
  const rafRef = useRef<number | null>(null)
  const lastUpdateRef = useRef(0)

  useEffect(() => {
    if (!stream || !active) {
      return
    }

    const ctx = new AudioContext()
    const source = ctx.createMediaStreamSource(stream)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)
    const data = new Uint8Array(analyser.frequencyBinCount)

    const tick = () => {
      analyser.getByteFrequencyData(data)
      const now = performance.now()
      if (now - lastUpdateRef.current >= THROTTLE_MS) {
        lastUpdateRef.current = now
        const step = Math.floor(data.length / 8)
        const next = Array.from({ length: 8 }, (_, i) => {
          const slice = data.slice(i * step, (i + 1) * step)
          const avg = slice.reduce((a, b) => a + b, 0) / slice.length
          return Math.min(100, Math.round((avg / 255) * 100))
        })
        setLevels(next)
      }
      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)

    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
      source.disconnect()
      void ctx.close()
    }
  }, [stream, active])

  if (!stream || !active) {
    return ZERO_LEVELS
  }

  return levels
}
