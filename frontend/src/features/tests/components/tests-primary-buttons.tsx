import { Link } from '@tanstack/react-router'
import { FileUp, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function TestsPrimaryButtons() {
  return (
    <div className='flex items-center gap-2'>
      <Button variant='outline' asChild>
        <Link to='/tests/import'>
          <FileUp />
          Import from Excel
        </Link>
      </Button>
      <Button asChild>
        <Link to='/tests/create'>
          <Plus />
          New Test
        </Link>
      </Button>
    </div>
  )
}
