import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  extractGapIds,
  nextGapId,
  parseCellText,
  segmentsToText,
  type FormField,
  type FormStructure,
} from '../../data/compound'
import { GapChipsRow } from './gap-chips-row'
import type { GapEditHandlers } from './table-structure-editor'

type Props = {
  structure: FormStructure
  onChange: (next: FormStructure) => void
  gapEdit?: GapEditHandlers
}

export function FormStructureEditor({ structure, onChange, gapEdit }: Props) {
  const setField = (fi: number, field: FormField) => {
    const fields = structure.fields.map((f, i) => (i === fi ? field : f))
    onChange({ ...structure, fields })
  }

  const handleGapLineText = (fi: number, text: string) => {
    const field = structure.fields[fi]
    if (field.type !== 'gap_line') return
    const otherIds = extractGapIds({
      ...structure,
      fields: structure.fields.map((f, i) =>
        i === fi
          ? { type: 'gap_line' as const, label: field.label, segments: [] }
          : f,
      ),
    })
    setField(fi, {
      type: 'gap_line',
      label: field.label,
      segments: parseCellText(text, otherIds),
    })
  }

  const addField = (type: 'static' | 'gap_line') => {
    const field: FormField =
      type === 'static'
        ? { type: 'static', label: 'Label', value: '' }
        : {
            type: 'gap_line',
            label: 'Label',
            segments: [
              { type: 'gap', gap_id: nextGapId(extractGapIds(structure)) },
            ],
          }
    onChange({ ...structure, fields: [...structure.fields, field] })
  }

  const removeField = (fi: number) => {
    if (structure.fields.length <= 1) return
    onChange({
      ...structure,
      fields: structure.fields.filter((_, i) => i !== fi),
    })
  }

  const gaps = extractGapIds(structure)

  return (
    <div className='space-y-3'>
      <p className='text-[11px] text-muted-foreground'>
        Gap fields: use <code className='rounded bg-muted px-1'>{'{gap}'}</code>{' '}
        or <code className='rounded bg-muted px-1'>{'{gap1}'}</code> for blanks.
      </p>
      <div className='space-y-1.5'>
        <Label className='text-xs text-muted-foreground'>Form title</Label>
        <Input
          className='h-8 text-sm'
          value={structure.form_title}
          onChange={(e) =>
            onChange({ ...structure, form_title: e.target.value })
          }
          placeholder='VIDEO LIBRARY APPLICATION FORM'
        />
      </div>

      <div className='space-y-2 rounded-md border border-border bg-card p-3'>
        {structure.fields.map((field, fi) => (
          <div
            key={fi}
            className='flex flex-wrap items-start gap-2 rounded border border-border p-2'
          >
            <div className='flex gap-1'>
              <Button
                type='button'
                size='sm'
                variant={field.type === 'static' ? 'default' : 'outline'}
                className='h-6 px-2 text-[10px]'
                onClick={() =>
                  field.type !== 'static' &&
                  setField(fi, {
                    type: 'static',
                    label: field.label,
                    value: '',
                  })
                }
              >
                Static
              </Button>
              <Button
                type='button'
                size='sm'
                variant={field.type === 'gap_line' ? 'default' : 'outline'}
                className='h-6 px-2 text-[10px]'
                onClick={() =>
                  field.type !== 'gap_line' &&
                  setField(fi, {
                    type: 'gap_line',
                    label: field.label,
                    segments: [
                      {
                        type: 'gap',
                        gap_id: nextGapId(extractGapIds(structure)),
                      },
                    ],
                  })
                }
              >
                Gap
              </Button>
            </div>

            <Input
              className='h-8 w-32 text-sm'
              value={field.label}
              onChange={(e) => setField(fi, { ...field, label: e.target.value })}
              placeholder='Label'
            />

            {field.type === 'static' ? (
              <Input
                className='h-8 min-w-[10rem] flex-1 text-sm'
                value={field.value}
                onChange={(e) =>
                  setField(fi, { ...field, value: e.target.value })
                }
                placeholder='Value'
              />
            ) : (
              <div className='min-w-0 flex-1 space-y-1'>
                <Textarea
                  rows={2}
                  className='font-mono text-sm'
                  value={segmentsToText(field.segments)}
                  onChange={(e) => handleGapLineText(fi, e.target.value)}
                  placeholder='Apartment 1,72 {gap} Street'
                />
                {field.segments.some((s) => s.type === 'gap') && (
                  <p className='text-[10px] text-muted-foreground'>
                    Preview:{' '}
                    {field.segments
                      .map((s) => (s.type === 'text' ? s.value : '___'))
                      .join('')}
                  </p>
                )}
              </div>
            )}

            <Button
              type='button'
              size='icon'
              variant='ghost'
              className='size-7'
              onClick={() => removeField(fi)}
              disabled={structure.fields.length <= 1}
            >
              <Trash2 className='size-3.5' />
            </Button>
          </div>
        ))}

        <div className='flex gap-2'>
          <Button
            type='button'
            size='sm'
            variant='outline'
            onClick={() => addField('static')}
          >
            <Plus className='mr-1 size-3.5' /> Static
          </Button>
          <Button
            type='button'
            size='sm'
            variant='outline'
            onClick={() => addField('gap_line')}
          >
            <Plus className='mr-1 size-3.5' /> Gap
          </Button>
        </div>
      </div>

      {gapEdit && <GapChipsRow gapIds={gaps} gapEdit={gapEdit} />}

      <p className='text-xs text-muted-foreground'>
        Gaps: {gaps.length}
        {gaps.length > 0 ? ` (${gaps.join(', ')})` : ''}
      </p>
    </div>
  )
}
