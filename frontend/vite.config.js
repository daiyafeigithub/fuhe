import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/zyfh/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/zyfh/qrcodes': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/zyfh/reports': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})
