import {
  asCompoundStructure,
  isCompoundType,
  type CompoundGroupDraft,
  type CompoundStructure,
} from '../data/compound'
import {
  assignGroupsSlotNumbers,
  type Question,
  type QuestionGroup,
  type Section,
  type SlotNumberingGroup,
  type SlotRange,
} from '../data/schema'
import { CompoundCompletionRenderer } from '../components/take/compound-completion-renderer'
import {
  ExamMapImage,
  MapLabelingRenderer,
} from '../components/take/question-renderer'
import { highlightCaps } from '../components/take/shared/instruction-block'
import { buildLiveSectionGroups } from './section-groups-live'

const MATCHING_SUBTYPES = new Set([
  'matching_headings',
  'matching_information',
  'matching_features',
])

type Props = {
  section: Section
  /** Live drafts keyed by group id from QuestionGroupEditor */
  drafts?: Record<string, CompoundGroupDraft>
  /**
   * Global IELTS number offset (0-based). Questions start at numberOffset + 1.
   * Listening: (partIndex) * 10. Reading: sum of slots in prior passages.
   */
  numberOffset?: number
}

function applyRange(q: Question, range: SlotRange | undefined): Question {
  if (!range) return q
  if (range.end !== range.start) {
    return {
      ...q,
      order: range.start,
      content: { ...q.content, display_slot_end: range.end },
    }
  }
  return { ...q, order: range.start }
}

function questionImageUrl(
  row: unknown,
  fallback: string | null | undefined,
): string | null {
  if (row && typeof row === 'object' && 'image_url' in row) {
    const value = (row as { image_url?: unknown }).image_url
    if (typeof value === 'string') return value.trim() || null
    if (value === null) return null
  }
  return fallback ?? null
}

function questionsForGroup(
  group: QuestionGroup,
  draft: CompoundGroupDraft | undefined,
  section: Section,
  ranges: Map<string, SlotRange>,
): Question[] {
  const questionType = (draft?.questionType ??
    group.question_type) as Question['question_type']

  const rows =
    draft?.questions && draft.questions.length > 0
      ? draft.questions
      : draft?.gapDrafts && draft.gapDrafts.length > 0
        ? draft.gapDrafts
        : group.questions.map((q) => ({
            id: q.id,
            order: q.order,
            content: q.content,
            answer_key: q.answer_key,
            image_url: q.image_url,
          }))

  return [...rows]
    .map((d, i) => {
      const id = d.id ?? `__draft-${group.id}-${i}`
      const savedImage = group.questions.find((q) => q.id === d.id)?.image_url
      const base: Question = {
        id,
        section_id: section.id,
        question_group_id: group.id,
        order: d.order,
        question_type: questionType,
        content: d.content ?? {},
        answer_key: d.answer_key ?? null,
        task_number: null,
        min_words: null,
        image_url: questionImageUrl(d, savedImage),
        essay_type: null,
        created_at: '',
        updated_at: '',
      }
      return applyRange(base, ranges.get(id))
    })
    .sort((a, b) => a.order - b.order)
}

function qLabel(q: Question): string {
  const slotEnd =
    typeof q.content.display_slot_end === 'number'
      ? q.content.display_slot_end
      : q.order
  return slotEnd !== q.order ? `Q${q.order}–${slotEnd}` : `Q${q.order}`
}

