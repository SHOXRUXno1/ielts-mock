import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, Loader2, Mic } from 'lucide-react'
import { toast } from 'sonner'
import {
  getIntroGreetingPhrase,
  isSpeakingAbortError,
} from '@/lib/api/speaking-examiner'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useMicCheck } from '@/features/speaking-examiner/hooks/use-mic-check'
import { markSpeakingAutostartGesture } from '@/features/speaking-examiner/lib/user-activation'
import { useTakeTest } from '../../take/take-test-context'

type PrewarmStatus = 'pending' | 'ok' | 'failed'

/**
 * Interstitial screen shown after Writing is sealed and before Speaking starts.
 *
 * Nothing on the server has moved yet — Speaking is still `not_started`, so no
 * timer is ticking. The 20-minute safety cap only starts on `enterSection`,
 * which happens on the button click. That means the student may spend as long
 * as they like on this screen without losing time.
 *
 * On mount we warm the intro-greeting TTS cache so the first examiner turn
 * plays without a synth round-trip.
 */
export function SpeakingReadyGate() {
  const ctx = useTakeTest()
  const { micStatus, checkMicrophone } = useMicCheck()
  const [prewarm, setPrewarm] = useState<PrewarmStatus>('pending')
  const [starting, setStarting] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    const ctrl = new AbortController()
    abortRef.current = ctrl
    getIntroGreetingPhrase(ctrl.signal)
      .then(() => {
        if (!ctrl.signal.aborted) setPrewarm('ok')
      })
      .catch((err) => {
        if (ctrl.signal.aborted || isSpeakingAbortError(err)) return
        setPrewarm('failed')
      })
    return () => {
      ctrl.abort()
    }
  }, [])

  const handleStart = async () => {
    if (starting) return
    setStarting(true)
    markSpeakingAutostartGesture()
    try {
      await ctx.enterSection('speaking')
      // Component will unmount once progress refetch flips speaking → active.
    } catch {
      setStarting(false)
      toast.error('Failed to start Speaking — please try again')
    }
  }

  const prewarmLabel =
    prewarm === 'ok'
      ? 'Examiner voice ready'
      : prewarm === 'failed'
        ? 'Voice will be prepared when you start'
        : 'Preparing examiner voice…'

  return (
    <div className='flex h-full items-center justify-center overflow-y-auto px-4 py-10'>
      <Card className='w-full max-w-xl'>
        <CardHeader>
          <CardTitle>Writing complete — Speaking is next</CardTitle>
          <CardDescription>
            You will have a live conversation with AI examiner James Harrison.
            The test follows the official IELTS Speaking format: Part 1
            (personal questions), Part 2 (long turn with cue card), and Part 3
            (abstract discussion). There is no timer on this screen — take a
            breath and start when you are ready.
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div
            className='flex items-center gap-2 text-sm text-slate-600'
            aria-live='polite'
          >
            {prewarm === 'pending' ? (
              <Loader2 className='size-4 animate-spin text-slate-400' />
            ) : prewarm === 'ok' ? (
              <CheckCircle2 className='size-4 text-emerald-600' />
            ) : (
              <span className='inline-block size-2 rounded-full bg-amber-500' />
            )}
            <span>{prewarmLabel}</span>
          </div>

          <Button
            variant='outline'
            className='w-full'
            disabled={micStatus === 'checking' || starting}
            onClick={() => {
              void checkMicrophone()
            }}
          >
            <Mic className='mr-2 size-4' />
            {micStatus === 'checking'
              ? 'Checking microphone…'
              : micStatus === 'ok'
                ? 'Microphone OK'
                : micStatus === 'denied'
                  ? 'Microphone blocked — check browser settings'
                  : 'Check microphone'}
          </Button>

          <Button
            size='lg'
            className='min-h-14 w-full'
            onClick={handleStart}
            disabled={starting}
          >
            {starting ? (
              <>
                <Loader2 className='mr-2 size-4 animate-spin' />
                Starting…
              </>
            ) : (
              <>
                <Mic className='mr-2 size-4' />
                Start Speaking Test
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
