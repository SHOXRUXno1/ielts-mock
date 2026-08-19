import { Link } from '@tanstack/react-router'
import {
  Panel,
  PanelBody,
  PanelHeader,
  PanelTitle,
  PanelToolbar,
  SkillBandRow,
} from '@/components/report'
import { Button } from '@/components/ui/button'
import type { SectionBands } from '@/lib/api/student'
import { ENTER } from '@/features/results/lib/motion'
import { SKILL_KEYS, SKILL_META } from '@/features/results/lib/skill'
import { skillHighlights } from '../lib/profile-stats'

type SkillAveragesPanelProps = {
  bands: SectionBands
}

export function SkillAveragesPanel({ bands }: SkillAveragesPanelProps) {
  const highlights = skillHighlights(bands)
  const strongest =
    highlights.strongest != null ? SKILL_META[highlights.strongest].label : null
  const focus =
    highlights.weakest != null && highlights.weakest !== highlights.strongest
      ? SKILL_META[highlights.weakest].label
      : null

  return (
    <Panel className={ENTER}>
      <PanelHeader>
        <PanelTitle>Skill averages</PanelTitle>
        <PanelToolbar>
          <Button
            asChild
            variant='ghost'
            size='sm'
            className='h-7 text-xs text-muted-foreground hover:text-foreground'
          >
            <Link to='/student/results'>View all results</Link>
          </Button>
        </PanelToolbar>
      </PanelHeader>
      <PanelBody className='mt-3 space-y-1'>
        {SKILL_KEYS.map((skill) => (
          <SkillBandRow key={skill} skill={skill} band={bands[skill]} />
        ))}
        {strongest && (
          <div className='mt-3 flex flex-wrap gap-x-6 gap-y-2 border-t border-border pt-4 text-sm'>
            <p>
              <span className='text-muted-foreground'>Strongest</span>{' '}
              <span className='font-medium text-foreground'>{strongest}</span>
            </p>
            {focus && (
              <p>
                <span className='text-muted-foreground'>Focus on</span>{' '}
                <span className='font-medium text-foreground'>{focus}</span>
              </p>
            )}
          </div>
        )}
      </PanelBody>
    </Panel>
  )
}
