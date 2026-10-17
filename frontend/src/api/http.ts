import axios, { AxiosError } from 'axios'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** FastAPI sends `detail` as a string, or as a list of validation errors (422). */
export function detailMessage(detail: unknown, status: number): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? String(d)).join('; ')
  return status ? `Request failed (${status})` : 'Cannot reach the server. Is the backend running?'
}

export const http = axios.create({ baseURL: '/api' })

// Every failed request becomes an ApiError with a human-readable message.
http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: unknown }>) => {
    const status = error.response?.status ?? 0
    return Promise.reject(new ApiError(status, detailMessage(error.response?.data?.detail, status)))
  },
)
