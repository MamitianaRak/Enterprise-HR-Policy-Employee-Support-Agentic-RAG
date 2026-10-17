import { useEffect, useRef } from 'react'
import type { DomainConfig } from '@/api/schemas'
import { Skeleton } from '@/components/ui/skeleton'
import type { ChatMessage } from '@/hooks/use-chat'
import { Composer } from './Composer'
import { MessageItem } from './MessageItem'
import { Welcome } from './Welcome'

interface Props {
  domain: DomainConfig
  messages: ChatMessage[]
  loading: boolean
  busy: boolean
  selectedId?: string
  onSelect: (id: string) => void
  onSend: (question: string) => void
}

export function ChatView({ domain, messages, loading, busy, selectedId, onSelect, onSend }: Props) {
  const endRef = useRef<HTMLDivElement>(null)
  const lastSteps = messages.at(-1)?.steps.length

  // Keep the newest message and the live status in view.
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [messages.length, lastSteps])

  const memoryTurns = messages.filter((m) => m.role === 'assistant' && m.status === 'done').length

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading ? (
          <div className="mx-auto max-w-3xl space-y-4 p-6">
            <Skeleton className="ml-auto h-10 w-2/3 rounded-2xl" />
            <Skeleton className="h-28 w-full rounded-2xl" />
          </div>
        ) : messages.length === 0 ? (
          <Welcome domain={domain} onPick={onSend} />
        ) : (
          <div className="mx-auto max-w-3xl space-y-5 px-4 py-6">
            {messages.map((m) => (
              <MessageItem
                key={m.id}
                message={m}
                webWarning={domain.web_warning}
                selected={m.id === selectedId}
                onShowTrace={() => onSelect(m.id)}
              />
            ))}
            <div ref={endRef} />
          </div>
        )}
      </div>
      <div className="border-t bg-background/80 px-4 pt-3 pb-4 backdrop-blur">
        <Composer placeholder={domain.placeholder} disabled={busy || loading} memoryTurns={memoryTurns} onSend={onSend} />
      </div>
    </div>
  )
}
