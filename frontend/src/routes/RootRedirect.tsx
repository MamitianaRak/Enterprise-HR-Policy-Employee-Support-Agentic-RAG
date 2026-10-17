import { Loader2, ServerCrash } from 'lucide-react'
import { Navigate } from 'react-router'
import { Button } from '@/components/ui/button'
import { useDomains } from '@/hooks/queries'

/** "/" sends the user to the default domain once the backend has told us which one it is. */
export function RootRedirect() {
  const { data, error, refetch, isFetching } = useDomains()

  if (data) return <Navigate to={`/${data.default}`} replace />

  return (
    <div className="flex h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
      {error ? (
        <>
          <ServerCrash className="size-10 text-muted-foreground" aria-hidden />
          <div>
            <h1 className="text-lg font-semibold">Cannot reach the backend</h1>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">{error.message}</p>
          </div>
          <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
            Try again
          </Button>
        </>
      ) : (
        <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
      )}
    </div>
  )
}
