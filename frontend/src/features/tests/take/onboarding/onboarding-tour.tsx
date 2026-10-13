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
        primaryColor: '#2563eb',
        backgroundColor: '#ffffff',
        textColor: '#0f172a',
        arrowColor: '#ffffff',
        overlayColor: 'rgba(15, 23, 42, 0.35)',
        zIndex: 10_000,
        showProgress: true,
        buttons: ['back', 'primary', 'skip'],
        overlayClickAction: false,
        spotlightPadding: 10,
      }}
      styles={{
        tooltip: {
          borderRadius: 16,
          fontSize: 14,
          width: 'min(360px, calc(100vw - 20px))',
          padding: 0,
          boxShadow:
            '0 0 0 1px rgba(0,0,0,0.06), 0 4px 8px rgba(0,0,0,0.04), 0 16px 40px rgba(0,0,0,0.1)',
          borderTop: '3px solid #2563eb',
          overflow: 'hidden',
        },
        tooltipContainer: {
          padding: '18px 20px 0',
          textAlign: 'left',
        },
        tooltipTitle: {
          fontSize: 15,
          fontWeight: 700,
          color: '#0f172a',
          letterSpacing: '-0.015em',
          lineHeight: 1.3,
          marginBottom: 0,
        },
        tooltipContent: {
          color: '#64748b',
          lineHeight: 1.65,
          fontSize: 14,
          padding: '8px 0 18px',
        },
        tooltipFooter: {
          padding: '10px 20px 14px',
          borderTop: '1px solid #f1f5f9',
          display: 'flex',
          alignItems: 'center',
        },
        buttonPrimary: {
          borderRadius: 8,
          padding: '7px 16px',
          fontSize: 13,
          fontWeight: 600,
          background: '#2563eb',
          color: '#ffffff',
          boxShadow: '0 1px 3px rgba(37,99,235,0.25)',
          letterSpacing: '0.005em',
        },
        buttonBack: {
          color: '#64748b',
          marginRight: 6,
          padding: '7px 10px',
          fontSize: 13,
          fontWeight: 500,
        },
        buttonSkip: {
          color: '#94a3b8',
          padding: '7px 0',
          fontSize: 12,
          fontWeight: 500,
          marginRight: 'auto',
        },
        buttonClose: {
          display: 'none',
        },
      }}
      locale={{
        back: '← Back',
        close: 'Close',
        last: preStart
          ? `Start ${section[0].toUpperCase()}${section.slice(1)}`
          : 'Got it ✓',
        next: 'Next →',
        skip: 'Skip tour',
      }}
      onEvent={handleEvent}
    />
  )
}

export const OnboardingTour = memo(OnboardingTourInner)
OnboardingTour.displayName = 'OnboardingTour'
