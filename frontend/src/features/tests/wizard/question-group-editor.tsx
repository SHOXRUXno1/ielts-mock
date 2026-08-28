import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, ImagePlus, Loader2, Plus, Settings2, Trash2, X } from 'lucide-react'
import type { AxiosError } from 'axios'
import { toast } from 'sonner'
import {
  createQuestionInGroup,
  deleteQuestionGroup,
  updateQuestionGroup,
} from '@/lib/api/question-groups'
import { mediaUrl, uploadImage } from '@/lib/api/attempts'
import { deleteQuestion, updateQuestion } from '@/lib/api/questions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import {
  asCompoundStructure,
  autoCompoundInstruction,
  defaultStructureForType,
  extractGapIds,
  instructionWordsFromMax,
  isCompoundType,
  variantFromType,
  WORD_LIMIT_OPTIONS,
  type CompoundGroupDraft,
  type CompoundStructure,
} from '../data/compound'
import {
  QUESTION_TYPE_LABELS,
  assignGroupsSlotNumbers,
  countScoringSlots,
  groupAllowedTypes,
  normaliseQuestionType,
  type Question,
  type QuestionGroup,
  type QuestionType,
  type SectionType,
  type SlotNumberingGroup,
  type SlotRange,
} from '../data/schema'
import { multiSelectValidationError } from '../data/multi-select'
import { CompoundStructureEditor } from './compound/compound-structure-editor'
import { QuestionEditor, type QuestionDraft } from './question-editor'

const MATCHING_SUBTYPES = new Set([
  'matching_headings',
  'matching_information',
  'matching_features',
  'map_labeling',
])

function toRoman(n: number): string {
  const vals = [10, 9, 5, 4, 1]
  const syms = ['x', 'ix', 'v', 'iv', 'i']
  let result = ''
  for (let i = 0; i < vals.length; i++) {
    while (n >= vals[i]) {
      result += syms[i]
      n -= vals[i]
    }
  }
  return result
}

function autoPrefix(qtype: string, index: number): string {
  return qtype === 'matching_headings'
    ? toRoman(index + 1)
    : String.fromCharCode(65 + index)
}

function stripOptionPrefix(opt: string): string {
  return opt.replace(/^[A-Za-z]+[.)]\s*/, '')
}

function formatWithPrefixes(texts: string[], qtype: string): string {
  return texts
    .map((t, i) => `${autoPrefix(qtype, i)}. ${t}`)
    .join('; ')
}

/** Stable id for unsaved drafts when computing section-wide slot numbers. */
function draftSlotKey(groupId: string, idx: number, id?: string): string {
  return id ?? `__draft-${groupId}-${idx}`
}

/**
 * IELTS display numbers for a draft row: cumulative across all groups in the section.
 * `baseOffset` is 0-based (questions start at baseOffset+1) — passage/part offset only.
 */
function draftDisplayRange(
  baseOffset: number,
  sectionGroups: SlotNumberingGroup[],
  groupId: string,
  groupType: string,
  drafts: QuestionDraft[],
  idx: number,
): SlotRange {
  const groups: SlotNumberingGroup[] = sectionGroups.map((g) => {
    if (g.id !== groupId) return g
    return {
      id: g.id,
      order: g.order,
      question_type: groupType,
      questions: drafts.map((d, i) => ({
        id: draftSlotKey(groupId, i, d.id),
        order: d.order,
        question_type: groupType,
        content: d.content,
        answer_key: d.answer_key,
      })),
    }
  })
  // Current group might be missing from sectionGroups (shouldn't happen) — append
  if (!groups.some((g) => g.id === groupId)) {
    groups.push({
      id: groupId,
      order: sectionGroups.length + 1,
      question_type: groupType,
      questions: drafts.map((d, i) => ({
        id: draftSlotKey(groupId, i, d.id),
        order: d.order,
        question_type: groupType,
        content: d.content,
        answer_key: d.answer_key,
      })),
    })
  }
  const ranges = assignGroupsSlotNumbers(groups, baseOffset)
  const key = draftSlotKey(groupId, idx, drafts[idx]?.id)
  return ranges.get(key) ?? { start: baseOffset + 1, end: baseOffset + 1 }
}

function optionsPlaceholder(qtype: string): string {
  if (qtype === 'matching_headings')
    return 'i. First heading; ii. Second heading; iii. Third heading'
  if (qtype === 'matching_information') return 'A; B; C; D; E; F; G'
  if (qtype === 'matching_features')
    return 'A. Person One; B. Person Two; C. Person Three'
  if (qtype === 'map_labeling') return 'A; B; C; D; E; F; G; H; I'
  return 'e.g. London; Paris; Berlin'
}

function instructionPlaceholder(qtype: string): string {
  if (qtype === 'true_false_ng')
    return 'Do the following statements agree with the information in the passage? Write TRUE, FALSE, or NOT GIVEN.'
  if (qtype === 'yes_no_ng')
    return 'Do the following statements agree with the views of the writer? Write YES, NO, or NOT GIVEN.'
  if (qtype === 'matching_headings')
    return 'The reading passage has several paragraphs. Choose the correct heading for each paragraph from the list of headings below.'
  if (qtype === 'matching_information')
    return 'The reading passage has several sections. Which section contains the following information?'
  if (qtype === 'matching_features')
    return 'Look at the following statements and the list of people below. Match each statement with the correct person.'
  if (qtype === 'sentence_completion')
    return 'Complete the sentences below. Choose NO MORE THAN THREE WORDS from the passage for each answer.'
  if (qtype === 'short_answer')
    return 'Answer the questions below. Choose NO MORE THAN THREE WORDS from the passage for each answer.'
  if (qtype === 'gap_fill')
    return 'Complete the notes below. Write NO MORE THAN TWO WORDS for each answer.'
  if (qtype === 'map_labeling')
    return 'Label the map below. Choose the correct letter, A-I.'
  if (isCompoundType(qtype))
    return autoCompoundInstruction(qtype, 2)
  return 'e.g. Choose the correct letter A, B, or C...'
}

