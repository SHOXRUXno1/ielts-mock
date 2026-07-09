import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Download,
  FileUp,
  Music,
  TriangleAlert,
  Upload,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  confirmImport,
  downloadTemplate,
  type ImportConfirmResult,
  type ImportPreview,
  type ListeningSectionInfo,
  previewImport,
  uploadSectionAudio,
} from '@/lib/api/tests'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

// ---------------------------------------------------------------------------
// Drop zone
// ---------------------------------------------------------------------------

function DropZone({
  onFile,
  disabled,
}: {
  onFile: (f: File) => void
  disabled?: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handle = (f: File | undefined) => {
    if (!f) return
    if (!f.name.endsWith('.xlsx')) {
      toast.error('Only .xlsx files are accepted.')
      return
    }
    onFile(f)
  }

  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
        dragging
          ? 'border-primary bg-primary/5'
          : 'border-muted-foreground/30 hover:border-primary/50'
      } ${disabled ? 'pointer-events-none opacity-50' : 'cursor-pointer'}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        handle(e.dataTransfer.files[0])
      }}
    >
      <FileUp className='text-muted-foreground mb-3 h-10 w-10' />
      <p className='text-sm font-medium'>Drop your Excel file here or click to browse</p>
      <p className='text-muted-foreground mt-1 text-xs'>Accepts .xlsx files only</p>
      <input
        ref={inputRef}
        type='file'
        accept='.xlsx'
        className='hidden'
        onChange={(e) => handle(e.target.files?.[0])}
      />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Section preview card
// ---------------------------------------------------------------------------

