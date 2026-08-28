import { useState } from 'react'
import { BookOpen, HelpCircle } from 'lucide-react'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { useIsDesktop } from '@/hooks/use-mobile'
import { cn } from '@/lib/utils'
import {
  hasTfngKeyLegend,
  hasYnngKeyLegend,
  highlightCaps,
  InstructionBlock,
  renderFormattedText,
} from './shared/instruction-block'
import { QuestionRangeTitle } from './shared/question-range-title'
import { PassageHighlighter } from './shared/passage-highlighter'
import {
  asCompoundStructure,
  isCompoundType,
  type CompoundStructure,
} from '../../data/compound'
import {
  countScoringSlots,
  withDisplayOrders,
  type Question,
  type QuestionGroup,
  type Section,
} from '../../data/schema'
import { CompoundCompletionRenderer } from './compound-completion-renderer'
import {
  CompoundTableCompletion,
  MapLabelingRenderer,
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
  /** Practice mode: force "Passage N" when siblings are scoped to one row. */
  passageNumberOverride?: number
  /** All reading sections — used for passage numbering offsets. */
  allSections?: Section[]
  /**
   * Questions keyed by section id. Preferred source for prior-passage slot
   * offsets (take-test loads questions separately from section.question_groups).
   */
  sectionQuestions?: Record<string, Question[]>
  flagged?: Set<string>
  onToggleFlag?: (id: string) => void
  previewMode?: boolean
  /** Used to persist passage highlights per attempt */
  attemptId?: string | null
}

// ── Legacy runtime-grouping (fallback for questions without question_group_id) ─

type RuntimeGroup = {
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
    map_labeling: 'Label the map below. Choose the correct letter, A-I.',
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

    // New compound model: structure lives on options_shared
    const compoundStructure = asCompoundStructure(group.options_shared)
    if (isCompoundType(group.question_type) && compoundStructure) {
      result.push({
        type: 'compound',
        questions: groupQs,
        instruction: group.instruction || undefined,
        subtitle: group.subtitle,
        structure: compoundStructure,
      })
      continue
    }

    // Within a group, detect compound sub-types (notes_card, table) using the
    // first question's content as a probe
    const firstNotes = groupQs[0].content?.notes_id as string | undefined
    const firstTable = groupQs[0].content?.table_id as string | undefined

    const opts = Array.isArray((group.options_shared as { options?: unknown[] } | null)?.options)
      ? (group.options_shared as { options: string[] }).options
      : undefined

    if (firstNotes) {
      result.push({ type: 'notes_card', questions: groupQs, subtitle: group.subtitle })
    } else if (firstTable) {
      result.push({ type: 'table', questions: groupQs, subtitle: group.subtitle })
    } else if (
      group.question_type === 'matching_headings' ||
      group.question_type === 'matching_information' ||
      group.question_type === 'matching_features'
    ) {
      const shared = group.options_shared as {
        questions_heading?: string
        options_heading?: string
      } | null
      result.push({
        type: group.question_type,
        questions: groupQs,
        instruction: group.instruction || undefined,
        subtitle: group.subtitle,
        options: opts ?? [],
        questionsHeading: shared?.questions_heading || undefined,
        optionsHeading: shared?.options_heading || undefined,
      })
    } else if (group.question_type === 'map_labeling') {
      const imgUrl =
        (group.options_shared as { image_url?: string } | null)?.image_url ||
        (groupQs[0]?.content?.image_url as string | undefined) ||
        groupQs[0]?.image_url
      result.push({
        type: 'map_labeling',
        questions: groupQs,
        instruction: group.instruction || undefined,
        subtitle: group.subtitle,
        options: opts ?? [],
        imageUrl: imgUrl || undefined,
      })
    } else {
      result.push({
        type: group.question_type,
        questions: groupQs,
        instruction: group.instruction || undefined,
        subtitle: group.subtitle,
        options: opts,
      })
    }
  }

  // Orphans (question_group_id null / missing from groups) are data bugs.
  // Never surface them in the student take UI — they create ghost rows and
  // skew IELTS numbering (e.g. duplicate "Questions 27–33").
  return result
}

// ── Group header ──────────────────────────────────────────────────────────────

