import { Server, Siren, Tag } from 'lucide-react'
import type { Triage } from '@/api/schemas'
import { toneBadge } from '@/lib/tones'
import type { StepTone } from '@/lib/trace'
import { cn } from '@/lib/utils'

const SEVERITY_TONE: Record<Exclude<Triage['severity'], 'none'>, StepTone> = {
  SEV1: 'danger',
  SEV2: 'warn',
  SEV3: 'info',
  SEV4: 'muted',
}

const pill = 'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium'

/** Incident assessment from the CloudOps triage step. Renders nothing for non-incidents. */
export function TriageBadges({ triage }: { triage?: Triage | null }) {
  if (!triage || (triage.severity === 'none' && !triage.service)) return null
  return (
    <div className="flex flex-wrap gap-1.5" aria-label="Incident triage">
      {triage.severity !== 'none' && (
        <span className={cn(pill, toneBadge[SEVERITY_TONE[triage.severity]])} title="Estimated severity">
          <Siren className="size-3" aria-hidden />
          {triage.severity}
        </span>
      )}
      {triage.service && (
        <span className={cn(pill, toneBadge.muted, 'font-mono')} title="Affected service">
          <Server className="size-3" aria-hidden />
          {triage.service}
        </span>
      )}
      {triage.category && triage.category !== 'other' && (
        <span className={cn(pill, toneBadge.muted)} title="Category">
          <Tag className="size-3" aria-hidden />
          {triage.category}
        </span>
      )}
    </div>
  )
}
