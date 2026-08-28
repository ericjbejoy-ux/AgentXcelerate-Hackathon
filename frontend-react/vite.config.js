import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8101',
      '/orders': 'http://127.0.0.1:8101',
      '/approve-execution': 'http://127.0.0.1:8101',
      '/traces': 'http://127.0.0.1:8101',
      '/stream-events': {
        target: 'http://127.0.0.1:8101',
        ws: true,
      },
    },
  },
})
