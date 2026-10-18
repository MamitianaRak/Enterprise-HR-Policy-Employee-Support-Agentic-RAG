import { Cpu, Loader2 } from 'lucide-react'
import { toneDot } from '@/lib/tones'
import { parseStep } from '@/lib/trace'
import { cn } from '@/lib/utils'

/** The LangGraph decision path, one dot per node. The last step pulses while the agent runs. */
export function TraceTimeline({ steps, running }: { steps: string[]; running: boolean }) {
  if (!steps.length && !running) {
    return <p className="text-sm text-muted-foreground">No trace for this message.</p>
  }
  return (
    <ol className="relative space-y-3 border-l border-border pl-5" aria-live="polite">
      {steps.map((line, i) => {
        const step = parseStep(line)
        return (
          <li key={`${i}-${line}`} className="relative">
            <span
              className={cn('absolute top-1.5 -left-[25px] size-2.5 rounded-full ring-4 ring-background', toneDot[step.tone])}
              aria-hidden
            />
            <p className="text-sm leading-tight font-medium">{step.title}</p>
            {step.detail && <p className="mt-0.5 text-xs wrap-break-word text-muted-foreground">{step.detail}</p>}
            {step.model && (
              <p className="mt-1 inline-flex max-w-full items-center gap-1 rounded-md border bg-muted/50 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground" title="Model that served this step (LLM gateway)">
                <Cpu className="size-3 shrink-0" aria-hidden />
                <span className="truncate">{step.model}</span>
              </p>
            )}
          </li>
        )
      })}
      {running && (
        <li className="relative">
          <Loader2 className="absolute top-0.5 -left-[27px] size-3.5 animate-spin text-muted-foreground" aria-hidden />
          <p className="text-sm text-muted-foreground">Running…</p>
        </li>
      )}
    </ol>
  )
}
