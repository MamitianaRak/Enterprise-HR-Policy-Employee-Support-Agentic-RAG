import { Monitor, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useAppStore, type Theme } from '@/stores/app-store'

const NEXT: Record<Theme, Theme> = { light: 'dark', dark: 'system', system: 'light' }
const ICON = { light: Sun, dark: Moon, system: Monitor }
const LABEL = { light: 'Light theme', dark: 'Dark theme', system: 'System theme' }

export function ThemeToggle() {
  const theme = useAppStore((s) => s.theme)
  const setTheme = useAppStore((s) => s.setTheme)
  const Icon = ICON[theme]
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button variant="ghost" size="icon" onClick={() => setTheme(NEXT[theme])} aria-label={`${LABEL[theme]} (click to change)`} />
        }
      >
        <Icon />
      </TooltipTrigger>
      <TooltipContent side="bottom">{LABEL[theme]}</TooltipContent>
    </Tooltip>
  )
}
