import { ArrowRight, Sparkles } from 'lucide-react'
import type { DomainConfig } from '@/api/schemas'

export function Welcome({ domain, onPick }: { domain: DomainConfig; onPick: (question: string) => void }) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-12 text-center sm:py-20">
      <div className="mb-5 flex size-12 items-center justify-center rounded-2xl bg-(--domain)/15 text-(--domain)">
        <Sparkles className="size-6" aria-hidden />
      </div>
      <h1 className="text-2xl font-semibold tracking-tight text-balance sm:text-3xl">{domain.title}</h1>
      <p className="mt-3 text-sm text-pretty text-muted-foreground sm:text-base">{domain.tagline}</p>
      <div className="mt-8 grid w-full gap-2 sm:grid-cols-2">
        {domain.examples.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => onPick(example)}
            className="group flex items-center justify-between gap-3 rounded-xl border bg-card px-4 py-3 text-left text-sm shadow-xs transition-colors hover:border-(--domain)/40 hover:bg-(--domain)/5"
          >
            <span>{example}</span>
            <ArrowRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" aria-hidden />
          </button>
        ))}
      </div>
    </div>
  )
}
