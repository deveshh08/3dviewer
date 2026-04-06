import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api':    'http://localhost:8000',
      '/static': 'http://localhost:8000',
    },
    fs: {
      strict: false,
    },
  },
  build: {
    chunkSizeWarningLimit: 2000,
  }
})
