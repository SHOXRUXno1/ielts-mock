import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { overrideBand, type EvaluationJobRead } from '@/lib/api/attempts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { formatBand } from '../lib/band'

type AdminBandOverrideProps = {
  job: EvaluationJobRead
  onOverride: () => void
}

export function AdminBandOverride({ job, onOverride }: AdminBandOverrideProps) {
  const [overrideValue, setOverrideValue] = useState(
    job.teacher_override_band?.toString() ?? '',
  )
  const mutation = useMutation({
    mutationFn: () => overrideBand(job.id, parseFloat(overrideValue)),
    onSuccess: () => {
      toast.success('Band override saved')
      onOverride()
    },
  })

  return (
    <Card className='shadow-none'>
      <CardContent className='flex flex-wrap items-center justify-between gap-4 py-4'>
        <div>
          <p className='text-xs text-muted-foreground'>AI Band</p>
          <p className='text-2xl font-bold tabular-nums'>{formatBand(job.band_score)}</p>
          <Badge variant='secondary' className='mt-1 capitalize'>
            {job.status}
          </Badge>
        </div>
        <div className='flex items-end gap-2'>
          <div>
            <p className='mb-1 text-xs text-muted-foreground'>Teacher override</p>
            <Input
              type='number'
              min={0}
              max={9}
              step={0.5}
              className='w-24'
              value={overrideValue}
              onChange={(e) => setOverrideValue(e.target.value)}
            />
          </div>
          <Button
            size='sm'
            disabled={mutation.isPending || overrideValue === ''}
            onClick={() => mutation.mutate()}
          >
            Save
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
