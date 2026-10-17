# Enterprise Copilot — Frontend

React 19 + TypeScript single-page app for the Agentic RAG backend in `../app`. See the [main README](../README.md) for the full project.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Dev server on http://localhost:5173, `/api` proxied to the backend |
| `npm run build` | Type-check and build to `dist/` |
| `npm test` | Vitest + Testing Library, API mocked with MSW |
| `npm run typecheck` | TypeScript only |
| `npm run lint` | oxlint |

Copy `.env.example` to `.env` to point the dev proxy at another backend (`API_PROXY_TARGET`).

## How it fits together

- **`api/`**: axios client with error normalisation, Zod schemas for every response, and `streamChat()`, which reads the Server-Sent Events of `/api/chat/{domain}/stream` with `fetch`.
- **`hooks/`**: TanStack Query hooks for conversations, history and documents. `useChat` merges a conversation's stored history with live streamed steps.
- **`routes/`**: the URL is the source of truth for the domain and the conversation (`/:domain/c/:threadId`).
- **`stores/`**: Zustand for UI preferences (theme, mobile drawers). Only the theme is persisted.
- **`components/ui/`**: shadcn/ui components (Base UI). The domain accent colour is the `--domain` CSS variable.

Domains, their labels, examples and colour come from `GET /api/domains`, so adding a backend domain adds a tab without frontend changes.
