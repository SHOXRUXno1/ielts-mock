import type { Step } from 'react-joyride'
import type { SectionType } from '../../data/schema'

/**
 * Per-section guided tour step lists.
 *
 * Each `target` is a CSS selector pointing at a stable anchor attribute
 * (``[data-tour="…"]``). The step shows when the targeted element is on
 * screen; if the user navigates away mid-tour the step is skipped by
 * ``react-joyride``.
 *
 * Tips are written for a first-time IELTS mock-test student. Keep lines
 * short — the tooltip card is narrow on mobile.
 */

const BASE: Pick<Step, 'skipBeacon' | 'blockTargetInteraction' | 'placement'> = {
  // Beacon-first mode adds an extra click; skip straight to the tooltip.
  skipBeacon: true,
  // The student should not accidentally interact with the UI while
  // reading the tip — joyride dims and locks everything underneath.
  blockTargetInteraction: true,
  placement: 'auto',
}

export const LISTENING_STEPS: Step[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    title: 'Listening section',
    content:
      "You'll hear each recording once. Make sure your headphones are on and the volume is comfortable before you begin.",
  },
  {
    ...BASE,
    target: '[data-tour="listening-audio"]',
    title: 'Audio player',
    content:
      'The recording starts automatically for each part. You can pause or adjust the volume with these controls.',
  },
  {
    ...BASE,
    target: '[data-tour="listening-questions"]',
    title: 'Answer the questions',
    content:
      'Type your answers here as you listen. Spelling and grammar count — read instructions carefully for word limits.',
  },
  {
    ...BASE,
    target: '[data-tour="exam-timer"]',
    title: 'Section timer',
    content:
      "You have 30 minutes. When the timer runs out, your answers are submitted automatically — don't wait too long on one question.",
  },
  {
    ...BASE,
    target: '[data-tour="submit-test"]',
    title: 'Submit when done',
    content:
      "Click Submit after you've answered every question. You can't come back to this section once it's submitted.",
  },
]

export const READING_STEPS: Step[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    title: 'Reading section',
    content:
      'You will read three passages and answer the questions after each one. 60 minutes total — pace yourself.',
  },
  {
    ...BASE,
    target: '[data-tour="reading-passage"]',
    title: 'The passage',
    content:
      "Read on the left panel. You can select text to highlight important parts — it stays highlighted while you work on the section.",
  },
  {
    ...BASE,
    target: '[data-tour="reading-questions"]',
    title: 'Questions',
    content:
      "Answer on the right. The two panels scroll independently — keep the relevant paragraph in view while you answer.",
  },
  {
    ...BASE,
    target: '[data-tour="exam-timer"]',
    title: 'Section timer',
    content:
      'Aim for about 20 minutes per passage. The test moves on automatically when the timer hits zero.',
  },
  {
    ...BASE,
    target: '[data-tour="submit-test"]',
    title: 'Submit when done',
    content:
      "Click Submit after you've answered every question. You can't come back to this section once it's submitted.",
  },
]

export const WRITING_STEPS: Step[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    title: 'Writing section',
    content:
      'Two tasks in 60 minutes. Task 1 is a short report (150 words). Task 2 is a longer essay (250 words).',
  },
  {
    ...BASE,
    target: '[data-tour="writing-prompt"]',
    title: 'Read the task',
    content:
      'Read the task carefully before you start. Plan what you want to say — a few minutes of planning saves time later.',
  },
  {
    ...BASE,
    target: '[data-tour="writing-textarea"]',
    title: 'Write your response here',
    content:
      'Use varied vocabulary and grammar. Your answer is saved automatically as you type.',
  },
  {
    ...BASE,
    target: '[data-tour="writing-wordcount"]',
    title: 'Word count',
    content:
      "Stay above the minimum. Writing less than the required words will lower your band — but filler text will too.",
  },
  {
    ...BASE,
    target: '[data-tour="exam-timer"]',
    title: 'Section timer',
    content:
      'Give yourself ~20 minutes for Task 1 and ~40 minutes for Task 2. Watch the timer.',
  },
  {
    ...BASE,
    target: '[data-tour="submit-test"]',
    title: 'Submit when done',
    content:
      "Click Submit once both tasks are complete. You can't return to this section.",
  },
]

export const SPEAKING_STEPS: Step[] = [
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    title: 'Speaking section',
    content:
      "You will have a 15-minute conversation with James, an AI examiner. Make sure your microphone and camera work before you start.",
  },
  {
    ...BASE,
    target: '[data-tour="speaking-avatar"]',
    title: 'Meet James',
    content:
      "James will ask you questions in three parts: a short interview, a 2-minute talk from a cue card, then a longer discussion.",
  },
  {
    ...BASE,
    target: '[data-tour="speaking-mic"]',
    title: 'Tap to speak',
    content:
      "Click this button when you're ready to answer. Speak clearly. Tap again when you finish your answer.",
  },
  {
    ...BASE,
    target: 'body',
    placement: 'center',
    title: "Didn't catch a question?",
    content:
      "Just say \"Pardon?\" or \"Could you repeat that?\" and James will repeat the question. This doesn't affect your score.",
  },
  {
    ...BASE,
    target: '[data-tour="speaking-end"]',
    title: 'End the test',
    content:
      "Click End Test once James has thanked you and told you the test is over. Your Speaking score will be ready in a minute.",
  },
]

export function stepsForSection(type: SectionType): Step[] {
  switch (type) {
    case 'listening':
      return LISTENING_STEPS
    case 'reading':
      return READING_STEPS
    case 'writing':
      return WRITING_STEPS
    case 'speaking':
      return SPEAKING_STEPS
    default:
      return []
  }
}

/**
 * Bumped whenever the step list for any section changes meaningfully.
 * Older "seen" flags in localStorage carry a version suffix and become
 * stale on bump — students will see the refreshed tour once more.
 */
export const TOUR_VERSION = 1
