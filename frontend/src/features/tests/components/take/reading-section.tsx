import { cn } from '@/lib/utils'
import type { Question, QuestionGroup, Section } from '../../data/schema'
import {
  CompoundTableCompletion,
  MatchingHeadingsRenderer,
  MatchingLetterRenderer,
  NoteCompletionCard,
  QuestionRendererWithFlag,
  type NotesSpec,
  type TableSpec,
} from './question-renderer'

type Props = {
  section?: Section
  passage?: string | null
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
  passageIndex?: number
  totalPassages?: number
  /** All reading sections — when provided, Passage tabs are shown inside content */
  allSections?: Section[]
  onSwitchSection?: (sectionId: string) => void
  flagged?: Set<string>
  onToggleFlag?: (id: string) => void
}

// ── Legacy runtime-grouping (fallback for questions without question_group_id) ─

type RuntimeGroup = {
  type: string
  questions: Question[]
  instruction?: string
  options?: string[]
}

function groupQuestionsLegacy(sorted: Question[]): RuntimeGroup[] {
  if (sorted.length === 0) return []
  const groups: RuntimeGroup[] = []
  let i = 0

  const TYPE_INSTRUCTIONS: Record<string, string> = {
    true_false_ng:
      'Do the following statements agree with the information given in Reading Passage? In boxes on your answer sheet, choose',
    gap_fill:
      'Complete the sentences below. Choose ONE WORD ONLY from the passage for each answer.',
    mcq: 'Choose the correct letter, A, B, C or D.',
    matching: 'Match each statement with the correct option.',
    map_labeling: 'Label the map below. Choose ONE WORD ONLY from the passage.',
    notes_card: '',
    table: '',
  }

  while (i < sorted.length) {
    const q = sorted[i]
    const tableId = q.content?.table_id as string | undefined
    const notesId = q.content?.notes_id as string | undefined

    if (notesId) {
      const group: Question[] = [q]
      let j = i + 1
      while (j < sorted.length && (sorted[j].content?.notes_id as string | undefined) === notesId) {
        group.push(sorted[j])
        j++
      }
      groups.push({ type: 'notes_card', questions: group })
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
    } else {
      const group: Question[] = [q]
      let j = i + 1
      while (
        j < sorted.length &&
        sorted[j].question_type === q.question_type &&
        !(sorted[j].content?.notes_id as string | undefined) &&
        !(sorted[j].content?.table_id as string | undefined)
      ) {
        group.push(sorted[j])
        j++
      }
      groups.push({
        type: q.question_type,
        questions: group,
        instruction: TYPE_INSTRUCTIONS[q.question_type] ?? '',
      })
      i = j
    }
  }

  return groups
}

// ── Build render-groups from QuestionGroup model ──────────────────────────────

function buildRenderGroups(apiGroups: QuestionGroup[], questions: Question[]): RuntimeGroup[] {
  if (apiGroups.length === 0) {
    // Legacy fallback: use runtime auto-grouping
    const sorted = [...questions].sort((a, b) => a.order - b.order)
    return groupQuestionsLegacy(sorted)
  }

  const result: RuntimeGroup[] = []

  for (const group of apiGroups) {
    const groupQs = [...group.questions].sort((a, b) => a.order - b.order)
    if (groupQs.length === 0) continue

    // Within a group, detect compound sub-types (notes_card, table) using the
    // first question's content as a probe
    const firstNotes = groupQs[0].content?.notes_id as string | undefined
    const firstTable = groupQs[0].content?.table_id as string | undefined

    const opts = Array.isArray((group.options_shared as { options?: unknown[] } | null)?.options)
      ? (group.options_shared as { options: string[] }).options
      : undefined

    if (firstNotes) {
      result.push({ type: 'notes_card', questions: groupQs })
    } else if (firstTable) {
      result.push({ type: 'table', questions: groupQs })
    } else if (
      group.question_type === 'matching_headings' ||
      group.question_type === 'matching_information' ||
      group.question_type === 'matching_features'
    ) {
      result.push({
        type: group.question_type,
        questions: groupQs,
        instruction: group.instruction || undefined,
        options: opts ?? [],
      })
    } else {
      result.push({
        type: group.question_type,
        questions: groupQs,
        instruction: group.instruction || undefined,
        options: opts,
      })
    }
  }

  // Also check for any orphan questions (no group) and append them as legacy groups
  const groupedIds = new Set(apiGroups.flatMap((g) => g.questions.map((q) => q.id)))
  const orphans = questions.filter((q) => !groupedIds.has(q.id)).sort((a, b) => a.order - b.order)
  if (orphans.length > 0) {
    result.push(...groupQuestionsLegacy(orphans))
  }

  return result
}

// ── Group header ──────────────────────────────────────────────────────────────

