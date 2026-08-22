import { useCallback, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { SectionType } from '../data/schema'
import {
  enterSection,
  getAttemptProgress,
  sealSection,
  type AttemptProgressRead,
  type SealReason,
  type SectionProgressRead,
  type SectionState,
} from '@/lib/api/section-progress'
import { skewFromServerNow } from './clock-skew'

type ProgressWithSkew = AttemptProgressRead & { skewMs: number }

function progressKey(attemptId: string) {
  return ['attempt-progress', attemptId] as const
}

async function fetchProgress(attemptId: string): Promise<ProgressWithSkew> {
  const data = await getAttemptProgress(attemptId)
  return { ...data, skewMs: skewFromServerNow(data.server_now) }
}

export function useSectionProgress(opts: {
  attemptId: string | null
  enabled: boolean
  /** When set, allSealed ignores progress rows outside the test's present skills. */
  presentTypes?: SectionType[]
}) {
  const { attemptId, enabled, presentTypes } = opts
  const qc = useQueryClient()

  const query = useQuery({
    queryKey: attemptId ? progressKey(attemptId) : ['attempt-progress', 'none'],
    queryFn: () => {
      if (!attemptId) throw new Error('No attempt')
      return fetchProgress(attemptId)
    },
    enabled: enabled && !!attemptId,
    staleTime: 5_000,
    // Re-sync ends_at / state with the server; skew recalculates each time.
    refetchInterval: enabled && !!attemptId ? 30_000 : false,
    refetchOnWindowFocus: true,
  })

  const applyProgress = useCallback(
    (data: AttemptProgressRead) => {
      if (!attemptId) return
      const withSkew: ProgressWithSkew = {
        ...data,
        skewMs: skewFromServerNow(data.server_now),
      }
      qc.setQueryData(progressKey(attemptId), withSkew)
    },
    [attemptId, qc],
  )

  const enterMutation = useMutation({
    mutationFn: (sectionType: string) => {
      if (!attemptId) throw new Error('No attempt')
      return enterSection(attemptId, sectionType)
    },
    onSuccess: async () => {
      if (!attemptId) return
      applyProgress(await getAttemptProgress(attemptId))
    },
  })

  const sealMutation = useMutation({
    mutationFn: (args: {
      sectionType: string
      answers?: Array<{
        question_id: string
        response: Record<string, unknown>
      }>
      reason?: SealReason
    }) => {
      if (!attemptId) throw new Error('No attempt')
      return sealSection(attemptId, args.sectionType, {
        answers: args.answers,
        reason: args.reason,
      })
    },
    onSuccess: (data) => {
      if (!attemptId) return
      qc.setQueryData(
        progressKey(attemptId),
        (old: ProgressWithSkew | undefined) => {
          if (!old) return old
          const sealed = data.sealed
          return {
            ...old,
            server_now: data.server_now,
            skewMs: skewFromServerNow(data.server_now),
            sections: old.sections.map((s) =>
              s.section_type === sealed.section_type ? { ...s, ...sealed } : s,
            ),
          }
        },
      )
    },
  })

  const sections = useMemo(
    () => query.data?.sections ?? [],
    [query.data?.sections],
  )

  const byType = useMemo(() => {
    const map = {} as Record<string, SectionProgressRead>
    for (const s of sections) {
      map[s.section_type] = s
    }
    return map
  }, [sections])

  const activeType = useMemo(() => {
    const active = sections.find((s) => s.state === 'active')
    return (active?.section_type as SectionType | undefined) ?? null
  }, [sections])

  const sealedTypes = useMemo(() => {
    const set = new Set<SectionType>()
    for (const s of sections) {
      if (s.state === 'sealed') set.add(s.section_type as SectionType)
    }
    return set
  }, [sections])

  const allSealed = useMemo(() => {
    if (sections.length === 0) return false
    const types =
      presentTypes && presentTypes.length > 0
        ? presentTypes
        : (sections.map((s) => s.section_type as SectionType) as SectionType[])
    return types.every((t) => byType[t]?.state === 'sealed')
  }, [sections, byType, presentTypes])

  const stateOf = useCallback(
    (type: string): SectionState | null => {
      const row = byType[type]
      return (row?.state as SectionState | undefined) ?? null
    },
    [byType],
  )

  const invalidate = useCallback(async () => {
    if (!attemptId) return
    await qc.invalidateQueries({ queryKey: progressKey(attemptId) })
  }, [attemptId, qc])

  return {
    progress: query.data
      ? {
          server_now: query.data.server_now,
          sections: query.data.sections,
        }
      : null,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    skewMs: query.data?.skewMs ?? 0,
    byType,
    activeType,
    sealedTypes,
    allSealed,
    stateOf,
    enterSection: enterMutation.mutateAsync,
    sealSection: sealMutation.mutateAsync,
    isEntering: enterMutation.isPending,
    isSealing: sealMutation.isPending,
    invalidate,
  }
}
