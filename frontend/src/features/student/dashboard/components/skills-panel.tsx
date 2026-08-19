import {
  Panel,
  PanelBody,
  PanelHeader,
  PanelTitle,
  SkillBandRow,
} from '@/components/report'
import type { SectionBands } from '@/lib/api/student'
import { ENTER } from '@/features/results/lib/motion'
import { SKILL_KEYS } from '@/features/results/lib/skill'

type SkillsPanelProps = {
  bands: SectionBands
}

export function SkillsPanel({ bands }: SkillsPanelProps) {
  return (
    <Panel className={ENTER}>
      <PanelHeader>
        <PanelTitle>Skills</PanelTitle>
      </PanelHeader>
      <PanelBody className='mt-3 space-y-1'>
        {SKILL_KEYS.map((skill) => (
          <SkillBandRow key={skill} skill={skill} band={bands[skill]} />
        ))}
      </PanelBody>
    </Panel>
  )
}
