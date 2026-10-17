import { z } from 'zod'
import { http } from './http'
import {
  conversationSchema,
  domainsResponseSchema,
  indexedDocumentSchema,
  memoryTurnSchema,
} from './schemas'

const adminHeaders = (adminKey: string) => ({ 'X-Admin-Key': adminKey })
const enc = encodeURIComponent

export const api = {
  async domains() {
    const { data } = await http.get('/domains')
    return domainsResponseSchema.parse(data)
  },

  async conversations(domain: string) {
    const { data } = await http.get(`/sessions/${domain}`)
    return z.array(conversationSchema).parse(data.sessions)
  },

  async history(domain: string, threadId: string) {
    const { data } = await http.get(`/sessions/${domain}/${enc(threadId)}`)
    return z.array(memoryTurnSchema).parse(data.turns)
  },

  async deleteConversation(domain: string, threadId: string) {
    await http.delete(`/sessions/${domain}/${enc(threadId)}`)
  },

  async documents(domain: string) {
    const { data } = await http.get(`/documents/${domain}`)
    return z.array(indexedDocumentSchema).parse(data.documents)
  },

  async uploadDocument(domain: string, file: File, adminKey: string) {
    const body = new FormData()
    body.append('file', file)
    const { data } = await http.post(`/ingest/${domain}`, body, { headers: adminHeaders(adminKey) })
    return z.object({ file: z.string(), chunks: z.number() }).parse(data)
  },

  async deleteDocument(domain: string, filename: string, adminKey: string) {
    await http.delete(`/documents/${domain}/${enc(filename)}`, { headers: adminHeaders(adminKey) })
  },
}
