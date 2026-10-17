import type { CSSProperties, ReactNode } from 'react'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { useAppStore } from '@/stores/app-store'

interface Props {
  accent: string
  header: ReactNode
  sidebar: (closeDrawer: () => void) => ReactNode
  inspector: ReactNode
  children: ReactNode
}

/**
 * Three columns on wide screens (conversations · chat · agent trace).
 * Below md the conversations, and below xl the trace, move into slide-over drawers.
 */
export function AppShell({ accent, header, sidebar, inspector, children }: Props) {
  const { sidebarOpen, inspectorOpen, setSidebarOpen, setInspectorOpen } = useAppStore()

  return (
    <div className="flex h-dvh flex-col bg-background" style={{ '--domain': accent } as CSSProperties}>
      {header}
      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-72 shrink-0 border-r bg-sidebar md:block">{sidebar(() => {})}</aside>
        <main className="min-w-0 flex-1">{children}</main>
        <aside className="hidden w-80 shrink-0 overflow-y-auto border-l bg-sidebar xl:block">{inspector}</aside>
      </div>

      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="w-80 p-0 pt-10" style={{ '--domain': accent } as CSSProperties}>
          <SheetTitle className="sr-only">Conversations</SheetTitle>
          {sidebar(() => setSidebarOpen(false))}
        </SheetContent>
      </Sheet>
      <Sheet open={inspectorOpen} onOpenChange={setInspectorOpen}>
        <SheetContent side="right" className="w-80 overflow-y-auto p-0 pt-8" style={{ '--domain': accent } as CSSProperties}>
          <SheetTitle className="sr-only">Agent trace</SheetTitle>
          {inspector}
        </SheetContent>
      </Sheet>
    </div>
  )
}