function PreviewGroup({
  group,
  draft,
  section,
  ranges,
}: {
  group: QuestionGroup
  draft?: CompoundGroupDraft
  section: Section
  ranges: Map<string, SlotRange>
}) {
  const questionType = draft?.questionType ?? group.question_type
  const instruction = draft?.instruction ?? group.instruction
  const subtitle =
    draft?.subtitle !== undefined ? draft.subtitle : group.subtitle
  const structure: CompoundStructure | null =
    draft?.structure ?? asCompoundStructure(group.options_shared)

  const matchingOptions: string[] =
    draft?.optionsShared ??
    (Array.isArray(
      (group.options_shared as { options?: unknown[] } | null)?.options,
    )
      ? ((group.options_shared as { options: string[] }).options ?? [])
      : [])

  const questionsHeading =
    draft?.questionsHeading ??
    (group.options_shared as { questions_heading?: string } | null)?.questions_heading

  const mapImageUrl =
    draft?.mapImageUrl !== undefined
      ? draft.mapImageUrl
      : ((group.options_shared as { image_url?: string } | null)?.image_url ?? null)

  const questions = questionsForGroup(group, draft, section, ranges)

  const starts = questions.map((q) => q.order)
  const ends = questions.map((q) => {
    const e = q.content?.display_slot_end
    return typeof e === 'number' ? e : q.order
  })
  const minQ = starts.length ? Math.min(...starts) : 0
  const maxQ = ends.length ? Math.max(...ends) : 0
  const rangeLabel =
    starts.length === 0
      ? 'No questions yet'
      : minQ === maxQ
        ? `Question ${minQ}`
        : `Questions ${minQ}–${maxQ}`

  return (
    <div className='mb-6 border-b border-border pb-5 last:mb-0 last:border-0 last:pb-0'>
      <p className='text-[12px] font-bold text-foreground'>{rangeLabel}</p>
      {instruction && (
        <p className='mt-1 whitespace-pre-wrap text-[12px] text-muted-foreground'>
          {highlightCaps(instruction)}
        </p>
      )}
      {subtitle?.trim() && (
        <p className='mt-3 mb-4 text-center text-[13px] font-bold text-foreground'>
          {subtitle.trim()}
        </p>
      )}

      {isCompoundType(questionType) && structure ? (
        <div className='mt-3 origin-top-left scale-[0.92]'>
          <CompoundCompletionRenderer
            structure={structure}
            questions={questions}
            answers={{}}
            onAnswer={() => {}}
            readOnly
            highlightCell={draft?.focusedCell ?? null}
          />
        </div>
      ) : questionType === 'map_labeling' ? (
        <div className='mt-3 origin-top-left scale-[0.92]'>
          <MapLabelingRenderer
            questions={questions}
            options={matchingOptions}
            imageUrl={mapImageUrl || undefined}
            answers={{}}
            onAnswer={() => {}}
            previewMode
          />
        </div>
      ) : questionType === 'mcq' || questionType === 'multi_select' ? (
        <div className='mt-2 space-y-3'>
          {questions.map((q) => {
            const opts = (q.content.options as string[]) ?? []
            const questionText =
              (q.content.question as string) ||
              (q.content.prompt as string) ||
              ''
            return (
              <div key={q.id} className='space-y-1'>
                <p className='text-[12px] text-foreground'>
                  <span className='font-semibold'>{qLabel(q)}.</span>{' '}
                  {questionText || (
                    <span className='italic text-muted-foreground'>No question text</span>
                  )}
                </p>
                {q.image_url?.trim() && (
                  <div className='py-1'>
                    <ExamMapImage src={q.image_url} />
                  </div>
                )}
                <ul className='space-y-0.5 pl-3'>
                  {opts.map((opt, i) => (
                    <li
                      key={i}
                      className='flex items-start gap-1.5 text-[11px] text-muted-foreground'
                    >
                      <span
                        className={
                          questionType === 'multi_select'
                            ? 'mt-0.5 size-3 shrink-0 rounded border border-border'
                            : 'mt-0.5 size-3 shrink-0 rounded-full border border-border'
                        }
                      />
                      <span>
                        <span className='font-semibold'>
                          {String.fromCharCode(65 + i)}.
                        </span>{' '}
                        {opt}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
          {questions.length === 0 && (
            <p className='text-[12px] text-muted-foreground'>No questions in this group.</p>
          )}
        </div>
      ) : MATCHING_SUBTYPES.has(questionType) ? (
        <div className='mt-3 space-y-2'>
          {/* Matching Information: letters are already in the instruction — no list card */}
          {matchingOptions.length > 0 && questionType !== 'matching_information' && (
            <div className='rounded border border-border bg-muted p-2'>
              <p className='mb-1 text-center text-[11px] font-medium uppercase tracking-wide text-muted-foreground'>
                {subtitle?.trim() || 'Options'}
              </p>
              <div className='flex flex-wrap gap-x-4 gap-y-0.5'>
                {matchingOptions.map((opt, i) => (
                  <span key={i} className='text-[11px] text-muted-foreground'>{opt}</span>
                ))}
              </div>
            </div>
          )}
          {questionsHeading && (
            <p className='text-[11px] font-medium text-foreground'>{questionsHeading}</p>
          )}
          <div className='space-y-1'>
            {questions.map((q) => {
              const statement = (q.content.question as string) || ''
              const correctKey = (q.answer_key?.correct as string) ?? ''
              return (
                <div key={q.id} className='flex items-center gap-2'>
                  <span className='text-[12px] font-medium text-primary'>{q.order}</span>
                  <span className='flex-1 truncate text-[11px] text-foreground'>
                    {statement || (
                      <span className='italic text-muted-foreground'>No statement</span>
                    )}
                  </span>
                  <span className='flex h-5 w-10 items-center justify-center rounded border border-border bg-card text-[11px] text-muted-foreground'>
                    {correctKey || '—'}
                  </span>
                </div>
              )
            })}
          </div>
          {questions.length === 0 && (
            <p className='text-[12px] text-muted-foreground'>No questions in this group.</p>
          )}
        </div>
      ) : (
        <ul className='mt-2 space-y-1.5'>
          {questions.map((q) => (
            <li key={q.id} className='text-[12px] text-foreground'>
              <span className='font-medium'>{qLabel(q)}.</span>{' '}
              {(q.content.question as string) ||
                (q.content.statement as string) ||
                (q.content.prompt as string) ||
                (q.content.text as string) ||
                questionType}
            </li>
          ))}
          {questions.length === 0 && (
            <li className='text-[12px] text-muted-foreground'>
              No questions in this group.
            </li>
          )}
        </ul>
      )}
    </div>
  )
}

export function SectionLivePreview({
  section,
  drafts = {},
  numberOffset = 0,
}: Props) {
  const groups = [...(section.question_groups ?? [])].sort(
    (a, b) => a.order - b.order,
  )

  const liveGroups: SlotNumberingGroup[] = buildLiveSectionGroups(
    groups,
    drafts,
  )
  const ranges = assignGroupsSlotNumbers(liveGroups, numberOffset)

  if (groups.length === 0) {
    return (
      <p className='py-8 text-center text-sm text-muted-foreground'>
        Add a question group to see the student preview.
      </p>
    )
  }

  return (
    <div>
      {groups.map((group) => (
        <PreviewGroup
          key={group.id}
          group={group}
          draft={drafts[group.id]}
          section={section}
          ranges={ranges}
        />
      ))}
    </div>
  )
}
