/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  // Read frontend/.env (all keys, not only VITE_*): API_PROXY_TARGET is used by the dev
  // server only and is never exposed to the browser bundle.
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.API_PROXY_TARGET || 'http://127.0.0.1:8080'

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    build: {
      rolldownOptions: {
        output: {
          // Libraries change less often than app code: separate chunks stay cached across deploys.
          codeSplitting: {
            groups: [
              { name: 'react', test: /node_modules[\\/](react|react-dom|react-router|scheduler)[\\/]/ },
              { name: 'ui', test: /node_modules[\\/](@base-ui|@floating-ui|lucide-react|sonner)[\\/]/ },
              { name: 'markdown', test: /node_modules[\\/](react-markdown|remark-.*|micromark.*|mdast-.*|hast-.*|unified|unist-.*|vfile.*)[\\/]/ },
              { name: 'data', test: /node_modules[\\/](@tanstack|axios|zod|zustand)[\\/]/ },
            ],
          },
        },
      },
    },
    server: {
      port: 5173,
      // In development, /api is proxied to FastAPI so the browser sees a single origin.
      proxy: { '/api': { target: apiTarget, changeOrigin: true } },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test/setup.ts'],
      css: false,
    },
  }
})
