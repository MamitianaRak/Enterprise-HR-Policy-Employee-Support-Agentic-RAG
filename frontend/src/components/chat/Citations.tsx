import { ChevronRight, ExternalLink, FileText, Globe } from 'lucide-react'
import type { Citation } from '@/api/schemas'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'

function CitationItem({ citation }: { citation: Citation }) {
  const isWeb = citation.type === 'web' && /^https?:\/\//.test(citation.url)
  const Icon = isWeb ? Globe : FileText
  return (
    <li className="rounded-lg border bg-muted/30 px-3 py-2">
      <div className="flex items-center gap-2 text-sm">
        <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        {isWeb ? (
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-w-0 items-center gap-1 font-medium hover:underline"
          >
            <span className="truncate">{citation.title}</span>
            <ExternalLink className="size-3 shrink-0" aria-hidden />
          </a>
        ) : (
          <span className="min-w-0 truncate font-medium">{citation.title}</span>
        )}
        {citation.page && (
          <span className="ml-auto shrink-0 rounded-md border px-1.5 text-xs text-muted-foreground">p. {citation.page}</span>
        )}
      </div>
      {citation.excerpt && (
        <Collapsible>
          <CollapsibleTrigger className="group mt-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
            <ChevronRight className="size-3 transition-transform group-data-[panel-open]:rotate-90" aria-hidden />
            Excerpt
          </CollapsibleTrigger>
          <CollapsibleContent>
            <blockquote className="mt-1.5 border-l-2 pl-3 text-xs leading-relaxed text-muted-foreground italic">
              {citation.excerpt}
            </blockquote>
          </CollapsibleContent>
        </Collapsible>
      )}
    </li>
  )
}

export function Citations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Sources</p>
      <ul className="space-y-1.5">
        {citations.map((c, i) => (
          <CitationItem key={`${c.title}-${c.page ?? ''}-${i}`} citation={c} />
        ))}
      </ul>
    </div>
  )
}
