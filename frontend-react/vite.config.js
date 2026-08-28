import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API + backend routes to the FastAPI backend instance
      '/api': 'http://localhost:8100',
      '/orders': 'http://localhost:8100',
      '/approve-execution': 'http://localhost:8100',
      '/traces': 'http://localhost:8100',
      '/stream-events': {
        target: 'http://localhost:8100',
        ws: true,
      },
    },
  },
})
