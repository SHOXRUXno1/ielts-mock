import { Loader2 } from 'lucide-react'

type Props = {
  simliConnecting?: boolean
}

export function ExaminerLoadingOverlay({ simliConnecting = false }: Props) {
  const label = simliConnecting
    ? 'Connecting video…'
    : 'Preparing examiner…'

  return (
    <div
      role='status'
      aria-live='polite'
      aria-busy='true'
      className='absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-background/80 backdrop-blur-sm transition-opacity duration-300'
    >
      <Loader2 className='size-10 animate-spin text-primary' aria-hidden='true' />
      <p className='text-lg font-semibold'>{label}</p>
    </div>
  )
}
