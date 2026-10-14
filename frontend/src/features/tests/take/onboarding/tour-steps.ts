import type { Step } from 'react-joyride'
import {
  type LucideIcon,
  BookOpen,
  Clock,
  Compass,
  Flag,
  Hash,
  Headphones,
  HelpCircle,
  ListChecks,
  MessageCircle,
  Mic,
  PenLine,
  Play,
  Send,
  Type,
  Volume2,
} from 'lucide-react'
import type { SectionType } from '../../data/schema'

/**
 * Per-section guided tour step lists.
 *
 * Each `target` is a CSS selector pointing at a stable anchor attribute
 * (``[data-tour="…"]``). The step shows when the targeted element is on
 * screen; if the user navigates away mid-tour the step is skipped by
 * ``react-joyride``.
 *
 * ``data`` carries presentation metadata consumed by the custom glass
 * tooltip ({@link ./tour-tooltip.tsx}):
 *   - ``icon`` — a lucide glyph shown in the header badge.
 *   - ``hint`` — a short spatial cue ("Top bar", "Right panel") so a
 *     first-time student instantly knows *where* the element lives.
 *
 * Instructions are written action-first and kept to one short line — the
 * tooltip card is narrow on mobile.
 */

export type TourStepData = {
  icon?: LucideIcon
  hint?: string
}

type TourStep = Step & { data?: TourStepData }

const BASE: Pick<
  TourStep,
  'skipBeacon' | 'blockTargetInteraction' | 'placement'
> = {
  // Beacon-first mode adds an extra click; skip straight to the tooltip.
  skipBeacon: true,
  // The student should not accidentally interact with the UI while
  // reading the tip — joyride dims and locks everything underneath.
  blockTargetInteraction: true,
  placement: 'auto',
}

export const LISTENING_STEPS: TourStep[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    data: { icon: Headphones },
    title: 'Listening section',
    content:
      "You'll hear each recording once. Put your headphones on and set a comfortable volume before you begin.",
  },
  {
    ...BASE,
    target: '[data-tour="listening-audio"]',
    data: { icon: Volume2, hint: 'Top of the panel' },
    title: 'Audio player',
    content:
      'The recording starts on its own. Use these controls to pause or adjust the volume.',
  },
  {
    ...BASE,
    target: '[data-tour="listening-questions"]',
    data: { icon: ListChecks, hint: 'Main area' },
    title: 'Type your answers here',
    content:
      'Fill in each answer as you listen. Watch the word limit in the instructions — spelling counts.',
  },
  {
    ...BASE,
    target: '[data-tour="question-navigator"]',
    data: { icon: Compass, hint: 'Bottom bar' },
    title: 'Jump between questions',
    content:
      'Tap any number to go straight to that question. Numbers are grouped by audio part.',
  },
  {
    ...BASE,
    target: '[data-tour="exam-timer"]',
    data: { icon: Clock, hint: 'Top bar' },
    title: 'Time remaining',
    content:
      'You have 30 minutes. At zero, your answers submit automatically — keep moving.',
  },
  {
    ...BASE,
    target: '[data-tour="submit-test"]',
    data: { icon: Send, hint: 'Top-right' },
    title: 'Submit the section',
    content:
      "Press Submit when every answer is in. You can't come back to this section afterwards.",
  },
]

export const READING_STEPS: TourStep[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    data: { icon: BookOpen },
    title: 'Reading section',
    content:
      "Three passages, 60 minutes — about 20 minutes each. Don't get stuck on one question.",
  },
  {
    ...BASE,
    target: '[data-tour="reading-passage"]',
    data: { icon: BookOpen, hint: 'Left panel' },
    title: 'The passage',
    content:
      'Read here. Select any text to highlight it — your highlights stay while you work.',
  },
  {
    ...BASE,
    target: '[data-tour="reading-questions"]',
    data: { icon: ListChecks, hint: 'Right panel' },
    title: 'The questions',
    content:
      'Answer on the right. The two panels scroll separately, so keep the matching lines in view.',
  },
  {
    ...BASE,
    target: '[data-tour="question-navigator"]',
    data: { icon: Compass, hint: 'Bottom bar' },
    title: 'Jump between questions',
    content:
      'Tap any number to go straight to that question. Numbers are grouped by passage.',
  },
  {
    ...BASE,
    target: '[data-tour="exam-timer"]',
    data: { icon: Clock, hint: 'Top bar' },
    title: 'Time remaining',
    content:
      'The test moves on automatically when the timer hits zero. Pace yourself across all three.',
  },
  {
    ...BASE,
    target: '[data-tour="submit-test"]',
    data: { icon: Send, hint: 'Top-right' },
    title: 'Submit the section',
    content:
      "Press Submit once every answer is in. You can't come back here afterwards.",
  },
]

