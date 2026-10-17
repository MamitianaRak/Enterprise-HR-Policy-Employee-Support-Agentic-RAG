import { useParams } from 'react-router'
import { useDomains } from './queries'

/** The domain and conversation selected in the URL: /:domain/c/:threadId */
export function useCurrentDomain() {
  const { domain: domainName, threadId } = useParams()
  const { data } = useDomains()
  const domain = data?.domains.find((d) => d.name === domainName)
  return { domains: data?.domains ?? [], domain, domainName: domainName ?? '', threadId }
}
