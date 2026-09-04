import { createElement, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

type Props = {
  children: ReactNode
  className?: string
}

export function InstructionBlock({ children, className }: Props) {
  return (
    <div
      className={cn(
        'rounded-lg border-l-[3px] border-blue-500 bg-slate-50 p-4 text-sm leading-[1.7] text-slate-700',
        className,
      )}
    >
      {children}
    </div>
  )
}

/**
 * Highlights sequences of 2+ consecutive UPPER CASE words (including
 * short connectors like AND, OR, A, AN, THE between them) as bold spans.
 *
 * Example: "Write ONE WORD AND/OR A NUMBER for each answer."
 *       →  "Write **ONE WORD AND/OR A NUMBER** for each answer."
 */
const SINGLE_CAPS_KEYWORDS = new Set(['TRUE', 'FALSE', 'YES', 'NO'])

/** Seeded group.instruction already lists the TFNG key — don't render it again. */
export function hasTfngKeyLegend(instruction: string): boolean {
  return /TRUE if the statement/i.test(instruction)
}

/** Seeded group.instruction already lists the YNNG key — don't render it again. */
export function hasYnngKeyLegend(instruction: string): boolean {
  return /YES if the statement/i.test(instruction)
}

export function highlightCaps(text: string): ReactNode[] {
  // Multi-word ALL-CAPS phrases, plus single IELTS keywords (TRUE/FALSE/YES/NO/…).
  const re =
    /\b([A-Z]{2,}(?:[\s/]+(?:AND|OR|A|AN|THE|[A-Z]{2,}))*(?:\/[A-Z]{2,})*)\b/g

  const parts: ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = re.exec(text)) !== null) {
    const wordCount = match[1].split(/[\s/]+/).length
    if (wordCount < 2 && !SINGLE_CAPS_KEYWORDS.has(match[1])) continue

    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    parts.push(
      <span key={match.index} className='font-bold text-foreground'>
        {match[1]}
      </span>,
    )
    lastIndex = re.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : [text]
}

/**
 * Parses simple markdown-style bold (**text**) and italic (*text*) within
 * a single string. Returns an array of ReactNodes with <strong> and <em>.
 */
function parseInlineFormatting(text: string): ReactNode[] {
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*)/g
  const parts: ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    if (match[2] != null) {
      parts.push(createElement('strong', { key: match.index }, match[2]))
    } else if (match[3] != null) {
      parts.push(createElement('em', { key: match.index }, match[3]))
    }
    lastIndex = re.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : [text]
}

/**
 * Split passage/body text into paragraphs.
 * Official IELTS copy uses blank lines; many seeds and admin pastes use a
 * single newline. Treat any run of newlines as a break.
 */
export function splitPassageParagraphs(text: string): string[] {
  return text
    .replace(/\r\n/g, '\n')
    .split(/\n+/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0)
}

/** Passage seeds use "[A]" on its own line or "[A] body…"; students see the letter only. */
export function parsePassageParagraphLabel(paragraph: string): {
  label: string | null
  body: string
} {
  const ownLine = paragraph.match(/^\[([A-Z])\]$/)
  if (ownLine) return { label: ownLine[1], body: '' }
  const inline = paragraph.match(/^\[([A-Z])\]\s+([\s\S]+)$/)
  if (inline) return { label: inline[1], body: inline[2] }
  return { label: null, body: paragraph }
}

export function formatPassageParagraphLabel(paragraph: string): string {
  const { label, body } = parsePassageParagraphLabel(paragraph)
  if (!label) return paragraph
  return body ? `${label} ${body}` : label
}

const SCREEN_LETTER_HINT_RE =
  /on screen, select the correct letter from the list/i

const SELECT_LETTER_GROUP_TYPES = new Set([
  'matching_information',
  'matching_features',
  'matching_headings',
  'map_labeling',
  'matching',
])

const CHOICE_GROUP_TYPES = new Set(['true_false_ng', 'yes_no_ng', 'mcq'])

type AdaptInstructionOptions = {
  /** Compound note/table/summary tasks with a letter word bank. */
  hasWordBank?: boolean
}

function normalizeLetterRange(raw: string): string {
  return raw.trim().replace(/\s*[-–]\s*/, '–')
}

