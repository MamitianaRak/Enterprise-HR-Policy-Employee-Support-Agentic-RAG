import type { ChatMessage } from '@/hooks/use-chat'
import { SourceBadges } from './SourceBadges'
import { TraceTimeline } from './TraceTimeline'
import { TriageBadges } from './TriageBadges'

/** Right panel: how the agent reached the selected answer. */
export function Inspector({ message }: { message?: ChatMessage }) {
  const response = message?.response
  return (
    <div className="space-y-6 p-4">
      <section>
        <h2 className="text-sm font-semibold">Agent trace</h2>
        <p className="mt-1 mb-4 text-xs text-muted-foreground">Each LangGraph step behind the selected answer.</p>
        {message ? (
          <TraceTimeline steps={message.steps} running={message.status === 'streaming'} />
        ) : (
          <p className="text-sm text-muted-foreground">Ask a question to see the agent at work.</p>
        )}
      </section>

      {response && (
        <section className="space-y-3 rounded-xl border bg-muted/30 p-3 text-sm">
          <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Summary</h3>
          <SourceBadges source={response.source_used} support={response.support_status} />
          <TriageBadges triage={response.triage} />
          {response.rewritten_query && (
            <div>
              <p className="text-xs text-muted-foreground">Search query used</p>
              <p className="mt-0.5 wrap-break-word">{response.rewritten_query}</p>
            </div>
          )}
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{response.citations.length} source(s)</span>
            <span>{response.memory_turns} turn(s) in memory</span>
          </div>
        </section>
      )}
    </div>
  )
}
