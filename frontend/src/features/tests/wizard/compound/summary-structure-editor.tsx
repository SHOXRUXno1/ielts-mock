import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  extractGapIds,
  parseSummaryGaps,
  summaryToEditableText,
  type SummaryStructure,
} from '../../data/compound'
import { GapChipsRow } from './gap-chips-row'
import type { GapEditHandlers } from './table-structure-editor'

type Props = {
  structure: SummaryStructure
  onChange: (next: SummaryStructure) => void
  gapEdit?: GapEditHandlers
}

export function SummaryStructureEditor({
  structure,
  onChange,
  gapEdit,
}: Props) {
  const text = summaryToEditableText(structure)
  const gaps = extractGapIds(structure)

  return (
    <div className='space-y-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs text-muted-foreground'>
          Summary text (use {'{gap1}'}, {'{gap2}'}, … or bare {'{gap}'} for blanks)
        </Label>
        <Textarea
          rows={6}
          className='font-mono text-sm'
          value={text}
          onChange={(e) =>
            onChange(
              parseSummaryGaps(e.target.value, {
                instruction_words: structure.instruction_words,
                max_words_per_gap: structure.max_words_per_gap,
              }),
            )
          }
          placeholder='The Kakapo is a {gap1} parrot found in New Zealand.'
        />
      </div>

      {gapEdit && <GapChipsRow gapIds={gaps} gapEdit={gapEdit} />}

      <p className='text-xs text-muted-foreground'>
        Gaps: {gaps.length}
        {gaps.length > 0 ? ` (${gaps.join(', ')})` : ''}
      </p>
    </div>
  )
}
