/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend origin when the frontend is hosted separately; empty for same-origin setups. */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
