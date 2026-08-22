import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Check, ChevronsUpDown, Download, FileText, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { downloadResultPdf, type AttemptListItem } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { formatBand } from '@/features/results/lib/band'

const EXPORTABLE_STATUSES = new Set([
  'auto_scored',
  'fully_scored',
  'scored',
  'completed_without_speaking',
  'partial',
  'completed',
  'speaking_in_progress',
])

type Student = { id: string; name: string; attemptCount: number }

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  attempts: AttemptListItem[]
}

export function ExportPdfDialog({ open, onOpenChange, attempts }: Props) {
  const [studentId, setStudentId] = useState<string | null>(null)
  const [attemptId, setAttemptId] = useState<string | null>(null)
  const [studentPickerOpen, setStudentPickerOpen] = useState(false)

  const exportable = useMemo(
    () =>
      attempts.filter(
        (a) => a.student_id != null && EXPORTABLE_STATUSES.has(a.status),
      ),
    [attempts],
  )

  const students = useMemo<Student[]>(() => {
    const map = new Map<string, Student>()
    for (const a of exportable) {
      if (!a.student_id) continue
      const existing = map.get(a.student_id)
      if (existing) {
        existing.attemptCount += 1
      } else {
        map.set(a.student_id, {
          id: a.student_id,
          name: a.student_name ?? 'Unknown student',
          attemptCount: 1,
        })
      }
    }
    return [...map.values()].sort((a, b) => a.name.localeCompare(b.name))
  }, [exportable])

  const studentAttempts = useMemo(() => {
    if (!studentId) return []
    return exportable
      .filter((a) => a.student_id === studentId)
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
  }, [exportable, studentId])

  const selectedStudent = students.find((s) => s.id === studentId) ?? null

  const download = useMutation({
    mutationFn: (id: string) => downloadResultPdf(id),
    onSuccess: () => {
      toast.success('PDF downloaded')
      onOpenChange(false)
    },
    onError: () => toast.error('Could not generate the PDF'),
  })

  function handleOpenChange(next: boolean) {
    if (!next && download.isPending) return
    onOpenChange(next)
    if (!next) {
      setStudentId(null)
      setAttemptId(null)
    }
  }

  function handleDownload() {
    if (!attemptId) return
    download.mutate(attemptId)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className='sm:max-w-lg'>
        <DialogHeader>
          <DialogTitle>Export attempt as PDF</DialogTitle>
          <DialogDescription>
            Pick a student, then choose one of their attempts.
          </DialogDescription>
        </DialogHeader>

        {students.length === 0 ? (
          <div className='flex flex-col items-center gap-2 rounded-lg border border-dashed py-10 text-sm text-muted-foreground'>
            <FileText className='size-6 text-muted-foreground/60' />
            No attempts available for export yet.
          </div>
        ) : (
          <div className='space-y-4'>
            <div className='space-y-1.5'>
              <label className='text-xs font-medium text-muted-foreground'>
                Student
              </label>
              <Popover
                open={studentPickerOpen}
                onOpenChange={setStudentPickerOpen}
              >
                <PopoverTrigger asChild>
                  <Button
                    variant='outline'
                    role='combobox'
                    aria-expanded={studentPickerOpen}
                    className='w-full justify-between font-normal'
                  >
                    <span className='truncate'>
                      {selectedStudent
                        ? selectedStudent.name
                        : 'Select a student...'}
                    </span>
                    <ChevronsUpDown className='ml-2 size-4 shrink-0 opacity-50' />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className='w-[--radix-popover-trigger-width] p-0'
                  align='start'
                >
                  <Command>
                    <CommandInput placeholder='Search students...' />
                    <CommandList>
                      <CommandEmpty>No students found.</CommandEmpty>
                      <CommandGroup>
                        {students.map((s) => (
                          <CommandItem
                            key={s.id}
                            value={`${s.name} ${s.id}`}
                            onSelect={() => {
                              setStudentId(s.id)
                              setAttemptId(null)
                              setStudentPickerOpen(false)
                            }}
                          >
                            <Check
                              className={cn(
                                'mr-2 size-4',
                                studentId === s.id ? 'opacity-100' : 'opacity-0',
                              )}
                            />
                            <span className='flex-1 truncate'>{s.name}</span>
                            <span className='ml-2 text-xs text-muted-foreground'>
                              {s.attemptCount}{' '}
                              {s.attemptCount === 1 ? 'attempt' : 'attempts'}
                            </span>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            <div className='space-y-1.5'>
              <label className='text-xs font-medium text-muted-foreground'>
                Attempt
              </label>
              {!studentId ? (
                <p className='rounded-lg border border-dashed px-3 py-6 text-center text-xs text-muted-foreground'>
                  Pick a student first
                </p>
              ) : studentAttempts.length === 0 ? (
                <p className='rounded-lg border border-dashed px-3 py-6 text-center text-xs text-muted-foreground'>
                  This student has no scored attempts yet.
                </p>
              ) : (
                <div className='max-h-64 space-y-1 overflow-y-auto rounded-lg border p-1'>
                  {studentAttempts.map((a) => {
                    const selected = a.id === attemptId
                    return (
                      <button
                        key={a.id}
                        type='button'
                        onClick={() => setAttemptId(a.id)}
                        className={cn(
                          'flex w-full items-center gap-3 rounded-md px-3 py-2 text-left transition-colors',
                          selected
                            ? 'bg-primary/10 ring-1 ring-primary/40'
                            : 'hover:bg-muted',
                        )}
                      >
                        <div className='min-w-0 flex-1'>
                          <div className='truncate text-sm font-medium'>
                            {a.test_title}
                          </div>
                          <div className='truncate text-xs text-muted-foreground'>
                            {new Date(a.created_at).toLocaleDateString(
                              undefined,
                              {
                                day: 'numeric',
                                month: 'short',
                                year: 'numeric',
                              },
                            )}
                            {' · '}
                            {a.status.replace(/_/g, ' ')}
                          </div>
                        </div>
                        <span className='ml-auto shrink-0 rounded-md bg-muted px-2 py-0.5 text-xs font-semibold tabular-nums'>
                          {formatBand(a.overall_band)}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        <DialogFooter>
          <Button
            variant='outline'
            onClick={() => handleOpenChange(false)}
            disabled={download.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDownload}
            disabled={!attemptId || download.isPending}
            className='gap-2'
          >
            {download.isPending ? (
              <Loader2 className='size-4 animate-spin' />
            ) : (
              <Download className='size-4' />
            )}
            Download PDF
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