function GroupHeader({ group }: { group: RuntimeGroup }) {
  const starts = group.questions.map((q) => q.order)
  const ends = group.questions.map((q) => {
    const e = q.content?.display_slot_end
    return typeof e === 'number' ? e : q.order
  })
  const minQ = Math.min(...starts)
  const maxQ = Math.max(...ends)
  const instruction = group.instruction ?? ''
  const subtitle = group.subtitle?.trim() || ''

  return (
    <div className='mb-5'>
      <QuestionRangeTitle min={minQ} max={maxQ} />
      {instruction && (
        <InstructionBlock className='mt-2'>
          {instruction.split('\n').map((line, i) => (
            <p key={i} className={i > 0 ? 'mt-1' : ''}>
              {highlightCaps(line)}
            </p>
          ))}
        </InstructionBlock>
      )}
      {subtitle &&
        group.type !== 'matching_headings' &&
        group.type !== 'matching_information' &&
        group.type !== 'matching_features' &&
        group.type !== 'map_labeling' && (
        <p className='mt-4 mb-5 text-center text-base font-bold text-slate-900'>
          {subtitle}
        </p>
      )}
      {group.type === 'true_false_ng' && !hasTfngKeyLegend(instruction) && (
        <div className='mt-2 space-y-0.5 text-[15px] font-[500] leading-7 text-foreground'>
          <p>
            <span className='font-bold uppercase'>TRUE</span>
            {' '}if the statement agrees with the information
          </p>
          <p>
            <span className='font-bold uppercase'>FALSE</span>
            {' '}if the statement contradicts the information
          </p>
          <p>
            <span className='font-bold uppercase'>NOT GIVEN</span>
            {' '}if there is no information on this
          </p>
        </div>
      )}
      {group.type === 'yes_no_ng' && !hasYnngKeyLegend(instruction) && (
        <div className='mt-2 space-y-0.5 text-[15px] font-[500] leading-7 text-foreground'>
          <p>
            <span className='font-bold uppercase'>YES</span>
            {' '}if the statement agrees with the claims of the writer
          </p>
          <p>
            <span className='font-bold uppercase'>NO</span>
            {' '}if the statement contradicts the claims of the writer
          </p>
          <p>
            <span className='font-bold uppercase'>NOT GIVEN</span>
            {' '}if it is impossible to say what the writer thinks about this
          </p>
        </div>
      )}
      {group.options && group.options.length > 0 &&
        group.type !== 'matching_headings' &&
        group.type !== 'matching_information' &&
        group.type !== 'matching_features' &&
        group.type !== 'map_labeling' && (
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
  passageNumberOverride,
  allSections,
  sectionQuestions,
  flagged,
  onToggleFlag,
  previewMode = false,
  attemptId = null,
}: Props) {
  const readingSiblings = (allSections ?? [])
    .filter((s) => s.type === 'reading')
    .sort((a, b) => a.order - b.order)
  const passageIdxInReading =
    section != null
      ? Math.max(0, readingSiblings.findIndex((s) => s.id === section.id))
      : passageIndex

  const priorQuestions = readingSiblings.slice(0, passageIdxInReading).flatMap((s) => {
    const fromMap = sectionQuestions?.[s.id]
    if (fromMap && fromMap.length > 0) return fromMap
    return (s.question_groups ?? []).flatMap((g) => g.questions)
  })
  const numberOffset = countScoringSlots(priorQuestions)

  const displayQuestions =
    section != null
      ? withDisplayOrders(section, questions, numberOffset)
      : questions
  const remappedById = new Map(displayQuestions.map((q) => [q.id, q]))
  const displaySection =
    section != null
      ? {
          ...section,
          question_groups: (section.question_groups ?? []).map((g) => ({
            ...g,
            questions: g.questions
              .map((q) => remappedById.get(q.id) ?? q)
              .sort((a, b) => a.order - b.order),
          })),
        }
      : undefined

  const sortedQuestions = [...displayQuestions].sort((a, b) => a.order - b.order)

  // Build groups: use section.question_groups when available, else runtime-group
  const apiGroups = displaySection?.question_groups ?? []
  const groups = buildRenderGroups(apiGroups, sortedQuestions)

  // Question range for subtitle
  const starts = sortedQuestions.map((q) => q.order)
  const ends = sortedQuestions.map((q) => {
    const e = q.content?.display_slot_end
    return typeof e === 'number' ? e : q.order
  })
  const minQ = starts.length > 0 ? Math.min(...starts) : 1
  const maxQ = ends.length > 0 ? Math.max(...ends) : 1
  const passageNum = passageNumberOverride ?? passageIdxInReading + 1

  const effectivePassage = section?.passage ?? passage ?? ''

  // When section.title is set, render the full passage as body.
  // Otherwise fall back to parsing the first non-empty line as a title.
  let displayTitle: string
  let body: string
  if (section?.title) {
    displayTitle = section.title
    body = effectivePassage.trim()
  } else {
    const lines = effectivePassage.split('\n')
    const firstLine = lines.find((l) => l.trim().length > 0) ?? ''
    displayTitle = firstLine
    body = effectivePassage.replace(firstLine, '').trim()
  }

  const [mobileTab, setMobileTab] = useState<'passage' | 'questions'>('passage')
  const isDesktop = useIsDesktop()

  // Shared passage content
  const passageContent = (
    <>
      <h2 className='text-lg font-medium text-slate-900'>
        Passage {passageNum}
      </h2>

      <p className='mt-1 text-[13px] text-slate-400'>
        You should spend about 20 minutes on Questions {minQ}
        {minQ !== maxQ ? `–${maxQ}` : ''}, which are based on Reading Passage{' '}
        {passageNum}.
      </p>

      {effectivePassage ? (
        <article className='mt-6'>
          {displayTitle && (
            <h3 className='mb-3 text-center text-[22px] font-bold leading-snug tracking-tight text-foreground'>
              {displayTitle}
            </h3>
          )}
          {section?.passage_subtitle && (
            <p className='mb-6 text-center text-sm font-semibold italic text-foreground'>
              {section.passage_subtitle}
            </p>
          )}
          {!section?.passage_subtitle && displayTitle && <div className='mb-5' />}
          <div className='space-y-5 text-justify'>
            {renderFormattedText(body || effectivePassage)}
          </div>
        </article>
      ) : (
        <p className='mt-6 text-sm italic text-slate-400'>
          No passage text has been added for this section.
        </p>
      )}
    </>
  )

  // Shared questions content
  const questionsContent = (
    <>
      {sortedQuestions.length === 0 ? (
        <p className='text-sm text-slate-400'>
          No questions added to this section yet.
        </p>
      ) : (
        <div>
          {groups.map((group, gi) => (
            <div
              key={gi}
              data-question-group
              className={gi > 0 ? 'mt-8 border-t border-border pt-6' : ''}
            >
              <GroupHeader group={group} />

              {group.type === 'compound' && group.structure && (
                <CompoundCompletionRenderer
                  structure={group.structure}
                  questions={group.questions}
                  answers={answers}
                  onAnswer={onAnswer}
                  previewMode={previewMode}
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

              {group.type === 'table' && (
                <CompoundTableCompletion
                  table={group.questions[0].content.table as TableSpec}
                  questions={group.questions}
                  answers={answers}
                  onAnswer={onAnswer}
                />
              )}

              {group.type === 'matching_headings' && (
                <MatchingLetterRenderer
                  questions={group.questions}
                  options={group.options ?? []}
                  answers={answers}
                  onAnswer={onAnswer}
                  listTitle='List of Headings'
                  questionsTitle={group.questionsHeading}
                  repeatable={false}
                  previewMode={previewMode}
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
                  repeatable
                  previewMode={previewMode}
                />
              )}

              {group.type === 'map_labeling' && (
                <MapLabelingRenderer
                  questions={group.questions}
                  options={group.options ?? []}
                  imageUrl={group.imageUrl}
                  answers={answers}
                  onAnswer={onAnswer}
                  previewMode={previewMode}
                />
              )}

              {group.type !== 'compound' &&
                group.type !== 'notes_card' &&
                group.type !== 'table' &&
                group.type !== 'matching_headings' &&
                group.type !== 'matching_information' &&
                group.type !== 'matching_features' &&
                group.type !== 'map_labeling' && (
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
                        previewMode={previewMode}
                        hideQuestionNumber={group.questions.length === 1}
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
            onClick={() => setMobileTab('passage')}
            className={cn(
              'flex flex-1 items-center justify-center gap-1.5 py-2.5 text-[13px] font-medium transition-colors',
              mobileTab === 'passage'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500 hover:text-slate-700',
            )}
          >
            <BookOpen className='size-3.5' />
            Passage
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
        {mobileTab === 'passage' && (
          <div className='min-h-0 flex-1 overflow-y-auto bg-white px-5 py-6'>
            {section?.id ? (
              <PassageHighlighter attemptId={attemptId} sectionId={section.id}>
                {passageContent}
              </PassageHighlighter>
            ) : (
              passageContent
            )}
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
        <div className='h-full overflow-y-auto overflow-x-hidden bg-white px-5 py-6 xl:px-10 xl:py-8'>
          {section?.id ? (
            <PassageHighlighter attemptId={attemptId} sectionId={section.id}>
              {passageContent}
            </PassageHighlighter>
          ) : (
            passageContent
          )}
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
