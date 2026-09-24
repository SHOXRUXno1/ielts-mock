import { useRef, useState } from 'react'
import { Crosshair, MapPin, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { mediaUrl } from '@/lib/api/attempts'
import {
  extractGapIds,
  parseCellText,
  segmentsToText,
  type DiagramMarker,
  type DiagramStructure,
} from '../../data/compound'
import { GapChipsRow } from './gap-chips-row'
import type { GapEditHandlers } from './table-structure-editor'

type Props = {
  structure: DiagramStructure
  onChange: (next: DiagramStructure) => void
  gapEdit?: GapEditHandlers
}

type Mode = 'idle' | 'add' | 'anchor'

const clampPct = (v: number) => Math.max(0, Math.min(100, v))

export function DiagramStructureEditor({ structure, onChange, gapEdit }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const dragIndex = useRef<number | null>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [mode, setMode] = useState<Mode>('idle')

  const markers = structure.markers

  const setMarkers = (next: DiagramMarker[]) =>
    onChange({ ...structure, markers: next })

  const updateMarker = (idx: number, patch: Partial<DiagramMarker>) =>
    setMarkers(markers.map((m, i) => (i === idx ? { ...m, ...patch } : m)))

  const pctFromEvent = (e: { clientX: number; clientY: number }) => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect || rect.width === 0 || rect.height === 0) return null
    return {
      x: clampPct(((e.clientX - rect.left) / rect.width) * 100),
      y: clampPct(((e.clientY - rect.top) / rect.height) * 100),
    }
  }

  const handleImageClick = (e: React.MouseEvent) => {
    const pos = pctFromEvent(e)
    if (!pos) return
    if (mode === 'add') {
      const next: DiagramMarker = {
        x: pos.x,
        y: pos.y,
        segments: [{ type: 'gap', gap_id: nextMarkerGapId(structure) }],
      }
      setMarkers([...markers, next])
      setSelected(markers.length)
      setMode('idle')
      return
    }
    if (mode === 'anchor' && selected != null) {
      updateMarker(selected, { anchor: { x: pos.x, y: pos.y } })
      setMode('idle')
    }
  }

  const startDrag = (idx: number) => (e: React.PointerEvent) => {
    e.stopPropagation()
    dragIndex.current = idx
    setSelected(idx)
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
  }

  const onPointerMove = (e: React.PointerEvent) => {
    if (dragIndex.current == null) return
    const pos = pctFromEvent(e)
    if (pos) updateMarker(dragIndex.current, { x: pos.x, y: pos.y })
  }

  const endDrag = () => {
    dragIndex.current = null
  }

  const handleText = (idx: number, text: string) => {
    const otherIds = markers.flatMap((m, i) =>
      i === idx ? [] : m.segments.flatMap((s) => (s.type === 'gap' ? [s.gap_id] : [])),
    )
    updateMarker(idx, { segments: parseCellText(text, otherIds) })
  }

  const removeMarker = (idx: number) => {
    setMarkers(markers.filter((_, i) => i !== idx))
    setSelected(null)
  }

  const gaps = extractGapIds(structure)

  return (
    <div className='space-y-3'>
      <p className='text-[11px] text-muted-foreground'>
        Upload a diagram image above, then <strong>Add marker</strong> and click on the
        image to place a numbered input. Drag a marker to move it. Select a marker and{' '}
        <strong>Set anchor</strong> to draw a leader line to the part it labels. Use{' '}
        <code className='rounded bg-muted px-1'>{'{gap}'}</code> in a marker's text for the blank.
      </p>

      {!structure.image_url ? (
        <div className='rounded-md border border-dashed border-border px-3 py-6 text-center text-sm text-muted-foreground'>
          Upload a diagram image first (the “Diagram image” control above).
        </div>
      ) : (
        <>
          <div className='flex flex-wrap items-center gap-2'>
            <Button
              type='button'
              size='sm'
              variant={mode === 'add' ? 'default' : 'outline'}
              onClick={() => setMode(mode === 'add' ? 'idle' : 'add')}
            >
              <MapPin className='mr-1 size-3.5' />
              {mode === 'add' ? 'Click image to place…' : 'Add marker'}
            </Button>
            {selected != null && (
              <Button
                type='button'
                size='sm'
                variant={mode === 'anchor' ? 'default' : 'outline'}
                onClick={() => setMode(mode === 'anchor' ? 'idle' : 'anchor')}
              >
                <Crosshair className='mr-1 size-3.5' />
                {mode === 'anchor' ? 'Click image for anchor…' : 'Set anchor'}
              </Button>
            )}
          </div>

          <div
            ref={containerRef}
            className={cn(
              'relative mx-auto w-full max-w-2xl select-none overflow-hidden rounded-lg border border-border',
              mode !== 'idle' && 'cursor-crosshair',
            )}
            onClick={handleImageClick}
            onPointerMove={onPointerMove}
            onPointerUp={endDrag}
            onPointerLeave={endDrag}
          >
            <img
              src={mediaUrl(structure.image_url)}
              alt='Diagram'
              draggable={false}
              className='block w-full'
            />
            <svg
              className='pointer-events-none absolute inset-0 h-full w-full'
              viewBox='0 0 100 100'
              preserveAspectRatio='none'
              aria-hidden
            >
              {markers.map((m, i) =>
                m.anchor ? (
                  <g key={i}>
                    <line
                      x1={m.x}
                      y1={m.y}
                      x2={m.anchor.x}
                      y2={m.anchor.y}
                      className='stroke-foreground/45'
                      strokeWidth={1}
                      vectorEffect='non-scaling-stroke'
                    />
                    <circle
                      cx={m.anchor.x}
                      cy={m.anchor.y}
                      r={1.6}
                      className='fill-foreground/60'
                      vectorEffect='non-scaling-stroke'
                    />
                  </g>
                ) : null,
              )}
            </svg>
            {markers.map((m, i) => {
              const preview =
                m.segments
                  .map((s) => (s.type === 'text' ? s.value : '___'))
                  .join('')
                  .trim() || `#${i + 1}`
              return (
                <button
                  key={i}
                  type='button'
                  onPointerDown={startDrag(i)}
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelected(i)
                  }}
                  className={cn(
                    'absolute -translate-x-1/2 -translate-y-1/2 cursor-move whitespace-nowrap rounded-md border bg-card/90 px-1.5 py-0.5 text-[11px] shadow-sm backdrop-blur-sm',
                    selected === i
                      ? 'border-primary ring-2 ring-primary/40'
                      : 'border-border',
                  )}
                  style={{ left: `${m.x}%`, top: `${m.y}%` }}
                >
                  {preview}
                </button>
              )
            })}
          </div>

          <div className='space-y-2'>
            {markers.map((m, i) => (
              <div
                key={i}
                className={cn(
                  'space-y-2 rounded-md border p-3',
                  selected === i ? 'border-primary bg-primary/5' : 'border-border bg-card',
                )}
                onClick={() => setSelected(i)}
              >
                <div className='flex items-center justify-between'>
                  <span className='text-xs font-medium text-muted-foreground'>
                    Marker {i + 1} · {Math.round(m.x)}%, {Math.round(m.y)}%
                    {m.anchor ? ' · anchored' : ''}
                  </span>
                  <div className='flex items-center gap-1'>
                    {m.anchor && (
                      <Button
                        type='button'
                        size='sm'
                        variant='ghost'
                        className='h-7 px-2 text-[11px]'
                        onClick={(e) => {
                          e.stopPropagation()
                          updateMarker(i, { anchor: undefined })
                        }}
                      >
                        Clear anchor
                      </Button>
                    )}
                    <Button
                      type='button'
                      size='icon'
                      variant='ghost'
                      className='size-7'
                      onClick={(e) => {
                        e.stopPropagation()
                        removeMarker(i)
                      }}
                    >
                      <Trash2 className='size-3.5' />
                    </Button>
                  </div>
                </div>
                <Textarea
                  rows={1}
                  className='font-mono text-sm'
                  value={segmentsToText(m.segments)}
                  onChange={(e) => handleText(i, e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  placeholder='width of mortar: {gap}'
                />
              </div>
            ))}
          </div>

          {gapEdit && <GapChipsRow gapIds={gaps} gapEdit={gapEdit} />}

          <div className='flex items-center justify-between'>
            <p className='text-xs text-muted-foreground'>
              Markers: {markers.length} · Gaps: {gaps.length}
              {gaps.length > 0 ? ` (${gaps.join(', ')})` : ''}
            </p>
            <Button
              type='button'
              size='sm'
              variant='outline'
              onClick={() => setMode('add')}
            >
              <Plus className='mr-1 size-3.5' /> Add marker
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

/** Allocate a stable diagram gap id not already used by any marker. */
function nextMarkerGapId(structure: DiagramStructure): string {
  const used = new Set(extractGapIds(structure))
  let n = 1
  while (used.has(`d${n}`)) n += 1
  return `d${n}`
}