/** One instruction line: paper "write in boxes" → on-screen select copy. */
function adaptInstructionLine(
  line: string,
  groupType: string,
  options?: AdaptInstructionOptions,
): string {
  const trimmed = line.trim()
  if (!trimmed || SCREEN_LETTER_HINT_RE.test(trimmed)) return line

  const letterInBoxes =
    /^(Write the correct letters?|Write the appropriate letters?|Choose the correct letters?),?\s+(?:\(([A-Z])\s*[-–]\s*([A-Z])\)|([A-Z](?:\s*[-–]\s*[A-Z])?))\s*,?\s+in boxes?\s+[\d\s–-]+ on your answer sheet\.?\s*$/i.exec(
      trimmed,
    )
  if (letterInBoxes && SELECT_LETTER_GROUP_TYPES.has(groupType)) {
    const range = normalizeLetterRange(
      letterInBoxes[2] && letterInBoxes[3]
        ? `${letterInBoxes[2]}–${letterInBoxes[3]}`
        : (letterInBoxes[4] ?? ''),
    )
    return range
      ? `Select the correct letter, ${range}, for each question.`
      : 'Select the correct letter for each question.'
  }

  if (
    /^Write the correct letters in boxes?\s+[\d\s–-]+ on your answer sheet\.?\s*$/i.test(
      trimmed,
    ) &&
    (options?.hasWordBank || groupType === 'compound')
  ) {
    return 'Select the correct letter from the list for each gap.'
  }

  if (
    groupType === 'matching_headings' &&
    /^(Write|Choose) the (correct|appropriate) number/i.test(trimmed) &&
    /on your answer sheet/i.test(trimmed)
  ) {
    return 'Select the correct heading for each paragraph.'
  }

  if (
    CHOICE_GROUP_TYPES.has(groupType) &&
    /^In boxes\s+[\d\s–-]+ on your answer sheet,?\s*write\s*$/i.test(trimmed)
  ) {
    return ''
  }

  if (
    CHOICE_GROUP_TYPES.has(groupType) &&
    /^In boxes\s+[\d\s–-]+ on your answer sheet,?\s*choose\s*$/i.test(trimmed)
  ) {
    return 'For each statement, choose:'
  }

  if (
    groupType === 'mcq' &&
    /^Write your answer in box\s+[\d\s–-]+ on your answer sheet\.?\s*$/i.test(
      trimmed,
    )
  ) {
    return 'Select the correct answer below.'
  }

  if (/^Write the correct letter/i.test(trimmed) && /next to Questions/i.test(trimmed)) {
    return trimmed.replace(/^Write the correct letter/i, 'Choose the correct letter')
  }

  return line
}

/**
 * Paper tests say "write in boxes on your answer sheet"; on-screen tasks use
 * dropdowns or radio buttons. Reword only the lines that mismatch the UI.
 */
export function adaptInstructionForScreen(
  instruction: string,
  groupType: string,
  options?: AdaptInstructionOptions,
): string {
  if (!instruction.trim()) return instruction

  const adapted = instruction
    .split('\n')
    .map((line) => adaptInstructionLine(line, groupType, options))

  const seenSelectFromList = new Set<string>()
  const lines: string[] = []

  for (const line of adapted) {
    const trimmed = line.trim()
    if (!trimmed) continue

    if (/select the correct letter from the list/i.test(trimmed)) {
      const key = trimmed.toLowerCase()
      if (seenSelectFromList.has(key)) continue
      seenSelectFromList.add(key)
    }

    if (
      SCREEN_LETTER_HINT_RE.test(trimmed) &&
      [...seenSelectFromList].some((k) => k.includes('select the correct letter from the list'))
    ) {
      continue
    }

    lines.push(line)
  }

  return lines.join('\n')
}

/**
 * Renders text with paragraph breaks and inline markdown (**bold**, *italic*).
 */
export function renderFormattedText(
  text: string,
  paragraphClassName = 'text-[15px] leading-[1.9] text-slate-700 tracking-[-0.01em]',
): ReactNode[] {
  const paragraphs = splitPassageParagraphs(text)
  if (paragraphs.length === 0) return []

  return paragraphs.map((para, i) => {
    const { label, body } = parsePassageParagraphLabel(para)
    const bodyText = body || (label ? '' : para)
    const children = [
      ...(label
        ? [
            createElement(
              'span',
              {
                key: 'label',
                className: 'mr-2 font-bold text-foreground',
              },
              label,
            ),
          ]
        : []),
      ...parseInlineFormatting(bodyText),
    ]
    return createElement(
      'p',
      { key: i, className: paragraphClassName },
      ...children,
    )
  })
}
