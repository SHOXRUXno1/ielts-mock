const TERMINAL_ATTEMPT_STATUSES = new Set([
  'auto_scored',
  'fully_scored',
  'completed_without_speaking',
  'partial',
])

type AttemptStatusTone = 'success' | 'warning' | 'muted' | 'info'

export type AttemptStatusMeta = {
  label: string
  variant: 'default' | 'secondary' | 'outline'
  tone: AttemptStatusTone
  dot: string
  text: string
}

const STATUS_MAP: Record<string, AttemptStatusMeta> = {
  fully_scored: {
    label: 'Fully scored',
    variant: 'default',
    tone: 'success',
    dot: 'bg-emerald-500',
    text: 'text-success-foreground',
  },
  auto_scored: {
    label: 'Auto scored',
    variant: 'default',
    tone: 'success',
    dot: 'bg-emerald-500',
    text: 'text-success-foreground',
  },
  scored: {
    label: 'Auto scored',
    variant: 'default',
    tone: 'success',
    dot: 'bg-emerald-500',
    text: 'text-success-foreground',
  },
  speaking_in_progress: {
    label: 'Speaking in progress',
    variant: 'secondary',
    tone: 'info',
    dot: 'bg-skill-speaking',
    text: 'text-skill-speaking',
  },
  completed_without_speaking: {
    label: 'Completed (no speaking)',
    variant: 'default',
    tone: 'success',
    dot: 'bg-emerald-500',
    text: 'text-success-foreground',
  },
  partial: {
    label: 'Partial',
    variant: 'outline',
    tone: 'warning',
    dot: 'bg-warning-foreground',
    text: 'text-warning-foreground',
  },
  completed: {
    label: 'Scoring writing',
    variant: 'secondary',
    tone: 'info',
    dot: 'bg-skill-reading',
    text: 'text-skill-reading',
  },
  abandoned: {
    label: 'Abandoned',
    variant: 'outline',
    tone: 'muted',
    dot: 'bg-muted-foreground',
    text: 'text-muted-foreground',
  },
  in_progress: {
    label: 'In Progress',
    variant: 'secondary',
    tone: 'warning',
    dot: 'bg-warning-foreground',
    text: 'text-warning-foreground',
  },
}

const FALLBACK_STATUS: AttemptStatusMeta = {
  label: 'In Progress',
  variant: 'secondary',
  tone: 'warning',
  dot: 'bg-warning-foreground',
  text: 'text-warning-foreground',
}

export function attemptStatusMeta(status: string): AttemptStatusMeta {
  return STATUS_MAP[status] ?? FALLBACK_STATUS
}

function isTerminalAttemptStatus(status: string): boolean {
  return TERMINAL_ATTEMPT_STATUSES.has(status)
}

export function isSectionNotAttempted(
  band: number | null | undefined,
  attemptStatus?: string,
): boolean {
  return band == null && !!attemptStatus && isTerminalAttemptStatus(attemptStatus)
}

export function formatAttemptDuration(
  startedAt: string | null | undefined,
  finishedAt: string | null | undefined,
): string | null {
  if (!startedAt || !finishedAt) return null
  const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime()
  if (!Number.isFinite(ms) || ms < 0) return null
  const minutes = Math.round(ms / 60_000)
  if (minutes < 1) return '< 1 min'
  return `${minutes} min`
}

export function formatAttemptDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}
