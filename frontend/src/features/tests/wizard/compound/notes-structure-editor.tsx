import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  extractGapIds,
  parseCellText,
  segmentsToText,
  type NoteItem,
  type NoteStructure,
} from '../../data/compound'
import { GapChipsRow } from './gap-chips-row'
import type { GapEditHandlers } from './table-structure-editor'

type Props = {
  structure: NoteStructure
  onChange: (next: NoteStructure) => void
  gapEdit?: GapEditHandlers
}

export function NotesStructureEditor({ structure, onChange, gapEdit }: Props) {
  const updateSection = (
    si: number,
    patch: Partial<NoteStructure['sections'][number]>,
  ) => {
    const sections = structure.sections.map((s, i) =>
      i === si ? { ...s, ...patch } : s,
    )
    onChange({ ...structure, sections })
  }

  const setItem = (si: number, ii: number, item: NoteItem) => {
    const section = structure.sections[si]
    const items = section.items.map((it, i) => (i === ii ? item : it))
    updateSection(si, { items })
  }

  const handleItemText = (si: number, ii: number, text: string) => {
    const otherIds = extractGapIds({
      ...structure,
      sections: structure.sections.map((sec, sIdx) =>
        sIdx === si
          ? {
              ...sec,
              items: sec.items.map((it, iIdx) =>
                iIdx === ii ? { segments: [] } : it,
              ),
            }
          : sec,
      ),
    })
    setItem(si, ii, { segments: parseCellText(text, otherIds) })
  }

  const addItem = (si: number) => {
    const section = structure.sections[si]
    updateSection(si, {
      items: [...section.items, { segments: [{ type: 'text', value: '' }] }],
    })
  }

  const removeItem = (si: number, ii: number) => {
    const section = structure.sections[si]
    if (section.items.length <= 1) return
    updateSection(si, {
      items: section.items.filter((_, i) => i !== ii),
    })
  }

  const addSection = () => {
    onChange({
      ...structure,
      sections: [
        ...structure.sections,
        { heading: '', items: [{ segments: [{ type: 'text', value: '' }] }] },
      ],
    })
  }

  const removeSection = (si: number) => {
    if (structure.sections.length <= 1) return
    onChange({
      ...structure,
      sections: structure.sections.filter((_, i) => i !== si),
    })
  }

  const gaps = extractGapIds(structure)

  return (
    <div className='space-y-3'>
      <p className='text-[11px] text-muted-foreground'>
        Use <code className='rounded bg-muted px-1'>{'{gap}'}</code> or{' '}
        <code className='rounded bg-muted px-1'>{'{gap1}'}</code> for blanks.
      </p>
      <div className='space-y-1.5'>
        <Label className='text-xs text-muted-foreground'>Notes title</Label>
        <Input
          className='h-8 text-sm'
          value={structure.title ?? ''}
          onChange={(e) => onChange({ ...structure, title: e.target.value })}
          placeholder='Farm Tours'
        />
      </div>

      <div className='flex items-center gap-2'>
        <Switch
          id='notes-bullets'
          checked={structure.bullets !== false}
          onCheckedChange={(v) => onChange({ ...structure, bullets: v })}
        />
        <Label htmlFor='notes-bullets' className='text-xs text-muted-foreground'>
          Show bullet points
        </Label>
      </div>

      {structure.sections.map((section, si) => (
        <div
          key={si}
          className='space-y-2 rounded-md border border-border bg-card p-3'
        >
          <div className='flex items-center gap-2'>
            <Input
              className='h-8 text-sm'
              value={section.heading ?? ''}
              onChange={(e) => updateSection(si, { heading: e.target.value })}
              placeholder={`Section ${si + 1} heading`}
            />
            <Button
              type='button'
              size='icon'
              variant='ghost'
              className='size-8'
              onClick={() => removeSection(si)}
              disabled={structure.sections.length <= 1}
            >
              <Trash2 className='size-3.5' />
            </Button>
          </div>

          {section.items.map((item, ii) => {
            const text = segmentsToText(item.segments)
            const preview = item.segments
              .map((s) => (s.type === 'text' ? s.value : '___'))
              .join('')
            return (
              <div
                key={ii}
                className='flex flex-wrap items-start gap-2 rounded border border-border p-2'
              >
                <div className='min-w-0 flex-1 space-y-1'>
                  <Textarea
                    rows={2}
                    className='font-mono text-sm'
                    value={text}
                    onChange={(e) => handleItemText(si, ii, e.target.value)}
                    placeholder='The address is {gap} Street'
                  />
                  {item.segments.some((s) => s.type === 'gap') && (
                    <p className='text-[10px] text-muted-foreground'>Preview: {preview}</p>
                  )}
                </div>
                <Button
                  type='button'
                  size='icon'
                  variant='ghost'
                  className='size-7'
                  onClick={() => removeItem(si, ii)}
                  disabled={section.items.length <= 1}
                >
                  <Trash2 className='size-3.5' />
                </Button>
              </div>
            )
          })}

          <Button
            type='button'
            size='sm'
            variant='outline'
            onClick={() => addItem(si)}
          >
            <Plus className='mr-1 size-3.5' /> Add Item
          </Button>
        </div>
      ))}

      {gapEdit && <GapChipsRow gapIds={gaps} gapEdit={gapEdit} />}

      <div className='flex items-center justify-between'>
        <p className='text-xs text-muted-foreground'>
          Gaps: {gaps.length}
          {gaps.length > 0 ? ` (${gaps.join(', ')})` : ''}
        </p>
        <Button type='button' size='sm' variant='outline' onClick={addSection}>
          <Plus className='mr-1 size-3.5' /> Add Section
        </Button>
      </div>
    </div>
  )
}