function GroupHeader({ group }: { group: RuntimeGroup }) {
  const orders = group.questions.map((q) => q.order)
  const minQ = Math.min(...orders)
  const maxQ = Math.max(...orders)
  const rangeLabel = minQ === maxQ ? `Question ${minQ}` : `Questions ${minQ}–${maxQ}`
  const instruction = group.instruction ?? ''

  return (
    <div className='mb-5'>
      <p className='text-[13px] font-bold text-[#111827]'>{rangeLabel}</p>
      {instruction &&
        instruction.split('\n').map((line, i) => (
          <p key={i} className='mt-1 text-[13px] text-[#6b7280]'>
            {line}
          </p>
        ))}
      {group.type === 'true_false_ng' && (
        <div className='mt-2 space-y-0.5 text-[13px] text-[#6b7280]'>
          <p>
            <span className='font-semibold uppercase text-[#111827]'>TRUE</span>
            {' '}— if the statement agrees with the information
          </p>
          <p>
            <span className='font-semibold uppercase text-[#111827]'>FALSE</span>
            {' '}— if the statement contradicts the information
          </p>
          <p>
            <span className='font-semibold uppercase text-[#111827]'>NOT GIVEN</span>
            {' '}— if there is no information on this
          </p>
        </div>
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

// ── Main component ────────────────────────────────────────────────────────────

export function ReadingSection({
  section,
  passage,
  questions,
  answers,
  onAnswer,
  passageIndex = 0,
  totalPassages: _totalPassages = 1,
  allSections,
  onSwitchSection,
  flagged,
  onToggleFlag,
}: Props) {
  const sortedQuestions = [...questions].sort((a, b) => a.order - b.order)

  // Build groups: use section.question_groups when available, else runtime-group
  const apiGroups = section?.question_groups ?? []
  const groups = buildRenderGroups(apiGroups, sortedQuestions)

  // Question range for subtitle
  const orders = sortedQuestions.map((q) => q.order)
  const minQ = orders.length > 0 ? Math.min(...orders) : 1
  const maxQ = orders.length > 0 ? Math.max(...orders) : 1
  const passageNum = passageIndex + 1

  // Passage title: prefer section.title, else parse from first non-empty line
  const effectivePassage = section?.passage ?? passage ?? ''
  const lines = effectivePassage.split('\n')
  const firstLine = lines.find((l) => l.trim().length > 0) ?? ''
  const parsedTitle = firstLine
  const body = effectivePassage.replace(firstLine, '').trim()
  const paragraphs = body.split(/\n{2,}/).filter((p) => p.trim().length > 0)

  const displayTitle = section?.title || parsedTitle

  return (
    <div className='flex h-full'>
      {/* ── Left: Passage 50% ──────────────────────────────────────────── */}
      <div className='w-1/2 overflow-y-auto bg-white px-10 py-8'>
        {/* Passage switcher tabs */}
        {allSections && allSections.length > 1 && onSwitchSection && (
          <div className='mb-6 flex gap-2'>
            {allSections.map((s, i) => {
              const isActive = s.id === section?.id
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
                  Passage {i + 1}
                </button>
              )
            })}
          </div>
        )}

        {/* PASSAGE N heading */}
        <h2
          className='uppercase text-slate-900'
          style={{ fontSize: '22px', fontWeight: 800, letterSpacing: '-0.3px' }}
        >
          Passage {passageNum}
        </h2>

        {/* Subtitle */}
        <p className='mt-1 text-[13px] text-[#6b7280]'>
          You should spend about 20 minutes on Questions {minQ}
          {minQ !== maxQ ? `–${maxQ}` : ''}, which are based on Reading Passage{' '}
          {passageNum}.
        </p>

        {effectivePassage ? (
          <>
            {displayTitle && (
              <h3 className='mb-6 mt-6 text-center text-[18px] font-bold leading-snug text-slate-900'>
                {displayTitle}
              </h3>
            )}
            <div className='space-y-5'>
              {paragraphs.length > 0 ? (
                paragraphs.map((para, i) => (
                  <p
                    key={i}
                    className={
                      i === 0
                        ? 'text-[16px] font-bold italic leading-[1.8] text-[#1f2937]'
                        : 'text-[16px] leading-[1.8] text-[#1f2937]'
                    }
                    style={{ fontFamily: 'Georgia, serif' }}
                  >
                    {para.trim()}
                  </p>
                ))
              ) : (
                <p
                  className='text-[16px] leading-[1.8] text-[#1f2937]'
                  style={{ fontFamily: 'Georgia, serif' }}
                >
                  {body || effectivePassage}
                </p>
              )}
            </div>
          </>
        ) : (
          <p className='mt-6 text-sm italic text-slate-400'>
            No passage text has been added for this section.
          </p>
        )}
      </div>

      {/* ── Right: Questions 50% ───────────────────────────────────────── */}
      <div className='w-1/2 overflow-y-auto border-l border-slate-200 bg-white px-8 py-8 pb-24'>
        {sortedQuestions.length === 0 ? (
          <p className='text-sm text-slate-400'>
            No questions added to this section yet.
          </p>
        ) : (
          <div>
            {groups.map((group, gi) => (
              <div
                key={gi}
                className={gi > 0 ? 'mt-8 border-t border-slate-200 pt-6' : ''}
              >
                <GroupHeader group={group} />

                {/* ── Compound notes-card (word-bank summary) ─── */}
                {group.type === 'notes_card' && (
                  <NoteCompletionCard
                    notes={group.questions[0].content.notes as NotesSpec}
                    questions={group.questions}
                    answers={answers}
                    onAnswer={onAnswer}
                  />
                )}

                {/* ── Compound table completion ──────────────── */}
                {group.type === 'table' && (
                  <CompoundTableCompletion
                    table={group.questions[0].content.table as TableSpec}
                    questions={group.questions}
                    answers={answers}
                    onAnswer={onAnswer}
                  />
                )}

                {/* ── Matching Headings ─────────────────────── */}
                {group.type === 'matching_headings' && (
                  <MatchingHeadingsRenderer
                    questions={group.questions}
                    options={group.options ?? []}
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

                {/* ── Standard per-question rendering ──────────── */}
                {group.type !== 'notes_card' &&
                  group.type !== 'table' &&
                  group.type !== 'matching_headings' &&
                  group.type !== 'matching_information' &&
                  group.type !== 'matching_features' && (
                  <div className='space-y-5'>
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
