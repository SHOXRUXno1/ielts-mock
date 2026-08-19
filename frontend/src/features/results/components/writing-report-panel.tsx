import type { EvaluationJobRead } from '@/lib/api/attempts'
import { EvaluationProgressCard, jobPhase } from '../evaluation-progress'
import { writingBandFromJobs, WritingFeedbackPanel } from '../writing-feedback-panel'
import { AdminBandOverride } from './admin-band-override'
import { ReportHeader } from './report-header'

type WritingReportPanelProps = {
  jobs: EvaluationJobRead[]
  isAdmin: boolean
  onOverride: () => void
}

export function WritingReportPanel({
  jobs,
  isAdmin,
  onOverride,
}: WritingReportPanelProps) {
  const job = jobs.find((j) => j.status === 'done') ?? jobs[0]
  const phase = jobPhase(jobs)
  const band = writingBandFromJobs(jobs) ?? job?.band_score ?? job?.teacher_override_band

  return (
    <div className='space-y-4'>
      <ReportHeader
        skill='writing'
        band={band}
        action={
          isAdmin && job ? (
            <AdminBandOverride job={job} onOverride={onOverride} />
          ) : undefined
        }
      />
      {(phase === 'queued' || phase === 'scoring' || phase === 'failed') && (
        <EvaluationProgressCard jobs={jobs} section='writing' />
      )}
      <WritingFeedbackPanel jobs={jobs} />
    </div>
  )
}
