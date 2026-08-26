import { useCallback, useMemo } from 'react'
import { useNavigate, useParams, useRouterState } from '@tanstack/react-router'
import {
  clampPart,
  isSectionType,
  partCount,
  partIndexForQuestion,
  resolvePart,
} from '../lib/part-resolver'
import type { SectionType } from '../data/schema'
import { TYPE_ORDER } from './constants'
import { useTakeTest } from './take-test-context'
import { scrollAndFlashQuestion } from './flash-question'
import { questionAnchorId, questionDisplayStart } from './question-anchor'

function parsePartParam(raw: string | undefined): number {
  if (!raw) return 1
  const n = parseInt(raw, 10)
  return Number.isFinite(n) ? n : 1
}

/**
 * URL-driven navigation for the take-test flow.
 * Position (section/part) is derived from route params — never from React state.
 */
export function useTestNavigation() {
  const ctx = useTakeTest()
  const navigate = useNavigate()
  const params = useParams({ strict: false }) as {
    bookSlug?: string
    testSlug?: string
    testId?: string
    section?: string
    part?: string
  }
  const hash = useRouterState({ select: (s) => s.location.hash })
  const search = useRouterState({
    select: (s) =>
      s.location.search as { section?: string; part?: string },
  })
  const sectionParam = params.section ?? search.section
  const partParam = params.part ?? search.part

  const isPracticePart = ctx.isPractice && ctx.practiceScope === 'part'

  const currentType: SectionType = isSectionType(sectionParam ?? '')
    ? (sectionParam as SectionType)
    : (ctx.presentTypes[0] ?? 'listening')

  const writingQs = useMemo(() => {
    const writingSec = ctx.sortedSections.find((s) => s.type === 'writing')
    return writingSec ? (ctx.sectionQuestions[writingSec.id] ?? []) : []
  }, [ctx.sortedSections, ctx.sectionQuestions])

  const rawPart = parsePartParam(partParam)
  // Single-part practice scopes sortedSections to one sibling, so clampPart
  // would collapse Part 3 → 1 and kick off an ensureValidPart ↔ flush loop.
  // Trust the URL part number. Whole-section practice uses normal clamping.
  const currentPart =
    currentType === 'speaking'
      ? 1
      : isPracticePart
        ? Math.max(1, rawPart)
        : clampPart(ctx.sortedSections, currentType, rawPart, writingQs)

  const resolved = useMemo(() => {
    if (isPracticePart) {
      const siblings = ctx.sortedSections.filter((s) => s.type === currentType)
      const section = siblings[0]
      if (!section) return null
      return {
        sectionId: section.id,
        writingTaskIdx:
          currentType === 'writing' ? Math.max(0, currentPart - 1) : null,
        partIndex: currentPart,
      }
    }
    return resolvePart(ctx.sortedSections, currentType, currentPart, writingQs)
  }, [
    isPracticePart,
    ctx.sortedSections,
    currentType,
    currentPart,
    writingQs,
  ])

  const activeSectionId = resolved?.sectionId ?? null
  const activeWritingTask = resolved?.writingTaskIdx ?? 0
  const activeListeningPart =
    currentType === 'listening' ? Math.max(0, currentPart - 1) : 0

  const currentTypeIdx = Math.max(0, ctx.presentTypes.indexOf(currentType))

  const goTo = useCallback(
    async (section: SectionType, part: number, opts?: { hash?: string; replace?: boolean }) => {
      // Single-part practice is a locked unit — never flush/navigate.
      if (isPracticePart) return

      const samePlace =
        section === currentType &&
        (section === 'speaking' || part === currentPart)
      if (samePlace && !opts?.hash) return

      await ctx.flushBeforeNavigate()

      const safePart =
        section === 'speaking'
          ? 1
          : clampPart(ctx.sortedSections, section, part, writingQs)
      const hashTarget = opts?.hash
        ? opts.hash.startsWith('#')
          ? opts.hash
          : `#${opts.hash}`
        : undefined

      if (ctx.isPreview) {
        const testId = params.testId ?? ctx.testId
        if (section === 'speaking') {
          await navigate({
            to: '/tests/$testId/preview/$section',
            params: { testId, section },
            hash: hashTarget,
            replace: opts?.replace,
          })
        } else {
          await navigate({
            to: '/tests/$testId/preview/$section/$part',
            params: { testId, section, part: String(safePart) },
            hash: hashTarget,
            replace: opts?.replace,
          })
        }
        return
      }

      // Whole-section practice: stay on /practice routes, keep attempt + scope.
      if (ctx.mode === 'practice') {
        const practiceTestId = params.testId ?? ctx.testId
        if (practiceTestId && !params.bookSlug) {
          await navigate({
            to: '/practice/$testId',
            params: { testId: practiceTestId },
            search: {
              attempt: ctx.attemptId ?? '',
              scope: 'section',
              section,
              part: String(safePart),
            },
            hash: hashTarget,
            replace: opts?.replace,
          })
          return
        }
        const bookSlug = params.bookSlug!
        const testSlug = params.testSlug!
        await navigate({
          to: '/practice/$bookSlug/$testSlug/$section/$part',
          params: {
            bookSlug,
            testSlug,
            section,
            part: String(safePart),
          },
          search: {
            attempt: ctx.attemptId ?? undefined,
            scope: 'section',
          },
          hash: hashTarget,
          replace: opts?.replace,
        })
        return
      }

      const liveTestId = params.testId ?? ctx.testId
      if (liveTestId && !params.bookSlug) {
        await navigate({
          to: '/take-test/$testId',
          params: { testId: liveTestId },
          search: {
            resume: ctx.attemptId,
            section,
            part: section === 'speaking' ? undefined : String(safePart),
          },
          hash: hashTarget,
          replace: opts?.replace,
        })
        return
      }

      const bookSlug = params.bookSlug!
      const testSlug = params.testSlug!
      const search = ctx.attemptId ? { resume: ctx.attemptId } : {}

      if (section === 'speaking') {
        await navigate({
          to: '/take-test/$bookSlug/$testSlug/$section',
          params: { bookSlug, testSlug, section: 'speaking' },
          search,
          hash: hashTarget,
          replace: opts?.replace,
        })
      } else {
        await navigate({
          to: '/take-test/$bookSlug/$testSlug/$section/$part',
          params: {
            bookSlug,
            testSlug,
            section,
            part: String(safePart),
          },
          search,
          hash: hashTarget,
          replace: opts?.replace,
        })
      }
    },
    [ctx, navigate, params, writingQs, isPracticePart, currentType, currentPart],
  )

  const goToSection = useCallback(
    (section: SectionType) => goTo(section, 1),
    [goTo],
  )

  const goToPart = useCallback(
    (part: number) => goTo(currentType, part),
    [goTo, currentType],
  )

  const goToQuestion = useCallback(
    async (
      sectionId: string,
      questionId: string,
      displayNumber?: number,
    ) => {
      const target = ctx.sortedSections.find((s) => s.id === sectionId)
      if (!target) return
      const type = target.type as SectionType
      const part =
        partIndexForQuestion(
          ctx.sortedSections,
          ctx.sectionQuestions,
          sectionId,
          questionId,
        ) ?? 1
      const qs = ctx.sectionQuestions[sectionId] ?? []
      const q = qs.find((item) => item.id === questionId)
      const n = displayNumber ?? (q ? questionDisplayStart(q) : undefined)
      const hash = n != null ? questionAnchorId(n) : undefined
      await goTo(type, part, { hash })
      if (n != null) scrollAndFlashQuestion(n)
    },
    [ctx.sortedSections, ctx.sectionQuestions, goTo],
  )

  const next = useCallback(async () => {
    if (currentType === 'speaking') return
    const count = partCount(ctx.sortedSections, currentType, writingQs)
    if (currentPart < count) {
      await goTo(currentType, currentPart + 1)
      return
    }
    const nextType = ctx.presentTypes[currentTypeIdx + 1]
    if (nextType) await goToSection(nextType)
  }, [
    currentType,
    currentPart,
    ctx.sortedSections,
    ctx.presentTypes,
    currentTypeIdx,
    writingQs,
    goTo,
    goToSection,
  ])

  const prev = useCallback(async () => {
    if (currentType === 'speaking') {
      const prevType = ctx.presentTypes[currentTypeIdx - 1]
      if (!prevType) return
      const count = partCount(ctx.sortedSections, prevType, writingQs)
      await goTo(prevType, count)
      return
    }
    if (currentPart > 1) {
      await goTo(currentType, currentPart - 1)
      return
    }
    const prevType = ctx.presentTypes[currentTypeIdx - 1]
    if (!prevType) return
    const count = partCount(ctx.sortedSections, prevType, writingQs)
    await goTo(prevType, Math.max(1, count))
  }, [
    currentType,
    currentPart,
    ctx.presentTypes,
    ctx.sortedSections,
    currentTypeIdx,
    writingQs,
    goTo,
  ])

  /** Clamp out-of-range part in URL after test loads. */
  const ensureValidPart = useCallback(async () => {
    if (isPracticePart) return
    if (currentType === 'speaking') return
    if (!partParam) return
    const count = partCount(ctx.sortedSections, currentType, writingQs)
    if (count <= 0) return
    if (rawPart !== currentPart) {
      await goTo(currentType, currentPart, { replace: true })
    }
  }, [
    isPracticePart,
    currentType,
    currentPart,
    rawPart,
    partParam,
    ctx.sortedSections,
    writingQs,
    goTo,
  ])

  return {
    currentType,
    currentPart,
    currentTypeIdx,
    activeSectionId,
    activeWritingTask,
    activeListeningPart,
    hash,
    goTo,
    goToSection,
    goToPart,
    goToQuestion,
    next,
    prev,
    ensureValidPart,
    typeOrder: TYPE_ORDER,
  }
}
