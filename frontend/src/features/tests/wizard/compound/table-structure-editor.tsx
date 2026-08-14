import { useState, type KeyboardEvent } from 'react'
import { MoreVertical, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import {
  bulletsToPlain,
  emptyPlainCell,
  extractGapIds,
  nextGapId,
  plainToBullets,
  appendGap,
  removeGapFromSegments,
  type BulletItem,
  type CellSegment,
  type TableCell,
  type TableStructure,
} from '../../data/compound'
import type { QuestionDraft } from '../question-editor'
import {
  SegmentsDisplay,
  SegmentsInlineEditor,
  type GapEditApi,
} from './segments-inline'

export type GapEditHandlers = {
  getDraft: (gapId: string) => QuestionDraft
  onSaveGap: (draft: QuestionDraft) => Promise<void>
  maxWords: number
  /** Listening part offset so chips show Q11+ in Part 2 */
  numberOffset?: number
}

type Props = {
  structure: TableStructure
  onChange: (next: TableStructure) => void
  gapEdit?: GapEditHandlers
  /** Notify parent which cell is focused (for preview highlight) */
  onFocusedCellChange?: (cell: { row: number; col: number } | null) => void
}

function otherGapIds(
  structure: TableStructure,
  ri: number,
  ci: number,
): string[] {
  return extractGapIds({
    ...structure,
    rows: structure.rows.map((row, i) =>
      i === ri
        ? row.map((c, j) => (j === ci ? emptyPlainCell() : c))
        : row,
    ),
  })
}

function cellSegments(cell: TableCell): CellSegment[] {
  if (cell.variant === 'bullets') {
    return cell.bullets.flatMap((b) => b.segments)
  }
  return cell.segments
}

export function TableStructureEditor({
  structure,
  onChange,
  gapEdit,
  onFocusedCellChange,
}: Props) {
  const [focused, setFocused] = useState<{ ri: number; ci: number } | null>(
    null,
  )
  const [hoveredRowGap, setHoveredRowGap] = useState<number | null>(null)
  const [hoveredColGap, setHoveredColGap] = useState<number | null>(null)

  const gapIds = extractGapIds(structure)
  const offset = gapEdit?.numberOffset ?? 0
  const gapOrder = new Map(gapIds.map((id, i) => [id, offset + i + 1]))
  const gapApi: GapEditApi | undefined = gapEdit
    ? {
        getDraft: gapEdit.getDraft,
        onSaveGap: gapEdit.onSaveGap,
        maxWords: gapEdit.maxWords,
        gapOrder,
      }
    : undefined

  const setCell = (ri: number, ci: number, cell: TableCell) => {
    onChange({
      ...structure,
      rows: structure.rows.map((row, i) =>
        i === ri ? row.map((c, j) => (j === ci ? cell : c)) : row,
      ),
    })
  }

  const setFocus = (ri: number, ci: number) => {
    setFocused({ ri, ci })
    onFocusedCellChange?.({ row: ri, col: ci })
  }

  const clearFocus = () => {
    setFocused(null)
    onFocusedCellChange?.(null)
  }

  const setHeader = (ci: number, value: string) => {
    const headers = [...structure.headers]
    headers[ci] = value
    onChange({ ...structure, headers })
  }

  const addColumnAt = (afterCi: number) => {
    const insertAt = afterCi + 1
    onChange({
      ...structure,
      headers: [
        ...structure.headers.slice(0, insertAt),
        `Column ${structure.headers.length + 1}`,
        ...structure.headers.slice(insertAt),
      ],
      rows: structure.rows.map((row) => [
        ...row.slice(0, insertAt),
        emptyPlainCell(),
        ...row.slice(insertAt),
      ]),
    })
  }

  const removeColumn = (ci: number) => {
    if (structure.headers.length <= 1) return
    onChange({
      ...structure,
      headers: structure.headers.filter((_, i) => i !== ci),
      rows: structure.rows.map((row) => row.filter((_, i) => i !== ci)),
    })
  }

  const addRowAt = (afterRi: number) => {
    const insertAt = afterRi + 1
    const newRow = structure.headers.map(() => emptyPlainCell())
    onChange({
      ...structure,
      rows: [
        ...structure.rows.slice(0, insertAt),
        newRow,
        ...structure.rows.slice(insertAt),
      ],
    })
  }

  const removeRow = (ri: number) => {
    if (structure.rows.length <= 1) return
    onChange({
      ...structure,
      rows: structure.rows.filter((_, i) => i !== ri),
    })
    if (focused?.ri === ri) clearFocus()
  }

  const convertToBullets = (ri: number, ci: number) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant === 'bullets') return
    setCell(ri, ci, plainToBullets(cell))
  }

  const convertToPlain = (ri: number, ci: number) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant === 'plain') return
    if (cell.bullets.length > 1) {
      const ok = window.confirm(
        'Convert multiple bullets into one plain cell? Joined with " / ".',
      )
      if (!ok) return
    }
    setCell(ri, ci, bulletsToPlain(cell, otherGapIds(structure, ri, ci)))
  }

  const clearCell = (ri: number, ci: number) => {
    setCell(ri, ci, emptyPlainCell())
  }

  const addGapToPlain = (ri: number, ci: number) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'plain') return
    const id = nextGapId(extractGapIds(structure))
    setCell(ri, ci, {
      variant: 'plain',
      segments: appendGap(cell.segments, id),
    })
  }

  const deleteGapFromPlain = (ri: number, ci: number, gapId: string) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'plain') return
    setCell(ri, ci, {
      variant: 'plain',
      segments: removeGapFromSegments(cell.segments, gapId),
    })
  }

  const setPlainSegments = (ri: number, ci: number, segments: CellSegment[]) => {
    setCell(ri, ci, { variant: 'plain', segments })
  }

  const setBulletSegments = (
    ri: number,
    ci: number,
    bi: number,
    segments: CellSegment[],
  ) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'bullets') return
    const bullets = cell.bullets.map((b, i) =>
      i === bi ? { segments } : b,
    )
    setCell(ri, ci, { variant: 'bullets', bullets })
  }

  const addGapToBullet = (ri: number, ci: number, bi: number) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'bullets') return
    const id = nextGapId(extractGapIds(structure))
    const bullets = cell.bullets.map((b, i) =>
      i === bi ? { segments: appendGap(b.segments, id) } : b,
    )
    setCell(ri, ci, { variant: 'bullets', bullets })
  }

  const deleteGapFromBullet = (
    ri: number,
    ci: number,
    bi: number,
    gapId: string,
  ) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'bullets') return
    const bullets = cell.bullets.map((b, i) =>
      i === bi
        ? { segments: removeGapFromSegments(b.segments, gapId) }
        : b,
    )
    setCell(ri, ci, { variant: 'bullets', bullets })
  }

  const addBullet = (ri: number, ci: number) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'bullets') return
    setCell(ri, ci, {
      variant: 'bullets',
      bullets: [
        ...cell.bullets,
        { segments: [{ type: 'text', value: '' }] },
      ],
    })
  }

  const onBulletKeyDown = (
    e: KeyboardEvent<HTMLDivElement>,
    ri: number,
    ci: number,
    bi: number,
  ) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'bullets') return
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const bullets: BulletItem[] = [
        ...cell.bullets.slice(0, bi + 1),
        { segments: [{ type: 'text', value: '' }] },
        ...cell.bullets.slice(bi + 1),
      ]
      setCell(ri, ci, { variant: 'bullets', bullets })
    }
  }

  const removeBullet = (ri: number, ci: number, bi: number) => {
    const cell = structure.rows[ri][ci]
    if (cell.variant !== 'bullets' || cell.bullets.length <= 1) return
    setCell(ri, ci, {
      variant: 'bullets',
      bullets: cell.bullets.filter((_, i) => i !== bi),
    })
  }

  const isEmptyCell = (cell: TableCell) => {
    const segs = cellSegments(cell)
    return (
      segs.length === 0 ||
      (segs.length === 1 && segs[0].type === 'text' && !segs[0].value)
    )
  }

  return (
    <div className='space-y-2'>
      {/* Table title (e.g. "Health Centres", "Talks for patients...") */}
      <Input
        value={structure.title ?? ''}
        onChange={(e) => onChange({ ...structure, title: e.target.value || undefined })}
        placeholder='Table title (optional)'
        className='text-center text-sm font-semibold'
      />

      {gapIds.length > 0 && (
        <p className='text-[11px] text-muted-foreground'>
          {gapIds.length} gap{gapIds.length === 1 ? '' : 's'}:{' '}
          {gapIds.map((_, i) => offset + i + 1).join(', ')}
        </p>
      )}

      <div className='relative overflow-x-auto rounded-md border border-border bg-card'>
        <table className='w-full border-collapse text-sm'>
          <thead>
            <tr>
              {structure.headers.map((h, ci) => (
                <th
                  key={ci}
                  className='group/col relative border border-border bg-muted p-0 align-top'
                  onMouseEnter={() => setHoveredColGap(ci)}
                  onMouseLeave={() => setHoveredColGap(null)}
                >
                  <div className='flex items-center gap-1 p-1.5'>
                    <Input
                      className='h-8 border-0 bg-transparent text-xs font-semibold shadow-none focus-visible:ring-1'
                      value={h}
                      onChange={(e) => setHeader(ci, e.target.value)}
                    />
                    <Button
                      type='button'
                      size='icon'
                      variant='ghost'
                      className='size-7 shrink-0 opacity-0 transition-opacity group-hover/col:opacity-100'
                      onClick={() => removeColumn(ci)}
                      disabled={structure.headers.length <= 1}
                      aria-label='Delete column'
                    >
                      <Trash2 className='size-3.5' />
                    </Button>
                  </div>
                  {/* Hover add-column indicator */}
                  <button
                    type='button'
                    title='Add column'
                    onClick={() => addColumnAt(ci)}
                    className={cn(
                      'absolute -right-2 top-0 z-10 flex h-full w-4 -translate-x-1/2 items-center justify-center transition-opacity',
                      hoveredColGap === ci ? 'opacity-100' : 'opacity-0',
                    )}
                  >
                    <span className='flex size-4 items-center justify-center rounded-full bg-sky-600 text-white shadow'>
                      <Plus className='size-2.5' />
                    </span>
                  </button>
                </th>
              ))}
              <th className='w-8 border border-border bg-muted' />
            </tr>
          </thead>
          <tbody>
            {structure.rows.map((row, ri) => (
              <tr
                key={ri}
                className='group/row'
                onMouseEnter={() => setHoveredRowGap(ri)}
                onMouseLeave={() => setHoveredRowGap(null)}
              >
                {row.map((cell, ci) => {
                  const isFocused =
                    focused?.ri === ri && focused?.ci === ci
                  const isBullets = cell.variant === 'bullets'

                  return (
                    <td
                      key={ci}
                      className={cn(
                        'group/cell relative border border-border p-0 align-top transition-colors',
                        isFocused
                          ? 'bg-sky-50/60 ring-2 ring-inset ring-sky-300'
                          : 'bg-card hover:bg-muted/50',
                      )}
                      onClick={() => setFocus(ri, ci)}
                      onBlur={(e) => {
                        const related = e.relatedTarget as HTMLElement | null
                        // If focus moved into a Radix portal (e.g. an open GapChip popover),
                        // keep this cell focused so the popover doesn't get unmounted.
                        if (
                          related?.closest?.(
                            '[data-radix-popper-content-wrapper]',
                          )
                        ) {
                          return
                        }
                        if (
                          !e.currentTarget.contains(e.relatedTarget as Node)
                        ) {
                          if (isFocused) clearFocus()
                        }
                      }}
                    >
                      {/* Hover options */}
                      <div className='absolute right-1 top-1 z-10 opacity-0 transition-opacity group-hover/cell:opacity-100'>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              type='button'
                              size='icon'
                              variant='ghost'
                              className='size-6 bg-card/90 shadow-sm'
                              onClick={(e) => e.stopPropagation()}
                              aria-label='Cell options'
                            >
                              <MoreVertical className='size-3.5' />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align='end' className='w-44'>
                            {isBullets ? (
                              <DropdownMenuItem
                                onClick={() => convertToPlain(ri, ci)}
                              >
                                Convert to Plain
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem
                                onClick={() => convertToBullets(ri, ci)}
                              >
                                Convert to Bullets
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => clearCell(ri, ci)}
                            >
                              Clear cell
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>

                      <div className='min-h-[3.5rem] p-2 pr-7'>
                        {!isFocused ? (
                          // Default / hover display
                          isBullets ? (
                            <ul className='list-disc space-y-1 pl-4 text-sm leading-relaxed'>
                              {cell.bullets.map((b, bi) => (
                                <li key={bi}>
                                  <SegmentsDisplay
                                    segments={b.segments}
                                    gapEdit={gapApi}
                                  />
                                  {isEmptyCell({
                                    variant: 'plain',
                                    segments: b.segments,
                                  }) && (
                                    <span className='text-muted-foreground'>—</span>
                                  )}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <SegmentsDisplay
                              segments={cell.segments}
                              gapEdit={gapApi}
                            />
                          )
                        ) : // Focus edit mode
                        isBullets ? (
                          <div className='space-y-2'>
                            {cell.bullets.map((b, bi) => (
                              <div
                                key={bi}
                                className='flex items-start gap-1'
                                onKeyDown={(e) =>
                                  onBulletKeyDown(e, ri, ci, bi)
                                }
                              >
                                <span className='mt-2 text-xs text-muted-foreground'>
                                  •
                                </span>
                                <div className='min-w-0 flex-1'>
                                  <SegmentsInlineEditor
                                    segments={b.segments}
                                    onChange={(segs) =>
                                      setBulletSegments(ri, ci, bi, segs)
                                    }
                                    gapEdit={gapApi}
                                    onAddGap={() =>
                                      addGapToBullet(ri, ci, bi)
                                    }
                                    onDeleteGap={(gid) =>
                                      deleteGapFromBullet(ri, ci, bi, gid)
                                    }
                                    autoFocus={bi === 0}
                                  />
                                </div>
                                <Button
                                  type='button'
                                  size='icon'
                                  variant='ghost'
                                  className='size-6 shrink-0'
                                  disabled={cell.bullets.length <= 1}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    removeBullet(ri, ci, bi)
                                  }}
                                >
                                  <Trash2 className='size-3' />
                                </Button>
                              </div>
                            ))}
                            <div className='flex items-center gap-2 pt-1'>
                              <button
                                type='button'
                                className='text-[11px] font-medium text-sky-700'
                                onClick={(e) => {
                                  e.stopPropagation()
                                  addBullet(ri, ci)
                                }}
                              >
                                + Add bullet
                              </button>
                              <button
                                type='button'
                                className='text-[11px] text-muted-foreground hover:text-foreground'
                                onClick={(e) => {
                                  e.stopPropagation()
                                  convertToPlain(ri, ci)
                                }}
                              >
                                Plain
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className='space-y-2'>
                            <SegmentsInlineEditor
                              segments={cell.segments}
                              onChange={(segs) =>
                                setPlainSegments(ri, ci, segs)
                              }
                              gapEdit={gapApi}
                              onAddGap={() => addGapToPlain(ri, ci)}
                              onDeleteGap={(gid) =>
                                deleteGapFromPlain(ri, ci, gid)
                              }
                              autoFocus
                            />
                            <div className='flex gap-2'>
                              <button
                                type='button'
                                className='text-[11px] text-muted-foreground hover:text-foreground'
                                onClick={(e) => {
                                  e.stopPropagation()
                                  convertToBullets(ri, ci)
                                }}
                              >
                                Bullets
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  )
                })}
                <td className='border border-border p-1 text-center'>
                  <Button
                    type='button'
                    size='icon'
                    variant='ghost'
                    className='size-7 opacity-0 transition-opacity group-hover/row:opacity-100'
                    onClick={() => removeRow(ri)}
                    disabled={structure.rows.length <= 1}
                    aria-label='Delete row'
                  >
                    <Trash2 className='size-3.5' />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Hover add-row strip under last hovered row */}
        {hoveredRowGap != null && (
          <button
            type='button'
            title='Add row'
            onClick={() => addRowAt(hoveredRowGap)}
            onMouseEnter={() => setHoveredRowGap(hoveredRowGap)}
            className='flex w-full items-center justify-center gap-1 border-t border-dashed border-border py-1.5 text-[11px] text-muted-foreground transition-colors hover:bg-sky-50 hover:text-sky-600'
          >
            <Plus className='size-3' /> Add row
          </button>
        )}
        {hoveredRowGap == null && (
          <button
            type='button'
            title='Add row'
            onClick={() => addRowAt(structure.rows.length - 1)}
            className='flex w-full items-center justify-center gap-1 border-t border-dashed border-border py-1.5 text-[11px] text-muted-foreground opacity-60 transition-opacity hover:bg-sky-50 hover:text-sky-600 hover:opacity-100'
          >
            <Plus className='size-3' /> Add row
          </button>
        )}
      </div>
    </div>
  )
}
