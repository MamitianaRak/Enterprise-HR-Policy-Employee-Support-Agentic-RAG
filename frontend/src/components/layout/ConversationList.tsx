import { MessageSquare, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import type { Conversation } from '@/api/schemas'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useConversations, useDeleteConversation } from '@/hooks/queries'
import { formatDate } from '@/lib/ids'
import { cn } from '@/lib/utils'

interface Props {
  domain: string
  activeId?: string
  onNavigate?: () => void
}

export function ConversationList({ domain, activeId, onNavigate }: Props) {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useConversations(domain)
  const remove = useDeleteConversation(domain)
  const [pending, setPending] = useState<Conversation | null>(null)

  const confirmDelete = () => {
    if (!pending) return
    remove.mutate(pending.thread_id, {
      onSuccess: () => {
        if (pending.thread_id === activeId) navigate(`/${domain}`)
      },
    })
    setPending(null)
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-14 w-full rounded-xl" />
        ))}
      </div>
    )
  }
  if (isError) return <p className="text-sm text-destructive">Could not load conversations.</p>
  if (!data?.length) return <p className="px-1 text-sm text-muted-foreground">No conversation yet.</p>

  return (
    <>
      <ul className="space-y-1.5">
        {data.map((c) => {
          const active = c.thread_id === activeId
          return (
            <li key={c.thread_id} className="group relative">
              <Link
                to={`/${domain}/c/${c.thread_id}`}
                onClick={onNavigate}
                aria-current={active ? 'page' : undefined}
                title={c.title}
                className={cn(
                  'flex items-start gap-2.5 rounded-xl border px-3 py-2.5 pr-9 transition-colors',
                  active
                    ? 'border-[var(--domain)]/50 bg-[var(--domain)]/10'
                    : 'border-transparent hover:border-border hover:bg-muted/60',
                )}
              >
                <MessageSquare className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{c.title}</span>
                  <span className="block text-xs text-muted-foreground">
                    {formatDate(c.updated_at)} · {c.turns} msg
                  </span>
                </span>
              </Link>
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => setPending(c)}
                aria-label={`Delete conversation "${c.title}"`}
                className="absolute top-2.5 right-2 opacity-0 group-focus-within:opacity-100 group-hover:opacity-100 hover:text-destructive"
              >
                <Trash2 />
              </Button>
            </li>
          )
        })}
      </ul>

      <AlertDialog open={pending !== null} onOpenChange={(open) => !open && setPending(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              “{pending?.title}” and the agent's memory of it will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={confirmDelete}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
