import { useEffect, useState } from 'react'
import { useAppStore } from '@/stores/app-store'

const darkQuery = () => window.matchMedia?.('(prefers-color-scheme: dark)')

/** Applies the chosen theme to <html class="dark"> and follows the OS when set to "system". */
export function useApplyTheme() {
  const theme = useAppStore((s) => s.theme)
  const [systemDark, setSystemDark] = useState(() => darkQuery()?.matches ?? false)

  useEffect(() => {
    const query = darkQuery()
    if (!query) return
    const onChange = (e: MediaQueryListEvent) => setSystemDark(e.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])

  const dark = theme === 'dark' || (theme === 'system' && systemDark)
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])
  return dark
}
