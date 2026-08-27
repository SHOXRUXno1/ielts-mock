import { useCallback, useEffect, useRef, type MutableRefObject } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  formatSimliUnavailable,
  getSimliFetchErrorMessage,
  getSimliToken,
  type SimliTokenResponse,
} from '@/lib/api/speaking-examiner'
import { isLiveSpeakingPhase } from '../lib/is-live-phase'
import type { Phase } from '../types/phase'

export const SIMLI_TOKEN_QUERY_KEY = ['speaking-examiner', 'simli-token'] as const

const initState = {
  bootstrapped: false,
  loadingFinished: false,
}

export function resetSpeakingInit() {
  initState.bootstrapped = false
  initState.loadingFinished = false
}

export function fetchSimliTokenQuery(
  queryClient: ReturnType<typeof useQueryClient>,
) {
  return queryClient.fetchQuery({
    queryKey: SIMLI_TOKEN_QUERY_KEY,
    queryFn: getSimliToken,
    staleTime: 0,
  })
}

type UseSpeakingInitOptions = {
  phase: Phase
  phaseRef: MutableRefObject<Phase>
  simliEnabled: boolean
  simliReady: boolean
  simliFallback: boolean
  beginLoading: () => void
  onSimliLoadingComplete: () => void
  handleSimliFallback: () => void
  setSimliToken: (token: string) => void
  setSimliFaceId: (faceId: string) => void
  setSimliIceServers: (servers: RTCIceServer[] | null) => void
  setSimliEnabled: (enabled: boolean) => void
  setPhase: (phase: Phase) => void
  simliLoadTimeoutMs: number
}

function applySimliTokenData(
  data: SimliTokenResponse,
  setters: {
    setSimliToken: (token: string) => void
    setSimliFaceId: (faceId: string) => void
    setSimliIceServers: (servers: RTCIceServer[] | null) => void
    setSimliEnabled: (enabled: boolean) => void
  },
) {
  if (data.enabled && data.session_token && data.face_id) {
    setters.setSimliToken(data.session_token)
    setters.setSimliFaceId(data.face_id)
    setters.setSimliIceServers(data.ice_servers ?? null)
    setters.setSimliEnabled(true)
    return true
  }
  setters.setSimliEnabled(false)
  return false
}

export function useSpeakingInit({
  phase,
  phaseRef,
  simliEnabled,
  simliReady,
  simliFallback,
  beginLoading,
  onSimliLoadingComplete,
  handleSimliFallback,
  setSimliToken,
  setSimliFaceId,
  setSimliIceServers,
  setSimliEnabled,
  setPhase,
  simliLoadTimeoutMs,
}: UseSpeakingInitOptions) {
  const queryClient = useQueryClient()
  const initAppliedRef = useRef(false)
  const simliReadyRef = useRef(simliReady)

  useEffect(() => {
    simliReadyRef.current = simliReady
  }, [simliReady])

  const tokenSetters = {
    setSimliToken,
    setSimliFaceId,
    setSimliIceServers,
    setSimliEnabled,
  }

  const { data, isPending, isError, error } = useQuery({
    queryKey: SIMLI_TOKEN_QUERY_KEY,
    queryFn: getSimliToken,
    staleTime: 5 * 60_000,
    retry: 1,
  })

  const restartInit = useCallback(async () => {
    resetSpeakingInit()
    initAppliedRef.current = false
    beginLoading()
    await queryClient.invalidateQueries({ queryKey: SIMLI_TOKEN_QUERY_KEY })
  }, [beginLoading, queryClient])

  useEffect(() => {
    if (!data) return
    // Never interrupt an in-flight examiner session (autostart / live turns).
    if (isLiveSpeakingPhase(phaseRef.current)) return

    if (applySimliTokenData(data, tokenSetters)) {
      if (initState.loadingFinished) {
        return
      }

      if (!initState.bootstrapped) {
        initState.bootstrapped = true
        beginLoading()
      }
      return
    }

    if (!initAppliedRef.current) {
      initAppliedRef.current = true
      if (!isLiveSpeakingPhase(phaseRef.current)) {
        setPhase('idle')
      }
      initState.loadingFinished = true
    }
  }, [
    data,
    beginLoading,
    setSimliToken,
    setSimliFaceId,
    setSimliIceServers,
    setSimliEnabled,
    setPhase,
    phaseRef,
  ])

  useEffect(() => {
    if (phase !== 'loading' || !simliEnabled || simliFallback) return

    if (simliReady) {
      let innerFrame = 0
      const outerFrame = requestAnimationFrame(() => {
        innerFrame = requestAnimationFrame(() => {
          // Bail if autostart already moved past loading while we waited for rAF.
          if (isLiveSpeakingPhase(phaseRef.current)) return
          if (
            phaseRef.current === 'loading' &&
            simliReadyRef.current &&
            !simliFallback
          ) {
            initState.loadingFinished = true
            onSimliLoadingComplete()
          }
        })
      })

      return () => {
        cancelAnimationFrame(outerFrame)
        cancelAnimationFrame(innerFrame)
      }
    }

    const timer = window.setTimeout(() => {
      if (phaseRef.current !== 'loading') return
      handleSimliFallback()
      initState.loadingFinished = true
      onSimliLoadingComplete()
    }, simliLoadTimeoutMs)

    return () => window.clearTimeout(timer)
  }, [
    phase,
    simliEnabled,
    simliReady,
    simliFallback,
    phaseRef,
    onSimliLoadingComplete,
    handleSimliFallback,
    simliLoadTimeoutMs,
  ])

  const simliBanner = (() => {
    if (isPending || phase === 'loading') return null
    if (data && !data.enabled) return formatSimliUnavailable(data)
    if (isError) return getSimliFetchErrorMessage(error)
    return null
  })()

  return {
    simliBanner,
    isTokenPending: isPending,
    restartInit,
    applySimliTokenFromResponse: (resp: SimliTokenResponse) =>
      applySimliTokenData(resp, tokenSetters),
  }
}

/** @internal test helper */
export function getSpeakingInitStateForTests() {
  return { ...initState }
}
