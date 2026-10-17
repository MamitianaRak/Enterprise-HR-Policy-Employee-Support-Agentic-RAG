// Turns raw trace lines from the LangGraph workflow ("Router → KB") into display steps.

export type StepTone = 'info' | 'ok' | 'warn' | 'danger' | 'muted'

export interface TraceStep {
  title: string
  detail: string
  tone: StepTone
}

const RULES: Array<[RegExp, (detail: string) => StepTone]> = [
  [/^memory/i, () => 'muted'],
  [/^router/i, () => 'info'],
  [/^triage/i, () => 'info'],
  [/retrieval/i, () => 'info'],
  [/evidence grade/i, (d) => (d.startsWith('GOOD') ? 'ok' : 'warn')],
  [/^relevance grade/i, (d) => (d.startsWith('0/') ? 'warn' : 'ok')],
  [/^web (fallback|search|query)/i, () => 'warn'],
  [/query rewrite/i, () => 'warn'],
  [/^answer generation/i, () => 'ok'],
  [/^support check/i, (d) => (d.startsWith('FULLY') ? 'ok' : d.startsWith('PARTIALLY') ? 'warn' : 'danger')],
  [/^revised answer/i, () => 'warn'],
  [/^usefulness check/i, (d) => (d.startsWith('USEFUL') ? 'ok' : 'danger')],
  [/^direct response/i, () => 'info'],
  [/^stopped/i, () => 'danger'],
]

export function parseStep(line: string): TraceStep {
  const [title, ...rest] = line.split(' → ')
  const detail = rest.join(' → ')
  const rule = RULES.find(([re]) => re.test(title))
  return { title, detail, tone: rule ? rule[1](detail) : 'muted' }
}

/** What the agent is doing next, shown in the "thinking" bubble after a step completes. */
export function nextStatus(line: string | undefined): string {
  if (!line) return 'Starting…'
  const { title, detail } = parseStep(line)
  if (/^memory/i.test(title)) return /saved/i.test(detail) ? 'Done' : 'Routing the question…'
  if (/^router/i.test(title) || /^triage/i.test(title)) {
    return detail.startsWith('KB') ? 'Searching the knowledge base…' : 'Replying…'
  }
  if (/retrieval/i.test(title)) return 'Grading the evidence…'
  if (/^relevance grade/i.test(title)) return detail.startsWith('0/') ? 'Refining the search…' : 'Writing the answer…'
  if (/^internal query rewrite/i.test(title)) return 'Searching the knowledge base again…'
  if (/^web query/i.test(title)) return 'Searching the web…'
  if (/^web search/i.test(title)) return 'Grading web results…'
  if (/kb evidence grade/i.test(title)) return detail === 'GOOD' ? 'Writing the answer…' : 'Searching the web…'
  if (/^web fallback/i.test(title)) return 'Grading web results…'
  if (/web evidence grade/i.test(title)) return detail === 'GOOD' ? 'Writing the answer…' : 'Retrying…'
  if (/^query rewrite/i.test(title)) return 'Searching again with a better query…'
  if (/^answer generation/i.test(title) || /^revised/i.test(title)) return 'Checking the answer against sources…'
  if (/^support check/i.test(title)) return 'Checking the answer is useful…'
  return 'Finishing…'
}
