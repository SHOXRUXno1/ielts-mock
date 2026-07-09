import Lottie from 'lottie-react'
import teacherAnimation from '@/assets/animations/teacher.json'
import { cn } from '@/lib/utils'

type Props = {
  isSpeaking: boolean
  isListening: boolean
  className?: string
}

export function LottieAvatar({ isSpeaking, isListening, className }: Props) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-2xl bg-neutral-900 shadow-lg',
        'size-[200px] md:size-[300px]',
        className,
      )}
    >
      <Lottie
        animationData={teacherAnimation}
        loop
        autoplay
        className='size-full object-cover'
      />

      {isListening && (
        <div className='absolute bottom-2 right-2 flex items-center gap-1 rounded-full bg-red-600/80 px-2 py-0.5'>
          <span className='size-1.5 animate-pulse rounded-full bg-white' />
          <span className='text-[10px] font-medium text-white'>REC</span>
        </div>
      )}

      {isSpeaking && (
        <div className='absolute bottom-2 left-2 flex items-center gap-1 rounded-full bg-blue-600/80 px-2 py-0.5'>
          <span className='size-1.5 animate-pulse rounded-full bg-white' />
          <span className='text-[10px] font-medium text-white'>Speaking</span>
        </div>
      )}
    </div>
  )
}
