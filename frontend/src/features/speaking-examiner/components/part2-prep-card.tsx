import { useEffect, useRef, useState } from 'react'
import { CueCardContent } from './cue-card-content'

const PREP_SECONDS = 60
const WARNING_AT = 10

type Part2PrepCardProps = {
  cueCardText: string
  onWarning: () => void
  onComplete: () => void
}

export function Part2PrepCard({
  cueCardText,
  onWarning,
  onComplete,
}: Part2PrepCardProps) {
  const [secondsLeft, setSecondsLeft] = useState(PREP_SECONDS)
  const [countdownAnnouncement, setCountdownAnnouncement] = useState('')
  const warnedRef = useRef(false)
  const onWarningRef = useRef(onWarning)
  const onCompleteRef = useRef(onComplete)

  useEffect(() => {
    onWarningRef.current = onWarning
    onCompleteRef.current = onComplete
  }, [onWarning, onComplete])

  useEffect(() => {
    warnedRef.current = false
    const completedRef = { current: false }

    const timer = window.setInterval(() => {
      setSecondsLeft((prev) => {
        const next = prev - 1
        if (next === WARNING_AT && !warnedRef.current) {
          warnedRef.current = true
          onWarningRef.current()
        }
        if (next <= 0) {
          if (!completedRef.current) {
            completedRef.current = true
            window.clearInterval(timer)
            window.setTimeout(() => onCompleteRef.current(), 0)
          }
          return 0
        }
        return next
      })
    }, 1000)

    return () => {
      completedRef.current = true
      window.clearInterval(timer)
    }
  }, [])

  const urgent = secondsLeft <= 10

  useEffect(() => {
    if (secondsLeft <= 10) {
      setCountdownAnnouncement(
        `${secondsLeft} seconds remaining in preparation time`,
      )
    } else if (secondsLeft === PREP_SECONDS || secondsLeft % 15 === 0) {
      setCountdownAnnouncement(
        `${secondsLeft} seconds of preparation time remaining`,
      )
    }
  }, [secondsLeft])

  return (
    <div className='mx-auto w-full max-w-md rounded-lg border border-border bg-card p-6 text-card-foreground shadow-lg'>
      <h2 className='text-center text-base font-semibold uppercase tracking-wide'>
        Cue Card
      </h2>

      {cueCardText.trim() ? (
        <CueCardContent text={cueCardText} className='mt-4' />
      ) : null}

      <div className='mt-6 border-t border-border pt-6'>
        <p
          className={`text-center text-lg font-medium ${
            urgent ? 'text-destructive' : 'text-muted-foreground'
          }`}
        >
          Preparation time: {secondsLeft}
        </p>
        <p
          className={`mt-2 text-center font-mono text-7xl font-bold tabular-nums ${
            urgent ? 'text-destructive' : 'text-foreground'
          }`}
          aria-live='polite'
          aria-atomic='true'
        >
          {secondsLeft}
        </p>
        <p
          className='sr-only'
          aria-live={urgent ? 'assertive' : 'polite'}
          aria-atomic='true'
        >
          {countdownAnnouncement}
        </p>
      </div>
    </div>
  )
}
