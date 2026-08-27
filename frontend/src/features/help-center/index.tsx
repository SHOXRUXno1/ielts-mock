import { useState } from 'react'
import { ChevronDown, BookOpen, FileSpreadsheet, BarChart3, Mic, Settings } from 'lucide-react'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { Separator } from '@/components/ui/separator'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const sections = [
  {
    id: 'getting-started',
    icon: BookOpen,
    title: 'Getting Started',
    items: [
      {
        q: 'How do I create a new test?',
        a: 'Go to Tests → click "New Test" in the top-right corner. Fill in the title, description, and type (Academic / General). The test is saved as a draft (unpublished) by default.',
      },
      {
        q: 'How do I add sections to a test?',
        a: 'Open the test detail page (click the test title). Each test supports up to four sections: Listening, Reading, Writing, and Speaking. Click the section card to expand it and fill in the required fields such as duration and audio URL.',
      },
      {
        q: 'How do I add questions to a section?',
        a: 'Inside a section, click "Add Question". Choose the question type (Multiple Choice, Fill-in-the-blank, Short Answer, Essay, etc.), enter the prompt and answer key, then save.',
      },
      {
        q: 'How do I publish a test so students can take it?',
        a: 'From the Tests list, find the test and toggle the "Published" switch, or open the test and click "Edit" → enable "Published" → save.',
      },
      {
        q: 'Can I preview a test before publishing?',
        a: 'Yes. On the test detail page, click "Preview Test" to open the student-facing test-taking view in a new tab.',
      },
    ],
  },
  {
    id: 'excel-import',
    icon: FileSpreadsheet,
    title: 'Excel Import',
    items: [
      {
        q: 'Where do I download the Excel template?',
        a: 'Go to Tests → click "Import from Excel" → then click "Download Template". The template includes all required sheets: Test Info, Reading 1–3, Writing, and Listening 1–4 with instructions in each column header.',
      },
      {
        q: 'What sheets does the template contain?',
        a: 'The template has six sheets: "Test Info" (title, type, description), "Reading 1", "Reading 2", "Reading 3" (passage + questions), "Writing" (tasks), and "Listening 1–4" (questions + answer key).',
      },
      {
        q: 'How do I upload audio files for Listening sections?',
        a: 'After confirming the import, the page shows a section for each Listening part. Upload the corresponding MP3 file for each part individually using the file pickers provided.',
      },
      {
        q: 'What happens if my Excel file has errors?',
        a: 'The preview step validates the file and lists all errors and warnings before anything is saved. Errors must be fixed in Excel and re-uploaded; warnings are non-blocking and will not prevent import.',
      },
    ],
  },
  {
    id: 'results',
    icon: BarChart3,
    title: 'Results & Scoring',
    items: [
      {
        q: 'Where do I see student results?',
        a: 'Open the Results page from the sidebar. Each row shows the student name, test title, date, overall band score, and status (Pending / Completed / Scored).',
      },
      {
        q: 'What does the "Pending" status mean?',
        a: '"Pending" means the AI evaluator has not yet finished grading the submission. The page auto-refreshes until the score is ready. This usually takes under a minute.',
      },
      {
        q: 'Can I manually override a band score?',
        a: 'Yes. Open the result detail page and find the "Manual Override" field next to any section. Enter your band score and click "Save Override".',
      },
      {
        q: 'How is the overall band score calculated?',
        a: 'The overall band is the official four-skill IELTS average, rounded to the nearest 0.5. A skipped section counts as 0. A manual override on any section directly affects the overall score.',
      },
    ],
  },
  {
    id: 'speaking',
    icon: Mic,
    title: 'AI Speaking Examiner',
    items: [
      {
        q: 'How do I start a speaking session?',
        a: 'Go to AI Examiner from the sidebar. Allow microphone access when prompted. Click "Start Session", then speak naturally — the AI will ask IELTS-style questions and respond in real time.',
      },
      {
        q: 'How does the AI score the speaking response?',
        a: 'At the end of the session the AI analyzes fluency, coherence, lexical resource, and grammatical range, then assigns a band score (0–9) with written feedback for each criterion.',
      },
      {
        q: 'What microphone setup is recommended?',
        a: 'Any standard headset or laptop microphone works. For best accuracy, speak in a quiet environment and keep the microphone 15–20 cm from your mouth.',
      },
    ],
  },
  {
    id: 'account',
    icon: Settings,
    title: 'Account & Settings',
    items: [
      {
        q: 'How do I change my display name?',
        a: 'Go to Settings → Account. In the "Display Name" field enter a new name and click "Update Name". The name updates immediately in the top-right profile dropdown.',
      },
      {
        q: 'How do I change my password?',
        a: 'Go to Settings → Account → scroll to "Change Password". Enter your current password, then the new password twice, and click "Change Password". You will need to use the new password on your next login.',
      },
      {
        q: 'How do I switch the UI theme?',
        a: 'Go to Settings → Appearance. Choose Light, Dark, or System theme and select a font. Changes apply immediately without a page reload.',
      },
    ],
  },
]

// ---------------------------------------------------------------------------
// FAQ Item
// ---------------------------------------------------------------------------

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className='flex w-full items-start justify-between gap-4 py-3 text-left text-sm font-medium hover:text-foreground/80 transition-colors'>
        <span>{q}</span>
        <ChevronDown
          size={16}
          className={cn(
            'mt-0.5 shrink-0 text-muted-foreground transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </CollapsibleTrigger>
      <CollapsibleContent className='pb-3 text-sm text-muted-foreground leading-relaxed'>
        {a}
      </CollapsibleContent>
    </Collapsible>
  )
}

// ---------------------------------------------------------------------------
// Section Card
// ---------------------------------------------------------------------------

function SectionCard({
  icon: Icon,
  title,
  items,
}: {
  icon: React.ElementType
  title: string
  items: { q: string; a: string }[]
}) {
  return (
    <div className='rounded-xl border bg-card p-6'>
      <div className='mb-4 flex items-center gap-2.5'>
        <div className='flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10'>
          <Icon size={16} className='text-primary' />
        </div>
        <h2 className='font-semibold'>{title}</h2>
      </div>
      <div className='divide-y'>
        {items.map((item) => (
          <FaqItem key={item.q} {...item} />
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function HelpCenter() {
  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='space-y-0.5 mb-4'>
          <h1 className='text-2xl font-bold tracking-tight md:text-3xl'>Help Center</h1>
          <p className='text-muted-foreground'>
            Frequently asked questions and guides for using the IELTS Mock admin panel.
          </p>
        </div>
        <Separator className='mb-6' />

        <div className='grid gap-4 md:grid-cols-2'>
          {sections.map((s) => (
            <SectionCard key={s.id} icon={s.icon} title={s.title} items={s.items} />
          ))}
        </div>
      </Main>
    </>
  )
}
