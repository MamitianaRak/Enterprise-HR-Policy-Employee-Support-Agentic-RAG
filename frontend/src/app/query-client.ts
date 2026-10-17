import { QueryClient } from '@tanstack/react-query'

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      // Refetching on focus would replace a live conversation with its stored copy.
      queries: { refetchOnWindowFocus: false, retry: 1 },
    },
  })
}
