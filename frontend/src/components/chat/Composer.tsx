import { ArrowUp } from 'lucide-react'
import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface Props {
  placeholder: string
  disabled: boolean
  memoryTurns: number
  onSend: (question: string) => void
}

const MIN_LENGTH = 2 // same rule as the API

export function Composer({ placeholder, disabled, memoryTurns, onSend }: Props) {
  const [value, setValue] = useState('')
  const canSend = !disabled && value.trim().length >= MIN_LENGTH

  const submit = (e?: FormEvent) => {
    e?.preventDefault()
    if (!canSend) return
    onSend(value.trim())
    setValue('')
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto w-full max-w-3xl">
      <div className="flex items-end gap-2 rounded-2xl border bg-card p-2 shadow-sm focus-within:ring-2 focus-within:ring-[var(--domain)]/30">
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          aria-label="Your question"
          maxLength={3000}
          rows={1}
          className="max-h-48 min-h-10 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0 dark:bg-transparent"
        />
        <Button
          type="submit"
          size="icon-lg"
          disabled={!canSend}
          aria-label="Send"
          className="rounded-xl bg-[var(--domain)] text-white hover:bg-[var(--domain)]/90"
        >
          <ArrowUp />
        </Button>
      </div>
      <div className="mt-1.5 flex justify-between px-1 text-xs text-muted-foreground">
        <span>{memoryTurns ? `Memory: ${memoryTurns} turn${memoryTurns > 1 ? 's' : ''}` : 'New conversation'}</span>
        <span className="hidden sm:inline">Enter to send · Shift+Enter for a new line</span>
      </div>
    </form>
  )
}
