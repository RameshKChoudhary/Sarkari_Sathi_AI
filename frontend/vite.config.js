import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the React app talks to the FastAPI backend through this proxy,
// so no CORS setup is needed. In production set VITE_API_BASE or serve both from one origin.
const target = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': { target, changeOrigin: true } } },
  preview: { port: 4173, proxy: { '/api': { target, changeOrigin: true } } },
  test: { environment: 'node' },
})
