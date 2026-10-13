import { memo, useMemo } from 'react'
import { Joyride, STATUS, type EventData } from 'react-joyride'
import { useIsDesktop } from '@/hooks/use-mobile'
import type { SectionType } from '../../data/schema'
import { stepsForSection } from './tour-steps'

type OnboardingTourProps = {
  section: SectionType | null
  speakingReady: boolean
  open: boolean
  preStart?: boolean
  retryToken?: number
  onStart?: () => void
  onClose: () => void
}

function OnboardingTourInner({
  section,
  speakingReady,
  open,
  preStart = false,
  retryToken = 0,
  onStart,
  onClose,
}: OnboardingTourProps) {
  const isDesktop = useIsDesktop()
  const steps = useMemo(
    () => (section ? stepsForSection(section, isDesktop, speakingReady) : []),
    [section, isDesktop, speakingReady]
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
      options={{
        // Visual theming — matches the exam blue of the Submit button
        // so the tour reads as native chrome, not a bolt-on overlay.
        primaryColor: '#2563eb',
        backgroundColor: '#0f172a',
        textColor: '#f8fafc',
        arrowColor: '#0f172a',
        overlayColor: 'rgba(2, 6, 23, 0.55)',
        zIndex: 10_000,
        // Behavior
        showProgress: true,
        // Which buttons appear in the tooltip. 'close' is intentionally
        // omitted — we hide the X and rely on Skip + the final Got it.
        buttons: ['back', 'primary', 'skip'],
        // Explicit `false` keeps the backdrop click inert so the student
        // can't dismiss the tour by misclicking outside the tooltip.
        overlayClickAction: false,
        spotlightPadding: 6,
      }}
      styles={{
        tooltip: {
          borderRadius: 12,
          fontSize: 14,
          width: 'min(360px, calc(100vw - 24px))',
          maxHeight: 'calc(100svh - 32px)',
          overflowY: 'auto',
          padding: 16,
        },
        tooltipTitle: {
          fontSize: 16,
        },
        tooltipContent: {
          paddingTop: 8,
          paddingBottom: 8,
        },
        buttonPrimary: {
          borderRadius: 8,
          padding: '7px 12px',
          fontSize: 13,
          fontWeight: 500,
        },
        buttonBack: {
          color: '#cbd5e1',
          marginRight: 4,
          padding: 7,
          fontSize: 13,
        },
        buttonSkip: {
          color: '#94a3b8',
          padding: 7,
          fontSize: 13,
        },
        buttonClose: {
          display: 'none',
        },
      }}
      locale={{
        back: 'Back',
        close: 'Close',
        last: preStart
          ? `Start ${section[0].toUpperCase()}${section.slice(1)}`
          : 'Got it',
        next: 'Next',
        skip: 'Skip',
      }}
      onEvent={handleEvent}
    />
  )
}

export const OnboardingTour = memo(OnboardingTourInner)
OnboardingTour.displayName = 'OnboardingTour'
