import { useState } from 'react'
import { AlertCircle, Headphones, HelpCircle } from 'lucide-react'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { useIsDesktop } from '@/hooks/use-mobile'
import { cn } from '@/lib/utils'
import { ListeningAudioPlayer } from './listening-audio-player'
import { highlightCaps, InstructionBlock } from './shared/instruction-block'
import { QuestionRangeTitle } from './shared/question-range-title'
import { PassageHighlighter } from './shared/passage-highlighter'
import {
  asCompoundStructure,
  isCompoundType,
  type CompoundStructure,
} from '../../data/compound'
import {
  withDisplayOrders,
  normaliseQuestionType,
  type Question,
  type QuestionGroup,
  type Section,
} from '../../data/schema'
import { CompoundCompletionRenderer } from './compound-completion-renderer'
import {
  CompoundMatchingDropdown,
  CompoundMultiSelectPair,
  CompoundTableCompletion,
  MapLabelingRenderer,
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
  subtitle?: string | null
  options?: string[]
  structure?: CompoundStructure
  questionsHeading?: string
  optionsHeading?: string
  imageUrl?: string
}

// ── Legacy runtime-grouping (fallback when no question_group_id) ──────────────

const LISTENING_INSTRUCTIONS: Record<string, string> = {
  mcq: 'Choose the correct letter, A, B, C or D.',
  true_false_ng:
    'Do the following statements agree with the information? Choose TRUE, FALSE or NOT GIVEN.',
  gap_fill:
    'Complete the notes below. Write ONE WORD AND/OR A NUMBER for each answer.',
  matching: 'Match each statement with the correct option.',
  map_labeling: 'Label the map below. Choose the correct letter, A-I.',
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

    const qType = normaliseQuestionType(group.question_type)
    const compoundStructure = asCompoundStructure(group.options_shared)
    if (isCompoundType(qType) && compoundStructure) {
      result.push({
        type: 'compound',
        questions: groupQs,
        instruction: group.instruction || undefined,
        subtitle: group.subtitle,
        structure: compoundStructure,
      })
      continue
    }

    const firstMatchingId = groupQs[0].content?.matching_id as string | undefined
    const firstPairId = groupQs[0].content?.pair_id as string | undefined
    const firstTableId = groupQs[0].content?.table_id as string | undefined
    const firstNotesId = groupQs[0].content?.notes_id as string | undefined

    const opts = Array.isArray((group.options_shared as { options?: unknown[] } | null)?.options)
      ? (group.options_shared as { options: string[] }).options
      : undefined

    if (firstMatchingId) {
      result.push({
        type: 'matching_dropdown',
        questions: groupQs,
        subtitle: group.subtitle,
      })
    } else if (firstPairId) {
      result.push({
        type: 'multi_select_pair',
        questions: groupQs,
        subtitle: group.subtitle,
      })
    } else if (firstTableId) {
      result.push({ type: 'table', questions: groupQs, subtitle: group.subtitle })
    } else if (firstNotesId) {
      result.push({ type: 'notes_card', questions: groupQs, subtitle: group.subtitle })
    } else if (
      group.question_type === 'matching_information' ||
      group.question_type === 'matching_features'
    ) {
      const instruction = group.instruction || ''
      const shared = group.options_shared as {
        questions_heading?: string
        options_heading?: string
      } | null
      result.push({
        type: group.question_type,
        questions: groupQs,
        instruction,
        subtitle: group.subtitle,
        options: opts ?? [],
        questionsHeading: shared?.questions_heading || undefined,
        optionsHeading: shared?.options_heading || undefined,
      })
    } else if (group.question_type === 'map_labeling') {
      const instruction = group.instruction || LISTENING_INSTRUCTIONS.map_labeling || ''
      const imgUrl =
        (group.options_shared as { image_url?: string } | null)?.image_url ||
        (groupQs[0]?.content?.image_url as string | undefined) ||
        groupQs[0]?.image_url
      result.push({
        type: 'map_labeling',
        questions: groupQs,
        instruction,
        subtitle: group.subtitle,
        options: opts ?? [],
        imageUrl: imgUrl || undefined,
      })
    } else {
      const instruction = group.instruction ||
        (groupQs[0]?.content?.instruction as string | undefined) ||
        LISTENING_INSTRUCTIONS[group.question_type] ||
        ''
      const optHead = (group.options_shared as { options_heading?: string } | null)?.options_heading
      result.push({
        type: group.question_type,
        questions: groupQs,
        instruction,
        subtitle: group.subtitle,
        options: opts,
        optionsHeading: optHead || undefined,
      })
    }
  }

  // Orphans (question_group_id null / missing from groups) are data bugs.
  // Never surface them in the student take UI — they create ghost rows and
  // skew IELTS numbering.
  return result
}

