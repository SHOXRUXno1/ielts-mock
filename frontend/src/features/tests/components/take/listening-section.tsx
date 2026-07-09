import { useEffect, useRef, useState } from 'react'
import { AlertCircle, Pause, Play, Volume2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { mediaUrl } from '@/lib/api/attempts'
import type { Question, QuestionGroup, Section } from '../../data/schema'
import {
  CompoundMatchingDropdown,
  CompoundMultiSelectPair,
  CompoundTableCompletion,
  MatchingLetterRenderer,
  NoteCompletionCard,
  QuestionRendererWithFlag,
  type NotesSpec,
  type TableSpec,
} from './question-renderer'

// ── Runtime group type (used for both legacy fallback and API-based groups) ───

type RenderGroup = {
  type: string
  questions: Question[]
  instruction?: string
  options?: string[]
}

// ── Legacy runtime-grouping (fallback when no question_group_id) ──────────────

const LISTENING_INSTRUCTIONS: Record<string, string> = {
  mcq: 'Choose the correct letter, A, B, C or D.',
  true_false_ng:
    'Do the following statements agree with the information? Choose TRUE, FALSE or NOT GIVEN.',
  gap_fill:
    'Complete the notes below. Write ONE WORD AND/OR A NUMBER for each answer.',
  matching: 'Match each statement with the correct option.',
  map_labeling: 'Label the map below. Choose ONE WORD ONLY from the recording.',
  table: 'Complete the table below. Write ONE WORD AND/OR A NUMBER for each answer.',
  notes_card: 'Complete the notes below. Write ONE WORD ONLY for each answer.',
  matching_dropdown: '',
  multi_select_pair: '',
}

function groupQuestionsLegacy(sorted: Question[]): RenderGroup[] {
  if (sorted.length === 0) return []
  const groups: RenderGroup[] = []
  let i = 0

  while (i < sorted.length) {
    const q = sorted[i]
    const tableId = q.content?.table_id as string | undefined
    const notesId = q.content?.notes_id as string | undefined
    const matchingId = q.content?.matching_id as string | undefined
    const pairId = q.content?.pair_id as string | undefined

    if (matchingId) {
      const group: Question[] = [q]
      let j = i + 1
      while (j < sorted.length && (sorted[j].content?.matching_id as string | undefined) === matchingId) {
        group.push(sorted[j])
        j++
      }
      groups.push({ type: 'matching_dropdown', questions: group })
      i = j
    } else if (pairId) {
      const group: Question[] = [q]
      let j = i + 1
      while (j < sorted.length && (sorted[j].content?.pair_id as string | undefined) === pairId) {
        group.push(sorted[j])
        j++
      }
      groups.push({ type: 'multi_select_pair', questions: group })
      i = j
    } else if (tableId) {
      const group: Question[] = [q]
      let j = i + 1
      while (j < sorted.length && (sorted[j].content?.table_id as string | undefined) === tableId) {
        group.push(sorted[j])
        j++
      }
      groups.push({ type: 'table', questions: group })
      i = j
    } else if (notesId) {
      const group: Question[] = [q]
      let j = i + 1
      while (j < sorted.length && (sorted[j].content?.notes_id as string | undefined) === notesId) {
        group.push(sorted[j])
        j++
      }
      groups.push({ type: 'notes_card', questions: group })
      i = j
    } else {
      const group: Question[] = [q]
      let j = i + 1
      while (
        j < sorted.length &&
        sorted[j].question_type === q.question_type &&
        !(sorted[j].content?.table_id as string | undefined) &&
        !(sorted[j].content?.notes_id as string | undefined) &&
        !(sorted[j].content?.matching_id as string | undefined) &&
        !(sorted[j].content?.pair_id as string | undefined)
      ) {
        group.push(sorted[j])
        j++
      }
      const legacyInstruction =
        (q.content?.instruction as string | undefined) ?? LISTENING_INSTRUCTIONS[q.question_type] ?? ''
      groups.push({ type: q.question_type, questions: group, instruction: legacyInstruction })
      i = j
    }
  }

  return groups
}

// ── Build render-groups from API QuestionGroup model ─────────────────────────

function buildRenderGroups(apiGroups: QuestionGroup[], questions: Question[]): RenderGroup[] {
  if (apiGroups.length === 0) {
    return groupQuestionsLegacy([...questions].sort((a, b) => a.order - b.order))
  }

  const result: RenderGroup[] = []

  for (const group of apiGroups) {
    const groupQs = [...group.questions].sort((a, b) => a.order - b.order)
    if (groupQs.length === 0) continue

    const firstMatchingId = groupQs[0].content?.matching_id as string | undefined
    const firstPairId = groupQs[0].content?.pair_id as string | undefined
    const firstTableId = groupQs[0].content?.table_id as string | undefined
    const firstNotesId = groupQs[0].content?.notes_id as string | undefined

    const opts = Array.isArray((group.options_shared as { options?: unknown[] } | null)?.options)
      ? (group.options_shared as { options: string[] }).options
      : undefined

    if (firstMatchingId) {
      result.push({ type: 'matching_dropdown', questions: groupQs })
    } else if (firstPairId) {
      result.push({ type: 'multi_select_pair', questions: groupQs })
    } else if (firstTableId) {
      result.push({ type: 'table', questions: groupQs })
    } else if (firstNotesId) {
      result.push({ type: 'notes_card', questions: groupQs })
    } else if (
      group.question_type === 'matching_information' ||
      group.question_type === 'matching_features'
    ) {
      const instruction = group.instruction || ''
      result.push({ type: group.question_type, questions: groupQs, instruction, options: opts ?? [] })
    } else {
      const instruction = group.instruction ||
        (groupQs[0]?.content?.instruction as string | undefined) ||
        LISTENING_INSTRUCTIONS[group.question_type] ||
        ''
      result.push({ type: group.question_type, questions: groupQs, instruction, options: opts })
    }
  }

  // Handle orphan questions (no question_group_id set)
  const groupedIds = new Set(apiGroups.flatMap((g) => g.questions.map((q) => q.id)))
  const orphans = questions.filter((q) => !groupedIds.has(q.id)).sort((a, b) => a.order - b.order)
  if (orphans.length > 0) {
    result.push(...groupQuestionsLegacy(orphans))
  }

  return result
}

// ── Group header ──────────────────────────────────────────────────────────────

function ListeningGroupHeader({ group }: { group: RenderGroup }) {
  const orders = group.questions.map((q) => q.order)
  const minQ = Math.min(...orders)
  const maxQ = Math.max(...orders)
  const rangeLabel = minQ === maxQ ? `Question ${minQ}` : `Questions ${minQ}–${maxQ}`

  const COMPOUND_TYPES = new Set([
    'notes_card', 'table', 'matching_dropdown', 'multi_select_pair',
    'matching_information', 'matching_features',
  ])
  const rawInstruction = COMPOUND_TYPES.has(group.type) ? '' : (group.instruction ?? '')
  const sectionTitle = (group.questions[0]?.content?.section_title as string | undefined) ?? ''

  return (
    <div className='mb-4'>
      <p className='text-[13px] font-bold text-[#111827]'>{rangeLabel}</p>
      {rawInstruction &&
        rawInstruction.split('\n').map((line, i) => (
          <p key={i} className='mt-0.5 text-[13px] text-[#6b7280]'>
            {line}
          </p>
        ))}
      {sectionTitle && (
        <p className='mt-2 text-center text-[15px] font-bold text-slate-900'>
          {sectionTitle}
        </p>
      )}
      {group.options && group.options.length > 0 && (
        <div className='mt-3 flex flex-wrap gap-1.5'>
          {group.options.map((opt, i) => (
            <span
              key={i}
              className='rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-[12px] text-slate-700'
            >
              {opt}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

type Props = {
  section: Section
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  /** Index of the active part (0-based), controlled from outside */
  activePart?: number
  /** All listening sections for the part switcher (Part 1/2/3/4 tabs) */
  allSections?: Section[]
  /** Callback to switch to a different listening section/part */
  onSwitchSection?: (sectionId: string) => void
  /** Show audioscript — only in review/admin mode, hidden during live test */
  reviewMode?: boolean
  flagged?: Set<string>
  onToggleFlag?: (id: string) => void
}

function getPartNumber(q: Question): number {
  const p = q.content.part
  if (typeof p === 'number') return p
  return 1
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ── Custom audio player ──────────────────────────────────────────────────────

function AudioPlayer({ src }: { src: string }) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [hasPlayed, setHasPlayed] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)

  useEffect(() => {
    const el = audioRef.current
    if (!el) return
    const onLoaded = () => setDuration(el.duration || 0)
    const onTime = () => setCurrentTime(el.currentTime)
    const onEnded = () => { setIsPlaying(false); setHasPlayed(true) }
    const onPause = () => setIsPlaying(false)
    const onPlay = () => setIsPlaying(true)
    el.addEventListener('loadedmetadata', onLoaded)
    el.addEventListener('timeupdate', onTime)
    el.addEventListener('ended', onEnded)
    el.addEventListener('pause', onPause)
    el.addEventListener('play', onPlay)
    return () => {
      el.removeEventListener('loadedmetadata', onLoaded)
      el.removeEventListener('timeupdate', onTime)
      el.removeEventListener('ended', onEnded)
      el.removeEventListener('pause', onPause)
      el.removeEventListener('play', onPlay)
    }
  }, [])

  const togglePlay = () => {
    const el = audioRef.current
    if (!el || hasPlayed) return
    if (isPlaying) {
      el.pause()
    } else {
      el.play()
    }
  }

  const handleVolume = (v: number) => {
    setVolume(v)
    if (audioRef.current) audioRef.current.volume = v
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className='rounded-xl border border-slate-200 bg-white p-5'>
      <audio ref={audioRef} src={src} preload='metadata' />

      <div className='flex items-center gap-4'>
        {/* Play / Pause */}
        <button
          type='button'
          onClick={togglePlay}
          disabled={hasPlayed}
          title={hasPlayed ? 'Audio already played' : isPlaying ? 'Pause' : 'Play'}
          className={cn(
            'flex size-10 shrink-0 items-center justify-center rounded-full transition-colors',
            hasPlayed
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
              : 'bg-slate-900 text-white hover:bg-slate-700',
          )}
        >
          {isPlaying ? (
            <Pause className='size-4' />
          ) : (
            <Play className='size-4 translate-x-0.5' />
          )}
        </button>

        <div className='flex flex-1 flex-col gap-1.5'>
          {/* Progress bar */}
          <div className='relative h-1.5 w-full overflow-hidden rounded-full bg-slate-200'>
            <div
              className='h-full rounded-full bg-slate-900 transition-all'
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Times */}
          <div className='flex justify-between text-xs text-slate-400'>
            <span>{formatTime(currentTime)}</span>
            <span>{duration > 0 ? formatTime(duration) : '--:--'}</span>
          </div>
        </div>

        {/* Volume */}
        <div className='flex items-center gap-1.5'>
          <Volume2 className='size-4 shrink-0 text-slate-400' />
          <input
            type='range'
            min={0}
            max={1}
            step={0.05}
            value={volume}
            onChange={(e) => handleVolume(Number(e.target.value))}
            className='w-16 accent-slate-800'
          />
        </div>
      </div>

      {hasPlayed && (
        <p className='mt-3 text-xs text-amber-600'>
          Audio has been played. You cannot replay it in a real exam.
        </p>
      )}
    </div>
  )
}

// ── Main section ─────────────────────────────────────────────────────────────

export function ListeningSection({
  section,
  questions,
  answers,
  onAnswer,
  activePart,
  allSections,
  onSwitchSection,
  reviewMode = false,
  flagged,
  onToggleFlag,
}: Props) {
  const sortedQuestions = [...questions].sort((a, b) => a.order - b.order)

  const parts = Array.from(
    new Set(sortedQuestions.map(getPartNumber)),
  ).sort((a, b) => a - b)

  // If caller controls activePart (0-based index), convert to part number
  const activePartNumber =
    activePart !== undefined && parts.length > 0
      ? (parts[activePart] ?? parts[0])
      : (parts[0] ?? 1)

  const visibleQuestions =
    parts.length > 1
      ? sortedQuestions.filter((q) => getPartNumber(q) === activePartNumber)
      : sortedQuestions

  // Build render groups: prefer section.question_groups, fallback to runtime grouping
  const apiGroups = section.question_groups ?? []
  // Filter API groups whose questions are in the visible set
  const visibleIds = new Set(visibleQuestions.map((q) => q.id))
  const visibleApiGroups = apiGroups.filter((g) =>
    g.questions.some((q) => visibleIds.has(q.id))
  ).map((g) => ({
    ...g,
    questions: g.questions.filter((q) => visibleIds.has(q.id)),
  }))

  const renderGroups = buildRenderGroups(visibleApiGroups, visibleQuestions)

  return (
    <div className='flex h-full'>
      {/* ── Left 50%: audio + audioscript ───────────────────────────── */}
      <div className='w-1/2 overflow-y-auto bg-white px-8 py-8'>
        {/* Part switcher tabs — only shown when multiple listening sections exist */}
        {allSections && allSections.length > 1 && onSwitchSection && (
          <div className='mb-6 flex gap-2'>
            {allSections.map((s, i) => {
              const isActive = s.id === section.id
              return (
                <button
                  key={s.id}
                  type='button'
                  onClick={() => onSwitchSection(s.id)}
                  className={cn(
                    'min-w-[52px] rounded-md border px-4 py-1.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'border-slate-900 bg-slate-900 text-white'
                      : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
                  )}
                >
                  Part {i + 1}
                </button>
              )
            })}
          </div>
        )}

        {/* PART heading */}
        <h2
          style={{ fontSize: '22px', fontWeight: 800, letterSpacing: '-0.3px' }}
          className='mb-6 uppercase text-slate-900'
        >
          Part {activePartNumber}
        </h2>

        {section.audio_url ? (
          <AudioPlayer src={mediaUrl(section.audio_url)} />
        ) : (
          <div className='flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600'>
            <AlertCircle className='size-4 shrink-0' />
            No audio file has been uploaded for this section.
          </div>
        )}

        {/* Audioscript — only visible in review/admin mode, never during the test */}
        {section.passage && reviewMode && (
          <details className='mt-6 rounded-lg border border-slate-200'>
            <summary className='cursor-pointer select-none px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50'>
              Audioscript
            </summary>
            <div
              className='px-4 pb-4 pt-2 text-[14px] leading-relaxed text-slate-700'
              style={{ fontFamily: 'Georgia, serif' }}
            >
              {section.passage}
            </div>
          </details>
        )}
      </div>

      {/* ── Right 50%: questions ─────────────────────────────────────── */}
      <div className='w-1/2 overflow-y-auto border-l border-slate-200 bg-white px-8 py-8 pb-24'>
        {visibleQuestions.length === 0 ? (
          <p className='text-sm text-slate-400'>
            No questions added to this section yet.
          </p>
        ) : (
          <div>
            {renderGroups.map((group, gi) => (
              <div
                key={gi}
                className={gi > 0 ? 'mt-8 border-t border-slate-200 pt-6' : ''}
              >
                <ListeningGroupHeader group={group} />

                {/* ── Matching dropdown group ─────────────────── */}
                {group.type === 'matching_dropdown' && (
                  <CompoundMatchingDropdown
                    questions={group.questions}
                    answers={answers}
                    onAnswer={onAnswer}
                  />
                )}

                {/* ── Multi-select pair group ──────────────────── */}
                {group.type === 'multi_select_pair' && (
                  <CompoundMultiSelectPair
                    questions={group.questions}
                    answers={answers}
                    onAnswer={onAnswer}
                  />
                )}

                {/* ── Compound table group ─────────────────────── */}
                {group.type === 'table' && (
                  <CompoundTableCompletion
                    table={group.questions[0].content.table as TableSpec}
                    questions={group.questions}
                    answers={answers}
                    onAnswer={onAnswer}
                  />
                )}

                {/* ── Compound notes-card group ────────────────── */}
                {group.type === 'notes_card' && (
                  <NoteCompletionCard
                    notes={group.questions[0].content.notes as NotesSpec}
                    questions={group.questions}
                    answers={answers}
                    onAnswer={onAnswer}
                  />
                )}

                {/* ── Matching Information ──────────────────── */}
                {group.type === 'matching_information' && (
                  <MatchingLetterRenderer
                    questions={group.questions}
                    options={group.options ?? []}
                    answers={answers}
                    onAnswer={onAnswer}
                    listTitle='List of Sections'
                    repeatable
                  />
                )}

                {/* ── Matching Features ─────────────────────── */}
                {group.type === 'matching_features' && (
                  <MatchingLetterRenderer
                    questions={group.questions}
                    options={group.options ?? []}
                    answers={answers}
                    onAnswer={onAnswer}
                    listTitle='List of People / Places'
                    repeatable={false}
                  />
                )}

                {/* ── Standard per-question rendering ─────────── */}
                {group.type !== 'table' &&
                  group.type !== 'notes_card' &&
                  group.type !== 'matching_dropdown' &&
                  group.type !== 'multi_select_pair' &&
                  group.type !== 'matching_information' &&
                  group.type !== 'matching_features' && (
                  <div className='space-y-6'>
                    {group.questions.map((q) => (
                      <div key={q.id}>
                        <QuestionRendererWithFlag
                          question={q}
                          answer={answers[q.id] ?? {}}
                          onAnswer={(resp) => onAnswer(q.id, resp)}
                          flagged={flagged?.has(q.id)}
                          onToggleFlag={
                            onToggleFlag ? () => onToggleFlag(q.id) : undefined
                          }
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

