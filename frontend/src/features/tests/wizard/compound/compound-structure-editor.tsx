import type { CompoundStructure, CompoundVariant } from '../../data/compound'
import { FlowStructureEditor } from './flow-structure-editor'
import { FormStructureEditor } from './form-structure-editor'
import { NotesStructureEditor } from './notes-structure-editor'
import { SummaryStructureEditor } from './summary-structure-editor'
import {
  TableStructureEditor,
  type GapEditHandlers,
} from './table-structure-editor'

type Props = {
  variant: CompoundVariant
  structure: CompoundStructure
  onChange: (next: CompoundStructure) => void
  gapEdit?: GapEditHandlers
  onFocusedCellChange?: (cell: { row: number; col: number } | null) => void
}

export function CompoundStructureEditor({
  variant,
  structure,
  onChange,
  gapEdit,
  onFocusedCellChange,
}: Props) {
  if (variant === 'table' && structure.variant === 'table') {
    return (
      <TableStructureEditor
        structure={structure}
        onChange={onChange}
        gapEdit={gapEdit}
        onFocusedCellChange={onFocusedCellChange}
      />
    )
  }
  if (variant === 'notes' && structure.variant === 'notes') {
    return (
      <NotesStructureEditor
        structure={structure}
        onChange={onChange}
        gapEdit={gapEdit}
      />
    )
  }
  if (variant === 'form' && structure.variant === 'form') {
    return (
      <FormStructureEditor
        structure={structure}
        onChange={onChange}
        gapEdit={gapEdit}
      />
    )
  }
  if (variant === 'summary' && structure.variant === 'summary') {
    return (
      <SummaryStructureEditor
        structure={structure}
        onChange={onChange}
        gapEdit={gapEdit}
      />
    )
  }
  if (variant === 'flow' && structure.variant === 'flow') {
    return (
      <FlowStructureEditor
        structure={structure}
        onChange={onChange}
        gapEdit={gapEdit}
      />
    )
  }
  return (
    <p className='text-sm text-warning-foreground'>
      Structure variant mismatch. Change the question type and save again.
    </p>
  )
}