function optionsLabel(qtype: string): string {
  if (qtype === 'matching_headings') return 'Headings list (semicolon-separated)'
  if (qtype === 'matching_information')
    return 'Section letters (semicolon-separated)'
  if (qtype === 'matching_features')
    return 'Features / People list (semicolon-separated)'
  if (qtype === 'gap_fill')
    return 'Word Bank (semicolon-separated)'
  if (qtype === 'map_labeling')
    return 'Map labels (e.g. A, B, C...)'
  return 'Shared Options (semicolon-separated)'
}

/** Shared option lists are only for matching / word-bank types — not MCQ subtitles. */
function needsSharedOptions(qtype: string): boolean {
  return (
    qtype === 'matching_headings' ||
    qtype === 'matching_information' ||
    qtype === 'matching_features' ||
    qtype === 'matching' ||
    qtype === 'gap_fill' ||
    qtype === 'map_labeling'
  )
}

function draftFromQuestion(q: Question): QuestionDraft {
  return {
    id: q.id,
    order: q.order,
    question_type: q.question_type,
    content: q.content,
    answer_key: q.answer_key,
    image_url: q.image_url ?? (q.content?.image_url as string | undefined) ?? null,
  }
}

function syncGapDrafts(
  structure: CompoundStructure,
  existing: QuestionDraft[],
  questionType: QuestionType,
): QuestionDraft[] {
  const gapIds = extractGapIds(structure)
  const byGap = new Map(
    existing
      .map((d) => [String(d.content?.gap_id ?? ''), d] as const)
      .filter(([id]) => id),
  )
  return gapIds.map((gapId, index) => {
    const prev = byGap.get(gapId)
    if (prev) {
      return {
        ...prev,
        order: index + 1,
        question_type: questionType,
        content: { ...prev.content, gap_id: gapId },
        answer_key: {
          ...(prev.answer_key ?? {}),
          correct: Array.isArray(prev.answer_key?.correct)
            ? prev.answer_key?.correct
            : prev.answer_key?.correct
              ? [String(prev.answer_key.correct)]
              : [],
          case_sensitive: false,
          max_words: structure.max_words_per_gap,
        },
      }
    }
    return {
      order: index + 1,
      question_type: questionType,
      content: { gap_id: gapId, hint: null },
      answer_key: {
        correct: [],
        case_sensitive: false,
        max_words: structure.max_words_per_gap,
      },
    }
  })
}

function withSyncedInstructionWords(
  structure: CompoundStructure,
): CompoundStructure {
  return {
    ...structure,
    instruction_words: instructionWordsFromMax(structure.max_words_per_gap),
  }
}

type CompoundSnapshot = {
  instruction: string
  subtitle: string
  questionType: string
  structure: CompoundStructure
}

function snapshotJson(s: CompoundSnapshot): string {
  return JSON.stringify(s)
}

type Props = {
  group: QuestionGroup
  groupNumber: number
  allowedTypes: QuestionType[]
  sectionType?: SectionType
  onRefresh: () => void
  onDraftChange?: (draft: CompoundGroupDraft | null) => void
  /** Called when the group's dirty state changes (true = has unsaved edits). */
  onDirtyChange?: (groupId: string, dirty: boolean) => void
  /**
   * 0-based IELTS offset for this section/passage/part only
   * (prior passages / listening parts). Do NOT include prior groups —
   * those are handled via sectionGroups.
   */
  numberOffset?: number
  /** All groups in this section (saved questions); live overrides applied inside. */
  sectionGroups?: SlotNumberingGroup[]
  /**
   * Highest question.order already saved in this section (other groups).
   * @deprecated Order is now local to each group; kept optional for compat.
   */
  sectionMaxOrder?: number
  /** Optional slot ranges for Listening multi_select-aware numbering */
  slotRanges?: Map<string, { start: number; end: number }>
}

