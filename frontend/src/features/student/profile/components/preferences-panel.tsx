import { fonts } from '@/config/fonts'
import { useFont } from '@/context/font-provider'
import { useTheme } from '@/context/theme-provider'
import { Panel, PanelBody, PanelHeader, PanelTitle } from '@/components/report'
import { ENTER } from '@/features/results/lib/motion'
import { ChoiceGroup, type Choice } from './choice-group'

const THEME_OPTIONS = [
  { value: 'system', label: 'System' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
] as const satisfies readonly Choice<'system' | 'light' | 'dark'>[]

const FONT_OPTIONS = fonts.map((name) => ({
  value: name,
  label: name.charAt(0).toUpperCase() + name.slice(1),
}))

export function PreferencesPanel() {
  const { theme, setTheme } = useTheme()
  const { font, setFont } = useFont()

  return (
    <Panel className={ENTER}>
      <PanelHeader>
        <PanelTitle>Preferences</PanelTitle>
      </PanelHeader>
      <PanelBody className='space-y-5'>
        <ChoiceGroup
          label='Appearance'
          value={theme}
          options={THEME_OPTIONS}
          onChange={setTheme}
        />
        <ChoiceGroup
          label='Typeface'
          value={font}
          options={FONT_OPTIONS}
          onChange={setFont}
        />
      </PanelBody>
    </Panel>
  )
}
