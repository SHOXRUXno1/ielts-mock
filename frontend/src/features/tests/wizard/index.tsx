import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { fetchQuestions } from '@/lib/api/questions'
import { createTest, fetchTest, publishTest, updateTest } from '@/lib/api/tests'
import { Button } from '@/components/ui/button'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import type { Question, Section, Test } from '../data/schema'
import { WizardProgressBar } from './progress-bar'
import { StepInfo, type StepInfoValues } from './step-info'
import { StepListening } from './step-listening'
import { StepReading } from './step-reading'
import { StepReview } from './step-review'
import { StepSpeaking } from './step-speaking'
import { StepWriting } from './step-writing'

const TOTAL_STEPS = 6
const STEP_TITLES = ['Test Info', 'Listening', 'Reading', 'Writing', 'Speaking', 'Review']

type Props = {
  testId?: string
}

export function TestWizard({ testId: initialTestId }: Props) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [step, setStep] = useState(1)
  const [testId, setTestId] = useState<string | undefined>(initialTestId)
  const [questionsMap, setQuestionsMap] = useState<Record<string, Question[]>>({})

  // Callback refs for step 1 form validation
  const getStepInfoValues = useRef<(() => StepInfoValues) | null>(null)
  const validateStepInfo = useRef<(() => Promise<boolean>) | null>(null)

  const { data: testDetail, isLoading: testLoading, refetch: refetchTest } = useQuery({
    queryKey: ['tests', testId],
    queryFn: () => fetchTest(testId!),
    enabled: !!testId,
  })

  const test: Test | null = testDetail ?? null
  const sections: Section[] = useMemo(() => testDetail?.sections ?? [], [testDetail])

  // Load questions for writing and speaking sections (reading/listening use question_groups)
  useEffect(() => {
    if (sections.length === 0) return
    const targetSections = sections.filter((s) => s.type === 'writing' || s.type === 'speaking')
    if (targetSections.length === 0) return
    const load = async () => {
      const entries = await Promise.all(
        targetSections.map(async (s) => {
          const qs = await fetchQuestions(s.id)
          return [s.id, qs] as [string, Question[]]
        })
      )
      setQuestionsMap(Object.fromEntries(entries))
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
          const qs = await fetchQuestions(s.id)
          return [s.id, qs] as [string, Question[]]
        })
      )
      setQuestionsMap(Object.fromEntries(entries))
    }
  }

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
        void navigate({ to: '/sign-in' })
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
        void navigate({ to: '/sign-in' })
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Failed to save test')
      }
    },
  })

  const publishMutation = useMutation({
    mutationFn: () => publishTest(testId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      queryClient.invalidateQueries({ queryKey: ['tests', testId] })
      toast.success('Test published!')
      void navigate({ to: '/tests' })
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: { errors?: string[] } } } })?.response?.data?.detail
      if (detail?.errors) {
        detail.errors.forEach((e: string) => toast.error(e))
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

  const isMutating =
    createMutation.isPending ||
    updateMutation.isPending ||
    publishMutation.isPending ||
    saveDraftMutation.isPending

  if (testLoading) {
    return (
      <div className='flex h-svh items-center justify-center'>
        <Loader2 className='size-8 animate-spin text-slate-400' />
      </div>
    )
  }

  const isLastStep = step === TOTAL_STEPS
  const stepTitle = STEP_TITLES[step - 1]

  return (
    <>
      <Header>
        <div className='flex items-center gap-3'>
          <Button variant='ghost' size='sm' onClick={() => void navigate({ to: '/tests' })}>
            ← Tests
          </Button>
          <span className='text-sm font-medium text-slate-600'>
            {initialTestId ? 'Edit Test' : 'Create Test'} — {stepTitle}
          </span>
        </div>
      </Header>

      <Main>
        <div className='mx-auto max-w-3xl space-y-8 py-8'>
          {/* Progress */}
          <WizardProgressBar currentStep={step} totalSteps={TOTAL_STEPS} />

          {/* Content */}
          <div className='rounded-xl border border-slate-200 bg-white p-8 shadow-sm'>
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
                onRefresh={handleRefresh}
              />
            )}

            {step === 3 && testId && (
              <StepReading
                testId={testId}
                sections={sections}
                onRefresh={handleRefresh}
              />
            )}

            {step === 4 && testId && (
              <StepWriting
                test={test}
                sections={sections}
                questionsMap={questionsMap}
                onRefresh={handleRefresh}
              />
            )}

            {step === 5 && testId && (
              <StepSpeaking
                testId={testId}
                sections={sections}
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

          {/* Footer */}
          <div className='flex items-center justify-between'>
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
                    onClick={() => publishMutation.mutate()}
                    disabled={isMutating || !testId}
                  >
                    {publishMutation.isPending && <Loader2 className='mr-1 size-4 animate-spin' />}
                    Publish Test ✓
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </Main>
    </>
  )
}
