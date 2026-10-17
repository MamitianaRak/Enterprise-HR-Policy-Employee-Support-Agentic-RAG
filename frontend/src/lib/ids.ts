/** Conversation ids accepted by the API: [A-Za-z0-9_-]{3,120}. */
export function newThreadId(): string {
  const id = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}${Math.random().toString(16).slice(2)}`
  return id.replace(/[^A-Za-z0-9_-]/g, '')
}

export function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
}
