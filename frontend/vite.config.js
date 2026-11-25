import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const target = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  base: '/Sarkari_Sathi_AI/',   // 👈 add this line only
  server: { port: 5173, proxy: { '/api': { target, changeOrigin: true } } },
  preview: { port: 4173, proxy: { '/api': { target, changeOrigin: true } } },
  test: { environment: 'node' },
})
