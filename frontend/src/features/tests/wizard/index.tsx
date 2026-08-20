import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { fetchQuestions } from '@/lib/api/questions'
import { createTest, fetchAdminTest, publishTest, updateTest } from '@/lib/api/tests'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { cn } from '@/lib/utils'
import type { Question, Section, SectionSettings, Test } from '../data/schema'
import { WizardProgressBar } from './progress-bar'
import { StepInfo } from './step-info'
import type { StepInfoValues } from './step-info'
import { StepListening } from './step-listening'
import { StepReading } from './step-reading'
import { StepReview } from './step-review'
import { StepSpeaking } from './step-speaking'
import { StepWriting } from './step-writing'
import { computeWizardStatuses } from './wizard-status'

const TOTAL_STEPS = 6

function questionsFromGroups(sections: Section[]): Record<string, Question[]> {
  const map: Record<string, Question[]> = {}
  for (const s of sections) {
    if (s.type !== 'writing' && s.type !== 'speaking') continue
    const qs = (s.question_groups ?? []).flatMap((g) => g.questions ?? [])
    if (qs.length > 0) map[s.id] = qs
  }
  return map
}

function useWizardStatus(
  test: Test | null,
  sections: Section[],
  questionsMap: Record<string, Question[]>,
) {
  return useMemo(
    () => computeWizardStatuses(test, sections, questionsMap),
    [test, sections, questionsMap],
  )
}

type Props = {
  testId?: string
}

