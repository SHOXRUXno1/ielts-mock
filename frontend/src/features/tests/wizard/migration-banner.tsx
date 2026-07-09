import { useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { normalizeSections } from '@/lib/api/tests'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

type Props = {
  testId: string
  message: string
  onRefresh: () => void
}

export function MigrationBanner({ testId, message, onRefresh }: Props) {
  const [loading, setLoading] = useState(false)

  const handleMigrate = async () => {
    setLoading(true)
    try {
      await normalizeSections(testId)
      toast.success('Sections updated to IELTS standard')
      onRefresh()
    } catch {
      toast.error('Migration failed — please try again')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Alert className='mb-4 border-amber-200 bg-amber-50'>
      <AlertTriangle className='size-4 text-amber-600' />
      <AlertDescription className='flex items-center justify-between gap-4'>
        <span className='text-sm text-amber-800'>{message}</span>
        <Button
          size='sm'
          variant='outline'
          className='shrink-0 border-amber-300 text-amber-800 hover:bg-amber-100'
          onClick={handleMigrate}
          disabled={loading}
        >
          {loading && <Loader2 className='mr-1 size-3.5 animate-spin' />}
          Migrate to IELTS standard
        </Button>
      </AlertDescription>
    </Alert>
  )
}
