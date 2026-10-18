import { nextStatus, parseStep } from './trace'

describe('parseStep', () => {
  it('splits title and detail and picks a tone', () => {
    expect(parseStep('KB evidence grade → GOOD')).toEqual({ title: 'KB evidence grade', detail: 'GOOD', tone: 'ok' })
    expect(parseStep('KB evidence grade → WEAK').tone).toBe('warn')
    expect(parseStep('Support check → NO_SUPPORT').tone).toBe('danger')
    expect(parseStep('Stopped → insufficient reliable evidence').tone).toBe('danger')
  })

  it('keeps arrows inside the detail', () => {
    expect(parseStep('Query rewrite → leave → policy').detail).toBe('leave → policy')
  })

  it('understands the CloudOps graded-retrieval steps', () => {
    expect(parseStep('Triage → KB · SEV2 · checkout-api').tone).toBe('info')
    expect(parseStep('Relevance grade (internal) → 2/4 relevant').tone).toBe('ok')
    expect(parseStep('Relevance grade (web) → 0/5 relevant').tone).toBe('warn')
    expect(parseStep('Internal query rewrite → checkout 502').tone).toBe('warn')
    expect(nextStatus('Triage → KB · SEV2')).toBe('Searching the knowledge base…')
    expect(nextStatus('Relevance grade (internal) → 0/4 relevant')).toBe('Refining the search…')
    expect(nextStatus('Web query → k8s crashloop')).toBe('Searching the web…')
  })

  it('separates the gateway model from the step text', () => {
    expect(parseStep('KB evidence grade → GOOD [groq:openai/gpt-oss-20b]')).toEqual({
      title: 'KB evidence grade', detail: 'GOOD', tone: 'ok', model: 'groq:openai/gpt-oss-20b',
    })
    expect(parseStep('Answer generation → PRIVATE KB [gemini:gemini-3.5-flash-lite (cached)]').model).toBe(
      'gemini:gemini-3.5-flash-lite (cached)',
    )
    expect(nextStatus('Router → KB [groq:openai/gpt-oss-20b]')).toBe('Searching the knowledge base…')
    expect(parseStep('Private KB retrieval → 4 chunks').model).toBeUndefined()
  })

  it('handles fallback markers and unknown steps', () => {
    expect(parseStep('Router → KB (fallback)')).toMatchObject({ detail: 'KB (fallback)', tone: 'info' })
    expect(parseStep('Something new').tone).toBe('muted')
  })
})

describe('nextStatus', () => {
  it('describes what the agent does after each step', () => {
    expect(nextStatus(undefined)).toBe('Starting…')
    expect(nextStatus('Router → KB')).toBe('Searching the knowledge base…')
    expect(nextStatus('KB evidence grade → WEAK')).toBe('Searching the web…')
    expect(nextStatus('Answer generation → PRIVATE KB')).toBe('Checking the answer against sources…')
  })
})
