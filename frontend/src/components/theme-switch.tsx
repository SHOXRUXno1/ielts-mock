import { useEffect } from 'react'
import { Check, Moon, Sun } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/context/theme-provider'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type ThemeSwitchProps = {
  studentSurface?: boolean
}

export function ThemeSwitch({ studentSurface = false }: ThemeSwitchProps) {
  const { theme, resolvedTheme, setTheme } = useTheme()

  /* Update theme-color meta tag
   * when theme is updated */
  useEffect(() => {
    const themeColor =
      resolvedTheme === 'dark'
        ? studentSurface
          ? '#191919'
          : '#020817'
        : '#fff'
    const metaThemeColor = document.querySelector("meta[name='theme-color']")
    if (metaThemeColor) metaThemeColor.setAttribute('content', themeColor)
  }, [studentSurface, resolvedTheme])

  // Student surface: no "System" — just a one-click toggle between
  // light and dark. If the student lands with theme="system" (default
  // from the cookie), the first click resolves to the opposite of
  // whatever their OS was giving them, which matches what they'd expect.
  if (studentSurface) {
    const isDark = resolvedTheme === 'dark'
    return (
      <Button
        variant='ghost'
        size='icon'
        className='scale-95 rounded-full'
        aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
        onClick={() => setTheme(isDark ? 'light' : 'dark')}
      >
        <Sun className='size-[1.2rem] scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90' />
        <Moon className='absolute size-[1.2rem] scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0' />
      </Button>
    )
  }

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button variant='ghost' size='icon' className='scale-95 rounded-full'>
          <Sun className='size-[1.2rem] scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90' />
          <Moon className='absolute size-[1.2rem] scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0' />
          <span className='sr-only'>Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align='end'>
        <DropdownMenuItem onClick={() => setTheme('light')}>
          Light{' '}
          <Check
            size={14}
            className={cn('ms-auto', theme !== 'light' && 'hidden')}
          />
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          Dark
          <Check
            size={14}
            className={cn('ms-auto', theme !== 'dark' && 'hidden')}
          />
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          System
          <Check
            size={14}
            className={cn('ms-auto', theme !== 'system' && 'hidden')}
          />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
