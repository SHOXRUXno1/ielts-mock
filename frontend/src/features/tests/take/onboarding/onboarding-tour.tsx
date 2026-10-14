import { memo, useMemo } from 'react'
import { Joyride, STATUS, type EventData } from 'react-joyride'
import { useIsDesktop } from '@/hooks/use-mobile'
import type { SectionType } from '../../data/schema'
import { stepsForSection } from './tour-steps'
import { TourTooltip } from './tour-tooltip'

type OnboardingTourProps = {
  section: SectionType | null
  speakingReady: boolean
  isPractice: boolean
  /**
   * The section the student will land on after pressing Finish section.
   * Used to name the destination in the last tour step ("go to Reading").
   * Pass undefined if the current section is the final one in this test.
   */
  nextSection?: SectionType
  open: boolean
  preStart?: boolean
  retryToken?: number
  onStart?: () => void
  onClose: () => void
}

function OnboardingTourInner({
  section,
  speakingReady,
  isPractice,
  nextSection,
  open,
  preStart = false,
  retryToken = 0,
  onStart,
  onClose,
}: OnboardingTourProps) {
  const isDesktop = useIsDesktop()
  const steps = useMemo(
    () =>
      section
        ? stepsForSection(
            section,
            isDesktop,
            speakingReady,
            isPractice,
            nextSection
          )
        : [],
    [section, isDesktop, speakingReady, isPractice, nextSection]
  )

  if (!section || steps.length === 0) return null

  const handleEvent = (data: EventData) => {
    const { status } = data
    const terminal: readonly string[] = [STATUS.FINISHED, STATUS.SKIPPED]
    if (terminal.includes(status)) {
      if (preStart) onStart?.()
      else onClose()
    }
  }

  return (
    <Joyride
      key={`${section}:${retryToken}` /* fresh state after a failed start */}
      steps={steps}
      run={open}
      continuous
      scrollToFirstStep={true}
      tooltipComponent={TourTooltip}
      options={{
        primaryColor: '#2563eb',
        arrowColor: '#ffffff',
        overlayColor: 'rgba(15, 23, 42, 0.55)',
        zIndex: 10_000,
        // Backdrop click is inert so a misclick can't dismiss the tour.
        overlayClickAction: false,
        spotlightPadding: 10,
      }}
      locale={{
        back: 'Back',
        close: 'Close',
        last: preStart
          ? `Start ${section[0].toUpperCase()}${section.slice(1)}`
          : 'Got it',
        next: 'Next',
        skip: 'Skip tour',
      }}
      onEvent={handleEvent}
    />
  )
}

export const OnboardingTour = memo(OnboardingTourInner)
OnboardingTour.displayName = 'OnboardingTour'