export const WRITING_STEPS: TourStep[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    data: { icon: PenLine },
    title: 'Writing section',
    content:
      'Two tasks in 60 minutes. Task 1 is a 150-word report; Task 2 is a 250-word essay.',
  },
  {
    ...BASE,
    target: '[data-tour="writing-prompt"]',
    data: { icon: BookOpen, hint: 'Top' },
    title: 'Read the task',
    content:
      'Read it carefully first. A couple of minutes of planning saves time later.',
  },
  {
    ...BASE,
    target: '[data-tour="writing-textarea"]',
    data: { icon: Type, hint: 'Main area' },
    title: 'Write your answer here',
    content:
      'Type your response. It saves automatically as you go — use varied vocabulary and grammar.',
  },
  {
    ...BASE,
    target: '[data-tour="writing-wordcount"]',
    data: { icon: Hash, hint: 'Below the editor' },
    title: 'Word count',
    content:
      'Stay above the minimum. Too few words lowers your band — and so does filler.',
  },
  {
    ...BASE,
    target: '[data-tour="exam-timer"]',
    data: { icon: Clock, hint: 'Top bar' },
    title: 'Time remaining',
    content: 'Aim for ~20 minutes on Task 1 and ~40 minutes on Task 2.',
  },
  {
    ...BASE,
    target: '[data-tour="submit-test"]',
    data: { icon: Send, hint: 'Top-right' },
    title: 'Submit the section',
    content: "Press Submit once both tasks are done. You can't return afterwards.",
  },
]

export const SPEAKING_STEPS: TourStep[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    data: { icon: Mic },
    title: 'Speaking section',
    content:
      'A ~15-minute conversation with James, your AI examiner. Check your mic and camera first.',
  },
  {
    ...BASE,
    target: '[data-tour="speaking-avatar"]',
    data: { icon: MessageCircle, hint: 'Main video' },
    title: 'Meet James',
    content:
      'He asks questions in three parts: a short interview, a 2-minute talk, then a discussion.',
  },
  {
    ...BASE,
    target: '[data-tour="speaking-mic"]',
    data: { icon: Mic, hint: 'Bottom bar' },
    title: 'Tap to speak',
    content:
      'Press this to answer. Speak clearly, then press again when you finish.',
  },
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    data: { icon: HelpCircle },
    title: "Didn't catch a question?",
    content:
      'Just say "Pardon?" or "Could you repeat that?" — James repeats it, and it won\'t affect your score.',
  },
  {
    ...BASE,
    target: '[data-tour="speaking-end"]',
    data: { icon: Flag, hint: 'Bottom bar' },
    title: 'End the test',
    content:
      'Press End Test after James says the test is over. Your score is ready within a minute.',
  },
]

const SPEAKING_READY_STEPS: TourStep[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    data: { icon: Mic },
    title: 'Speaking section',
    content:
      "A live conversation with James, your AI examiner. Let's check your mic before the timer starts.",
  },
  {
    ...BASE,
    target: '[data-tour="speaking-mic-check"]',
    data: { icon: Mic, hint: 'Here' },
    title: 'Check your microphone',
    content:
      'Make sure James can hear you. Take your time — the Speaking timer has not started yet.',
  },
  {
    ...BASE,
    target: '[data-tour="speaking-start"]',
    data: { icon: Play, hint: 'Here' },
    title: 'Start when ready',
    content:
      'Press Start Speaking Test when you are set. The timer begins the moment you start.',
  },
]

/**
 * The final step in a full-mock L/R/W tour.
 *
 * In a mock, submitting the whole test only happens after the final section
 * (usually Speaking). After Listening / Reading / Writing a student instead
 * clicks "Finish section" to move on, so pointing them at the Submit button
 * would mislearn the flow. Practice tests (one section) keep the Submit
 * step because Finish section isn't shown.
 */
const MOCK_FINISH_SECTION_STEP: TourStep = {
  ...BASE,
  target: '[data-tour="finish-section"]',
  data: { icon: Flag, hint: 'Top-right' },
  title: 'Finish this section',
  content:
    'Press Finish section once every answer is in — you will move on to the next section automatically.',
}

/** Swap the trailing "Submit" step for a "Finish section" one in full mock. */
function withSectionEndStep(
  baseSteps: TourStep[],
  isPractice: boolean
): TourStep[] {
  if (isPractice) return baseSteps
  return [...baseSteps.slice(0, -1), MOCK_FINISH_SECTION_STEP]
}

export function stepsForSection(
  type: SectionType,
  isDesktop = true,
  speakingReady = false,
  isPractice = true
): TourStep[] {
  switch (type) {
    case 'listening': {
      const base = isDesktop
        ? LISTENING_STEPS
        : [
            ...LISTENING_STEPS.slice(0, 2),
            {
              ...LISTENING_STEPS[2],
              target: '[data-tour="listening-questions-tab"]',
              data: { icon: ListChecks, hint: 'Questions tab' },
              content:
                'Tap Questions to open the answer area. Switch back to Audio whenever you need the recording.',
            },
            ...LISTENING_STEPS.slice(3),
          ]
      return withSectionEndStep(base, isPractice)
    }
    case 'reading': {
      const base = isDesktop
        ? READING_STEPS
        : [
            ...READING_STEPS.slice(0, 2),
            {
              ...READING_STEPS[2],
              target: '[data-tour="reading-questions-tab"]',
              data: { icon: ListChecks, hint: 'Questions tab' },
              content:
                'Tap Questions to switch from the passage to your answers. Tap Passage to go back.',
            },
            ...READING_STEPS.slice(3),
          ]
      return withSectionEndStep(base, isPractice)
    }
    case 'writing':
      return withSectionEndStep(WRITING_STEPS, isPractice)
    case 'speaking':
      return speakingReady ? SPEAKING_READY_STEPS : SPEAKING_STEPS
    default:
      return []
  }
}

/**
 * Bumped whenever the step list for any section changes meaningfully.
 * Older "seen" flags in localStorage carry a version suffix and become
 * stale on bump — students will see the refreshed tour once more.
 */
export const TOUR_VERSION = 12