export function TestWizard({ testId: initialTestId }: Props) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [step, setStep] = useState(1)
  const [testId, setTestId] = useState<string | undefined>(initialTestId)
  const [fetchedQuestions, setFetchedQuestions] = useState<Record<string, Question[]>>({})

  const getStepInfoValues = useRef<(() => StepInfoValues) | null>(null)
  const validateStepInfo = useRef<(() => Promise<boolean>) | null>(null)

  const { data: testDetail, isLoading: testLoading, refetch: refetchTest } = useQuery({
    queryKey: ['tests', testId],
    queryFn: () => fetchAdminTest(testId!),
    enabled: !!testId,
  })

  const test: Test | null = testDetail ?? null
  const sections: Section[] = useMemo(() => testDetail?.sections ?? [], [testDetail])
  const sectionSettings: SectionSettings[] = useMemo(
    () => testDetail?.section_settings ?? [],
    [testDetail],
  )
  const questionsMap = useMemo(
    () => ({ ...questionsFromGroups(sections), ...fetchedQuestions }),
    [sections, fetchedQuestions],
  )

  useEffect(() => {
    if (sections.length === 0) return
    const targetSections = sections.filter((s) => s.type === 'writing' || s.type === 'speaking')
    if (targetSections.length === 0) return
    const load = async () => {
      const entries = await Promise.all(
        targetSections.map(async (s) => {
          try {
            const qs = await fetchQuestions(s.id)
            return [s.id, qs] as [string, Question[]]
          } catch {
            return [s.id, []] as [string, Question[]]
          }
        })
      )
      const loaded = Object.fromEntries(
        entries.filter(([, qs]) => qs.length > 0),
      )
      if (Object.keys(loaded).length > 0) setFetchedQuestions(loaded)
    }
    void load()
  }, [sections])

  const handleRefresh = async () => {
    const result = await refetchTest()
    const updatedSections = result.data?.sections ?? []
    const targetSections = updatedSections.filter((s) => s.type === 'writing' || s.type === 'speaking')
    if (targetSections.length > 0) {
      const entries = await Promise.all(
        targetSections.map(async (s) => {
          try {
            const qs = await fetchQuestions(s.id)
            return [s.id, qs] as [string, Question[]]
          } catch {
            return [s.id, []] as [string, Question[]]
          }
        })
      )
      const loaded = Object.fromEntries(
        entries.filter(([, qs]) => qs.length > 0),
      )
      if (Object.keys(loaded).length > 0) setFetchedQuestions(loaded)
    }
  }

  const stepStatuses = useWizardStatus(test, sections, questionsMap)

  // ── Create / update test ──────────────────────────────────────────────────

  const createMutation = useMutation({
    mutationFn: (values: StepInfoValues) =>
      createTest({
        title: values.title,
        book_name: values.book_name || null,
        test_number: values.test_number ?? 1,
        type: values.type,
        description: values.description || null,
        is_published: false,
      }),
    onSuccess: (created) => {
      setTestId(created.id)
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      toast.success('Test created as draft')
      setStep(2)
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      const apiStatus = axiosErr?.response?.status
      const detail = axiosErr?.response?.data?.detail
      if (apiStatus === 401) {
        toast.error('Session expired — please sign in again')
        void navigate({ to: '/login' })
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Failed to create test')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (values: StepInfoValues) =>
      updateTest(testId!, {
        title: values.title,
        book_name: values.book_name || null,
        test_number: values.test_number ?? 1,
        type: values.type,
        description: values.description || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests', testId] })
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      toast.success('Test info saved')
      setStep(2)
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      const apiStatus = axiosErr?.response?.status
      const detail = axiosErr?.response?.data?.detail
      if (apiStatus === 401) {
        toast.error('Session expired — please sign in again')
        void navigate({ to: '/login' })
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Failed to save test')
      }
    },
  })

  const [publishWarnings, setPublishWarnings] = useState<string[]>([])
  const [confirmPublishOpen, setConfirmPublishOpen] = useState(false)

  const publishMutation = useMutation({
    mutationFn: (force: boolean = false) => publishTest(testId!, force),
    onSuccess: () => {
      setConfirmPublishOpen(false)
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      queryClient.invalidateQueries({ queryKey: ['tests', testId] })
      toast.success('Test published!')
      void navigate({ to: '/tests' })
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: { errors?: string[] } } } })?.response?.data?.detail
      if (detail?.errors) {
        setPublishWarnings(detail.errors)
        setConfirmPublishOpen(true)
      } else {
        toast.error('Failed to publish')
      }
    },
  })

  const saveDraftMutation = useMutation<void, Error, void>({
    mutationFn: async () => {
      if (!testId) return
      await updateTest(testId, {})
    },
    onSuccess: () => toast.success('Draft saved'),
    onError: () => toast.error('Failed to save draft'),
  })

  // ── Navigation ────────────────────────────────────────────────────────────

  const handleNext = async () => {
    if (step === 1) {
      const isValid = await validateStepInfo.current?.()
      if (!isValid) return
      const values = getStepInfoValues.current!()
      if (!testId) {
        createMutation.mutate(values)
      } else {
        updateMutation.mutate(values)
      }
      return
    }
    setStep((s) => Math.min(s + 1, TOTAL_STEPS))
  }

  const handleBack = () => setStep((s) => Math.max(s - 1, 1))

  const handleStepClick = (target: number) => {
    if (target === step) return
    if (target > 1 && !testId) {
      toast.error('Save test info first to unlock other steps')
      return
    }
    setStep(target)
  }

  const isMutating =
    createMutation.isPending ||
    updateMutation.isPending ||
    publishMutation.isPending ||
    saveDraftMutation.isPending

  if (testLoading) {
    return (
      <div className='flex h-svh items-center justify-center'>
        <Loader2 className='size-8 animate-spin text-muted-foreground' />
      </div>
    )
  }

  const isLastStep = step === TOTAL_STEPS

  return (
    <>
      <Header>
        <div className='flex items-center gap-3'>
          <Button variant='ghost' size='sm' onClick={() => void navigate({ to: '/tests' })}>
            ← Tests
          </Button>
          <div className='flex items-center gap-2'>
            <span className='text-sm font-medium text-foreground'>
              {test?.title ?? (initialTestId ? 'Edit Test' : 'New Test')}
            </span>
            {test && (
              <Badge variant={test.is_published ? 'default' : 'secondary'} className='text-[10px]'>
                {test.is_published ? 'Published' : 'Draft'}
              </Badge>
            )}
          </div>
        </div>
      </Header>

      <Main>
        <div className={cn(
          'mx-auto space-y-6 py-6',
          step === 2 || step === 3 ? 'max-w-[1400px] px-4' : 'max-w-3xl',
        )}>
          <WizardProgressBar
            currentStep={step}
            statuses={stepStatuses}
            onStepClick={handleStepClick}
          />

          <div className={cn(
            'rounded-xl border border-border bg-card shadow-sm',
            step === 2 || step === 3 ? 'p-5' : 'p-8',
          )}>
            {step === 1 && (
              <StepInfo
                test={test}
                onFormReady={(getValues, validate) => {
                  getStepInfoValues.current = getValues
                  validateStepInfo.current = validate
                }}
              />
            )}

            {step === 2 && testId && (
              <StepListening
                testId={testId}
                sections={sections}
                sectionSettings={sectionSettings}
                onRefresh={handleRefresh}
              />
            )}

            {step === 3 && testId && (
              <StepReading
                testId={testId}
                sections={sections}
                sectionSettings={sectionSettings}
                onRefresh={handleRefresh}
              />
            )}

            {step === 4 && testId && (
              <StepWriting
                test={test}
                sections={sections}
                sectionSettings={sectionSettings}
                questionsMap={questionsMap}
                onRefresh={handleRefresh}
              />
            )}

            {step === 5 && testId && (
              <StepSpeaking
                testId={testId}
                sections={sections}
                sectionSettings={sectionSettings}
                questionsMap={questionsMap}
                onRefresh={handleRefresh}
              />
            )}

            {step === 6 && test && (
              <StepReview
                test={test}
                sections={sections}
                questionsMap={questionsMap}
              />
            )}
          </div>

          {/* Sticky footer */}
          <div className='sticky bottom-0 z-10 -mx-4 border-t border-border bg-background/95 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80'>
            <div className='mx-auto flex items-center justify-between' style={{ maxWidth: step === 2 || step === 3 ? '1400px' : '48rem' }}>
              <Button
                variant='outline'
                onClick={handleBack}
                disabled={step === 1 || isMutating}
              >
                ← Back
              </Button>

              <div className='flex items-center gap-2'>
                {testId && !isLastStep && (
                  <Button
                    variant='outline'
                    onClick={() => saveDraftMutation.mutate()}
                    disabled={isMutating}
                  >
                    {saveDraftMutation.isPending && <Loader2 className='mr-1 size-4 animate-spin' />}
                    Save Draft
                  </Button>
                )}

                {!isLastStep ? (
                  <Button onClick={() => void handleNext()} disabled={isMutating}>
                    {(createMutation.isPending || updateMutation.isPending) && (
                      <Loader2 className='mr-1 size-4 animate-spin' />
                    )}
                    Next →
                  </Button>
                ) : (
                  <div className='flex items-center gap-2'>
                    <Button
                      variant='outline'
                      onClick={() => saveDraftMutation.mutate()}
                      disabled={isMutating}
                    >
                      Save as Draft
                    </Button>
                    <Button
                      onClick={() => publishMutation.mutate(false)}
                      disabled={isMutating || !testId}
                    >
                      {publishMutation.isPending && <Loader2 className='mr-1 size-4 animate-spin' />}
                      Publish Test
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </Main>

      <AlertDialog open={confirmPublishOpen} onOpenChange={setConfirmPublishOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className='flex items-center gap-2'>
              <AlertTriangle className='size-5 text-warning-foreground' />
              Publish with warnings?
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className='space-y-2'>
                <p>This test has the following issues:</p>
                <ul className='list-disc space-y-1 pl-5 text-sm text-warning-foreground'>
                  {publishWarnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
                <p>Do you want to publish anyway?</p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => publishMutation.mutate(true)}
            >
              {publishMutation.isPending && <Loader2 className='mr-1 size-4 animate-spin' />}
              Publish anyway
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
