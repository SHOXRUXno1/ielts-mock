import { createContext, useContext, type MutableRefObject } from 'react'
import type { AttemptDetailRead, AttemptRead } from '@/lib/api/attempts'
import type {
  AttemptProgressRead,
  SealReason,
  SealSectionResponse,
  SectionState,
} from '@/lib/api/section-progress'
import type { SpeakingSessionControls } from '@/features/speaking-examiner/speaking-examiner-session'
import type { Question, Section, SectionType, TestDetail } from '../data/schema'

export type SectionAnswers = Record<string, Record<string, unknown>>

export type PracticeScope = 'part' | 'section'

export type TakeTestContextValue = {
  mode: 'live' | 'preview' | 'practice'
  isPreview: boolean
  isPractice: boolean
  /** Practice only: 'part' = single part, 'section' = whole skill. */
  practiceScope: PracticeScope
  isReviewRoute: boolean
  test: TestDetail
  testId: string
  bookSlug?: string
  testSlug?: string
  attemptId: string | null
  attempt: AttemptRead | AttemptDetailRead | null
  sortedSections: Section[]
  presentTypes: SectionType[]
  sectionQuestions: Record<string, Question[]>
  answers: Record<string, SectionAnswers>
  updateAnswer: (
    sectionId: string,
    questionId: string,
    response: Record<string, unknown>,
  ) => void
  flagged: Set<string>
  toggleFlag: (questionId: string) => void
  speakingActive: boolean
  setSpeakingActive: (active: boolean) => void
  speakingControlsRef: MutableRefObject<SpeakingSessionControls | null>
  /** Flush localStorage + server answers before URL navigation. True if SECTION_EXPIRED. */
  flushBeforeNavigate: () => Promise<boolean>
  isFlushing: boolean
  finished: boolean
  startTest: () => void
  isStarting: boolean
  submitTest: () => void
  isSubmitting: boolean
  showSubmitDialog: boolean
  setShowSubmitDialog: (open: boolean) => void
  /** Access denied / load error for attempt */
  attemptError: 'forbidden' | 'not_found' | null

  // ── Section progress / timer ────────────────────────────────────────────
  progress: AttemptProgressRead | null
  sealedTypes: Set<SectionType>
  activeSectionType: SectionType | null
  allSealed: boolean
  stateOf: (type: string) => SectionState | null
  inputsLocked: boolean
  /** Open the timeout modal (timer hit 0 or 409 SECTION_EXPIRED). */
  reportSectionExpired: (info: {
    from: SectionType
    next: SectionType | null
  }) => void
  enterSection: (sectionType: string) => Promise<unknown>
  sealSection: (args: {
    sectionType: string
    answers?: Array<{
      question_id: string
      response: Record<string, unknown>
    }>
    reason?: SealReason
  }) => Promise<SealSectionResponse>
  isEntering: boolean
  isSealing: boolean
}

const TakeTestContext = createContext<TakeTestContextValue | null>(null)

export function TakeTestProvider({
  value,
  children,
}: {
  value: TakeTestContextValue
  children: React.ReactNode
}) {
  return (
    <TakeTestContext.Provider value={value}>{children}</TakeTestContext.Provider>
  )
}

export function useTakeTest(): TakeTestContextValue {
  const ctx = useContext(TakeTestContext)
  if (!ctx) {
    throw new Error('useTakeTest must be used within TakeTestProvider')
  }
  return ctx
}

export function useTakeTestOptional(): TakeTestContextValue | null {
  return useContext(TakeTestContext)
}
