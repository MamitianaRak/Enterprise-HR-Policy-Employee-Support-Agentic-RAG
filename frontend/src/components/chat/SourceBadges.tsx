import { BadgeCheck, Building2, CircleHelp, Globe, MessageCircle, ShieldAlert } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { SourceUsed, SupportStatus } from '@/api/schemas'
import { toneBadge } from '@/lib/tones'
import type { StepTone } from '@/lib/trace'
import { cn } from '@/lib/utils'

const SOURCES: Record<SourceUsed, { label: string; tone: StepTone; icon: LucideIcon }> = {
  private_kb: { label: 'Company knowledge base', tone: 'ok', icon: Building2 },
  web_search: { label: 'External web', tone: 'warn', icon: Globe },
  direct: { label: 'General reply', tone: 'info', icon: MessageCircle },
  insufficient_evidence: { label: 'Not enough evidence', tone: 'muted', icon: CircleHelp },
}

const SUPPORT: Partial<Record<SupportStatus, { label: string; tone: StepTone; icon: LucideIcon }>> = {
  fully_supported: { label: 'Verified against sources', tone: 'ok', icon: BadgeCheck },
  partially_supported: { label: 'Partially verified', tone: 'warn', icon: ShieldAlert },
}

function Pill({ label, tone, icon: Icon }: { label: string; tone: StepTone; icon: LucideIcon }) {
  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium', toneBadge[tone])}>
      <Icon className="size-3" aria-hidden />
      {label}
    </span>
  )
}

export function SourceBadges({ source, support }: { source?: SourceUsed; support?: SupportStatus }) {
  if (!source) return null
  const verified = support ? SUPPORT[support] : undefined
  return (
    <div className="flex flex-wrap gap-1.5">
      <Pill {...SOURCES[source]} />
      {verified && <Pill {...verified} />}
    </div>
  )
}
