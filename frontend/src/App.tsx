import { QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense, useState } from 'react'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { createQueryClient } from '@/app/query-client'
import { routes } from '@/app/routes'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useApplyTheme } from '@/hooks/use-theme'

const router = createBrowserRouter(routes)

// Loaded only in development, so it never ships in the production bundle.
const ReactQueryDevtools = import.meta.env.DEV
  ? lazy(() => import('@tanstack/react-query-devtools').then((m) => ({ default: m.ReactQueryDevtools })))
  : () => null

export default function App() {
  const [queryClient] = useState(createQueryClient)
  useApplyTheme()
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <RouterProvider router={router} />
        <Toaster position="top-right" richColors />
      </TooltipProvider>
      <Suspense>
        <ReactQueryDevtools buttonPosition="bottom-right" />
      </Suspense>
    </QueryClientProvider>
  )
}
