import type { AnswerRead, AttemptDetailRead } from '@/lib/api/attempts'
import { answerOutcome, groupAnswersByPart } from './answers'
import { formatBand } from './band'
import { SKILL_BAND_FIELD, SKILL_KEYS, type SkillKey } from './skill'

export type ScoredSkill = {
  key: SkillKey
  band: number
}

export type ProfileInsights = {
  scored: ScoredSkill[]
  strongest: ScoredSkill | null
  weakest: ScoredSkill | null
  spread: number | null
  even: boolean | null
  rawAverage: number | null
  roundedAverage: number | null
}

export type PartAccuracy = {
  key: string
  label: string
  correct: number
  incorrect: number
  skipped: number
  total: number
}

export function scoredSkills(attempt: AttemptDetailRead): ScoredSkill[] {
  return SKILL_KEYS.map((key) => ({
    key,
    band: attempt[SKILL_BAND_FIELD[key]],
  })).filter((row): row is ScoredSkill => row.band != null)
}

function nearestHalf(value: number): number {
  return Math.round(value * 2) / 2
}

export function profileInsights(attempt: AttemptDetailRead): ProfileInsights {
  const scored = scoredSkills(attempt)
  const strongest = scored.reduce<ScoredSkill | null>(
    (best, row) => (!best || row.band > best.band ? row : best),
    null,
  )
  const weakest = scored.reduce<ScoredSkill | null>(
    (worst, row) => (!worst || row.band < worst.band ? row : worst),
    null,
  )
  const spread =
    strongest && weakest && scored.length > 1
      ? strongest.band - weakest.band
      : null
  const even = spread == null ? null : spread <= 1
  const rawAverage =
    scored.length >= 3
      ? scored.reduce((sum, row) => sum + row.band, 0) / scored.length
      : null
  const roundedAverage = rawAverage == null ? null : nearestHalf(rawAverage)

  return {
    scored,
    strongest,
    weakest: scored.length > 1 ? weakest : null,
    spread,
    even,
    rawAverage,
    roundedAverage,
  }
}

export function formatRoundingExample(insights: ProfileInsights): string | null {
  if (insights.rawAverage == null || insights.roundedAverage == null) return null
  return `${formatBand(insights.rawAverage)} → ${formatBand(insights.roundedAverage)}`
}

export function accuracyByPart(
  answers: AnswerRead[],
  skill: 'listening' | 'reading',
): PartAccuracy[] {
  const scored = answers.filter(
    (answer) => answer.is_correct !== null && answer.section?.type === skill,
  )
  return groupAnswersByPart(scored, skill).map((group) => {
    let correct = 0
    let incorrect = 0
    let skipped = 0
    for (const answer of group.answers) {
      const outcome = answerOutcome(answer)
      if (outcome === 'correct') correct += 1
      else if (outcome === 'skipped') skipped += 1
      else incorrect += 1
    }
    return {
      key: group.key,
      label: group.label,
      correct,
      incorrect,
      skipped,
      total: group.answers.length,
    }
  })
}
