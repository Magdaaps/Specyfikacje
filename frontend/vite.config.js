import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/produkty': 'http://localhost:8000',
      '/surowce': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
    }
  }
})
