import { useEffect, type ReactNode } from 'react'
import { useRouterState } from '@tanstack/react-router'
import { ListeningSection } from '../components/take/listening-section'
import { ReadingSection } from '../components/take/reading-section'
import { WritingSection } from '../components/take/writing-section'
import { SpeakingSection } from '../components/take/speaking-section'
import { SpeakingReadyGate } from '../components/take/speaking-ready-gate'
import { scrollAndFlashQuestion } from './flash-question'
import { useTakeTest } from './take-test-context'
import { useTestNavigation } from './use-test-navigation'

function scrollToHash(hash: string) {
  const id = hash.startsWith('#') ? hash.slice(1) : hash
  if (!id) return
  const n = id.startsWith('q-') ? Number(id.slice(2)) : NaN
  if (Number.isFinite(n)) {
    scrollAndFlashQuestion(n)
    return
  }
  requestAnimationFrame(() => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else {
      const main = document.querySelector('main')
      main?.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
}

/** Renders the active section/part from URL params via context + navigation. */
export function SectionContent() {
  const ctx = useTakeTest()
  const nav = useTestNavigation()
  const hash = useRouterState({ select: (s) => s.location.hash })

  const { ensureValidPart, activeSectionId, currentPart } = nav

  useEffect(() => {
    void ensureValidPart()
  }, [ensureValidPart])

  useEffect(() => {
    if (hash) scrollToHash(hash)
  }, [hash, activeSectionId, currentPart])

  const activeSection =
    ctx.sortedSections.find((s) => s.id === nav.activeSectionId) ??
    ctx.sortedSections.find((s) => s.type === nav.currentType)

  if (!activeSection) return null

  const questions = ctx.sectionQuestions[activeSection.id] ?? []
  const answers = ctx.answers[activeSection.id] ?? {}
  const onAnswer = (qId: string, resp: Record<string, unknown>) =>
    ctx.updateAnswer(activeSection.id, qId, resp)

  const locked = ctx.inputsLocked && !ctx.isPreview

  let body: ReactNode
  switch (activeSection.type) {
    case 'listening': {
      const listeningSections = ctx.sortedSections.filter(
        (s) => s.type === 'listening',
      )
      body = (
        <ListeningSection
          section={activeSection}
          questions={questions}
          answers={answers}
          onAnswer={onAnswer}
          activePart={nav.activeListeningPart}
          partNumberOverride={
            ctx.practiceScope === 'part' ? nav.currentPart : undefined
          }
          allSections={
            listeningSections.length > 1 ? listeningSections : undefined
          }
          flagged={ctx.flagged}
          onToggleFlag={ctx.toggleFlag}
          previewMode={ctx.isPreview}
          attemptId={ctx.isPreview ? null : ctx.attemptId}
        />
      )
      break
    }
    case 'reading': {
      const readingSiblings = ctx.sortedSections.filter(
        (s) => s.type === 'reading',
      )
      const passageIndex = readingSiblings.findIndex(
        (s) => s.id === activeSection.id,
      )
      body = (
        <ReadingSection
          section={activeSection}
          passage={activeSection.passage}
          questions={questions}
          answers={answers}
          onAnswer={onAnswer}
          passageIndex={passageIndex >= 0 ? passageIndex : 0}
          totalPassages={readingSiblings.length}
          passageNumberOverride={
            ctx.practiceScope === 'part' ? nav.currentPart : undefined
          }
          allSections={readingSiblings.length > 1 ? readingSiblings : undefined}
          sectionQuestions={ctx.sectionQuestions}
          flagged={ctx.flagged}
          onToggleFlag={ctx.toggleFlag}
          previewMode={ctx.isPreview}
          attemptId={ctx.isPreview ? null : ctx.attemptId}
        />
      )
      break
    }
    case 'writing':
      body = (
        <WritingSection
          questions={questions}
          answers={answers}
          onAnswer={onAnswer}
          attemptId={ctx.isPreview ? null : ctx.attemptId}
          activeTaskIdx={nav.activeWritingTask}
          previewMode={ctx.isPreview}
          showInstantFeedback={ctx.isPreview || ctx.isPractice}
        />
      )
      break
    case 'speaking': {
      // Live-exam gate: hold on a readiness screen until the student clicks
      // Start. Only then does enterSection() kick off the 20-min safety cap.
      // Preview and practice paths keep their existing behaviour.
      const isLiveExam = !ctx.isPreview && !ctx.isPractice && !!ctx.attemptId
      if (isLiveExam && ctx.stateOf('speaking') === 'not_started') {
        body = <SpeakingReadyGate />
        break
      }
      body = (
        <SpeakingSection
          attemptId={ctx.isPreview ? null : ctx.attemptId}
          questions={questions}
          previewMode={ctx.isPreview}
          onActiveChange={ctx.setSpeakingActive}
          controlsRef={ctx.speakingControlsRef}
        />
      )
      break
    }
    default:
      return null
  }

  return (
    <div
      className={locked ? 'pointer-events-none h-full opacity-70' : 'h-full'}
      aria-disabled={locked || undefined}
    >
      {body}
    </div>
  )
}
