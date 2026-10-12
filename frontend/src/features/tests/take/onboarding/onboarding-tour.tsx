import { memo, useMemo } from 'react'
import { Joyride, STATUS, type EventData } from 'react-joyride'
import type { SectionType } from '../../data/schema'
import { stepsForSection } from './tour-steps'

type OnboardingTourProps = {
  section: SectionType | null
  open: boolean
  onClose: () => void
}

function OnboardingTourInner({ section, open, onClose }: OnboardingTourProps) {
  const steps = useMemo(() => (section ? stepsForSection(section) : []), [section])

  if (!section || steps.length === 0) return null

  const handleEvent = (data: EventData) => {
    const { status } = data
    const terminal: readonly string[] = [STATUS.FINISHED, STATUS.SKIPPED]
    if (terminal.includes(status)) {
      onClose()
    }
  }

  return (
    <Joyride
      key={section /* fresh state when section changes */}
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
          padding: 20,
        },
        buttonPrimary: {
          borderRadius: 8,
          padding: '8px 16px',
          fontWeight: 500,
        },
        buttonBack: {
          color: '#cbd5e1',
          marginRight: 8,
        },
        buttonSkip: {
          color: '#94a3b8',
        },
        buttonClose: {
          display: 'none',
        },
      }}
      locale={{
        back: 'Back',
        close: 'Close',
        last: 'Got it',
        next: 'Next',
        skip: 'Skip',
      }}
      onEvent={handleEvent}
    />
  )
}

export const OnboardingTour = memo(OnboardingTourInner)
OnboardingTour.displayName = 'OnboardingTour'
