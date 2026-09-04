import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  extractGapIds,
  parseCellText,
  segmentsToText,
  type FlowStep,
  type FlowStructure,
} from '../../data/compound'
import { GapChipsRow } from './gap-chips-row'
import type { GapEditHandlers } from './table-structure-editor'

type Props = {
  structure: FlowStructure
  onChange: (next: FlowStructure) => void
  gapEdit?: GapEditHandlers
}

export function FlowStructureEditor({ structure, onChange, gapEdit }: Props) {
  const setStep = (idx: number, step: FlowStep) => {
    const steps = structure.steps.map((s, i) => (i === idx ? step : s))
    onChange({ ...structure, steps })
  }

  const handleStepText = (idx: number, text: string) => {
    const otherIds = extractGapIds({
      ...structure,
      steps: structure.steps.map((s, i) =>
        i === idx ? { segments: [] } : s,
      ),
    })
    setStep(idx, { segments: parseCellText(text, otherIds) })
  }

  const addStep = () => {
    onChange({
      ...structure,
      steps: [
        ...structure.steps,
        { segments: [{ type: 'text', value: '' }] },
      ],
    })
  }

  const removeStep = (idx: number) => {
    if (structure.steps.length <= 1) return
    onChange({
      ...structure,
      steps: structure.steps.filter((_, i) => i !== idx),
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
        <Label className='text-xs text-muted-foreground'>Flow-chart title</Label>
        <Input
          className='h-8 text-sm'
          value={structure.title ?? ''}
          onChange={(e) => onChange({ ...structure, title: e.target.value })}
          placeholder='Process of making chocolate'
        />
      </div>

      {structure.steps.map((step, idx) => {
        if (step.fork?.length) {
          return (
            <div
              key={idx}
              className='grid grid-cols-2 gap-2 rounded border border-border p-2'
            >
              {step.fork.map((branch, bi) => (
                <div key={bi} className='space-y-1'>
                  <span className='text-[10px] font-semibold text-muted-foreground'>
                    Branch {bi + 1}
                  </span>
                  <Textarea
                    rows={2}
                    className='font-mono text-sm'
                    value={segmentsToText(branch.segments)}
                    onChange={(e) => {
                      const otherIds = extractGapIds({
                        ...structure,
                        steps: structure.steps.map((s, i) => {
                          if (i !== idx) return s
                          return {
                            segments: [],
                            fork: (s.fork ?? []).map((b, j) =>
                              j === bi ? { segments: [] } : b,
                            ),
                          }
                        }),
                      })
                      const nextFork = (step.fork ?? []).map((b, j) =>
                        j === bi
                          ? { segments: parseCellText(e.target.value, otherIds) }
                          : b,
                      )
                      setStep(idx, { segments: [], fork: nextFork })
                    }}
                    placeholder='Revise before {gap}'
                  />
                </div>
              ))}
            </div>
          )
        }
        const text = segmentsToText(step.segments)
        const preview = step.segments
          .map((s) => (s.type === 'text' ? s.value : '___'))
          .join('')
        return (
          <div
            key={idx}
            className='flex flex-wrap items-start gap-2 rounded border border-border p-2'
          >
            <span className='mt-2 rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground'>
              {idx + 1}
            </span>
            <div className='min-w-0 flex-1 space-y-1'>
              <Textarea
                rows={2}
                className='font-mono text-sm'
                value={text}
                onChange={(e) => handleStepText(idx, e.target.value)}
                placeholder='Beans are {gap} in the sun'
              />
              {step.segments.some((s) => s.type === 'gap') && (
                <p className='text-[10px] text-muted-foreground'>Preview: {preview}</p>
              )}
            </div>
            <Button
              type='button'
              size='icon'
              variant='ghost'
              className='size-7'
              onClick={() => removeStep(idx)}
              disabled={structure.steps.length <= 1}
            >
              <Trash2 className='size-3.5' />
            </Button>
          </div>
        )
      })}

      {gapEdit && <GapChipsRow gapIds={gaps} gapEdit={gapEdit} />}

      <div className='flex items-center justify-between'>
        <p className='text-xs text-muted-foreground'>
          Gaps: {gaps.length}
          {gaps.length > 0 ? ` (${gaps.join(', ')})` : ''}
        </p>
        <Button type='button' size='sm' variant='outline' onClick={addStep}>
          <Plus className='mr-1 size-3.5' /> Add Step
        </Button>
      </div>
    </div>
  )
}