function SectionCard({ s }: { s: ImportPreview['sections'][number] }) {
  const kindLabel: Record<string, string> = {
    reading: 'Reading',
    writing: 'Writing',
    listening: 'Listening',
  }

  return (
    <div className='bg-card rounded-lg border p-4'>
      <div className='flex items-center justify-between'>
        <span className='font-medium'>{s.sheet_name}</span>
        <Badge variant='outline'>{kindLabel[s.kind] ?? s.kind}</Badge>
      </div>
      <div className='text-muted-foreground mt-2 flex gap-4 text-sm'>
        {s.kind === 'reading' && (
          <span>{s.passage_word_count ?? 0} words in passage</span>
        )}
        {s.kind === 'writing' && <span>{s.tasks_count ?? 0} task(s)</span>}
        {s.kind === 'listening' && s.audio_filename && (
          <span className='flex items-center gap-1'>
            <Music className='h-3 w-3' /> {s.audio_filename}
          </span>
        )}
        <span>{s.questions_count} question(s)</span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Audio upload step
// ---------------------------------------------------------------------------

function AudioUploadStep({
  testId,
  listeningSections,
}: {
  testId: string
  listeningSections: ListeningSectionInfo[]
}) {
  const [uploaded, setUploaded] = useState<Record<string, string>>({})

  const mutation = useMutation({
    mutationFn: ({
      sectionId,
      file,
    }: {
      sectionId: string
      file: File
    }) => uploadSectionAudio(testId, sectionId, file),
    onSuccess: (data, vars) => {
      setUploaded((prev) => ({ ...prev, [vars.sectionId]: data.url }))
      toast.success('Audio uploaded.')
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof Error ? err.message : 'Upload failed'
      toast.error(msg)
    },
  })

  return (
    <div className='space-y-4'>
      <h3 className='text-base font-semibold'>Upload Listening Audio (MP3)</h3>
      {listeningSections.map((sec) => {
        const done = Boolean(uploaded[sec.id])
        return (
          <div
            key={sec.id}
            className='bg-card flex items-center gap-4 rounded-lg border p-4'
          >
            <div className='flex-1'>
              <p className='text-sm font-medium'>{sec.name}</p>
              {sec.audio_filename && (
                <p className='text-muted-foreground text-xs'>
                  Expected: {sec.audio_filename}
                </p>
              )}
            </div>
            {done ? (
              <CheckCircle2 className='h-5 w-5 text-green-500' />
            ) : (
              <label className='cursor-pointer'>
                <input
                  type='file'
                  accept='.mp3,audio/mpeg'
                  className='hidden'
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) mutation.mutate({ sectionId: sec.id, file: f })
                  }}
                />
                <Button variant='outline' size='sm' asChild>
                  <span>
                    <Upload className='mr-1 h-3 w-3' /> Upload MP3
                  </span>
                </Button>
              </label>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function TestsImport() {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [confirmResult, setConfirmResult] = useState<ImportConfirmResult | null>(null)

  // --- preview mutation ---
  const previewMutation = useMutation({
    mutationFn: (f: File) => previewImport(f),
    onSuccess: (data) => {
      setPreview(data)
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Preview failed'
      toast.error(msg)
    },
  })

  // --- confirm mutation ---
  const confirmMutation = useMutation({
    mutationFn: (f: File) => confirmImport(f),
    onSuccess: (data) => {
      setConfirmResult(data)
      void queryClient.invalidateQueries({ queryKey: ['tests'] })
      const r = data.sections_created
      const q = data.questions_created
      toast.success(`Test imported: ${r} section(s), ${q} question(s).`)
    },
    onError: (err: unknown) => {
      let msg = 'Import failed'
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message) as { errors?: string[] }
          if (parsed.errors) {
            msg = parsed.errors.join('; ')
          } else {
            msg = err.message
          }
        } catch {
          msg = err.message
        }
      }
      toast.error(msg)
    },
  })

  const handleFile = (f: File) => {
    setFile(f)
    setPreview(null)
    setConfirmResult(null)
    previewMutation.mutate(f)
  }

  const hasErrors = (preview?.errors.length ?? 0) > 0
  const isPreviewing = previewMutation.isPending
  const isConfirming = confirmMutation.isPending

  return (
    <>
      <Header fixed>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main>
        {/* Top bar */}
        <div className='mb-4 flex items-center gap-3'>
          <Link to='/tests'>
            <Button variant='ghost' size='sm'>
              <ArrowLeft className='mr-1 h-4 w-4' />
              Back to Tests
            </Button>
          </Link>
          <div className='flex-1' />
          <Button
            variant='outline'
            size='sm'
            onClick={() => downloadTemplate()}
          >
            <Download className='mr-1 h-4 w-4' />
            Download Template
          </Button>
        </div>

        <div className='mb-6'>
          <h1 className='text-2xl font-semibold'>Import Test from Excel</h1>
          <p className='text-muted-foreground text-sm'>
            Download the template, fill it in, and upload it here to create a
            new IELTS test.
          </p>
        </div>

        {/* Drop zone — hidden once confirmed */}
        {!confirmResult && (
          <div className='mb-6'>
            <DropZone
              onFile={handleFile}
              disabled={isPreviewing || isConfirming}
            />
            {file && (
              <p className='text-muted-foreground mt-2 text-xs'>
                Selected: {file.name}
              </p>
            )}
          </div>
        )}

        {/* Preview loading */}
        {isPreviewing && (
          <div className='mb-6 space-y-2'>
            <p className='text-sm'>Parsing file…</p>
            <Progress value={undefined} className='h-1' />
          </div>
        )}

        {/* Preview result */}
        {preview && !confirmResult && (
          <div className='mb-6 space-y-4'>
            <div className='rounded-lg border p-4'>
              <p className='text-sm font-medium'>
                Title:{' '}
                <span className='font-normal'>{preview.title || '—'}</span>
              </p>
              {preview.description && (
                <p className='text-muted-foreground text-sm'>
                  {preview.description}
                </p>
              )}
              <p className='text-muted-foreground text-sm'>
                Type: {preview.type} · {preview.total_questions} question(s)
              </p>
            </div>

            {/* Section cards */}
            <div className='grid gap-3 sm:grid-cols-2 lg:grid-cols-3'>
              {preview.sections.map((s) => (
                <SectionCard key={s.sheet_name} s={s} />
              ))}
            </div>

            {/* Warnings */}
            {preview.warnings.length > 0 && (
              <div className='rounded-lg border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-700 dark:bg-yellow-950/30'>
                <div className='mb-2 flex items-center gap-2 text-sm font-medium text-yellow-700 dark:text-yellow-400'>
                  <TriangleAlert className='h-4 w-4' />
                  Warnings ({preview.warnings.length})
                </div>
                <ul className='list-disc space-y-1 pl-5 text-sm text-yellow-700 dark:text-yellow-400'>
                  {preview.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Errors */}
            {preview.errors.length > 0 && (
              <div className='rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950/30'>
                <div className='mb-2 flex items-center gap-2 text-sm font-medium text-red-700 dark:text-red-400'>
                  <AlertCircle className='h-4 w-4' />
                  Errors — fix before importing ({preview.errors.length})
                </div>
                <ul className='list-disc space-y-1 pl-5 text-sm text-red-700 dark:text-red-400'>
                  {preview.errors.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Import button */}
            <div className='flex gap-3'>
              <Button
                disabled={hasErrors || isConfirming || !file}
                onClick={() => file && confirmMutation.mutate(file)}
              >
                {isConfirming ? (
                  <>Importing…</>
                ) : (
                  <>
                    <Upload className='mr-1 h-4 w-4' />
                    Import Test
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Confirm progress */}
        {isConfirming && (
          <div className='mb-6 space-y-2'>
            <p className='text-sm'>Saving to database…</p>
            <Progress value={undefined} className='h-1' />
          </div>
        )}

        {/* Post-confirm audio upload */}
        {confirmResult && (
          <div className='space-y-6'>
            <div className='flex items-center gap-2 rounded-lg border border-green-300 bg-green-50 p-4 dark:border-green-700 dark:bg-green-950/30'>
              <CheckCircle2 className='h-5 w-5 text-green-600' />
              <p className='text-sm font-medium text-green-700 dark:text-green-400'>
                Test created with {confirmResult.sections_created} section(s) and{' '}
                {confirmResult.questions_created} question(s).
              </p>
            </div>

            {confirmResult.listening_sections.length > 0 && (
              <AudioUploadStep
                testId={confirmResult.test_id}
                listeningSections={confirmResult.listening_sections}
              />
            )}

            <Link to='/tests/$testId' params={{ testId: confirmResult.test_id }}>
              <Button>Go to Test →</Button>
            </Link>
          </div>
        )}
      </Main>
    </>
  )
}
