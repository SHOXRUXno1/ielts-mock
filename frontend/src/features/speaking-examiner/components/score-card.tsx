import type {
  ConversationTurn,
  ExaminerScore,
} from '@/lib/api/speaking-examiner'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { resolveScoreDialogHistory } from '../lib/resolve-score-dialog-history'
import { TranscriptPanel } from './transcript-panel'

type Props = {
  score: ExaminerScore
  history?: ConversationTurn[]
}

function formatBand(band: number): string {
  return band.toFixed(1)
}

const CRITERIA = [
  { key: 'fluency_coherence' as const, label: 'Fluency & Coherence' },
  { key: 'lexical_resource' as const, label: 'Lexical Resource' },
  { key: 'grammatical_range' as const, label: 'Grammar' },
  { key: 'pronunciation' as const, label: 'Pronunciation' },
]

export function ScoreCard({ score, history }: Props) {
  const dialogHistory = resolveScoreDialogHistory(score, history)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Speaking Score</CardTitle>
      </CardHeader>
      <CardContent className='space-y-6'>
        <div className='text-center'>
          <p className='text-xs text-muted-foreground'>Overall Band</p>
          <p className='text-4xl font-bold text-primary'>
            {formatBand(score.overall_band)}
          </p>
        </div>

        <div className='space-y-4'>
          {CRITERIA.map(({ key, label }) => {
            const criterion = score[key]
            return (
              <div key={key} className='space-y-1'>
                <div className='flex items-center justify-between text-sm'>
                  <span className='font-medium'>{label}</span>
                  <span className='font-bold'>{formatBand(criterion.band)}</span>
                </div>
                <Progress value={(criterion.band / 9) * 100} className='h-2' />
                <p className='text-xs text-muted-foreground'>
                  {criterion.feedback}
                </p>
              </div>
            )
          })}
        </div>

        {score.corrections && score.corrections.length > 0 && (
          <div>
            <p className='mb-2 text-sm font-medium'>Corrections</p>
            <div className='space-y-3'>
              {score.corrections.map((c, i) => (
                <div
                  key={i}
                  className='rounded-md border bg-muted/30 p-3 text-sm'
                >
                  <p>
                    You said: <span className='italic'>&ldquo;{c.quote}&rdquo;</span>
                  </p>
                  <p className='mt-1 text-primary'>
                    Better: <span className='font-medium'>&ldquo;{c.better}&rdquo;</span>
                  </p>
                  {c.note && (
                    <p className='mt-1 text-xs text-muted-foreground'>{c.note}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {score.example_phrases && score.example_phrases.length > 0 && (
          <div>
            <p className='mb-2 text-sm font-medium'>Useful phrases you could use</p>
            <div className='flex flex-wrap gap-2'>
              {score.example_phrases.map((phrase, i) => (
                <span
                  key={i}
                  className='rounded-full border bg-background px-3 py-1 text-xs'
                >
                  {phrase}
                </span>
              ))}
            </div>
          </div>
        )}

        {score.strengths.length > 0 && (
          <div>
            <p className='mb-1 text-sm font-medium'>Strengths</p>
            <ul className='list-inside list-disc space-y-1 text-sm text-muted-foreground'>
              {score.strengths.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}

        {score.improvements.length > 0 && (
          <div>
            <p className='mb-1 text-sm font-medium'>Areas for Improvement</p>
            <ul className='list-inside list-disc space-y-1 text-sm text-muted-foreground'>
              {score.improvements.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}

        {dialogHistory.length > 0 && (
          <div>
            <p className='mb-2 text-sm font-medium'>Full transcript</p>
            <div className='max-h-64 overflow-y-auto scroll-smooth rounded-lg'>
              <TranscriptPanel history={dialogHistory} autoScroll={false} />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