// ── Group header ──────────────────────────────────────────────────────────────

function ListeningGroupHeader({ group }: { group: RenderGroup }) {
  const starts = group.questions.map((q) => q.order)
  const ends = group.questions.map((q) => {
    const e = q.content?.display_slot_end
    return typeof e === 'number' ? e : q.order
  })
  const minQ = Math.min(...starts)
  const maxQ = Math.max(...ends)

  // Show group.instruction for new-model compound groups; suppress only legacy compound cards
  // that embed instruction inside notes/table content.
  const rawInstruction =
    group.type === 'notes_card' || group.type === 'table'
      ? ''
      : (group.instruction ?? '')
  const subtitle = group.subtitle?.trim() || ''
  // Legacy per-question section_title (prefer group.subtitle when set)
  const sectionTitle =
    subtitle ||
    ((group.questions[0]?.content?.section_title as string | undefined) ?? '')

  return (
    <div className='mb-4'>
      <QuestionRangeTitle min={minQ} max={maxQ} />
      {rawInstruction && (
        <InstructionBlock className='mt-2'>
          {rawInstruction.split('\n').map((line, i) => (
            <p key={i} className={i > 0 ? 'mt-1' : ''}>
              {highlightCaps(line)}
            </p>
          ))}
        </InstructionBlock>
      )}
      {sectionTitle &&
        group.type !== 'matching_information' &&
        group.type !== 'matching_features' &&
        group.type !== 'matching' &&
        group.type !== 'map_labeling' && (
        <p className='mt-4 mb-5 text-center text-base font-bold text-foreground'>
          {sectionTitle}
        </p>
      )}
      {group.options && group.options.length > 0 &&
        group.type !== 'matching_information' &&
        group.type !== 'matching_features' &&
        group.type !== 'matching' &&
        group.type !== 'map_labeling' && (
        <div className='mt-3 flex flex-wrap gap-1.5'>
          {group.options.map((opt, i) => (
            <span
              key={i}
              className='rounded border border-border bg-muted px-2 py-0.5 text-[12px] text-foreground'
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
  /**
   * When the shell has already scoped to a single practice part, force the
   * visible "Part N" label (avoids legacy content.part fallback showing Part 1).
   */
  partNumberOverride?: number
  /** All listening sections — used to resolve the visible Part number. */
  allSections?: Section[]
  /** Show audioscript — only in review/admin mode, hidden during live test */
  reviewMode?: boolean
  flagged?: Set<string>
  onToggleFlag?: (id: string) => void
  previewMode?: boolean
  attemptId?: string | null
}

function getPartNumber(q: Question): number {
  const p = q.content.part
  if (typeof p === 'number') return p
  return 1
}

// ── Main section ─────────────────────────────────────────────────────────────

export function ListeningSection({
  section,
  questions,
  answers,
  onAnswer,
  activePart,
  partNumberOverride,
  allSections,
  reviewMode = false,
  flagged,
  onToggleFlag,
  previewMode = false,
  attemptId = null,
}: Props) {
  // Multi-section mode: each IELTS Part is its own Section row (preferred).
  // Legacy mode: one section with questions tagged via content.part.
  const multiSectionMode = Boolean(allSections && allSections.length > 1)

  // Single source of truth for the visible part: the section currently rendered.
  const activePartIndex = multiSectionMode
    ? Math.max(0, allSections!.findIndex((s) => s.id === section.id))
    : (activePart ?? 0)
  const displayPartNumber = multiSectionMode
    ? activePartIndex + 1
    : undefined

  // IELTS Listening: show Q11–Q20 in Part 2, etc.
  const displayQuestions = withDisplayOrders(section, questions)
  const remappedById = new Map(displayQuestions.map((q) => [q.id, q]))
  const displaySection: Section = {
    ...section,
    question_groups: (section.question_groups ?? []).map((g) => ({
      ...g,
      questions: g.questions
        .map((q) => remappedById.get(q.id) ?? q)
        .sort((a, b) => a.order - b.order),
    })),
  }

  const sortedQuestions = [...displayQuestions].sort((a, b) => a.order - b.order)

  const parts = Array.from(
    new Set(sortedQuestions.map(getPartNumber)),
  ).sort((a, b) => a - b)

  // Legacy single-section: filter by content.part using activePart index.
  // Multi-section: the parent already swapped `section`/`questions` — show all.
  const legacyPartNumber =
    activePart !== undefined && parts.length > 0
      ? (parts[activePart] ?? parts[0])
      : (parts[0] ?? 1)

  const activePartNumber =
    partNumberOverride ?? displayPartNumber ?? legacyPartNumber

  const visibleQuestions =
    !multiSectionMode && parts.length > 1
      ? sortedQuestions.filter((q) => getPartNumber(q) === activePartNumber)
      : sortedQuestions

  // Build render groups: prefer section.question_groups, fallback to runtime grouping
  const apiGroups = displaySection.question_groups ?? []
  // Filter API groups whose questions are in the visible set
  const visibleIds = new Set(visibleQuestions.map((q) => q.id))
  const visibleApiGroups = apiGroups.filter((g) =>
    g.questions.some((q) => visibleIds.has(q.id))
  ).map((g) => ({
    ...g,
    questions: g.questions.filter((q) => visibleIds.has(q.id)),
  }))

  const renderGroups = buildRenderGroups(visibleApiGroups, visibleQuestions)

  const [mobileTab, setMobileTab] = useState<'audio' | 'questions'>('audio')
  const isDesktop = useIsDesktop()

  const audioContent = (
    <>
      <h2 className='mb-6 text-lg font-medium text-slate-900'>
        Part {activePartNumber}
      </h2>

      {section.audio_url ? (
        <ListeningAudioPlayer section={section} partNumber={activePartNumber} />
      ) : (
        <div className='flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600'>
          <AlertCircle className='size-4 shrink-0' />
          No audio file has been uploaded for this section.
        </div>
      )}

      {section.audioscript && reviewMode && (
        <details className='mt-6 rounded-lg border border-slate-200'>
          <summary className='cursor-pointer select-none px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50'>
            Audioscript
          </summary>
          <div
            className='px-4 pb-4 pt-2 text-[14px] leading-relaxed text-slate-700'
            style={{ fontFamily: 'Georgia, serif' }}
          >
            {section.audioscript}
          </div>
        </details>
      )}
    </>
  )

  const questionsContent = (
    <>
      {visibleQuestions.length === 0 ? (
        <p className='text-sm text-slate-400'>
          No questions added to this section yet.
        </p>
      ) : (
        <div>
          {renderGroups.map((group, gi) => (
            <div
              key={gi}
              data-question-group
              className={gi > 0 ? 'mt-8 border-t border-border pt-6' : ''}
            >
              <ListeningGroupHeader group={group} />

              {group.type === 'compound' && group.structure && (
                <CompoundCompletionRenderer
                  structure={group.structure}
                  questions={group.questions}
                  answers={answers}
                  onAnswer={onAnswer}
                  previewMode={previewMode}
                />
              )}

              {group.type === 'matching_dropdown' && (
                <CompoundMatchingDropdown
                  questions={group.questions}
                  answers={answers}
                  onAnswer={onAnswer}
                  previewMode={previewMode}
                />
              )}

              {group.type === 'multi_select_pair' && (
                <CompoundMultiSelectPair
                  questions={group.questions}
                  answers={answers}
                  onAnswer={onAnswer}
                  previewMode={previewMode}
                />
              )}

              {group.type === 'table' && (
                <CompoundTableCompletion
                  table={group.questions[0].content.table as TableSpec}
                  questions={group.questions}
                  answers={answers}
                  onAnswer={onAnswer}
                />
              )}

              {group.type === 'notes_card' && (
                <NoteCompletionCard
                  notes={group.questions[0].content.notes as NotesSpec}
                  questions={group.questions}
                  answers={answers}
                  onAnswer={onAnswer}
                />
              )}

              {group.type === 'matching_information' && (
                <MatchingLetterRenderer
                  questions={group.questions}
                  options={group.options ?? []}
                  answers={answers}
                  onAnswer={onAnswer}
                  listTitle={group.subtitle || 'List of Sections'}
                  questionsTitle={group.questionsHeading}
                  repeatable
                  showOptionsList={false}
                  previewMode={previewMode}
                />
              )}

              {group.type === 'matching_features' && (
                <MatchingLetterRenderer
                  questions={group.questions}
                  options={group.options ?? []}
                  answers={answers}
                  onAnswer={onAnswer}
                  listTitle={group.optionsHeading || group.subtitle || undefined}
                  questionsTitle={group.questionsHeading}
                  repeatable={false}
                  previewMode={previewMode}
                />
              )}

              {group.type === 'matching' && (
                <MatchingLetterRenderer
                  questions={group.questions}
                  options={group.options ?? []}
                  answers={answers}
                  onAnswer={onAnswer}
                  listTitle={group.optionsHeading || 'Options'}
                  questionsTitle={group.subtitle || undefined}
                  repeatable
                  previewMode={previewMode}
                />
              )}

              {group.type === 'map_labeling' && (
                <MapLabelingRenderer
                  questions={group.questions}
                  options={group.options ?? []}
                  imageUrl={group.imageUrl}
                  imageCaption={group.subtitle?.trim() || undefined}
                  answers={answers}
                  onAnswer={onAnswer}
                  previewMode={previewMode}
                />
              )}

              {group.type !== 'compound' &&
                group.type !== 'table' &&
                group.type !== 'notes_card' &&
                group.type !== 'matching_dropdown' &&
                group.type !== 'multi_select_pair' &&
                group.type !== 'matching_information' &&
                group.type !== 'matching_features' &&
                group.type !== 'matching' &&
                group.type !== 'map_labeling' && (
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
                        previewMode={previewMode}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  )

  if (!isDesktop) {
    return (
      <div className='flex h-full flex-col'>
        <div className='flex border-b border-slate-200'>
          <button
            type='button'
            onClick={() => setMobileTab('audio')}
            className={cn(
              'flex flex-1 items-center justify-center gap-1.5 py-2.5 text-[13px] font-medium transition-colors',
              mobileTab === 'audio'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500 hover:text-slate-700',
            )}
          >
            <Headphones className='size-3.5' />
            Audio
          </button>
          <button
            type='button'
            onClick={() => setMobileTab('questions')}
            className={cn(
              'flex flex-1 items-center justify-center gap-1.5 py-2.5 text-[13px] font-medium transition-colors',
              mobileTab === 'questions'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500 hover:text-slate-700',
            )}
          >
            <HelpCircle className='size-3.5' />
            Questions
          </button>
        </div>
        {mobileTab === 'audio' && (
          <div className='min-h-0 flex-1 overflow-y-auto bg-white px-5 py-6'>
            {audioContent}
          </div>
        )}
        {mobileTab === 'questions' && (
          <div
            data-exam-scroll-pane
            className='min-h-0 flex-1 overflow-y-auto overflow-x-clip bg-white px-5 py-6 pb-24'
          >
            {section?.id ? (
              <PassageHighlighter
                attemptId={attemptId}
                sectionId={section.id}
                storageKeySuffix='questions'
              >
                {questionsContent}
              </PassageHighlighter>
            ) : (
              questionsContent
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <ResizablePanelGroup orientation='horizontal' className='h-full'>
      <ResizablePanel defaultSize='50%' minSize='25%'>
        <div className='h-full overflow-y-auto overflow-x-hidden bg-white px-5 py-6 xl:px-8 xl:py-8'>
          {audioContent}
        </div>
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize='50%' minSize='25%'>
        <div
          data-exam-scroll-pane
          className='h-full overflow-y-auto overflow-x-clip bg-white px-5 py-6 pb-24 xl:px-8 xl:py-8'
        >
          {section?.id ? (
            <PassageHighlighter
              attemptId={attemptId}
              sectionId={section.id}
              storageKeySuffix='questions'
            >
              {questionsContent}
            </PassageHighlighter>
          ) : (
            questionsContent
          )}
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}

