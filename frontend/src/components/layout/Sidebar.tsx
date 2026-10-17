import { Plus } from 'lucide-react'
import { useNavigate } from 'react-router'
import type { DomainConfig } from '@/api/schemas'
import { DocumentsDialog } from '@/components/documents/DocumentsDialog'
import { Button } from '@/components/ui/button'
import { ConversationList } from './ConversationList'

interface Props {
  domain: DomainConfig
  activeThread?: string
  onNavigate?: () => void
}

export function Sidebar({ domain, activeThread, onNavigate }: Props) {
  const navigate = useNavigate()
  return (
    <div className="flex h-full flex-col gap-4 p-3">
      <Button
        onClick={() => {
          navigate(`/${domain.name}`)
          onNavigate?.()
        }}
        className="w-full justify-start bg-[var(--domain)] text-white hover:bg-[var(--domain)]/90"
      >
        <Plus data-icon="inline-start" /> New chat
      </Button>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <p className="mb-2 px-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">Conversations</p>
        <ConversationList domain={domain.name} activeId={activeThread} onNavigate={onNavigate} />
      </div>
      <DocumentsDialog domain={domain} />
    </div>
  )
}
