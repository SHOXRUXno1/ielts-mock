import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import type { CompoundStructure } from '../../data/compound'

type Props = {
  structure: CompoundStructure
  onChange: (next: CompoundStructure) => void
}

export function CompoundMetaFields({ structure, onChange }: Props) {
  return (
    <div className='grid grid-cols-2 gap-3'>
      <div className='space-y-1.5'>
        <Label className='text-xs text-muted-foreground'>Instruction words</Label>
        <Input
          className='h-8 text-sm'
          value={structure.instruction_words}
          onChange={(e) =>
            onChange({ ...structure, instruction_words: e.target.value })
          }
          placeholder='ONE WORD AND/OR A NUMBER'
        />
      </div>
      <div className='space-y-1.5'>
        <Label className='text-xs text-muted-foreground'>Max words per gap</Label>
        <div className='flex gap-1'>
          {[1, 2, 3].map((n) => (
            <Button
              key={n}
              type='button'
              size='sm'
              variant={structure.max_words_per_gap === n ? 'default' : 'outline'}
              className='h-8 w-10'
              onClick={() => onChange({ ...structure, max_words_per_gap: n })}
            >
              {n}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
