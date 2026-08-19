import { useNavigate, useRouter } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

type GeneralErrorProps = React.HTMLAttributes<HTMLDivElement> & {
  minimal?: boolean
  error?: unknown
}

function errorMessage(error: unknown): string | null {
  if (error instanceof Error && error.message) return error.message
  if (typeof error === 'string' && error) return error
  return null
}

export function GeneralError({
  className,
  minimal = false,
  error,
}: GeneralErrorProps) {
  const navigate = useNavigate()
  const { history } = useRouter()
  const detail = errorMessage(error)
  return (
    <div className={cn('h-svh w-full', className)}>
      <div className='m-auto flex h-full w-full flex-col items-center justify-center gap-2'>
        {!minimal && (
          <h1 className='text-[7rem] leading-tight font-bold'>500</h1>
        )}
        <span className='font-medium'>Oops! Something went wrong {`:')`}</span>
        <p className='text-center text-muted-foreground'>
          We apologize for the inconvenience. <br /> Please try again later.
        </p>
        {detail && (
          <p className='mt-2 max-w-lg px-4 text-center font-mono text-xs break-words text-muted-foreground'>
            {detail}
          </p>
        )}
        {!minimal && (
          <div className='mt-6 flex gap-4'>
            <Button variant='outline' onClick={() => history.go(-1)}>
              Go Back
            </Button>
            <Button onClick={() => navigate({ to: '/' })}>Back to Home</Button>
          </div>
        )}
      </div>
    </div>
  )
}
