import type { AttemptDetailRead } from '@/lib/api/attempts'
import { accuracyByPart } from '../lib/insights'
import { ENTER, staggerStyle } from '../lib/motion'
import { SKILL_META } from '../lib/skill'
import { OutcomeBar } from './outcome-bar'
import { Panel, PanelBody, PanelHeader, PanelTitle } from '@/components/report'

type AccuracyByPartProps = {
  attempt: AttemptDetailRead
}

export function AccuracyByPart({ attempt }: AccuracyByPartProps) {
  const listening = accuracyByPart(attempt.answers, 'listening')
  const reading = accuracyByPart(attempt.answers, 'reading')
  if (listening.length === 0 && reading.length === 0) return null

  return (
    <Panel className={ENTER} style={staggerStyle(3)}>
      <PanelHeader>
        <PanelTitle>Accuracy by part</PanelTitle>
      </PanelHeader>
      <PanelBody className='mt-4 space-y-6'>
        {listening.length > 0 && (
          <PartGroup
            label={SKILL_META.listening.label}
            parts={listening}
          />
        )}
        {reading.length > 0 && (
          <PartGroup label={SKILL_META.reading.label} parts={reading} />
        )}
      </PanelBody>
    </Panel>
  )
}

function PartGroup({
  label,
  parts,
}: {
  label: string
  parts: ReturnType<typeof accuracyByPart>
}) {
  return (
    <div className='space-y-3'>
      <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
        {label}
      </p>
      <div className='grid gap-4 sm:grid-cols-2'>
        {parts.map((part) => (
          <div key={part.key} className='space-y-2'>
            <div className='flex items-baseline justify-between gap-2'>
              <p className='text-sm font-medium text-foreground'>{part.label}</p>
              <p className='text-[11px] tabular-nums text-muted-foreground'>
                {part.correct}/{part.total}
              </p>
            </div>
            <OutcomeBar
              correct={part.correct}
              incorrect={part.incorrect}
              skipped={part.skipped}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