export function QuestionGroupEditor({
  group,
  groupNumber: _groupNumber,
  allowedTypes,
  sectionType,
  onRefresh,
  onDraftChange,
  onDirtyChange,
  numberOffset = 0,
  sectionGroups,
  sectionMaxOrder: _sectionMaxOrder = 0,
  slotRanges: _slotRanges,
}: Props) {
  const normalisedType = normaliseQuestionType(group.question_type)
  const isMismatch = !allowedTypes.includes(normalisedType)
  const dropdownTypes: QuestionType[] = isMismatch
    ? [normalisedType, ...allowedTypes]
    : allowedTypes
  const initialStructure = useMemo(() => {
    const existing = asCompoundStructure(group.options_shared)
    return existing
      ? withSyncedInstructionWords(existing)
      : withSyncedInstructionWords(defaultStructureForType(group.question_type))
  }, [group.options_shared, group.question_type])

  const [instruction, setInstruction] = useState(group.instruction ?? '')
  const [subtitle, setSubtitle] = useState(group.subtitle ?? '')
  const [instructionTouched, setInstructionTouched] = useState(
    Boolean(group.instruction?.trim()),
  )
  const [questionType, setQuestionType] = useState<string>(normalisedType)
  const [optionsShared, setOptionsShared] = useState<string>(
    Array.isArray(
      (group.options_shared as { options?: unknown[] } | null)?.options,
    )
      ? (
          (group.options_shared as { options: string[] }).options ?? []
        ).join('; ')
      : '',
  )
  const [optionTexts, setOptionTexts] = useState<string[]>(() => {
    const raw = (group.options_shared as { options?: string[] } | null)?.options
    if (!Array.isArray(raw) || raw.length === 0) return ['', '']
    return group.question_type === 'map_labeling' ? raw : raw.map(stripOptionPrefix)
  })
  const [questionsHeading, setQuestionsHeading] = useState<string>(
    (group.options_shared as { questions_heading?: string } | null)?.questions_heading ?? '',
  )
  const [mapImageUrl, setMapImageUrl] = useState<string>(
    (group.options_shared as { image_url?: string } | null)?.image_url ?? '',
  )
  const [uploadingMapImage, setUploadingMapImage] = useState(false)

  // Keep local map image in sync after server refresh
  const savedMapImage =
    (group.options_shared as { image_url?: string } | null)?.image_url ?? ''
  const prevSavedMapImageRef = useRef(savedMapImage)
  useEffect(() => {
    if (prevSavedMapImageRef.current === savedMapImage) return
    prevSavedMapImageRef.current = savedMapImage
    setMapImageUrl(savedMapImage)
  }, [savedMapImage])
  const [structure, setStructure] = useState<CompoundStructure>(initialStructure)
  const [savedSnapshot, setSavedSnapshot] = useState<CompoundSnapshot>(() => ({
    instruction: group.instruction ?? '',
    subtitle: group.subtitle ?? '',
    questionType: group.question_type,
    structure: initialStructure,
  }))
  const [deletingGroup, setDeletingGroup] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [localQuestions, setLocalQuestions] = useState<QuestionDraft[]>(
    group.questions.map(draftFromQuestion),
  )
  const [savingIdx, setSavingIdx] = useState<number | null>(null)

  // Sync localQuestions with server data after onRefresh, preserving unsaved drafts
  const prevGroupQuestionsRef = useRef(group.questions)
  useEffect(() => {
    if (prevGroupQuestionsRef.current === group.questions) return
    prevGroupQuestionsRef.current = group.questions
    setLocalQuestions((prev) => {
      const serverDrafts = group.questions.map(draftFromQuestion)
      const serverIds = new Set(serverDrafts.map((d) => d.id))
      const unsaved = prev.filter((d) => !d.id && d.content && Object.keys(d.content).length > 0)
      const merged = [...serverDrafts, ...unsaved.filter((u) => !serverIds.has(u.id))]
      return merged
    })
  }, [group.questions])

  const [focusedCell, setFocusedCell] = useState<{
    row: number
    col: number
  } | null>(null)

  const compound = isCompoundType(questionType)
  const onDraftChangeRef = useRef(onDraftChange)
  const lastDraftJsonRef = useRef<string>('')
  const draftDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    onDraftChangeRef.current = onDraftChange
  }, [onDraftChange])

  const isDirty = useMemo(() => {
    if (compound) {
      return (
        snapshotJson({ instruction, subtitle, questionType, structure }) !==
        snapshotJson(savedSnapshot)
      )
    }
    const savedInstruction = group.instruction ?? ''
    const savedSubtitle = group.subtitle ?? ''
    const savedType = group.question_type
    const savedOpts = Array.isArray(
      (group.options_shared as { options?: unknown[] } | null)?.options,
    )
      ? ((group.options_shared as { options: string[] }).options ?? []).join('; ')
      : ''
    const savedQHeading =
      (group.options_shared as { questions_heading?: string } | null)?.questions_heading ?? ''
    const savedMapImage =
      (group.options_shared as { image_url?: string } | null)?.image_url ?? ''
    return (
      instruction !== savedInstruction ||
      subtitle !== savedSubtitle ||
      questionType !== savedType ||
      optionsShared !== savedOpts ||
      questionsHeading !== savedQHeading ||
      mapImageUrl !== savedMapImage
    )
  }, [compound, instruction, subtitle, questionType, structure, savedSnapshot, optionsShared, questionsHeading, mapImageUrl, group.instruction, group.subtitle, group.question_type, group.options_shared])

  useEffect(() => {
    onDirtyChange?.(group.id, isDirty)
  }, [isDirty, group.id, onDirtyChange])

  const gapDrafts = useMemo(() => {
    if (!compound) return []
    return syncGapDrafts(structure, localQuestions, questionType as QuestionType)
  }, [compound, structure, localQuestions, questionType])

  const resolvedSectionGroups: SlotNumberingGroup[] = useMemo(() => {
    if (sectionGroups && sectionGroups.length > 0) return sectionGroups
    return [
      {
        id: group.id,
        order: group.order,
        question_type: group.question_type,
        questions: group.questions.map((q) => ({
          id: q.id,
          order: q.order,
          question_type: q.question_type,
          content: q.content,
          answer_key: q.answer_key,
        })),
      },
    ]
  }, [sectionGroups, group.id, group.order, group.question_type, group.questions])

  /** 0-based offset for the first scoring slot in this group (gaps / compound). */
  const groupBaseOffset = useMemo(() => {
    let prior = 0
    for (const g of [...resolvedSectionGroups].sort((a, b) => a.order - b.order)) {
      if (g.id === group.id) break
      prior += countScoringSlots(
        g.questions.map((q) => ({
          question_type: (q.question_type ??
            g.question_type ??
            'mcq') as Question['question_type'],
          content: q.content ?? {},
          answer_key: q.answer_key ?? null,
        })),
      )
    }
    return numberOffset + prior
  }, [resolvedSectionGroups, group.id, numberOffset])

  // Notify parent for live preview (debounced 300ms; JSON guard against loops)
  useEffect(() => {
    const cb = onDraftChangeRef.current
    if (!cb) return

    if (draftDebounceRef.current) clearTimeout(draftDebounceRef.current)

    draftDebounceRef.current = setTimeout(() => {
      const normalizedSubtitle = subtitle.trim() || null
      const questionRows = localQuestions.map((d) => ({
        id: d.id,
        order: d.order,
        content: d.content,
        answer_key: d.answer_key,
        image_url: d.image_url ?? null,
      }))
      if (!compound) {
        const liveOpts = MATCHING_SUBTYPES.has(questionType)
          ? questionType === 'map_labeling'
            ? optionTexts.filter((t) => t.trim().length > 0)
            : optionTexts
                .map((t, i) => `${autoPrefix(questionType, i)}. ${t}`)
                .filter((s) => s.replace(/^[A-Za-z]+\.\s*$/, '').length > 0)
          : undefined
        const payload: CompoundGroupDraft = {
          groupId: group.id,
          questionType,
          instruction,
          subtitle: normalizedSubtitle,
          gapDrafts: [],
          questions: questionRows,
          optionsShared: liveOpts,
          mapImageUrl: mapImageUrl.trim() || null,
          questionsHeading: questionsHeading.trim() || undefined,
        }
        const json = JSON.stringify(payload)
        if (json === lastDraftJsonRef.current) return
        lastDraftJsonRef.current = json
        cb(payload)
        return
      }
      const payload: CompoundGroupDraft = {
        groupId: group.id,
        questionType,
        instruction,
        subtitle: normalizedSubtitle,
        structure,
        gapDrafts: gapDrafts.map((d) => ({
          id: d.id,
          order: d.order,
          content: d.content,
          answer_key: d.answer_key,
        })),
        questions: questionRows,
        focusedCell,
      }
      const json = JSON.stringify(payload)
      if (json === lastDraftJsonRef.current) return
      lastDraftJsonRef.current = json
      cb(payload)
    }, 300)

    return () => {
      if (draftDebounceRef.current) clearTimeout(draftDebounceRef.current)
    }
  }, [compound, group.id, questionType, instruction, subtitle, structure, gapDrafts, focusedCell, localQuestions, optionTexts, questionsHeading, mapImageUrl])

  // Immediate focus sync (no debounce) so preview highlight feels instant
  useEffect(() => {
    const cb = onDraftChangeRef.current
    if (!cb || !compound) return
    const payload: CompoundGroupDraft = {
      groupId: group.id,
      questionType,
      instruction,
      subtitle: subtitle.trim() || null,
      structure,
      gapDrafts: gapDrafts.map((d) => ({
        id: d.id,
        order: d.order,
        content: d.content,
        answer_key: d.answer_key,
      })),
      focusedCell,
    }
    const json = JSON.stringify(payload)
    if (json === lastDraftJsonRef.current) return
    lastDraftJsonRef.current = json
    cb(payload)
  }, [focusedCell]) // eslint-disable-line react-hooks/exhaustive-deps -- intentional: focus-only flush

  const persistCompoundMeta = useCallback(
    async (
      nextInstruction: string,
      nextSubtitle: string,
      nextStructure: CompoundStructure,
      nextType: string,
    ) => {
      if (!isCompoundType(nextType)) return false
      const synced = withSyncedInstructionWords(nextStructure)
      setSaving(true)
      try {
        await updateQuestionGroup(group.id, {
          question_type: nextType,
          instruction: nextInstruction,
          subtitle: nextSubtitle.trim() || null,
          options_shared: synced as unknown as Record<string, unknown>,
        })
        // Prune orphan gap questions
        const keep = new Set(extractGapIds(synced))
        for (const q of group.questions) {
          const gapId = String(q.content?.gap_id ?? '')
          if (gapId && !keep.has(gapId)) {
            await deleteQuestion(group.section_id, q.id)
          }
        }
        setSavedSnapshot({
          instruction: nextInstruction,
          subtitle: nextSubtitle,
          questionType: nextType,
          structure: synced,
        })
        setStructure(synced)
        onRefresh()
        toast.success('Group saved')
        return true
      } catch (err) {
        const axErr = err as AxiosError<{ detail?: string }>
        toast.error(
          typeof axErr?.response?.data?.detail === 'string'
            ? axErr.response.data.detail
            : 'Failed to save group',
        )
        return false
      } finally {
        setSaving(false)
      }
    },
    [group.id, group.questions, group.section_id, onRefresh],
  )

  const handleSaveCompound = () => {
    void persistCompoundMeta(instruction, subtitle, structure, questionType)
  }

  /** Save from inside the Settings popover — closes popover on success. */
  const handleSaveSettings = async () => {
    const ok = await persistCompoundMeta(instruction, subtitle, structure, questionType)
    if (ok) setSettingsOpen(false)
  }

  const handleStructureChange = (next: CompoundStructure) => {
    const synced = withSyncedInstructionWords(next)
    setStructure(synced)
    setLocalQuestions((prev) =>
      syncGapDrafts(synced, prev, questionType as QuestionType),
    )
  }

  const handleWordLimit = (n: number) => {
    const synced = withSyncedInstructionWords({
      ...structure,
      max_words_per_gap: n,
    })
    setStructure(synced)
    const nextInstruction = instructionTouched
      ? instruction
      : autoCompoundInstruction(questionType, n)
    if (!instructionTouched) setInstruction(nextInstruction)
    setLocalQuestions((prev) =>
      syncGapDrafts(synced, prev, questionType as QuestionType),
    )
  }

  const handleInstructionChange = (value: string) => {
    setInstruction(value)
    setInstructionTouched(true)
  }

  const handleTypeChange = (type: string) => {
    setQuestionType(type)
    if (isCompoundType(type)) {
      const next = withSyncedInstructionWords(defaultStructureForType(type))
      setStructure(next)
      if (!instructionTouched) {
        setInstruction(autoCompoundInstruction(type, next.max_words_per_gap))
      }
      setLocalQuestions((prev) =>
        syncGapDrafts(next, prev, type as QuestionType),
      )
    }
  }

  const revertSettings = () => {
    setInstruction(savedSnapshot.instruction)
    setSubtitle(savedSnapshot.subtitle)
    setInstructionTouched(Boolean(savedSnapshot.instruction.trim()))
    setStructure(
      withSyncedInstructionWords({
        ...structure,
        max_words_per_gap: savedSnapshot.structure.max_words_per_gap,
      }),
    )
  }

  const handleSettingsOpenChange = (open: boolean) => {
    if (!open) {
      // Silently revert unsaved settings changes when the popover closes
      // (either via Cancel button or click-outside). No confirm dialog.
      revertSettings()
    }
    setSettingsOpen(open)
  }

  const updateOptionTexts = (next: string[]) => {
    setOptionTexts(next)
    setOptionsShared(
      questionType === 'map_labeling'
        ? next.join('; ')
        : formatWithPrefixes(next, questionType),
    )
  }

  const [savingNonCompound, setSavingNonCompound] = useState(false)

  /** Persist map image immediately so Take/Preview see it without waiting for Save. */
  const persistMapImage = async (url: string | null) => {
    const existing =
      (group.options_shared as Record<string, unknown> | null) ?? {}
    const liveOpts = optionTexts.map((t) => t.trim()).filter(Boolean)
    const savedOpts = Array.isArray(existing.options)
      ? (existing.options as string[]).filter((o) => String(o).trim())
      : []
    const opts = liveOpts.length > 0 ? liveOpts : savedOpts
    const nextShared: Record<string, unknown> = {
      ...existing,
      options: opts.length > 0 ? opts : ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
    }
    if (url) nextShared.image_url = url
    else delete nextShared.image_url

    setMapImageUrl(url ?? '')
    await updateQuestionGroup(group.id, { options_shared: nextShared })
    onRefresh()
  }

  const handleSaveMetaNonCompound = async () => {
    const opts = optionsShared.trim()
      ? optionsShared
          .split(';')
          .map((o) => o.trim())
          .filter(Boolean)
      : []

    if (questionType === 'matching_headings' && opts.length < 3) {
      toast.error('Matching Headings requires at least 3 headings.')
      return
    }
    if (
      (questionType === 'matching_features' || questionType === 'matching_information') &&
      opts.length < 2
    ) {
      toast.error('Matching requires at least 2 options.')
      return
    }

    setSavingNonCompound(true)
    try {
      const qh = questionsHeading.trim() || undefined
      const imgUrl = mapImageUrl.trim() || undefined
      const shared =
        needsSharedOptions(questionType) && opts.length > 0
          ? {
              options: opts,
              ...(qh ? { questions_heading: qh } : {}),
              ...(questionType === 'map_labeling' && imgUrl ? { image_url: imgUrl } : {}),
            }
          : null
      await updateQuestionGroup(group.id, {
        question_type: questionType,
        instruction,
        subtitle: subtitle.trim() || null,
        options_shared: shared,
      })
      toast.success('Group saved')
      onRefresh()
    } catch {
      toast.error('Failed to save group')
    } finally {
      setSavingNonCompound(false)
    }
  }

  const handleDeleteGroup = async () => {
    setDeletingGroup(true)
    try {
      await deleteQuestionGroup(group.id)
      toast.success('Group deleted')
      onRefresh()
    } catch {
      toast.error('Failed to delete group')
    } finally {
      setDeletingGroup(false)
    }
  }

  const handleAddQuestion = () => {
    const isMulti = questionType === 'multi_select'
    setLocalQuestions((prev) => {
      // Order is local to the group (1, 2, 3…). Use max(count, maxOrder)+1 so
      // new questions never conflict with existing ones even when existing orders
      // are section-cumulative (legacy data created before the per-group fix).
      const localMax = prev.reduce((m, q) => Math.max(m, q.order), 0)
      const nextOrder = Math.max(prev.length, localMax) + 1
      return [
        ...prev,
        {
          order: nextOrder,
          question_type: questionType as QuestionType,
          content: isMulti
            ? { choose_n: 2, options: ['', '', '', '', ''] }
            : {},
          answer_key: isMulti ? { correct: [] } : null,
        },
      ]
    })
  }

  const handleSaveQuestion = async (draft: QuestionDraft, idx: number) => {
    if (savingIdx !== null) return
    if (questionType === 'multi_select') {
      const err = multiSelectValidationError(draft.content, draft.answer_key)
      if (err) {
        toast.error(err)
        return
      }
    }
    const orderClash = localQuestions.some(
      (q, i) => i !== idx && q.order === draft.order,
    )
    if (orderClash) {
      toast.error('Order already exists')
      return
    }
    setSavingIdx(idx)
    try {
      let saved: Question
      if (draft.id) {
        saved = await updateQuestion(group.section_id, draft.id, {
          order: draft.order,
          content: draft.content,
          answer_key: draft.answer_key ?? undefined,
          image_url: draft.image_url ?? null,
        })
      } else {
        saved = await createQuestionInGroup(group.id, {
          order: draft.order,
          content: draft.content,
          answer_key: draft.answer_key ?? undefined,
          image_url: draft.image_url ?? null,
        })
      }
      setLocalQuestions((prev) =>
        prev.map((q, i) => (i === idx ? draftFromQuestion(saved) : q)),
      )
      const needsKey = !['essay', 'speaking_part'].includes(saved.question_type)
      const keyEmpty = !saved.answer_key || Object.keys(saved.answer_key).length === 0
      if (needsKey && keyEmpty) {
        toast.warning('Question saved without correct answer — students will not get credit for this question.')
      } else {
        toast.success('Question saved')
      }
      onRefresh()
    } catch (err) {
      const axErr = err as AxiosError<{ detail?: string | { msg: string }[] }>
      const detail = axErr?.response?.data?.detail
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? (detail[0]?.msg ?? 'Failed to save question')
            : 'Failed to save question'
      toast.error(msg)
    } finally {
      setSavingIdx(null)
    }
  }

  const handleSaveGap = async (draft: QuestionDraft) => {
    try {
      // Flush current structure before gap validation on the server
      await updateQuestionGroup(group.id, {
        question_type: questionType,
        instruction,
        options_shared: withSyncedInstructionWords(
          structure,
        ) as unknown as Record<string, unknown>,
      })
      setSavedSnapshot({
        instruction,
        subtitle,
        questionType,
        structure: withSyncedInstructionWords(structure),
      })

      const gapId = String(draft.content.gap_id)
      // Use localQuestions (updated immediately after each save) instead of the
      // stale group.questions prop — prevents duplicate creates when onRefresh
      // hasn't propagated yet.
      const existingLocal = localQuestions.find(
        (d) => String(d.content?.gap_id ?? '') === gapId && d.id != null,
      )
      const effectiveType = isCompoundType(group.question_type)
        ? group.question_type
        : questionType

      let saved: Question
      if (existingLocal?.id) {
        saved = await updateQuestion(group.section_id, existingLocal.id, {
          order: existingLocal.order,
          question_type: effectiveType,
          content: draft.content,
          answer_key: draft.answer_key ?? undefined,
        })
      } else {
        // Omit order — backend assigns next_question_order (max+1 in section),
        // guaranteeing no conflict with questions from other groups.
        // Backend also upserts by gap_id, so concurrent saves are safe.
        saved = await createQuestionInGroup(group.id, {
          question_type: effectiveType,
          content: draft.content,
          answer_key: draft.answer_key ?? undefined,
        })
      }

      setLocalQuestions((prev) => {
        const byGap = new Map(
          prev.map((d) => [String(d.content?.gap_id ?? ''), d] as const),
        )
        byGap.set(gapId, draftFromQuestion(saved))
        return syncGapDrafts(
          structure,
          Array.from(byGap.values()),
          questionType as QuestionType,
        )
      })
      const keyEmpty = !saved.answer_key || Object.keys(saved.answer_key).length === 0
      if (keyEmpty) {
        toast.warning(`Gap ${gapId} saved without correct answer — students will not get credit.`)
      } else {
        toast.success(`Gap ${gapId} saved`)
      }
      onRefresh()
    } catch (err: unknown) {
      const axErr = err as AxiosError<{ detail?: string | { msg: string }[] }>
      const detail = axErr?.response?.data?.detail
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? (detail[0]?.msg ?? 'Failed to save gap')
            : err instanceof Error
              ? err.message
              : 'Failed to save gap'
      throw new Error(msg)
    }
  }

  const handleDeleteQuestion = async (draft: QuestionDraft, idx: number) => {
    if (draft.id) {
      try {
        await deleteQuestion(group.section_id, draft.id)
        toast.success('Question deleted')
        onRefresh()
      } catch {
        toast.error('Failed to delete question')
        return
      }
    }
    setLocalQuestions((prev) => prev.filter((_, i) => i !== idx))
  }

  const getGapDraft = useCallback(
    (gapId: string): QuestionDraft => {
      const found = gapDrafts.find((d) => String(d.content?.gap_id) === gapId)
      if (found) return found
      return {
        order: gapDrafts.length + 1,
        question_type: questionType as QuestionType,
        content: { gap_id: gapId, hint: null },
        answer_key: {
          correct: [],
          case_sensitive: false,
          max_words: structure.max_words_per_gap,
        },
      }
    },
    [gapDrafts, questionType, structure.max_words_per_gap],
  )

  const parsedOptions = optionsShared.trim()
    ? optionsShared
        .split(';')
        .map((o) => o.trim())
        .filter(Boolean)
    : []

  const hasLegacyCompound =
    group.questions.some(
      (q) =>
        q.content?.table_id != null ||
        q.content?.notes_id != null ||
        q.content?.gap_key != null,
    ) && !asCompoundStructure(group.options_shared)

  return (
    <div className='space-y-3 rounded-lg border border-border bg-card p-3'>
      {/* Compact primary toolbar */}
      <div className='flex flex-wrap items-center gap-2'>
        <span className='rounded-md bg-muted px-2 py-1 text-xs font-semibold text-foreground'>
          {QUESTION_TYPE_LABELS[questionType as QuestionType] ?? questionType}
        </span>
        <Select value={questionType} onValueChange={handleTypeChange}>
          <SelectTrigger className='h-8 w-[160px] text-sm' aria-label='Question type'>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {groupAllowedTypes(dropdownTypes).map((g) => (
              <SelectGroup key={g.label}>
                <SelectLabel>{g.label}</SelectLabel>
                {g.types.map((t) => (
                  <SelectItem key={t} value={t}>
                    {QUESTION_TYPE_LABELS[t]}
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}
          </SelectContent>
        </Select>

        {compound && (
          <Popover open={settingsOpen} onOpenChange={handleSettingsOpenChange}>
            <PopoverTrigger asChild>
              <Button
                type='button'
                variant='ghost'
                size='icon'
                className='size-8'
                aria-label='Group settings'
              >
                <Settings2 className='size-4' />
              </Button>
            </PopoverTrigger>
            <PopoverContent className='w-96 space-y-3' align='start'>
              <div className='flex items-center justify-between'>
                <p className='text-sm font-semibold'>Group Settings</p>
              </div>
              <div className='space-y-1.5'>
                <Label className='text-xs'>Instruction</Label>
                <Textarea
                  rows={3}
                  className='text-sm'
                  value={instruction}
                  onChange={(e) => handleInstructionChange(e.target.value)}
                  placeholder={instructionPlaceholder(questionType)}
                />
              </div>
              <div className='space-y-1.5'>
                <Label className='text-xs'>Subtitle (optional)</Label>
                <Input
                  className='h-8 text-sm'
                  value={subtitle}
                  maxLength={500}
                  onChange={(e) => setSubtitle(e.target.value)}
                  placeholder='e.g. Loneliness and mental health'
                />
              </div>
              <div className='space-y-1.5'>
                <Label className='text-xs'>Word limit per gap</Label>
                <Select
                  value={String(structure.max_words_per_gap)}
                  onValueChange={(v) => handleWordLimit(Number(v))}
                >
                  <SelectTrigger className='h-8 text-sm'>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {WORD_LIMIT_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={String(opt.value)}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className='flex justify-end gap-2 border-t pt-2'>
                <Button
                  type='button'
                  variant='ghost'
                  size='sm'
                  onClick={() => {
                    revertSettings()
                    setSettingsOpen(false)
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type='button'
                  size='sm'
                  disabled={!isDirty || saving}
                  onClick={() => void handleSaveSettings()}
                >
                  {saving && <Loader2 className='mr-1 size-3.5 animate-spin' />}
                  Save
                </Button>
              </div>
            </PopoverContent>
          </Popover>
        )}

        {compound && (
          <Button
            type='button'
            size='sm'
            className='h-8'
            disabled={!isDirty || saving}
            onClick={() => void handleSaveCompound()}
          >
            {saving && <Loader2 className='mr-1 size-3.5 animate-spin' />}
            Save
            {isDirty && (
              <span className='ml-1.5 size-1.5 rounded-full bg-warning' />
            )}
          </Button>
        )}

        <div className='ml-auto'>
          <Button
            variant='ghost'
            size='icon'
            className='size-8 text-muted-foreground hover:text-destructive'
            onClick={() => void handleDeleteGroup()}
            disabled={deletingGroup}
            aria-label='Delete group'
          >
            {deletingGroup ? (
              <Loader2 className='size-4 animate-spin' />
            ) : (
              <Trash2 className='size-4' />
            )}
          </Button>
        </div>
      </div>

      {(hasLegacyCompound || (group.question_type === 'matching' && !MATCHING_SUBTYPES.has(questionType)) || (isMismatch && sectionType)) && (
        <div className='space-y-1.5'>
          {hasLegacyCompound && (
            <div className='flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning-foreground'>
              <AlertTriangle className='mt-0.5 size-3.5 shrink-0' />
              <span>Legacy compound data detected. Consider recreating as a compound type.</span>
            </div>
          )}
          {group.question_type === 'matching' && !MATCHING_SUBTYPES.has(questionType) && (
            <div className='flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning-foreground'>
              <AlertTriangle className='mt-0.5 size-3.5 shrink-0' />
              <span>Consider specifying: Matching Headings, Information, or Features.</span>
            </div>
          )}
          {isMismatch && sectionType && (
            <div className='flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning-foreground'>
              <AlertTriangle className='mt-0.5 size-3.5 shrink-0' />
              <span>
                <strong>{QUESTION_TYPE_LABELS[group.question_type as QuestionType] ?? group.question_type}</strong>
                {' '}is not standard for {sectionType}. It still works, but consider changing it.
              </span>
            </div>
          )}
        </div>
      )}

      {/* Non-compound meta */}
      {!compound && (
        <>
          {needsSharedOptions(questionType) && (
            MATCHING_SUBTYPES.has(questionType) ? (
              <div className='space-y-2'>
                <Label className='text-xs text-muted-foreground'>
                  {optionsLabel(questionType)}
                </Label>
                {optionTexts.map((text, i) => (
                  <div key={i} className='flex items-center gap-2'>
                    {questionType !== 'map_labeling' && (
                      <span className='w-8 text-right text-sm font-medium text-muted-foreground'>
                        {autoPrefix(questionType, i)}.
                      </span>
                    )}
                    <Input
                      className='h-8 flex-1 text-sm'
                      placeholder={
                        questionType === 'map_labeling'
                          ? String.fromCharCode(65 + i)
                          : `Option ${autoPrefix(questionType, i)}`
                      }
                      value={text}
                      onChange={(e) => {
                        const next = [...optionTexts]
                        next[i] = e.target.value
                        updateOptionTexts(next)
                      }}
                    />
                    <Button
                      type='button'
                      variant='ghost'
                      size='icon'
                      className='size-8 text-muted-foreground hover:text-destructive'
                      disabled={optionTexts.length <= 2}
                      onClick={() => updateOptionTexts(optionTexts.filter((_, j) => j !== i))}
                    >
                      <Trash2 className='size-4' />
                    </Button>
                  </div>
                ))}
                <Button
                  type='button'
                  variant='outline'
                  size='sm'
                  disabled={optionTexts.length >= 26}
                  onClick={() => updateOptionTexts([...optionTexts, ''])}
                >
                  <Plus className='mr-1 size-4' /> Add option
                </Button>
              </div>
            ) : (
              <div className='grid grid-cols-2 gap-3'>
                <div className='space-y-1.5 col-span-2 sm:col-span-1'>
                  <Label className='text-xs text-muted-foreground'>
                    {optionsLabel(questionType)}
                  </Label>
                  <Input
                    className='h-8 text-sm'
                    placeholder={optionsPlaceholder(questionType)}
                    value={optionsShared}
                    onChange={(e) => setOptionsShared(e.target.value)}
                  />
                </div>
              </div>
            )
          )}
          {questionType === 'map_labeling' && (
            <div className='space-y-1.5'>
              <Label className='text-xs text-muted-foreground'>Map image</Label>
              {mapImageUrl ? (
                <div className='relative inline-block'>
                  <img
                    src={mediaUrl(mapImageUrl)}
                    alt='Map'
                    className='max-h-48 rounded-lg border border-border object-contain'
                  />
                  <Button
                    type='button'
                    variant='ghost'
                    size='icon'
                    className='absolute -right-2 -top-2 size-6 rounded-full bg-card shadow'
                    onClick={() => void persistMapImage(null)}
                    disabled={uploadingMapImage}
                  >
                    <X className='size-3.5' />
                  </Button>
                </div>
              ) : (
                <label className='flex cursor-pointer items-center gap-2 rounded-md border border-dashed border-border px-3 py-4 text-sm text-muted-foreground hover:border-primary/40 hover:bg-muted/50'>
                  {uploadingMapImage ? (
                    <Loader2 className='size-4 animate-spin' />
                  ) : (
                    <ImagePlus className='size-4' />
                  )}
                  {uploadingMapImage ? 'Uploading...' : 'Upload map image'}
                  <input
                    type='file'
                    accept='image/*'
                    className='hidden'
                    disabled={uploadingMapImage}
                    onChange={async (e) => {
                      const file = e.target.files?.[0]
                      if (!file) return
                      setUploadingMapImage(true)
                      try {
                        const url = await uploadImage(file)
                        await persistMapImage(url)
                        toast.success('Map image uploaded')
                      } catch {
                        toast.error('Failed to upload image')
                      } finally {
                        setUploadingMapImage(false)
                        e.target.value = ''
                      }
                    }}
                  />
                </label>
              )}
            </div>
          )}
          <div className='space-y-1.5'>
            <Label className='text-xs text-muted-foreground'>Instruction</Label>
            <Textarea
              rows={2}
              placeholder={instructionPlaceholder(questionType)}
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
            />
          </div>
          <div className='space-y-1.5'>
            <Label className='text-xs text-muted-foreground'>Subtitle (optional)</Label>
            <Input
              className='h-8 text-sm'
              maxLength={500}
              placeholder='e.g. Loneliness and mental health'
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
            />
          </div>
          {MATCHING_SUBTYPES.has(questionType) && (
            <div className='space-y-1.5'>
              <Label className='text-xs text-muted-foreground'>Questions heading (optional)</Label>
              <Input
                className='h-8 text-sm'
                placeholder='e.g. Area of voluntary work'
                value={questionsHeading}
                onChange={(e) => setQuestionsHeading(e.target.value)}
              />
            </div>
          )}
          <div className='flex justify-end'>
            <Button
              variant='outline'
              size='sm'
              disabled={!isDirty || savingNonCompound}
              onClick={() => void handleSaveMetaNonCompound()}
            >
              {savingNonCompound && <Loader2 className='mr-1 size-3.5 animate-spin' />}
              Save Group Settings
              {isDirty && (
                <span className='ml-1.5 size-1.5 rounded-full bg-warning' />
              )}
            </Button>
          </div>
        </>
      )}

      {/* Compound diagram image (optional) — shown above the completion card */}
      {compound && (
        <div className='space-y-1.5'>
          <Label className='text-xs text-muted-foreground'>Diagram image (optional)</Label>
          {structure.image_url ? (
            <div className='relative inline-block'>
              <img
                src={mediaUrl(structure.image_url)}
                alt='Diagram'
                className='max-h-48 rounded-lg border border-border object-contain'
              />
              <Button
                type='button'
                variant='ghost'
                size='icon'
                className='absolute -right-2 -top-2 size-6 rounded-full bg-card shadow'
                onClick={() => {
                  const { image_url: _omit, ...rest } = structure
                  setStructure(rest as CompoundStructure)
                }}
                disabled={uploadingMapImage}
              >
                <X className='size-3.5' />
              </Button>
            </div>
          ) : (
            <label className='flex cursor-pointer items-center gap-2 rounded-md border border-dashed border-border px-3 py-4 text-sm text-muted-foreground hover:border-primary/40 hover:bg-muted/50'>
              {uploadingMapImage ? (
                <Loader2 className='size-4 animate-spin' />
              ) : (
                <ImagePlus className='size-4' />
              )}
              {uploadingMapImage ? 'Uploading...' : 'Upload diagram image'}
              <input
                type='file'
                accept='image/*'
                className='hidden'
                disabled={uploadingMapImage}
                onChange={async (e) => {
                  const file = e.target.files?.[0]
                  if (!file) return
                  setUploadingMapImage(true)
                  try {
                    const url = await uploadImage(file)
                    setStructure({ ...structure, image_url: url })
                    toast.success('Diagram image uploaded')
                  } catch {
                    toast.error('Failed to upload image')
                  } finally {
                    setUploadingMapImage(false)
                    e.target.value = ''
                  }
                }}
              />
            </label>
          )}
          <p className='text-[11px] text-muted-foreground'>
            Appears above the card. Press the top Save button to persist.
          </p>
        </div>
      )}

      {/* Compound structure */}
      {compound && (
        <CompoundStructureEditor
          variant={variantFromType(questionType)}
          structure={structure}
          onChange={handleStructureChange}
          gapEdit={{
            getDraft: getGapDraft,
            onSaveGap: handleSaveGap,
            maxWords: structure.max_words_per_gap,
            numberOffset: groupBaseOffset,
          }}
          onFocusedCellChange={setFocusedCell}
        />
      )}

      {/* Non-compound questions */}
      {!compound && (() => {
        // Sort once per render. Q-number labels use this order to match
        // assignGroupsSlotNumbers (which also sorts by order internally).
        const sortedQuestions = [...localQuestions].sort((a, b) => a.order - b.order)
        return (
        <div className='space-y-3 pt-1'>
          {sortedQuestions.map((q, sortedIdx) => {
            // Original index needed for state mutations (onChange / onDelete / onSave)
            const origIdx = localQuestions.indexOf(q)
            const range = draftDisplayRange(
              numberOffset,
              resolvedSectionGroups,
              group.id,
              questionType,
              sortedQuestions,
              sortedIdx,
            )
            return (
            <div key={origIdx}>
              <QuestionEditor
                question={q}
                questionNumber={range.start}
                questionNumberEnd={
                  range.end !== range.start ? range.end : undefined
                }
                allowedTypes={allowedTypes}
                groupType={questionType as QuestionType}
                sharedOptions={
                  MATCHING_SUBTYPES.has(questionType)
                    ? parsedOptions
                    : undefined
                }
                onChange={(updated) =>
                  setLocalQuestions((prev) =>
                    prev.map((x, i) => (i === origIdx ? updated : x)),
                  )
                }
                onDelete={() => void handleDeleteQuestion(q, origIdx)}
              />
              <div className='mt-1 flex items-center justify-end gap-2'>
                {isDirty && (
                  <span className='text-xs text-warning-foreground'>
                    Save group settings first
                  </span>
                )}
                <Button
                  size='sm'
                  variant='outline'
                  disabled={
                    savingIdx !== null ||
                    isDirty ||
                    (questionType === 'multi_select' &&
                      multiSelectValidationError(q.content, q.answer_key) !=
                        null) ||
                    localQuestions.some(
                      (other, i) => i !== origIdx && other.order === q.order,
                    )
                  }
                  onClick={() => void handleSaveQuestion(q, origIdx)}
                >
                  {savingIdx === origIdx ? 'Saving…' : 'Save question'}
                </Button>
              </div>
            </div>
            )
          })}

          <Button variant='outline' size='sm' onClick={handleAddQuestion}>
            <Plus className='mr-1 size-4' /> Add Question
          </Button>
        </div>
        )
      })()}
    </div>
  )
}
