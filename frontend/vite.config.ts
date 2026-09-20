import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://wwqxl2uzid.execute-api.us-east-1.amazonaws.com/prod',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
