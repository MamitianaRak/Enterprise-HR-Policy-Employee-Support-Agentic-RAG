import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { TooltipProvider } from '@/components/ui/tooltip'
import { createQueryClient } from '@/app/query-client'
import { routes } from '@/app/routes'
import { server } from '@/test/setup'
import { sse } from '@/test/handlers'

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(
    <QueryClientProvider client={createQueryClient()}>
      <TooltipProvider>
        <RouterProvider router={router} />
      </TooltipProvider>
    </QueryClientProvider>,
  )
  return router
}

describe('ChatPage', () => {
  it('redirects to the default domain and shows its welcome screen', async () => {
    const router = renderAt('/')
    expect(await screen.findByRole('heading', { name: 'HR Policy & Employee Support' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/hr')
    expect(screen.getByRole('button', { name: /How many annual leave days/ })).toBeInTheDocument()
  })

  it('lists previous conversations of the domain', async () => {
    renderAt('/hr')
    const link = await screen.findByRole('link', { name: /Remote work policy\?/ })
    expect(link).toHaveAttribute('href', '/hr/c/old-1')
  })

  it('streams an answer with sources, verification badge and trace', async () => {
    const user = userEvent.setup()
    const router = renderAt('/hr')
    const input = await screen.findByRole('textbox', { name: 'Your question' })

    await user.type(input, 'How many leave days?{Enter}')

    expect(await screen.findByText('20 days')).toBeInTheDocument() // Markdown bold rendered
    expect(screen.getByText('How many leave days?')).toBeInTheDocument()
    expect(screen.getAllByText('Company knowledge base').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Verified against sources').length).toBeGreaterThan(0)
    expect(screen.getByText('company_hr_handbook.md')).toBeInTheDocument()
    // The new conversation got its own URL.
    expect(router.state.location.pathname).toMatch(/^\/hr\/c\/[A-Za-z0-9_-]+$/)
    // Trace steps are shown in the inspector.
    const trace = screen.getAllByRole('list').find((l) => within(l).queryByText('Router'))
    expect(trace).toBeDefined()
  })

  it('shows a readable error when the agent fails', async () => {
    server.use(
      http.post('*/api/chat/hr/stream', () =>
        new HttpResponse(sse([['error', { status: 503, detail: 'The AI service is busy.' }]]), {
          headers: { 'Content-Type': 'text/event-stream' },
        }),
      ),
    )
    const user = userEvent.setup()
    renderAt('/hr')
    await user.type(await screen.findByRole('textbox', { name: 'Your question' }), 'Hello there{Enter}')
    expect(await screen.findByRole('alert')).toHaveTextContent('The AI service is busy.')
  })

  it('shows an error screen when the backend is down', async () => {
    server.use(http.get('*/api/domains', () => HttpResponse.error()))
    renderAt('/')
    expect(await screen.findByText('Cannot reach the backend', {}, { timeout: 4000 })).toBeInTheDocument()
  })
})
