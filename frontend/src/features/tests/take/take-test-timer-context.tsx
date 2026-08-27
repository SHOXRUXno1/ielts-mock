import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useSectionTimer } from './use-section-timer'

export type TakeTestTimerValue = {
  remainingMs: number | null
  remainingSec: number
  timerExpired: boolean
}

const TakeTestTimerContext = createContext<TakeTestTimerValue | null>(null)

type TakeTestTimerProviderProps = {
  endsAt: string | null | undefined
  skewMs: number
  enabled: boolean
  children: ReactNode
}

/**
 * Owns the 2Hz section countdown. Keep this below TakeTestProvider.
 *
 * Only ExamTimerChrome (a sibling of the section body) should call
 * useTakeTestTimer. A parent that wraps Speaking and also reads remainingSec
 * re-renders WebRTC on every tick.
 */
export function TakeTestTimerProvider({
  endsAt,
  skewMs,
  enabled,
  children,
}: TakeTestTimerProviderProps) {
  const timer = useSectionTimer({ endsAt, skewMs, enabled })
  const value = useMemo<TakeTestTimerValue>(
    () => ({
      remainingMs: timer.remainingMs,
      remainingSec: timer.remainingSec,
      timerExpired: timer.expired,
    }),
    [timer.remainingMs, timer.remainingSec, timer.expired],
  )

  return (
    <TakeTestTimerContext.Provider value={value}>
      {children}
    </TakeTestTimerContext.Provider>
  )
}

export function useTakeTestTimer(): TakeTestTimerValue {
  const ctx = useContext(TakeTestTimerContext)
  if (!ctx) {
    throw new Error('useTakeTestTimer must be used within TakeTestTimerProvider')
  }
  return ctx
}
