import type { ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

export type ExaminerLoadingStage = 'video' | 'examiner' | 'starting'

type Props = {
  stage?: ExaminerLoadingStage
  /** @deprecated Prefer `stage="video"`. Kept for call-site compatibility. */
  simliConnecting?: boolean
  action?: ReactNode
}

const STAGE_LABEL: Record<ExaminerLoadingStage, string> = {
  video: 'Connecting video…',
  examiner: 'Preparing examiner…',
  starting: 'Starting your speaking test…',
}

function resolveStage(
  stage: ExaminerLoadingStage | undefined,
  simliConnecting: boolean | undefined,
): ExaminerLoadingStage {
  if (stage) return stage
  return simliConnecting ? 'video' : 'examiner'
}

export function ExaminerLoadingOverlay({
  stage,
  simliConnecting = false,
  action,
}: Props) {
  const resolved = resolveStage(stage, simliConnecting)
  const label = STAGE_LABEL[resolved]

  return (
    <div
      role='status'
      aria-live='polite'
      aria-busy={!action}
      className='absolute inset-0 z-10 flex flex-col items-center justify-center bg-background/60 p-4 backdrop-blur-md transition-opacity duration-300'
    >
      <div className='flex w-full max-w-sm flex-col items-center gap-4 rounded-2xl border border-white/15 bg-white/10 px-6 py-8 shadow-xl dark:border-white/10 dark:bg-white/5'>
        {action ? (
          <div className='w-full'>{action}</div>
        ) : (
          <>
            <Loader2 className='size-10 animate-spin text-primary' aria-hidden='true' />
            <p className='text-center text-lg font-semibold text-foreground'>{label}</p>
          </>
        )}
      </div>
    </div>
  )
}
