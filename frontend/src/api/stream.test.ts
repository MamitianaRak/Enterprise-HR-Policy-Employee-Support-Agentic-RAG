import { http, HttpResponse } from 'msw'
import { server } from '@/test/setup'
import { CHAT_RESULT, sse } from '@/test/handlers'
import { ApiError } from './http'
import { parseSseBlock, streamChat, type StreamEvent } from './stream'

describe('parseSseBlock', () => {
  it('parses step events and validates results', () => {
    expect(parseSseBlock('event: step\ndata: {"line":"Router → KB"}')).toEqual({ event: 'step', data: { line: 'Router → KB' } })
    expect(parseSseBlock(`event: result\ndata: ${JSON.stringify(CHAT_RESULT)}`)?.event).toBe('result')
    expect(parseSseBlock('event: ping')).toBeNull()
  })

  it('rejects a result that does not match the API contract', () => {
    expect(() => parseSseBlock('event: result\ndata: {"answer": 42}')).toThrow()
  })
})

describe('streamChat', () => {
  it('emits events in order, even when chunks split an event', async () => {
    const body = sse([
      ['step', { line: 'Router → KB' }],
      ['result', CHAT_RESULT],
    ])
    server.use(
      http.post('*/api/chat/hr/stream', () => {
        const stream = new ReadableStream({
          start(controller) {
            const bytes = new TextEncoder().encode(body)
            controller.enqueue(bytes.slice(0, 10)) // split mid-event
            controller.enqueue(bytes.slice(10))
            controller.close()
          },
        })
        return new HttpResponse(stream, { headers: { 'Content-Type': 'text/event-stream' } })
      }),
    )
    const events: StreamEvent[] = []
    await streamChat('hr', { question: 'leave?', thread_id: 't1' }, (e) => events.push(e))
    expect(events.map((e) => e.event)).toEqual(['step', 'result'])
  })

  it('turns HTTP errors into ApiError with the FastAPI detail', async () => {
    server.use(http.post('*/api/chat/hr/stream', () => HttpResponse.json({ detail: 'Unknown domain: hr' }, { status: 404 })))
    await expect(streamChat('hr', { question: 'x?', thread_id: 't1' }, () => {})).rejects.toEqual(
      new ApiError(404, 'Unknown domain: hr'),
    )
  })
})
