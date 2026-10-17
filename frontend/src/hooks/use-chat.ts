import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { ChatResponse, Citation, MemoryTurn, SourceUsed } from '@/api/schemas'
import { streamChat } from '@/api/stream'
import { newThreadId } from '@/lib/ids'
import { queryKeys, useHistory } from './queries'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  status: 'streaming' | 'done' | 'error'
  steps: string[] // live trace lines; empty for messages restored from history
  sourceUsed?: SourceUsed
  citations: Citation[]
  response?: ChatResponse
}

let counter = 0
const messageId = () => `m${++counter}`

function fromHistory(turns: MemoryTurn[]): ChatMessage[] {
  return turns.flatMap((t) => [
    { id: messageId(), role: 'user', content: t.question, status: 'done', steps: [], citations: [] },
    {
      id: messageId(),
      role: 'assistant',
      content: t.answer,
      status: 'done',
      steps: [],
      sourceUsed: t.source_used,
      citations: t.citations,
    },
  ])
}

/**
 * Messages of one conversation: restored from the server once per thread, then extended
 * live from the streaming endpoint. `onThreadCreated` lets the caller put a new
 * conversation id in the URL when the first question of a new chat is sent.
 */
export function useChat(domain: string, threadId: string | undefined, onThreadCreated: (id: string) => void) {
  const queryClient = useQueryClient()
  const history = useHistory(domain, threadId)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const loadedFor = useRef<string | undefined>(undefined)
  const abortRef = useRef<AbortController | null>(null)

  // A different conversation was opened: drop live state; history fills it in below.
  useEffect(() => {
    if (threadId && threadId === loadedFor.current) return // the thread we just created
    abortRef.current?.abort()
    loadedFor.current = undefined
    setMessages([])
  }, [domain, threadId])

  // Restore from the server only once per thread, so live trace data is never overwritten.
  useEffect(() => {
    if (threadId && history.data && loadedFor.current !== threadId) {
      loadedFor.current = threadId
      setMessages(fromHistory(history.data))
    }
  }, [threadId, history.data])

  useEffect(() => () => abortRef.current?.abort(), [])

  const update = (id: string, patch: (m: ChatMessage) => Partial<ChatMessage>) =>
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch(m) } : m)))

  const send = useCallback(
    async (question: string) => {
      let id = threadId
      if (!id) {
        id = newThreadId()
        loadedFor.current = id
        onThreadCreated(id)
      }
      const assistantId = messageId()
      setMessages((prev) => [
        ...prev,
        { id: messageId(), role: 'user', content: question, status: 'done', steps: [], citations: [] },
        { id: assistantId, role: 'assistant', content: '', status: 'streaming', steps: [], citations: [] },
      ])

      const controller = new AbortController()
      abortRef.current = controller
      try {
        await streamChat(
          domain,
          { question, thread_id: id },
          (event) => {
            if (event.event === 'step') update(assistantId, (m) => ({ steps: [...m.steps, event.data.line] }))
            else if (event.event === 'result') {
              const r = event.data
              update(assistantId, () => ({
                content: r.answer,
                status: 'done',
                steps: r.trace,
                sourceUsed: r.source_used,
                citations: r.citations,
                response: r,
              }))
            } else if (event.event === 'error') {
              update(assistantId, () => ({ content: event.data.detail, status: 'error' }))
            }
          },
          controller.signal,
        )
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          update(assistantId, () => ({ content: (err as Error).message, status: 'error' }))
        }
      } finally {
        queryClient.invalidateQueries({ queryKey: queryKeys.conversations(domain) })
        // Next visit to this thread re-reads it from the server; the live view is kept as is.
        queryClient.invalidateQueries({ queryKey: queryKeys.history(domain, id), refetchType: 'none' })
      }
    },
    [domain, threadId, onThreadCreated, queryClient],
  )

  const busy = messages.some((m) => m.status === 'streaming')
  const loading = Boolean(threadId) && history.isLoading && messages.length === 0
  return { messages, send, busy, loading, historyError: history.error }
}
